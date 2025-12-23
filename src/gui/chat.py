from typing import Generator, List, Tuple

import gradio as gr

from ..core.models import ChatHistory, Mode, MultimodalMessage
from ..core.project_manager import ProjectManager
from ..core.llm import get_agent_response
from .utils import build_conversation_history


def respond(
    message: MultimodalMessage,
    history: ChatHistory,
    ctx: ProjectManager,
) -> Generator[dict, None, None]:
    """Handle chat responses with streaming, yielding response dictionaries."""
    # Convert history to conversation messages, excluding the new messages
    print(message.text)
    print(message.files)
    print(history)

    yield {
        "role": "assistant",
        "content": "test",
    }

    # conversation_history = build_conversation_history(history)

    # for agent_response in get_agent_response(
    #     message, conversation_history, ctx
    # ):
    #     if agent_response.response:
    #         # Yield updated response message
    #         yield {
    #             "role": "assistant",
    #             "content": agent_response.response,
    #         }

    #     # NOTE: yield latest status
    #     if agent_response.status and agent_response.status.strip():
    #         yield {
    #             "role": "assistant",
    #             "content": agent_response.status,
    #             "metadata": {"title": "📊 Status"},
    #         }

    #     # NOTE: yield latest action
    #     if agent_response.action and agent_response.action.strip():
    #         yield {
    #             "role": "assistant",
    #             "content": agent_response.action,
    #             "metadata": {"title": "⚡ Action"},
    #         }

    #     # NOTE: yield each intermediate_step
    #     if (
    #         agent_response.intermediate_step
    #         and agent_response.intermediate_step.strip()
    #     ):
    #         yield {
    #             "role": "assistant",
    #             "content": agent_response.intermediate_step,
    #             "metadata": {"title": "🔄 Intermediate step"},
    #         }


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
