from pathlib import Path
import threading
import subprocess
import sys

import gradio as gr


def run_data_loader_script(file_path: str, output_path: str) -> str:
    """Run the data_loader.py script in a thread."""

    def run_script():
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "DATA-SCIENCE/data_loader.py",
                    file_path,
                    output_path,
                ],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
            )
            if result.returncode == 0:
                print("Script ran successfully.")
                print(result.stdout)
            else:
                print("Script failed.")
                print(result.stderr)
        except Exception as e:
            print(f"Error running script: {e}")

    thread = threading.Thread(target=run_script)
    thread.start()
    return "Data loader script started in background. Check console for output."


def create_data_science_tab():
    # State
    # current_context = gr.State(context_manager)
    # experiment_plans = gr.State(value=None)
    # uploaded_file_path = gr.State(value=None)

    with gr.Tab("Experiments"):
        gr.Markdown("# River Chat")

        # Data Upload Section
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Upload TDMS Data for Training")
                file_upload = gr.File(
                    label="Upload .tdms file (with corrosion at center)",
                    file_types=[".tdms"],
                    type="filepath",
                )
                output_path_input = gr.Textbox(
                    label="Output Path",
                    value="EXPERIMENTS/data/train_test_data.npz",
                )
                run_script_button = gr.Button("Run Data Loader Script")
                upload_status = gr.Textbox(
                    label="Processing Status",
                    value="No file uploaded",
                    interactive=False,
                )

        # Event handlers
        run_script_button.click(
            fn=run_data_loader_script,
            inputs=[file_upload, output_path_input],
            outputs=upload_status,
        )
