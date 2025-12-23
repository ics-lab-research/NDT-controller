import gradio as gr
  
  
def respond(message: str, history: list) -> str:
    """Respond to user message with 'hello world'."""
    return "hello world"
  
  
example_message = ["aaaaaa", "bbbbbbb", "cccccc"]
example_label = ["A", "B", "C"]
chatbot = gr.Chatbot(type='messages')
demo = gr.ChatInterface(
    respond,
    multimodal=True,
    chatbot=chatbot,
    editable=True,
    examples=example_message,
    example_labels=example_label,
    type='messages',
)
  
if __name__ == "__main__":
    demo.launch(inbrowser=True)
