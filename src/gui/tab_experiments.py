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


def create_experiments_tab(project_manager: ProjectManager) -> gr.Tab:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans = []
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
            param_str = ", ".join(f"{k}={repr(v)}" for k, v in params.items())
            initial_data.append([tool_name, param_str])

    def update_details(selected_filename):
        logger.info(
            f"Updating details for selected experiment: {selected_filename}"
        )
        if not selected_filename:
            return []
        plan = next((p for p in plans if p.filename == selected_filename), None)
        if not plan:
            logger.warning(f"Plan not found for filename: {selected_filename}")
            return [["Error", "Plan not found"]]
        data = []
        for tool in plan.experiment:
            if tool == "unknown":
                continue
            tool_name = tool.tool_name
            params = vars(tool)
            params.pop("tool_name", None)
            param_str = ", ".join(f"{k}={repr(v)}" for k, v in params.items())
            data.append([tool_name, param_str])
        logger.info(f"Details updated with {len(data)} tools")
        return data

    with gr.Tab("Plans Viewer") as tab:
        dropdown = gr.Dropdown(
            choices=filenames,
            label="Select Experiment",
            value=filenames[0] if filenames else None,
        )
        details_df = gr.Dataframe(
            headers=["Tool Name", "Parameters"], value=initial_data
        )
        dropdown.change(update_details, inputs=dropdown, outputs=details_df)
    return tab
