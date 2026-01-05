from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple

import gradio as gr
import pandas as pd
from loguru import logger

from ..agents.experiment_execution import execute_multiple_plans
from ..agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ..baml_client.types import (
    ConnectToViTool,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
    StopViTool,
    WaitForOperationCompleteTool,
)
from ..core.models import (
    ChatHistory,
    ExperimentPlan,
    ExperimentStatus,
    ExperimentStep,
    ExperimentTool,
    MessageType,
)
from ..core.project_manager import ProjectManager
from .chat_utils import create_message

tool_map = {
    "ConnectToViTool": ConnectToViTool,
    "HandleSaveDialogTool": HandleSaveDialogTool,
    "PressButtonTool": PressButtonTool,
    "RunOpenViTool": RunOpenViTool,
    "SelectComboBoxTool": SelectComboBoxTool,
    "SelectTabTool": SelectTabTool,
    "SetButtonStateTool": SetButtonStateTool,
    "SetNumericControlTool": SetNumericControlTool,
    "StopViTool": StopViTool,
    "WaitForOperationCompleteTool": WaitForOperationCompleteTool,
}

tool_name_map: Dict[str, str] = {
    "ConnectToViTool": "connect_to_vi",
    "HandleSaveDialogTool": "handle_save_dialog",
    "PressButtonTool": "press_button",
    "RunOpenViTool": "run_open_vi",
    "SelectComboBoxTool": "select_combo_box",
    "SelectTabTool": "select_tab",
    "SetButtonStateTool": "set_button_state",
    "SetNumericControlTool": "set_numeric_control",
    "StopViTool": "stop_vi",
    "WaitForOperationCompleteTool": "wait_for_operation_complete",
}


def _tool_to_table_row(tool: ExperimentTool) -> List[str]:
    """Converts an experiment tool into a list of strings for table display."""
    tool_name = type(tool).__name__
    params = {k: v for k, v in vars(tool).items() if k != "tool_name"}
    param_list = [
        f"{k}={v.value if isinstance(v, Enum) else str(v)}"
        for k, v in params.items()
    ]
    param1 = param_list[0] if param_list else ""
    param2 = param_list[1] if len(param_list) > 1 else ""
    return [tool_name, param1, param2]


def convert_plan_to_table_data(plan: ExperimentPlan) -> List[List[str]]:
    """Converts an experiment plan into a list of table data rows."""
    rows = []
    for step in plan.experiment:
        tool_sequence = step.tool_sequence
        for i, tool in enumerate(tool_sequence):
            row = _tool_to_table_row(tool)
            if row:
                step_name = step.step_name if i == 0 else ""
                rows.append([step_name] + row)
    return rows


def convert_table_data_to_experiment_steps(
    table_data: pd.DataFrame,
) -> List[ExperimentStep]:
    """Converts table data back into a list of experiment steps."""
    steps: List[ExperimentStep] = []
    current_step_name: str | None = None
    current_tools: List[ExperimentTool] = []
    for _, row in table_data.iterrows():
        if len(row) < 4:
            continue  # Skip invalid rows
        step_name: str = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        tool_name: str = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
        param1: str = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
        param2: str = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""

        if step_name:
            if current_step_name:
                steps.append(
                    ExperimentStep(
                        step_name=current_step_name, tool_sequence=current_tools
                    )
                )
            current_step_name = step_name
            current_tools = []
        # Parse parameters
        params: Dict[str, Any] = {}
        for param in [param1, param2]:
            if param:
                try:
                    key: str
                    value: Any
                    key, value = param.split("=", 1)
                    # Attempt to convert to int if possible, otherwise keep as str
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    params[key] = value
                except ValueError:
                    continue  # Skip malformed params
        # Add tool_name if available
        if tool_name in tool_name_map:
            params["tool_name"] = tool_name_map[tool_name]
        # Instantiate tool
        tool_class: Any | None = tool_map.get(tool_name)
        if tool_class:
            try:
                tool: ExperimentTool = tool_class(**params)
                current_tools.append(tool)
            except Exception:
                logger.warning(
                    f"Failed to instantiate {tool_name} with params {params}"
                )
    if current_step_name:
        steps.append(
            ExperimentStep(
                step_name=current_step_name, tool_sequence=current_tools
            )
        )
    return steps


def update_experiment_details(
    plans: List[ExperimentPlan], selected_id: str
) -> List[List[str]]:
    """Updates and returns table data for the selected experiment plan."""
    if not selected_id:
        return []
    plan = next((p for p in plans if p.id == selected_id), None)
    if not plan:
        logger.warning(f"Plan not found for id: {selected_id}")
        return [["Error", "", ""]]
    return convert_plan_to_table_data(plan)


def save_experiment_changes(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_id: str,
    table_data: pd.DataFrame,
) -> List[ExperimentPlan]:
    """Saves changes to the selected experiment plan from table data."""
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="⚠️ Warning")
        return plans
    try:
        steps = convert_table_data_to_experiment_steps(table_data)
        plan = next((p for p in plans if p.id == selected_id), None)
        if not plan:
            gr.Info("Error: Plan not found", title="⚠️ Warning")
            return plans
        plan.experiment = steps
        save_experiment_plans(plans, plans_path)
        gr.Info(
            "Experiment changes saved successfully", duration=1, title="✅ Info"
        )
        return plans
    except Exception as e:
        error_msg = f"Error saving changes: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return plans


def get_experiment_status(plans: List[ExperimentPlan], selected_id: str) -> str:
    """Gets the status value for the selected experiment."""
    plan = next((p for p in plans if p.id == selected_id), None)
    return plan.status.value if plan else ""


def update_scan_status(
    plans_path: Path | None, log: bool = False
) -> gr.Dataframe:
    if not plans_path:
        return gr.Dataframe(value=[])
    try:
        plans = load_experiment_plans(plans_path, log=log)
        filenames = [plan.filename for plan in plans]
        statuses = get_experiment_statuses(plans)
        return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])
    except Exception as e:
        if log:
            logger.error(f"Error updating scan status: {e}")
        return gr.Dataframe(value=[])


def get_experiment_statuses(
    plans: List[ExperimentPlan],
) -> List[str]:
    return [plan.status.value for plan in plans]


def approve_all_plans(
    plans: List[ExperimentPlan], plans_path: Path | None
) -> gr.Dataframe:
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="⚠️ Warning")
        return gr.Dataframe(value=[])
    for plan in plans:
        if plan.status == ExperimentStatus.NOT_APPROVED:
            plan.status = ExperimentStatus.APPROVED
    try:
        save_experiment_plans(plans, plans_path)
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
    filenames = [plan.filename for plan in plans]
    statuses = get_experiment_statuses(plans)
    return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])


def reload_plans(
    plans_path: Path | None,
) -> Tuple[gr.Dropdown, gr.Dataframe, str, List[ExperimentPlan]]:
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="⚠️ Warning")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []
    try:
        plans = load_experiment_plans(plans_path, log=True)
        filenames = [plan.filename for plan in plans]
        ids = [plan.id for plan in plans]
        initial_data = convert_plan_to_table_data(plans[0]) if plans else []
        initial_status = plans[0].status.value if plans else ""
        gr.Info(
            "Successfully reloaded experiment plans",
            duration=1,
            title="✅ Info",
        )
        return (
            gr.Dropdown(
                choices=[(f, i) for f, i in zip(filenames, ids)],
                value=ids[0] if ids else None,
            ),
            gr.Dataframe(value=initial_data),
            initial_status,
            plans,
        )
    except Exception as e:
        error_msg = f"Error reloading plans: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []


def delete_experiment(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_id: str,
) -> Tuple[gr.Dropdown, gr.Dataframe, str, List[ExperimentPlan]]:
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="⚠️ Warning")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []
    try:
        # Find and remove the plan
        plans = [p for p in plans if p.id != selected_id]
        save_experiment_plans(plans, plans_path)
        filenames = [plan.filename for plan in plans]
        ids = [plan.id for plan in plans]
        initial_data = convert_plan_to_table_data(plans[0]) if plans else []
        initial_status = plans[0].status.value if plans else ""
        gr.Info("Experiment deleted successfully", duration=1, title="✅ Info")
        return (
            gr.Dropdown(
                choices=[(f, i) for f, i in zip(filenames, ids)],
                value=ids[0] if ids else None,
            ),
            gr.Dataframe(value=initial_data),
            initial_status,
            plans,
        )
    except Exception as e:
        error_msg = f"Error deleting experiment: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []


def update_experiment_status(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_id: str,
    new_status: str,
) -> List[ExperimentPlan]:
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="❌ Error")
        return plans
    try:
        for plan in plans:
            if plan.id == selected_id:
                plan.status = ExperimentStatus(new_status)
                break
        save_experiment_plans(plans, plans_path)
        gr.Info(
            "Experiment status updated successfully",
            duration=1,
            title="✅ Info",
        )
        return plans
    except Exception as e:
        error_msg = f"Error updating experiment status: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return plans


def delete_all_experiments(
    plans: List[ExperimentPlan], plans_path: Path | None
) -> gr.Dataframe:
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="⚠️ Warning")
        return gr.Dataframe(value=[])
    try:
        plans.clear()
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
                create_message(
                    content="Error: Plans path not configured",
                    message_type=MessageType.STATUS,
                )
            ],
        )
        return
    runnable_statuses = [
        ExperimentStatus.APPROVED,
        ExperimentStatus.PENDING,
        ExperimentStatus.ERROR,
        ExperimentStatus.SCANNING,
    ]
    if not any(plan.status in runnable_statuses for plan in plans):
        yield (
            gr.Dataframe(value=[]),
            current_chatbot
            + [
                create_message(
                    content="No experiments available to run",
                    message_type=MessageType.STATUS,
                )
            ],
        )
        return
    plans_to_run = [
        p
        for p in plans
        if p.status in [ExperimentStatus.APPROVED, ExperimentStatus.SCANNING]
    ]
    if plans_to_run:
        # Set to PENDING
        for plan in plans_to_run:
            plan.status = ExperimentStatus.PENDING
        try:
            save_experiment_plans(plans, plans_path)
        except Exception as e:
            error_msg = f"Error saving plans: {e}"
            logger.error(error_msg)
            yield (
                update_scan_status(plans_path),
                current_chatbot
                + [
                    create_message(
                        content=error_msg, message_type=MessageType.STATUS
                    )
                ],
            )
            return

    # Execute all plans
    execution_gen = execute_multiple_plans(plans, project_manager)
    status_index = None
    try:
        for message in execution_gen:
            if status_index is None:
                current_chatbot = current_chatbot + [
                    create_message(
                        content=message, message_type=MessageType.STATUS
                    )
                ]
                status_index = len(current_chatbot) - 1
            else:
                current_chatbot[status_index]["content"] = message
            yield update_scan_status(plans_path), current_chatbot
    except StopIteration as e:
        error = e.value
        if error:
            if status_index is None:
                current_chatbot = current_chatbot + [
                    create_message(
                        content=f"Execution error: {error.error_message}",
                        message_type=MessageType.STATUS,
                    )
                ]
            else:
                current_chatbot[status_index]["content"] = (
                    f"Execution error: {error.error_message}"
                )
            yield update_scan_status(plans_path), current_chatbot
