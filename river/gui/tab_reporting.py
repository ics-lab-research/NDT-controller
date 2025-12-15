import base64
from pathlib import Path

import gradio as gr

from ..core.project_manager import ProjectManager
from ..core.models import Mode, ReportingMetadata


def generate_pdf_html(b64: str) -> str:
    """Generate HTML for displaying PDF using base64."""
    return f"""
    <div style="width:100%; height:670px;">
        <object
            data="data:application/pdf;base64,{b64}"
            type="application/pdf"
            width="100%"
            height="100%">
            <embed
                src="data:application/pdf;base64,{b64}"
                type="application/pdf"
                width="100%"
                height="100%" />
        </object>
    </div>
    """


def display_pdf(file: str | Path | None) -> str | None:
    """Display PDF as HTML if file exists, else return error message."""
    if file is None:
        return None

    file_path = Path(file)
    if not file_path.exists():
        return "<p>PDF file not found.</p>"

    try:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
    except OSError as e:
        raise ValueError(f"Error reading PDF file: {e}")

    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return generate_pdf_html(b64)


def create_reporting_tab(project_manager: ProjectManager) -> gr.HTML:
    """Create Gradio tab for reporting with PDF display."""
    metadata = project_manager.get_mode_metadata(Mode.REPORTING)
    if not isinstance(metadata, ReportingMetadata):
        raise TypeError("Expected ReportingMetadata for reporting mode")

    pdf_path = metadata.output_pdf_path

    with gr.Tabs():
        with gr.TabItem("Output PDF"):
            pdf_html = gr.HTML(display_pdf(pdf_path))
            reload_btn = gr.Button("Reload PDF")
            reload_btn.click(fn=lambda: display_pdf(pdf_path), outputs=pdf_html)

    return pdf_html
