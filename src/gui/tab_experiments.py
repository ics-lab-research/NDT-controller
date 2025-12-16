import ast
import json
import queue
from dataclasses import asdict
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
from ..core.utils import load_experiment_plans, read_file, save_experiment_plans


def parse_tool_from_params(tool_name: str, params: dict) -> ExperimentTool:
    """Parse tool parameters and create appropriate tool instance."""
    tool_map = {
        "SetNumericControlTool": SetNumericControlTool,
        "SelectTabTool": SelectTabTool,
        "RunOpenViTool": RunOpenViTool,
        "ConnectToViTool": ConnectToViTool,
        "HandleSaveDialogTool": HandleSaveDialogTool,
        "PressButtonTool": PressButtonTool,
        "SetButtonStateTool": SetButtonStateTool,
        "SelectComboBoxTool": SelectComboBoxTool,
    }

    tool_class = tool_map.get(tool_name)
    if not tool_class:
        logger.warning(f"Unknown tool type: {tool_name}")
        return "unknown"

    try:
        tool_params = {"tool_name": tool_name, **params}

        if tool_class == SetNumericControlTool and "value" in params:
            tool_params["value"] = float(params["value"])
        elif tool_class == SelectTabTool and "index" in params:
            tool_params["index"] = int(params["index"])
        elif tool_class == SetButtonStateTool and "state" in params:
            tool_params["state"] = params["state"].lower() == "true"

        return tool_class(**tool_params)
    except Exception as e:
        logger.error(f"Failed to create tool {tool_name}: {e}")
        return "unknown"


def create_experiments_tab(project_manager: ProjectManager) -> gr.Tab:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans: List[ExperimentPlan] = []
    plans_path = None
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path)

    filenames = [plan.filename for plan in plans] if plans else []

    initial_data = []
    if filenames:
        first_plan = plans[0]
        for tool in first_plan.experiment:
            if tool == "unknown":
                continue
            tool_name = tool.tool_name
            params = vars(tool)
            params.pop("tool_name", None)
            param_list = [f"{k}={v}" for k, v in params.items()]
            param1 = param_list[0] if len(param_list) > 0 else ""
            param2 = param_list[1] if len(param_list) > 1 else ""
            initial_data.append([tool_name, param1, param2])

    def update_details(selected_filename: str) -> List[List[str]]:
        logger.info(
            f"Updating details for selected experiment: {selected_filename}"
        )
        if not selected_filename:
            return []
        plan = next((p for p in plans if p.filename == selected_filename), None)
        if not plan:
            logger.warning(f"Plan not found for filename: {selected_filename}")
            return [["Error", "", ""]]
        data = []
        for tool in plan.experiment:
            if tool == "unknown":
                continue
            tool_name = tool.tool_name
            params = vars(tool)
            params.pop("tool_name", None)
            param_list = [f"{k}={v}" for k, v in params.items()]
            param1 = param_list[0] if len(param_list) > 0 else ""
            param2 = param_list[1] if len(param_list) > 1 else ""
            data.append([tool_name, param1, param2])
        logger.info(f"Details updated with {len(data)} tools")
        return data

    def save_changes(
        selected_filename: str, dataframe_data: List[List[str]]
    ) -> str:
        logger.info(f"Saving changes for experiment: {selected_filename}")
        if not selected_filename or not plans_path:
            logger.warning("No filename selected or plans path not available")
            return "Error: No experiment selected or path not configured"

        plan_index = next(
            (i for i, p in enumerate(plans) if p.filename == selected_filename),
            None,
        )
        if plan_index is None:
            logger.warning(f"Plan not found for filename: {selected_filename}")
            return "Error: Experiment not found"

        tools: List[ExperimentTool] = []
        for row_str in dataframe_data:
            row = ast.literal_eval(row_str)
            tool_name = row[0]
            param1_str = row[1] if len(row) > 1 else ""
            param2_str = row[2] if len(row) > 2 else ""

            params = {}
            for param_str in [param1_str, param2_str]:
                if param_str and "=" in param_str:
                    key, value = param_str.split("=", 1)
                    params[key.strip()] = value.strip()

            logger.debug(tool_name)
            logger.debug(params)

            tool = parse_tool_from_params(tool_name, params)
            if tool != "unknown":
                tools.append(tool)

        plans[plan_index] = ExperimentPlan(
            filename=selected_filename, experiment=tools
        )

        result = save_experiment_plans(plans, plans_path)
        if result.get("success"):
            logger.info(f"Successfully saved changes for {selected_filename}")
            return f"Successfully saved changes to {selected_filename}"
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Failed to save changes: {error_msg}")
            return f"Error saving: {error_msg}"

    with gr.Tab("Plans Viewer") as tab:
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
        save_btn = gr.Button("Save Changes")
        save_status = gr.Textbox(label="Status", interactive=False)

        dropdown.change(update_details, inputs=dropdown, outputs=details_df)
        save_btn.click(
            save_changes, inputs=[dropdown, details_df], outputs=save_status
        )
    return tab
