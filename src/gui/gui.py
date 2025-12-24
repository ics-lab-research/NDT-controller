import gradio as gr
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from ..core.models import Mode
from ..core.project_manager import init_project_context
from .artifacts import create_sidebar, toggle_sidebar
from .chat import (
    handle_mode_change,
    respond,
)

custom_css = """
/* --- Chat area --- */
.chatbot-container {
    flex: 1 1 auto;
    height: 65vh !important;       /* ⚖️ good balance */
    max-height: 65vh !important;
    overflow-y: auto !important;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 4px;
}

/* --- Align dropdown and button heights --- */
.small-dropdown {
    height: 60px !important;
}
"""


def create_main_interface() -> gr.Blocks:
    """Create the main GUI interface with tabs."""
    with gr.Blocks(
        title="River Chat",
        fill_width=True,
        fill_height=True,
        css=custom_css,
    ) as iface:
        # State
        project_manager = init_project_context()

        # NOTE: set mode to test
        project_manager.set_mode(Mode.EXPERIMENTS)
        current_context = gr.State(project_manager)

        with gr.Row():
            with gr.Column():
                with gr.Row():
                    with gr.Column(scale=3):
                        gr.Markdown("# River Chat")

                    with gr.Column(scale=1):
                        show_sidebar = gr.Checkbox(
                            label="Show Sidebar",
                            value=False,
                            elem_classes="checkbox-group",
                            min_width=100,
                        )

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
                            additional_inputs=[current_context],
                            chatbot=gr.Chatbot(
                                type="messages",
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
                            type="messages",
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
                    sidebar_column = create_sidebar(
                        project_manager,
                        chat_interface.chatbot,
                    )
                    sidebar_column.visible = False

        # Wire up events (only for Chat tab)
        clear_button.click(lambda: [], outputs=chat_interface.chatbot)

        mode_dropdown.select(
            handle_mode_change,
            inputs=[mode_dropdown, current_context],
            outputs=[current_context],
        )

        show_sidebar.change(
            toggle_sidebar,
            inputs=[show_sidebar],
            outputs=[sidebar_column],
        )

        def select_and_set_data_dir(current_context):
            """Select a folder using tkinter, set it in context, and return the path."""
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            folder_path = filedialog.askdirectory(title="Select Data Dir Folder")
            root.destroy()
            if folder_path:
                current_context.set_data_dir_path(Path(folder_path))
                return folder_path, current_context
            return "No folder selected", current_context

        with gr.Sidebar():
            data_dir_textbox = gr.Textbox(
                label="Data Dir Path",
                value=str(project_manager.data_dir_path),
                interactive=False,
            )
            select_data_dir_button = gr.Button("Select Data Dir Folder")
            select_data_dir_button.click(
                select_and_set_data_dir,
                inputs=[current_context],
                outputs=[data_dir_textbox, current_context],
            )

    return iface
