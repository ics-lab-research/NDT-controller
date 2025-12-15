import json
import os
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


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, queue: queue.Queue, file_path: Path):
        self.queue = queue
        self.file_path = file_path

    def on_modified(self, event):
        if event.src_path == str(self.file_path):
            try:
                content = self.file_path.read_text()
                self.queue.put(content)
            except Exception:
                pass


def create_file_watcher(
    file_path: Path, file_queue: queue.Queue
) -> BaseObserver:
    handler = FileChangeHandler(file_queue, file_path)
    observer = Observer()
    observer.schedule(handler, str(file_path.parent), recursive=False)
    observer.start()
    return observer


def setup_file_watchers(
    project_manager: ProjectManager,
) -> Tuple[queue.Queue, List[BaseObserver]]:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        raise TypeError("Expected ExperimentsMetadata for experiments mode")
    exp_constraint_path = metadata.exp_constraint_path
    queue_ = queue.Queue()
    observer = create_file_watcher(exp_constraint_path, queue_)
    return queue_, [observer]


def create_save_function(
    file_path: Path, file_queue: queue.Queue
) -> Callable[[str], None]:
    def save_file(content: str):
        try:
            file_path.write_text(content)
            while not file_queue.empty():
                file_queue.get_nowait()
            gr.Info(f"✅ Saved {file_path.name}")
        except Exception as e:
            gr.Warning(f"Error saving {file_path.name}: {e}")

    return save_file


def create_update_function(
    queue_: queue.Queue,
) -> Callable[[], str]:
    def check_updates() -> str:
        try:
            update = queue_.get_nowait()
            return update
        except queue.Empty:
            return gr.skip()

    return check_updates


def read_file_content(file_path: Path) -> str:
    if file_path and file_path.exists():
        try:
            return file_path.read_text()
        except OSError:
            return ""
    return ""


def get_available_filenames(project_manager: ProjectManager) -> list[str]:
    """Get the list of available experiment filenames from the plans JSON."""
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        return []
    json_filepath = str(metadata.plans_path)
    if not os.path.exists(json_filepath):
        return []
    try:
        with open(json_filepath, "r") as f:
            data = json.load(f)
        return [plan["filename"] for plan in data]
    except (json.JSONDecodeError, KeyError):
        return []


def create_experiments_tab(project_manager: ProjectManager):
    """Create the experiments tab with plan display, approval button, and hot loading."""
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        raise TypeError("Expected ExperimentsMetadata")

    def load_plan(filename: str) -> tuple[str, gr.update]:
        """Load and display the experiment plan from the single JSON file, and reload available filenames."""
        available_filenames = get_available_filenames(project_manager)
        metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
        if not isinstance(metadata, ExperimentsMetadata):
            return "Not in experiments mode", gr.update(
                choices=available_filenames, value=None
            )
        json_filepath = str(metadata.plans_path)
        if not os.path.exists(json_filepath):
            return (
                "No plans available. Please generate experiment plans first.",
                gr.update(choices=available_filenames, value=None),
            )
        try:
            with open(json_filepath, "r") as f:
                data = json.load(f)
            for plan in data:
                if plan["filename"] == filename:
                    tools: List[ExperimentTool] = []
                    for tool_dict in plan["tools"]:
                        tool_name = tool_dict.get("tool_name")
                        if tool_name == "set_numeric_control":
                            tools.append(SetNumericControlTool(**tool_dict))
                        elif tool_name == "select_tab":
                            tools.append(SelectTabTool(**tool_dict))
                        elif tool_name == "run_open_vi":
                            tools.append(RunOpenViTool(**tool_dict))
                        elif tool_name == "press_button":
                            tools.append(PressButtonTool(**tool_dict))
                        elif tool_name == "set_button_state":
                            tools.append(SetButtonStateTool(**tool_dict))
                        elif tool_name == "select_combo_box":
                            tools.append(SelectComboBoxTool(**tool_dict))
                        elif tool_name == "connect_to_vi":
                            tools.append(ConnectToViTool(**tool_dict))
                        elif tool_name == "handle_save_dialog":
                            tools.append(HandleSaveDialogTool(**tool_dict))

                    plan_description = "\n".join(
                        describe_tool(tool) for tool in tools
                    )
                    approved_status = (
                        "✓ APPROVED"
                        if plan.get("approved", False)
                        else "⚠ PENDING APPROVAL"
                    )
                    new_value = (
                        filename
                        if filename in available_filenames
                        else (
                            available_filenames[0]
                            if available_filenames
                            else None
                        )
                    )
                    return (
                        f"Experiment plan for {filename} [{approved_status}]:\n\n{plan_description}",
                        gr.update(choices=available_filenames, value=new_value),
                    )
            new_value = available_filenames[0] if available_filenames else None
            return f"No plan found for {filename}.", gr.update(
                choices=available_filenames, value=new_value
            )
        except (json.JSONDecodeError, KeyError) as e:
            return f"Error loading plans: {str(e)}", gr.update(
                choices=available_filenames, value=None
            )

    def approve_and_execute(filename: str) -> str:
        """Approve the plan, update the JSON, and execute the experiment."""
        metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
        if not isinstance(metadata, ExperimentsMetadata):
            return "Not in experiments mode"
        json_filepath = str(metadata.plans_path)
        if not os.path.exists(json_filepath):
            return "No plans available."
        try:
            with open(json_filepath, "r") as f:
                data = json.load(f)

            found = False
            for plan in data:
                if plan["filename"] == filename:
                    found = True
                    plan["approved"] = True

                    tools: List[ExperimentTool] = []
                    for tool_dict in plan["tools"]:
                        tool_name = tool_dict.get("tool_name")
                        if tool_name == "set_numeric_control":
                            tools.append(SetNumericControlTool(**tool_dict))
                        elif tool_name == "select_tab":
                            tools.append(SelectTabTool(**tool_dict))
                        elif tool_name == "run_open_vi":
                            tools.append(RunOpenViTool(**tool_dict))
                        elif tool_name == "press_button":
                            tools.append(PressButtonTool(**tool_dict))
                        elif tool_name == "set_button_state":
                            tools.append(SetButtonStateTool(**tool_dict))
                        elif tool_name == "select_combo_box":
                            tools.append(SelectComboBoxTool(**tool_dict))
                        elif tool_name == "connect_to_vi":
                            tools.append(ConnectToViTool(**tool_dict))
                        elif tool_name == "handle_save_dialog":
                            tools.append(HandleSaveDialogTool(**tool_dict))

                    execute_multiple_plans([tools], project_manager)
                    # break

            if found:
                with open(json_filepath, "w") as f:
                    json.dump(data, f, indent=4)
                return f"Plan for {filename} approved and executed."

            return f"No plan found for {filename}."
        except Exception as e:
            return f"Error approving plan: {str(e)}"

    with gr.Tabs():
        with gr.TabItem("Experiment Planning"):
            available_filenames = get_available_filenames(project_manager)
            filename_input = gr.Dropdown(
                label="Experiment Filename",
                choices=available_filenames,
                value=available_filenames[0] if available_filenames else None,
            )
            plan_display = gr.Textbox(
                label="Current Plan", lines=10, interactive=False
            )
            load_button = gr.Button("Load Plan")
            approve_button = gr.Button("Approve and Execute")

            # Load plan on button click
            load_button.click(
                fn=load_plan,
                inputs=filename_input,
                outputs=[plan_display, filename_input],
            )

            # Approve on button click
            approve_button.click(
                fn=approve_and_execute,
                inputs=filename_input,
                outputs=gr.Textbox(label="Execution Status"),
            )

        with gr.TabItem("LabVIEW Constraints"):
            queue_, observers = setup_file_watchers(project_manager)
            exp_constraint_content = gr.Textbox(
                label="LabVIEW.md",
                value=read_file_content(metadata.exp_constraint_path),
                lines=20,
                interactive=True,
                autoscroll=False,
            )
            save_button = gr.Button("Save")
            save_fn = create_save_function(metadata.exp_constraint_path, queue_)
            save_button.click(
                save_fn, inputs=exp_constraint_content, outputs=[]
            )
            update_fn = create_update_function(queue_)
            timer = gr.Timer(1)
            timer.tick(update_fn, outputs=[exp_constraint_content])
