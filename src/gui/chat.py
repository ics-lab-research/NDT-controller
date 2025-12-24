from pathlib import Path
from typing import Generator, List, Tuple

import gradio as gr

from ..core.models import (
    ChatHistory,
    Mode,
    MultimodalMessage,
    ChatMessage,
    MessageType,
)
from ..core.project_manager import ProjectManager
from ..core.llm import get_agent_response
from .utils import build_conversation_history, create_message


def respond(
    message: MultimodalMessage | dict,
    history: ChatHistory,
    project_manager: ProjectManager,
    progress=gr.Progress(),
) -> Generator[dict, None, None]:
    """Handle chat responses with streaming, yielding ChatMessage instances."""
    progress(0.0, desc="Starting agent...")
    # Handle multimodal message input
    if isinstance(message, dict):
        message = MultimodalMessage(
            text=message.get("text", ""), files=message.get("files", [])
        )

    # Add uploaded files to project manager
    for file_path_str in message.files:
        project_manager.add_multimodal_upload(Path(file_path_str))

    # Convert history to conversation messages, excluding the new messages
    conversation_history = build_conversation_history(history)

    progress(0.25, desc="Processing request...")
    for agent_response in get_agent_response(
        message.text, conversation_history, project_manager
    ):
        if agent_response.response:
            # Yield updated response message
            yield create_message(agent_response.response).to_dict()

        # NOTE: yield latest status
        if agent_response.status and agent_response.status.strip():
            yield create_message(
                agent_response.status, MessageType.STATUS
            ).to_dict()

        # NOTE: yield latest action
        if agent_response.action and agent_response.action.strip():
            yield create_message(
                agent_response.action, MessageType.ACTION
            ).to_dict()

        # NOTE: yield each intermediate_step
        if (
            agent_response.intermediate_step
            and agent_response.intermediate_step.strip()
        ):
            yield create_message(
                agent_response.intermediate_step, MessageType.INTERMEDIATE_STEP
            ).to_dict()

    progress(1.0, desc="Complete")


def create_chat_interface(
    project_manager: ProjectManager,
) -> Tuple[gr.Chatbot, gr.Textbox, gr.Dropdown, gr.Button]:
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

    clear.click(
        fn=clear_chat,
        inputs=None,
        outputs=[chatbot, msg],
    )

    return chatbot, msg, mode_dropdown, clear


def handle_mode_change(mode: str, ctx: ProjectManager) -> ProjectManager:
    """Handle mode dropdown change"""
    try:
        new_mode = Mode.from_string(mode)
        ctx.set_mode(new_mode)

        return ctx

    except ValueError:
        return ctx


def clear_chat() -> Tuple[List, str]:
    """Clear the chat interface."""
    return [], ""
