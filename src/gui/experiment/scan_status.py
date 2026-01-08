from pathlib import Path
from typing import Any, Generator, List, Tuple

import gradio as gr
from loguru import logger

from ...agents.experiment_execution import execute_multiple_plans
from ...agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ...core.models import (
    ChatHistory,
    ExperimentPlan,
    ExperimentStatus,
    MessageType,
)
from ...core.project_manager import ProjectManager
from ..chat_utils import create_message


def get_experiment_statuses(
    plans: List[ExperimentPlan],
) -> List[str]:
    return [plan.status.value for plan in plans]


def update_scan_status(plans_path: Path, log: bool = False) -> gr.Dataframe:
    if not plans_path:
        return gr.Dataframe(value=[])
    try:
        if log:
            logger.debug("Loading experiment plans for scan status update")
        plans = load_experiment_plans(plans_path, log=log)
        filenames = [plan.filename for plan in plans]
        statuses = get_experiment_statuses(plans)
        return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])
    except Exception as e:
        if log:
            logger.error(f"Error updating scan status: {e}")
        return gr.Dataframe(value=[])


def delete_all_experiments(plans_path: Path) -> gr.Dataframe:
    try:
        plans = load_experiment_plans(plans_path)
        plans.clear()
        logger.debug("Saving empty plans after deleting all experiments")
        save_experiment_plans(plans, plans_path)
        gr.Info(
            "All experiments deleted successfully", duration=1, title="✅ Info"
        )
        return gr.Dataframe(value=[])
    except Exception as e:
        error_msg = f"Error deleting all experiments: {e}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return gr.Dataframe(value=[])


def _yield_error(
    plans_path: Path,
    current_chatbot: ChatHistory,
    error_message: str,
) -> Generator[Tuple[gr.Dataframe, ChatHistory], None, None]:
    """Yields error state with updated chatbot history."""
    updated_chatbot = current_chatbot + [
        create_message(content=error_message, message_type=MessageType.STATUS)
    ]
    yield update_scan_status(plans_path), updated_chatbot


def _load_plans_safely(
    plans_path: Path,
) -> Tuple[List[ExperimentPlan] | None, str | None]:
    """Loads experiment plans and returns plans or error message."""
    try:
        logger.debug("Loading experiment plans to prepare for execution")
        plans = load_experiment_plans(plans_path, log=False)
        return plans, None
    except Exception as e:
        error_msg = f"Error loading plans: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def _get_runnable_plans(
    plans: List[ExperimentPlan],
) -> List[ExperimentPlan]:
    """Filters plans that can be executed."""
    if plans is None:
        return []
    runnable_statuses = ExperimentStatus.get_initial_runnable_statuses()
    return [p for p in plans if p.status in runnable_statuses]


def _set_plans_to_pending(
    plans: List[ExperimentPlan],
    plans_to_run: List[ExperimentPlan],
    plans_path: Path,
) -> str | None:
    """Sets runnable plans to pending status and saves. Returns error if any."""
    if plans is None:
        return "Plans is None"
    for plan in plans_to_run:
        plan.status = ExperimentStatus.PENDING
    try:
        logger.debug(
            "Saving plans after setting runnable plans to pending status"
        )
        save_experiment_plans(plans, plans_path)
        return None
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        return error_msg


def _update_chatbot_with_message(
    current_chatbot: ChatHistory,
    message: str,
    status_index: int | None,
) -> Tuple[ChatHistory, int]:
    """Updates chatbot with execution message and returns updated chatbot and index."""
    if status_index is None:
        updated_chatbot = current_chatbot + [
            create_message(content=message, message_type=MessageType.STATUS)
        ]
        return updated_chatbot, len(updated_chatbot) - 1
    else:
        current_chatbot[status_index]["content"] = message
        return current_chatbot, status_index


def _handle_execution_error(
    current_chatbot: ChatHistory,
    status_index: int | None,
    error: Any,
) -> ChatHistory:
    """Handles execution error and returns updated chatbot."""
    if not error:
        return current_chatbot

    error_message = f"Execution error: {error.error_message}"
    if status_index is None:
        return current_chatbot + [
            create_message(
                content=error_message, message_type=MessageType.STATUS
            )
        ]
    else:
        current_chatbot[status_index]["content"] = error_message
        return current_chatbot


def start_execution(
    plans_path: Path,
    current_chatbot: ChatHistory,
    project_manager: ProjectManager,
) -> Generator[Tuple[gr.Dataframe, ChatHistory], None, None]:
    """Executes experiment plans and yields progress updates."""
    if not plans_path:
        yield from _yield_error(
            plans_path, current_chatbot, "Error: Plans path not configured"
        )
        return

    plans, error_msg = _load_plans_safely(plans_path)
    if error_msg:
        yield from _yield_error(plans_path, current_chatbot, error_msg)
        return

    plans_to_run = _get_runnable_plans(plans)
    if not plans_to_run:
        yield from _yield_error(
            plans_path, current_chatbot, "No experiments available to run"
        )
        return

    error_msg = _set_plans_to_pending(plans, plans_to_run, plans_path)
    if error_msg:
        yield from _yield_error(plans_path, current_chatbot, error_msg)
        return

    execution_gen = execute_multiple_plans(plans_path, project_manager)
    status_index = None

    try:
        for message in execution_gen:
            current_chatbot, status_index = _update_chatbot_with_message(
                current_chatbot, message, status_index
            )
            yield update_scan_status(plans_path), current_chatbot
    except StopIteration as e:
        current_chatbot = _handle_execution_error(
            current_chatbot, status_index, e.value
        )
        yield update_scan_status(plans_path), current_chatbot
