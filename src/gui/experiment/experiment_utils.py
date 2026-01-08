from enum import Enum
from pathlib import Path
from typing import List, Tuple

import gradio as gr
from loguru import logger

from ...agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ...core.models import (
    ExperimentPlan,
    ExperimentTool,
)


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


def get_experiment_status(plans: List[ExperimentPlan], selected_id: str) -> str:
    """Gets the status value for the selected experiment."""
    plan = next((p for p in plans if p.id == selected_id), None)
    return plan.status.value if plan else ""


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


def reload_plans(
    plans_path: Path | None,
) -> Tuple[gr.Dropdown, gr.Dataframe, str, List[ExperimentPlan]]:
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="⚠️ Warning")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []
    try:
        logger.debug("Loading experiment plans for GUI reload")
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
        logger.debug("Saving plans after deleting experiment")
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
