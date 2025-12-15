from typing import Any, Dict, Generator, List, Tuple, Union

import gradio as gr
from loguru import logger

from ..core.models import ChatHistory, Mode
from ..core.project_manager import ProjectManager
from ..core.llm import get_agent_response
from baml_py import BamlSyncStream
from .utils import build_conversation_history


def update_files(files):
    """Update the files display and visibility."""
    if not files:
        return gr.update(value=None, visible=False), gr.update(visible=True)
    files_list = files if isinstance(files, list) else [files]
    return gr.update(value=files_list, visible=True), gr.update(visible=False)


def handle_file_upload(files, ctx):
    """Handle file upload by adding docs to context and updating display."""
    handle_upload(files, ctx)
    display_updates = update_files(files)
    return display_updates[0], display_updates[1], ctx


def handle_file_change(files, ctx):
    """Handle when files are removed via X button."""
    file_paths = []
    if files:
        file_list = files if isinstance(files, list) else [files]
        file_paths = [f.name for f in file_list]
    ctx.set_uploaded_docs(file_paths)
    display_updates = update_files(files)
    return display_updates[0], display_updates[1], ctx


def handle_upload(files: Union[Any, List[Any]] | None, ctx: ProjectManager):
    """Handle file uploads by adding their paths to the project context."""
    file_paths = []
    if files:
        file_list = files if isinstance(files, list) else [files]
        file_paths = [f.name for f in file_list]
    logger.debug("Uploaded file paths: {}", file_paths)
    ctx.add_docs(file_paths)


def respond_stream(
    message: str,
    history: ChatHistory,
    ctx: ProjectManager,
) -> Generator[Tuple[ChatHistory, str], None, None]:
    """Handle chat responses with streaming."""
    # Add user message to history
    history.append({"role": "user", "content": message})
    # Add thinking placeholder
    history.append(
        {
            "role": "assistant",
            "content": "",
            "metadata": {"title": "🧠 Thinking"},
        }
    )
    # Add response placeholder
    history.append({"role": "assistant", "content": ""})
    yield history, ""

    # Convert history to conversation messages, excluding the new messages
    conversation_history = build_conversation_history(history[:-3])

    for agent_response in get_agent_response(
        message, conversation_history, ctx
    ):
        if agent_response.thinking:
            # Update thinking message
            history[-2]["content"] = agent_response.thinking
            yield history, ""

        if agent_response.response:
            # Update response message
            history[-1]["content"] = agent_response.response
            yield history, ""


def create_chat_interface(
    project_manager: ProjectManager,
    current_context: gr.State,
) -> Tuple[
    gr.Chatbot, gr.UploadButton, gr.Files, gr.Textbox, gr.Dropdown, gr.Button
]:
    """Create the chat interface components."""
    chatbot = gr.Chatbot(
        type="messages",
        elem_classes="chatbot-container",
        latex_delimiters=[
            {"left": "$", "right": "$", "display": False},
            {"left": "$$", "right": "$$", "display": True},
        ],
    )

    with gr.Row():
        with gr.Column(scale=1):
            upload_button = gr.UploadButton(
                "📎 Attach Files",
                file_types=[
                    "image/*",
                    ".pdf",
                    ".txt",
                    ".doc",
                    ".docx",
                ],
                # NOTE: same height with Textbox, I don't know why?
                elem_classes="upload-button",
            )

            # TODO: use it later
            uploaded_files = gr.Files(
                label="Uploaded Files",
                interactive=True,
                visible=False,
            )

        msg = gr.Textbox(
            placeholder="Type your message here...",
            show_label=False,
            scale=5,
        )
        mode_dropdown = gr.Dropdown(
            choices=Mode.get_values(),
            value=project_manager.current_mode.value,
            scale=1,
            show_label=False,
            interactive=True,
            allow_custom_value=True,
        )

    with gr.Row():
        clear = gr.Button("Clear")

    upload_button.upload(
        fn=handle_file_upload,
        inputs=[upload_button, current_context],
        outputs=[uploaded_files, upload_button, current_context],
    )

    uploaded_files.change(
        fn=handle_file_change,
        inputs=[uploaded_files, current_context],
        outputs=[uploaded_files, upload_button, current_context],
    )

    clear.click(
        fn=clear_chat,
        inputs=None,
        outputs=[chatbot, msg, uploaded_files],
    )

    return chatbot, upload_button, uploaded_files, msg, mode_dropdown, clear


def handle_mode_change(mode: str, ctx: ProjectManager) -> ProjectManager:
    """Handle mode dropdown change"""
    try:
        new_mode = Mode.from_string(mode)
        ctx.set_mode(new_mode)

        return ctx

    except ValueError:
        return ctx


def clear_chat() -> Tuple[List, str, Dict[str, Any]]:
    """Clear the chat interface."""
    return [], "", gr.update(value=None, visible=False)
