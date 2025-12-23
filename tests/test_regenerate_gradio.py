import gradio as gr
import time
from typing import Generator


def test_stream() -> Generator[str, None, None]:
    yield "1"

    time.sleep(1)
    yield "2"

    time.sleep(2)
    yield "3"


def respond(message: str, history: list) -> Generator[dict, None, None]:
    """Respond to user message with a streamed response using test_stream."""
    time.sleep(5)
    accumulated_content = ""
    for chunk in test_stream():
        accumulated_content += chunk
        yield {
            "role": "assistant",
            "content": accumulated_content,
        }

    # Final yield with metadata
    yield {
        "role": "assistant",
        "content": accumulated_content,
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
