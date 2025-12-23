import gradio as gr


def respond(message: str, history: list) -> str:
    """Respond to user message with 'hello world'."""
    return "hello world"


chatbot = gr.Chatbot()
demo = gr.ChatInterface(respond, multimodal=True, chatbot=chatbot)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
