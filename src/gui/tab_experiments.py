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


def create_json_viewer_tab(project_manager: ProjectManager) -> gr.Tab:
    json_content = read_file(project_manager)
    with gr.Tab("JSON Viewer") as tab:
        gr.Code(value=json_content, language="json")
    return tab
