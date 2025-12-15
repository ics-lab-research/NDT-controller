import queue
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import gradio as gr
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer, ObserverType
from watchdog.observers.api import BaseObserver

from ..core.project_manager import ProjectManager
from ..core.models import IdeaMetadata, Mode


def create_idea_tab(
    project_manager: ProjectManager,
) -> Tuple[gr.Textbox, gr.Textbox, gr.Textbox, gr.Textbox]:
    queues, _ = setup_file_watchers(project_manager)
    file_configs = get_idea_file_configs(project_manager)

    save_functions = {
        name: create_save_function(config["path"], queues[name])
        for name, config in file_configs.items()
    }

    with gr.Tabs():
        idea_content = create_file_tab(
            "Idea",
            file_configs["idea"]["label"],
            file_configs["idea"]["path"],
            save_functions["idea"],
        )
        experiment_plan_content = create_file_tab(
            "Experiment Plan",
            file_configs["experiment_plan"]["label"],
            file_configs["experiment_plan"]["path"],
            save_functions["experiment_plan"],
        )
        data_science_plan_content = create_file_tab(
            "Data-science Plan",
            file_configs["data_science_plan"]["label"],
            file_configs["data_science_plan"]["path"],
            save_functions["data_science_plan"],
        )
        system_content = create_file_tab(
            "System Specs",
            file_configs["system"]["label"],
            file_configs["system"]["path"],
            save_functions["system"],
        )

        update_fn = create_update_function(queues)
        timer = gr.Timer(1)
        timer.tick(
            update_fn,
            outputs=[
                idea_content,
                experiment_plan_content,
                data_science_plan_content,
                system_content,
            ],
        )

    return (
        idea_content,
        experiment_plan_content,
        data_science_plan_content,
        system_content,
    )


def create_file_tab(
    name: str,
    label: str,
    file_path: Path | None,
    save_function,
) -> gr.Textbox:
    with gr.TabItem(name):
        content_value = read_file_content(file_path)
        content = gr.Textbox(
            label=label,
            value=content_value,
            interactive=True,
            lines=20,
            autoscroll=False,
            elem_classes="file-content-textbox",
        )
        save_button = gr.Button("Save")
        save_button.click(save_function, inputs=content, outputs=[])
        return content


def read_file_content(file_path: Path | None) -> str:
    if file_path and file_path.exists():
        try:
            return file_path.read_text()
        except OSError:
            return ""
    return ""


def get_idea_file_configs(project_manager: ProjectManager) -> Dict[str, Dict]:
    metadata = project_manager.get_mode_metadata(Mode.IDEA)
    if not isinstance(metadata, IdeaMetadata):
        raise TypeError("Expected IdeaMetadata for idea mode")
    return {
        "idea": {
            "path": metadata.idea_output_path,
            "label": "Your Brainstormed Idea",
        },
        "experiment_plan": {
            "path": metadata.experiment_plan_path,
            "label": "Your Generated Experiment Plan",
        },
        "data_science_plan": {
            "path": metadata.data_science_plan_path,
            "label": "Your Generated Data-science Plan",
        },
        "system": {
            "path": metadata.system_spec_path,
            "label": "System Requirements and Specifications",
        },
    }


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
) -> Tuple[Dict[str, queue.Queue], List[ObserverType]]:
    metadata = project_manager.get_mode_metadata(Mode.IDEA)
    if not isinstance(metadata, IdeaMetadata):
        raise TypeError("Expected IdeaMetadata for idea mode")
    file_configs_paths = {
        "idea": metadata.idea_output_path,
        "experiment_plan": metadata.experiment_plan_path,
        "data_science_plan": metadata.data_science_plan_path,
        "system": metadata.system_spec_path,
    }

    queues = {name: queue.Queue() for name in file_configs_paths}
    observers = []

    for name, path in file_configs_paths.items():
        if path:
            observer = create_file_watcher(path, queues[name])
            observers.append(observer)

    return queues, observers


def create_save_function(
    file_path: Path | None, file_queue: queue.Queue
) -> Callable[[str], None]:
    def save_file(content: str):
        if not file_path:
            gr.Warning("No path configured")
            return

        try:
            file_path.write_text(content)
            while not file_queue.empty():
                file_queue.get_nowait()
            gr.Info(f"✅ Saved {file_path.name}")
        except Exception as e:
            gr.Warning(f"Error saving {file_path.name}: {e}")

    return save_file


def create_update_function(
    queues: Dict[str, queue.Queue],
) -> Callable[[], Tuple]:
    def check_updates() -> Tuple:
        updates = []
        for name in ["idea", "experiment_plan", "data_science_plan", "system"]:
            try:
                update = queues[name].get_nowait()
                updates.append(update)
            except queue.Empty:
                updates.append(gr.skip())
        return tuple(updates)

    return check_updates
