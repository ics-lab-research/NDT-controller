from pathlib import Path
from typing import Dict, Generator, List, Tuple

import gradio as gr
from loguru import logger

from ..core.models import (
    ChatHistory,
    Mode,
    MultimodalMessage,
    MessageType,
    ChatMessage,
    AgentResponse,
)
from ..core.project_manager import ProjectManager
from ..core.llm import get_agent_response
from .utils import build_conversation_history, create_message


def parse_multimodal_message(
    message: Dict[str, str | List[str]] | str,
) -> MultimodalMessage:
    """Parse message input into MultimodalMessage."""
    if isinstance(message, str):
        return MultimodalMessage(text=message, files=[])

    text = message.get("text", "")
    text = text if isinstance(text, str) else ""
    files = message.get("files", [])
    files = [files] if isinstance(files, str) else files

    return MultimodalMessage(text=text, files=[Path(f) for f in files])


def register_uploaded_files(
    multimodal_message: MultimodalMessage, project_manager: ProjectManager
) -> None:
    """Register uploaded files with project manager."""
    for file_path in multimodal_message.files:
        project_manager.add_multimodal_upload(file_path)


def yield_agent_response_messages(
    agent_response: AgentResponse,
) -> Generator[ChatMessage, None, None]:
    """Yield chat messages from agent response."""
    if agent_response.response:
        yield create_message(agent_response.response)

    if agent_response.status and agent_response.status.strip():
        yield create_message(agent_response.status, MessageType.STATUS)

    if agent_response.action and agent_response.action.strip():
        yield create_message(agent_response.action, MessageType.ACTION)

    if (
        agent_response.intermediate_step
        and agent_response.intermediate_step.strip()
    ):
        yield create_message(
            agent_response.intermediate_step, MessageType.INTERMEDIATE_STEP
        )


def respond(
    message: Dict[str, str | List[str]] | str,
    history: ChatHistory,
    project_manager: ProjectManager,
) -> Generator[ChatMessage, None, None]:
    """Handle chat responses with streaming."""
    logger.info("Starting chat response processing")

    multimodal_message = parse_multimodal_message(message)
    register_uploaded_files(multimodal_message, project_manager)
    conversation_history = build_conversation_history(history)

    logger.debug(
        f"Processing message with {len(multimodal_message.files)} files"
    )

    for agent_response in get_agent_response(
        multimodal_message.text, conversation_history, project_manager
    ):
        yield from yield_agent_response_messages(agent_response)

    logger.info("Chat response complete")


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

    # Add spinner for loading animation during response
    with gr.Spinner():
        msg.submit(
            fn=respond,
            inputs=[msg, chatbot, project_manager],
            outputs=[chatbot],
        )

    mode_dropdown.change(
        fn=handle_mode_change,
        inputs=[mode_dropdown, project_manager],
        outputs=[project_manager],
    )

    clear.click(
        fn=clear_chat,
        inputs=None,
        outputs=[chatbot, msg],
    )

    return chatbot, msg, mode_dropdown, clear


def handle_mode_change(mode: str, ctx: ProjectManager) -> ProjectManager:
    """Handle mode dropdown change."""
    try:
        new_mode = Mode.from_string(mode)
        ctx.set_mode(new_mode)
        logger.info(f"Mode changed to: {new_mode.value}")
        return ctx
    except ValueError:
        logger.warning(f"Invalid mode value: {mode}")
        return ctx


def clear_chat() -> Tuple[List, str]:
    """Clear the chat interface."""
    logger.debug("Chat cleared")
    return [], ""
