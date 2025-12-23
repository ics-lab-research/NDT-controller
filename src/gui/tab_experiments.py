from pathlib import Path
from typing import Generator, List, Tuple

import gradio as gr
from loguru import logger

from ..agents.experiment_execution import execute_multiple_plans
from ..agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ..core.models import (
    ChatHistory,
    ExperimentExecutionError,
    ExperimentPlan,
    ExperimentsMetadata,
    ExperimentStatus,
    Mode,
)
from ..core.project_manager import ProjectManager
from .experiment_table_utils import (
    update_experiment_details,
    convert_plan_to_table_data,
    save_experiment_changes,
)


def update_scan_status(
    plans_path: Path | None, log: bool = False
) -> gr.Dataframe:
    if not plans_path:
        return gr.Dataframe(value=[])
    try:
        plans = load_experiment_plans(plans_path, log=log)
        filenames = [plan.filename for plan in plans]
        statuses = _get_experiment_statuses(plans)
        return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])
    except Exception as e:
        if log:
            logger.error(f"Error updating scan status: {e}")
        return gr.Dataframe(value=[])


def _get_experiment_statuses(
    plans: List[ExperimentPlan],
) -> List[str]:
    return [plan.status.value for plan in plans]


def approve_all_plans(
    plans: List[ExperimentPlan], plans_path: Path | None
) -> gr.Dataframe:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return gr.Dataframe(value=[])
    for plan in plans:
        if plan.status == ExperimentStatus.NOT_APPROVED:
            plan.status = ExperimentStatus.APPROVED
    try:
        save_experiment_plans(plans, plans_path)
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        gr.Info(error_msg)
    filenames = [plan.filename for plan in plans]
    statuses = _get_experiment_statuses(plans)
    return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])


def start_all_approved_plans(
    plans: List[ExperimentPlan], plans_path: Path | None
) -> gr.Dataframe:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return gr.Dataframe(value=[])
    for plan in plans:
        if plan.status == ExperimentStatus.APPROVED:
            plan.status = ExperimentStatus.PENDING
    try:
        save_experiment_plans(plans, plans_path)
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        gr.Info(error_msg)
    filenames = [plan.filename for plan in plans]
    statuses = _get_experiment_statuses(plans)
    return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])


def reload_plans(
    plans_path: Path | None,
) -> Tuple[gr.Dropdown, gr.Dataframe, List[ExperimentPlan]]:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), []
    try:
        plans = load_experiment_plans(plans_path, log=True)
        filenames = [plan.filename for plan in plans]
        initial_data = convert_plan_to_table_data(plans[0]) if plans else []
        gr.Info("Successfully reloaded experiment plans")
        return (
            gr.Dropdown(
                choices=filenames, value=filenames[0] if filenames else None
            ),
            gr.Dataframe(value=initial_data),
            plans,
        )
    except Exception as e:
        error_msg = f"Error reloading plans: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg)
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), []


def start_execution(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    current_chatbot: ChatHistory,
    project_manager: ProjectManager,
) -> Generator[Tuple[gr.Dataframe, ChatHistory], None, None]:
    if not plans_path:
        yield (
            gr.Dataframe(value=[]),
            current_chatbot
            + [
                {
                    "role": "assistant",
                    "content": "Error: Plans path not configured",
                }
            ],
        )
        return
    approved_plans = [p for p in plans if p.status == ExperimentStatus.APPROVED]
    if not approved_plans:
        yield (
            update_scan_status(plans_path),
            current_chatbot
            + [{"role": "assistant", "content": "No approved plans to start"}],
        )
        return
    # Set to PENDING
    for plan in approved_plans:
        plan.status = ExperimentStatus.PENDING
    try:
        save_experiment_plans(plans, plans_path)
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        yield (
            update_scan_status(plans_path),
            current_chatbot + [{"role": "assistant", "content": error_msg}],
        )
        return
    # Execute all plans (dummy)
    for i in range(5):
        current_chatbot = current_chatbot + [
            {"role": "assistant", "content": f"Dummy message {i}"}
        ]
        yield update_scan_status(plans_path), current_chatbot


def start_execution2(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    current_chatbot: ChatHistory,
    project_manager: ProjectManager,
) -> Generator[Tuple[gr.Dataframe, ChatHistory], None, None]:
    if not plans_path:
        yield (
            gr.Dataframe(value=[]),
            current_chatbot
            + [
                {
                    "role": "assistant",
                    "content": "Error: Plans path not configured",
                }
            ],
        )
        return
    approved_plans = [p for p in plans if p.status == ExperimentStatus.APPROVED]
    if not approved_plans:
        yield (
            update_scan_status(plans_path),
            current_chatbot
            + [{"role": "assistant", "content": "No approved plans to start"}],
        )
        return
    # Set to PENDING
    for plan in approved_plans:
        plan.status = ExperimentStatus.PENDING
    try:
        save_experiment_plans(plans, plans_path)
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        yield (
            update_scan_status(plans_path),
            current_chatbot + [{"role": "assistant", "content": error_msg}],
        )
        return
    # Execute all plans
    try:
        for msg in execute_multiple_plans(plans, project_manager):
            current_chatbot = current_chatbot + [
                {"role": "assistant", "content": str(msg)}
            ]
            yield update_scan_status(plans_path), current_chatbot
    except ExperimentExecutionError as e:
        current_chatbot = current_chatbot + [
            {
                "role": "assistant",
                "content": f"Execution error: {e.error_message}",
            }
        ]
        yield update_scan_status(plans_path), current_chatbot
    except Exception as e:
        current_chatbot = current_chatbot + [
            {"role": "assistant", "content": f"Error during execution: {e}"}
        ]
        yield update_scan_status(plans_path), current_chatbot


def create_experiments_tab(
    project_manager: ProjectManager,
    chatbot: gr.Chatbot,
) -> gr.Tabs:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans = []
    plans_path = None
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path, log=True)
    filenames = [plan.filename for plan in plans]
    initial_data = convert_plan_to_table_data(plans[0]) if plans else []
    plans_state = gr.State(plans)
    statuses = _get_experiment_statuses(plans)
    plans_path_state = gr.State(plans_path)
    log_state = gr.State(False)
    project_manager_state = gr.State(project_manager)

    with gr.Tabs() as interface:
        with gr.TabItem("Plans Viewer"):
            dropdown = gr.Dropdown(
                choices=filenames,
                label="Select Experiment",
                value=filenames[0] if filenames else None,
            )
            details_df = gr.Dataframe(
                headers=["Tool Name", "Parameter 1", "Parameter 2"],
                value=initial_data,
                interactive=True,
            )
            with gr.Row():
                save_button = gr.Button("Save Changes")
                reload_button = gr.Button("Reload Plans")
            dropdown.change(
                lambda filename, current_plans: update_experiment_details(
                    current_plans, filename
                ),
                inputs=[dropdown, plans_state],
                outputs=details_df,
            )
            save_button.click(
                lambda filename, data, current_plans: save_experiment_changes(
                    current_plans, plans_path, filename, data
                ),
                inputs=[dropdown, details_df, plans_state],
                outputs=[],
            )
            reload_button.click(
                lambda: reload_plans(plans_path),
                inputs=[],
                outputs=[dropdown, details_df, plans_state],
            )
        with gr.TabItem("Scan Status"):
            status_df = gr.Dataframe(
                headers=["Experiment Name", "Status"],
                value=[[f, s] for f, s in zip(filenames, statuses)],
                interactive=False,
            )

            with gr.Row():
                approve_button = gr.Button("Approve all plans")
                start_button = gr.Button("Start scan")

            # link to logic
            approve_button.click(
                lambda plans, plans_path, current_chatbot: (
                    approve_all_plans(plans, plans_path),
                    current_chatbot
                    + [{"role": "assistant", "content": "All plans approved"}],
                ),
                inputs=[plans_state, plans_path_state, chatbot],
                outputs=[status_df, chatbot],
            )

            start_button.click(
                start_execution2,
                inputs=[
                    plans_state,
                    plans_path_state,
                    chatbot,
                    project_manager_state,
                ],
                outputs=[status_df, chatbot],
            )

            timer = gr.Timer(1)
            timer.tick(
                update_scan_status,
                inputs=[plans_path_state, log_state],
                outputs=status_df,
            )

    return interface
