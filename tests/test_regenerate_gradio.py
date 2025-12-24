import gradio as gr
import time


def respond(message: str, history: list) -> list:
    """Respond to user message with progress bar simulating agent behavior."""
    with gr.Progress() as prog:
        prog(0, desc="Starting agent...")
        time.sleep(0.5)
        prog(0.25, desc="Thinking...")
        time.sleep(0.5)
        prog(0.5, desc="Planning...")
        time.sleep(0.5)
        full_content = """# Hello World

This is a **longer response** in markdown format.

Here are some features:
- **Bold text** for emphasis
- *Italic text* for style
- `Code snippets` for technical details

Enjoy your interaction!"""
        prog(1, desc="Complete")
        history = history + [
            {"role": "assistant", "content": full_content, "metadata": {"title": "📊 Status"}}
        ]
    return history


# example_message = ["aaaaaa", "bbbbbbb", "cccccc"]
# example_label = ["A", "B", "C"]
with gr.Blocks(title="Test", fill_width=True) as demo:
    chatbot = gr.Chatbot(type="messages")
    textbox = gr.Textbox()
    submit_btn = gr.Button("Submit")
    
    submit_btn.click(respond, [textbox, chatbot], chatbot)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
