from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr
import pandas as pd
from loguru import logger

from ...agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ...baml_client.types import (
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
from ...core.models import (
    ExperimentStatus,
    ExperimentStep,
    ExperimentTool,
)
from .experiment_utils import convert_plan_to_table_data

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


def get_experiment_details(
    plans_path: Path, selected_id: str
) -> List[List[str]]:
    """Updates and returns table data for the selected experiment plan."""
    if not selected_id:
        return []
    logger.debug(
        f"Loading experiment plans from {plans_path} for selected_id: {selected_id}"
    )
    plans = load_experiment_plans(plans_path)
    plan = next((p for p in plans if p.id == selected_id), None)
    if not plan:
        logger.warning(f"Plan not found for id: {selected_id}")
        gr.Info(
            "Plan not found. Please press 'Reload Plans' button.",
            title="⚠️ Warning",
        )
        return []
    return convert_plan_to_table_data(plan)


def _convert_table_data_to_experiment_steps(
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
                logger.error(
                    f"Failed to instantiate {tool_name} with params {params}"
                )
    if current_step_name:
        steps.append(
            ExperimentStep(
                step_name=current_step_name, tool_sequence=current_tools
            )
        )
    return steps


def save_experiment_changes(
    plans_path: Path,
    selected_id: str,
    table_data: pd.DataFrame,
):
    """Saves changes to the selected experiment plan from table data."""
    try:
        logger.debug("Loading experiment plans to save changes")
        plans = load_experiment_plans(plans_path)
        steps = _convert_table_data_to_experiment_steps(table_data)
        plan = next((p for p in plans if p.id == selected_id), None)
        if not plan:
            gr.Info(
                "Plan not found. Please press 'Reload Plans' button.",
                title="⚠️ Warning",
            )
            return
        plan.experiment = steps
        logger.debug("Saving experiment changes from GUI dataframe")
        save_experiment_plans(plans, plans_path)
        gr.Info(
            "Experiment changes saved successfully", duration=1, title="✅ Info"
        )
    except Exception as e:
        error_msg = f"Error saving changes: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")


def update_experiment_status(
    plans_path: Path,
    selected_id: str,
    new_status: str,
):
    try:
        logger.debug("Loading experiment plans to update status")
        plans = load_experiment_plans(plans_path)
        if not any(plan.id == selected_id for plan in plans):
            gr.Info(
                "Plan not found. Please press 'Reload Plans' button.",
                title="⚠️ Warning",
            )
            return
        for plan in plans:
            if plan.id == selected_id:
                plan.status = ExperimentStatus(new_status)
                break
        logger.debug("Saving plans after updating experiment status")
        save_experiment_plans(plans, plans_path, log=True)
        gr.Info(
            "Experiment status updated successfully",
            duration=1,
            title="✅ Info",
        )
    except Exception as e:
        error_msg = f"Error updating experiment status: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")


def reload_plans(
    plans_path: Path,
) -> Tuple[gr.Dropdown, gr.Dataframe, str]:
    try:
        logger.debug("Loading experiment plans for GUI reload")
        plans = load_experiment_plans(plans_path, log=True)
        display_names = [plan.experiment_name or plan.filename for plan in plans]
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
                choices=[(n, i) for n, i in zip(display_names, ids)],
                value=ids[0] if ids else None,
            ),
            gr.Dataframe(value=initial_data),
            initial_status,
        )
    except Exception as e:
        error_msg = f"Error reloading plans: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), ""


def delete_experiment(
    plans_path: Path,
    selected_id: str,
) -> Tuple[gr.Dropdown, gr.Dataframe, str]:
    try:
        logger.debug("Loading experiment plans to delete experiment")
        plans = load_experiment_plans(plans_path)
        if not any(plan.id == selected_id for plan in plans):
            gr.Info(
                "Plan not found. Please press 'Reload Plans' button.",
                title="⚠️ Warning",
            )
            return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), ""
        # Find and remove the plan
        plans = [p for p in plans if p.id != selected_id]
        logger.debug("Saving plans after deleting experiment")
        save_experiment_plans(plans, plans_path, log=True)
        display_names = [plan.experiment_name or plan.filename for plan in plans]
        ids = [plan.id for plan in plans]
        initial_data = convert_plan_to_table_data(plans[0]) if plans else []
        initial_status = plans[0].status.value if plans else ""
        gr.Info("Experiment deleted successfully", duration=1, title="✅ Info")
        return (
            gr.Dropdown(
                choices=[(n, i) for n, i in zip(display_names, ids)],
                value=ids[0] if ids else None,
            ),
            gr.Dataframe(value=initial_data),
            initial_status,
        )
    except Exception as e:
        error_msg = f"Error deleting experiment: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), ""


def get_experiment_status(plans_path: Path, selected_id: str) -> str:
    """Gets the status value for the selected experiment."""
    logger.debug(
        f"Loading experiment plans from {plans_path} to get status for selected_id: {selected_id}"
    )
    plans = load_experiment_plans(plans_path)
    plan = next((p for p in plans if p.id == selected_id), None)
    return plan.status.value if plan else ""
