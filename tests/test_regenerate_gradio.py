import gradio as gr
import time
from typing import Generator


def test_stream() -> Generator[str, None, None]:
    yield "1"

    time.sleep(1)
    yield "2"

    time.sleep(2)
    yield "3"


def respond(message: str, history: list) -> dict:
    """Respond to user message with a longer markdown-formatted response."""
    time.sleep(5)
    for chunk in test_stream():
        yield chunk

    return {
        "role": "assistant",
        "content": """# Hello World

This is a **longer response** in markdown format.

Here are some features:
- **Bold text** for emphasis
- *Italic text* for style
- `Code snippets` for technical details

Enjoy your interaction!""",
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
