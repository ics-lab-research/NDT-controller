import gradio as gr


def respond(message: str, history: list) -> str:
    """Respond to user message with 'hello world'."""
    return "hello world"


with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Type your message here...")
    msg.submit(respond, inputs=[msg, chatbot], outputs=[chatbot])

if __name__ == "__main__":
    demo.launch(inbrowser=True)
