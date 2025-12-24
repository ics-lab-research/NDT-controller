import gradio as gr
import time
from typing import Generator


def respond(
    message: str, history: list, progress=gr.Progress()
) -> Generator[dict, None, None]:
    """Respond to user message with multiple yields simulating agent behavior."""
    progress(0.0, desc="Starting agent...")
    yield {"role": "assistant", "content": "Starting agent..."}
    time.sleep(5)
    progress(0.25, desc="Thinking...")
    yield {"role": "assistant", "content": "Thinking..."}
    time.sleep(5)
    progress(0.5, desc="Planning...")
    yield {"role": "assistant", "content": "Planning..."}
    time.sleep(5)
    progress(0.75, desc="Generating response...")
    full_content = """# Hello World

This is a **longer response** in markdown format.

Here are some features:
- **Bold text** for emphasis
- *Italic text* for style
- `Code snippets` for technical details

Enjoy your interaction!"""
    progress(1.0, desc="Complete")
    yield {
        "role": "assistant",
        "content": full_content,
        "metadata": {"title": "📊 Status"},
    }


# example_message = ["aaaaaa", "bbbbbbb", "cccccc"]
# example_label = ["A", "B", "C"]
chatbot = gr.Chatbot(type="messages")
demo = gr.ChatInterface(
    respond,
    multimodal=True,
    chatbot=chatbot,
    editable=True,
    # examples=example_message,
    # example_labels=example_label,
    title="Test",
    fill_width=True,
    type="messages",
)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
