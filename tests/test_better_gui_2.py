import gradio as gr


def noop():
    return "Ready"


with gr.Blocks(title="NDT Agent – Timeline View") as demo:
    gr.Markdown("## ⏱️ Agent Execution Timeline")

    def timeline_step(title, body, icon="➡️"):
        with gr.Row():
            gr.Markdown(f"### {icon} {title}")
        with gr.Row():
            gr.Markdown(body)

    timeline_step(
        "Step 0 – Initialization",
        """
- **ConnectToVITool**
  - `vi_path`: `example.vi`
        """,
        icon="⚙️",
    )

    timeline_step(
        "Step 1 – Configure Signal (Gaussian)",
        """
- Select **Pulse Types** tab  
- Set **Gauss freq (Hz)** = 1000  
- Set **Gauss amp** = 10  
- Set **Gauss atten (dB)** = 3  
- Set **Gauss Nor. Band** = 0.8
        """,
        icon="🎛️",
    )

    timeline_step(
        "Step 2.1 – Pre-configure Grid Scan (20×20)",
        """
- Set **X Auto Distance** = 20  
- Set **Y Auto Distance** = 20
        """,
        icon="📐",
    )

    timeline_step(
        "Step 2.2 – Execute Grid Scan",
        """
- Press **Scan** button  
- ⏳ **Wait until SCAN operation completes**
        """,
        icon="🟡",
    )

    gr.Markdown("---")
    gr.Button("Run (disabled in review)", interactive=False)

demo.launch()
