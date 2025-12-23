import gradio as gr
  
  
def respond(message: str, history: list) -> list:
    """Respond to user message with 'hello world'."""
    history.append([message, "hello world"])
    return history
  
  
with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Type your message here...")
    msg.submit(respond, inputs=[msg, chatbot], outputs=[chatbot])
  
if __name__ == "__main__":
    demo.launch(inbrowser=True)
