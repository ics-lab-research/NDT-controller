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
from ..core.models import ExperimentsMetadata, ExperimentTool, Mode
from ..core.project_manager import ProjectManager
from ..core.utils import load_experiment_plans, read_file


def create_experiments_tab(project_manager: ProjectManager) -> gr.Tab:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            json_content = read_file(plans_path)
            if len(json_content) > 10000:
                json_content = json_content[:10000] + "\n... (truncated)"
        else:
            json_content = "Error: plans_path is not a Path object"
    else:
        json_content = "Error: Invalid metadata type for experiments mode"
    with gr.Tab("JSON Viewer") as tab:
        gr.Code(value=json_content, language="json", max_lines=30)
    return tab
