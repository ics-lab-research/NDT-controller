from typing import Any, Dict, Generator, List, Tuple, Union

import gradio as gr
from loguru import logger

from ..core.models import ChatHistory, Mode
from ..core.project_manager import ProjectManager
from ..core.llm import get_agent_response
from .utils import build_conversation_history




def respond_stream(
    message: str,
    history: ChatHistory,
    ctx: ProjectManager,
) -> Generator[Tuple[ChatHistory, str], None, None]:
    """Handle chat responses with streaming."""
    # Add user message to history
    history.append({"role": "user", "content": message})
    # Add response placeholder
    history.append({"role": "assistant", "content": ""})
    yield history, ""

    thinking_added = False

    # Convert history to conversation messages, excluding the new messages
    conversation_history = build_conversation_history(history[:-2])

    for agent_response in get_agent_response(
        message, conversation_history, ctx
    ):
        if agent_response.thinking and agent_response.thinking.strip():
            if not thinking_added:
                # Insert thinking message before response
                history.insert(
                    -1,
                    {
                        "role": "assistant",
                        "content": agent_response.thinking,
                        "metadata": {"title": "🧠 Thinking"},
                    },
                )
                thinking_added = True
                yield history, ""
            else:
                # Update existing thinking message
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
    gr.Chatbot, gr.Textbox, gr.Dropdown, gr.Button
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
