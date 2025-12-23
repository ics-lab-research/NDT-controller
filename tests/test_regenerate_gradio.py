import gradio as gr
import time


def respond(message: str, history: list) -> str:
    """Respond to user message with a longer markdown-formatted response."""
    time.sleep(5)

    return """# Hello World

This is a **longer response** in markdown format.

Here are some features:
- **Bold text** for emphasis
- *Italic text* for style
- `Code snippets` for technical details

Enjoy your interaction!"""


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
    show_progress="full",
    fill_width=True,
    save_history=True,
    type="messages",
)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
