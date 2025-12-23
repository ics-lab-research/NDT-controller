import gradio as gr


def respond(message: str, history: list) -> str:
    """Respond to user message with 'hello world'."""
    return "hello world"


demo = gr.ChatInterface(respond)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
