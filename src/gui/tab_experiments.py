import json
import queue
from pathlib import Path
from typing import Callable, List, Tuple

import gradio as gr
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
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path)
            data = [[plan.filename, str(plan.experiment)] for plan in plans]
            headers = ["Filename", "Experiment"]
        else:
            data = [["Error", "plans_path is not a Path object"]]
            headers = ["Status", "Message"]
    else:
        data = [["Error", "Invalid metadata type for experiments mode"]]
        headers = ["Status", "Message"]
    with gr.Tab("Plans Viewer") as tab:
        gr.Dataframe(value=data, headers=headers)
    return tab
