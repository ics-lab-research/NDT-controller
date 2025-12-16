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
from ..core.utils import load_experiment_plans, read_file


def create_experiments_tab(project_manager: ProjectManager) -> gr.Tab:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans = []
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

    def update_details(selected_filename):
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

    def save_changes(selected_filename, df_data):
        if not selected_filename or not plans_path:
            return
        plan = next((p for p in plans if p.filename == selected_filename), None)
        if not plan:
            return
        tools = []
        tool_class_map = {
            "SetNumericControlTool": SetNumericControlTool,
            "SelectTabTool": SelectTabTool,
            "RunOpenViTool": RunOpenViTool,
            "ConnectToViTool": ConnectToViTool,
            "HandleSaveDialogTool": HandleSaveDialogTool,
            "PressButtonTool": PressButtonTool,
            "SetButtonStateTool": SetButtonStateTool,
            "SelectComboBoxTool": SelectComboBoxTool,
        }
        for row in df_data:
            if len(row) < 3:
                continue
            tool_name, param1, param2 = row
            if not tool_name.strip():
                continue
            params = {}
            if param1.strip():
                try:
                    k, v = param1.split("=", 1)
                    params[k.strip()] = v.strip()
                except ValueError:
                    logger.warning(f"Invalid parameter format: {param1}")
            if param2.strip():
                try:
                    k, v = param2.split("=", 1)
                    params[k.strip()] = v.strip()
                except ValueError:
                    logger.warning(f"Invalid parameter format: {param2}")
            tool_class = tool_class_map.get(tool_name)
            if tool_class:
                try:
                    tool = tool_class(tool_name=tool_name, **params)
                    tools.append(tool)
                except Exception as e:
                    logger.error(f"Error creating tool {tool_name}: {e}")
                    tools.append("unknown")
            else:
                tools.append("unknown")
        plan.experiment = tools
        try:
            with open(plans_path, "w") as f:
                json.dump([asdict(p) for p in plans], f, indent=2)
            logger.info(f"Saved changes to {plans_path}")
        except Exception as e:
            logger.error(f"Error saving plans: {e}")

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
        dropdown.change(update_details, inputs=dropdown, outputs=details_df)
        save_btn.click(save_changes, inputs=[dropdown, details_df], outputs=[])
    return tab
