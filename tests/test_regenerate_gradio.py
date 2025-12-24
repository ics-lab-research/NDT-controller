import gradio as gr
import time
from typing import Generator


def respond(message: str, history: list) -> Generator[dict, None, None]:
    """Respond to user message with multiple yields simulating agent behavior."""
    yield {"role": "assistant", "content": "Starting agent..."}
    time.sleep(0.5)
    yield {"role": "assistant", "content": "Thinking..."}
    time.sleep(0.5)
    yield {"role": "assistant", "content": "Planning..."}
    time.sleep(0.5)
    full_content = """# Hello World

This is a **longer response** in markdown format.

Here are some features:
- **Bold text** for emphasis
- *Italic text* for style
- `Code snippets` for technical details

Enjoy your interaction!"""
    yield {
        "role": "assistant",
        "content": full_content,
        "metadata": {"title": "📊 Status"},
    }


example_message = ["aaaaaa", "bbbbbbb", "cccccc"]
example_label = ["A", "B", "C"]
chatbot = gr.Chatbot(type="messages")
demo = gr.ChatInterface(
    respond,
    multimodal=True,
    chatbot=chatbot,
    editable=True,
    examples=example_message,
    example_labels=example_label,
    title="Test",
    fill_width=True,
    type="messages",
)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
