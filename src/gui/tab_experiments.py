import json
import queue
from pathlib import Path
from typing import Callable, List, Tuple

import gradio as gr
from loguru import logger
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

from ..agents.experiment_execution import describe_tool, execute_multiple_plans
from ..baml_client.types import (
    ConnectToViTool,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
)
from ..core.models import (
    ExperimentPlan,
    ExperimentsMetadata,
    ExperimentTool,
    Mode,
)
from ..core.project_manager import ProjectManager
from ..core.utils import load_experiment_plans, read_file


def get_max_params(plans: List[ExperimentPlan]) -> int:
    max_params = 0
    for plan in plans:
        for tool in plan.experiment:
            if tool == "unknown":
                continue
            params = vars(tool)
            params.pop("tool_name", None)
            max_params = max(max_params, len(params))
    return max_params


def format_tool_row(tool: ExperimentTool, max_params: int) -> List[str]:
    if tool == "unknown":
        return []
    tool_dict = tool.model_dump()
    logger.debug(f"Tool type: {type(tool).__name__}, tool_dict: {tool_dict}")
    tool_name = tool_dict.get("tool_name", "unknown")
    params = {k: v for k, v in tool_dict.items() if k != "tool_name"}
    param_values = [repr(v) for v in params.values()]
    while len(param_values) < max_params:
        param_values.append("")
    return [tool_name] + param_values


def create_experiments_tab(project_manager: ProjectManager) -> gr.Tab:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans = []
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path)

    filenames = [plan.filename for plan in plans] if plans else []
    max_params = get_max_params(plans) if plans else 0
    headers = ["Tool Name"] + [f"Parameter {i + 1}" for i in range(max_params)]

    initial_data = []
    if filenames:
        first_plan = plans[0]
        for tool in first_plan.experiment:
            row = format_tool_row(tool, max_params)
            if row:
                initial_data.append(row)

    def update_details(selected_filename):
        logger.info(
            f"Updating details for selected experiment: {selected_filename}"
        )
        if not selected_filename:
            return []
        plan = next((p for p in plans if p.filename == selected_filename), None)
        if not plan:
            logger.warning(f"Plan not found for filename: {selected_filename}")
            error_row = ["Error"] + [""] * max_params
            error_row[1] = "Plan not found"
            return [error_row]
        data = []
        for tool in plan.experiment:
            row = format_tool_row(tool, max_params)
            if row:
                data.append(row)
        logger.info(f"Details updated with {len(data)} tools")
        return data

    with gr.Tab("Plans Viewer") as tab:
        dropdown = gr.Dropdown(
            choices=filenames,
            label="Select Experiment",
            value=filenames[0] if filenames else None,
        )
        details_df = gr.Dataframe(headers=headers, value=initial_data)
        dropdown.change(update_details, inputs=dropdown, outputs=details_df)
    return tab
