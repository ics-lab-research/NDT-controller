import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import gradio as gr

from ..core.models import Mode
from ..core.project_manager import ProjectManager, init_project_context
from .artifacts import create_sidebar
from .chat import (
    handle_mode_change,
    respond,
)


def create_main_interface() -> gr.Blocks:
    """Create the main GUI interface with tabs."""
    with gr.Blocks(
        title="River Chat",
        fill_width=True,
        fill_height=True,
    ) as iface:
        # State
        project_manager = init_project_context()

        # NOTE: set mode to test
        project_manager.set_mode(Mode.EXPERIMENT)
        project_state = gr.State(project_manager)

        with gr.Row():
            with gr.Column():
                with gr.Row():
                    with gr.Column(scale=3):
                        gr.Markdown("# River Chat")

                with gr.Row():
                    # Chat Column
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        - Choose your interaction mode from the dropdown menu
                        - Type your message and press Enter to send
                        """)

                        # Create ChatInterface with custom chatbot styling
                        chat_interface = gr.ChatInterface(
                            respond,
                            multimodal=True,
                            editable=True,
                            additional_inputs=[project_state],
                            chatbot=gr.Chatbot(
                                elem_classes="chatbot-container",
                                latex_delimiters=[
                                    {
                                        "left": "$",
                                        "right": "$",
                                        "display": False,
                                    },
                                    {
                                        "left": "$$",
                                        "right": "$$",
                                        "display": True,
                                    },
                                ],
                            ),
                            fill_width=True,
                        )

                        with gr.Row():
                            mode_dropdown = gr.Dropdown(
                                choices=Mode.get_values(),
                                value=project_manager.current_mode.value,
                                scale=1,
                                show_label=False,
                                interactive=True,
                                allow_custom_value=True,
                                elem_classes="small-dropdown",
                            )
                            clear_button = gr.Button(
                                "🧹 Clear",
                                scale=4,
                                elem_classes="small-dropdown",
                            )

                    # Sidebar with tabs (hidden by default)
                    create_sidebar(
                        project_state,
                        chat_interface.chatbot,
                    )

        # Wire up events (only for Chat tab)
        clear_button.click(lambda: [], outputs=chat_interface.chatbot)

        mode_dropdown.select(
            handle_mode_change,
            inputs=[mode_dropdown, project_state],
            outputs=[project_state],
        )

        def select_and_set_data_dir(
            current_context: ProjectManager,
        ) -> tuple[str, ProjectManager]:
            """Select a folder using tkinter, set it in context, and return the path."""
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            folder_path = filedialog.askdirectory(title="Select data folder")
            root.destroy()
            if folder_path:
                current_context.set_experiment_data_path(Path(folder_path))
                return folder_path, current_context
            return "No folder selected", current_context

        with gr.Sidebar():
            data_dir_textbox = gr.Textbox(
                label="Data folder path",
                value=str(project_manager.experiment_data_path),
                interactive=False,
            )
            select_data_dir_button = gr.Button("Select data folder")
            select_data_dir_button.click(
                select_and_set_data_dir,
                inputs=[project_state],
                outputs=[data_dir_textbox, project_state],
            )

    return iface
