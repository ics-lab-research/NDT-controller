import gradio as gr
import tkinter as tk
from tkinter import filedialog


def select_folder():
    """Select a folder using tkinter and return its path."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder_path = filedialog.askdirectory(title="Select a Folder")
    root.destroy()
    return folder_path if folder_path else "No folder selected"


def create_interface():
    """Create a gradio interface for folder selection."""
    with gr.Blocks() as demo:
        gr.Markdown("# Folder Selector")
        select_button = gr.Button("Select Folder")
        path_output = gr.Textbox(
            label="Selected Folder Path", interactive=False
        )
        select_button.click(fn=select_folder, outputs=path_output)
    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(inbrowser=True)
