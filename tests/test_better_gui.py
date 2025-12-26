import gradio as gr


def noop():
    return "Ready"


with gr.Blocks(title="NDT Agent – Step Review") as demo:
    gr.Markdown("## 🧠 Agent Execution Plan (Review Mode)")

    with gr.Accordion("Step 0 – Initialization", open=False):
        gr.Markdown("""
**• ConnectToVITool**
- `vi_path`: `example.vi`
        """)

    with gr.Accordion("Step 1 – Configure Signal (Gaussian)", open=True):
        gr.Markdown("""
**• SelectTabTool**
- `tab`: Pulse Types

**• SetNumericControlTool**
- `Gauss freq (Hz)`: 1000  
- `Gauss amp`: 10  
- `Gauss atten (dB)`: 3  
- `Gauss Nor. Band`: 0.8
        """)

    with gr.Accordion("Step 2.1 – Pre-configure Grid Scan (20×20)", open=False):
        gr.Markdown("""
**• SelectTabTool**
- `tab`: Measurement Mode

**• SetNumericControlTool**
- `X Auto Distance`: 20  
- `Y Auto Distance`: 20
        """)

    with gr.Accordion("Step 2.2 – Execute Grid Scan", open=False):
        gr.Markdown("""
**• SetButtonStateTool**
- `button`: Scan

**• WaitForOperationCompleteTool**
- `operation`: SCAN ⏳
        """)

    gr.Button("Run (disabled in review)", interactive=False)

demo.launch()
