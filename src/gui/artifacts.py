import gradio as gr

from ..core.project_manager import ProjectManager
from .tab_experiments import create_experiments_tab


def create_sidebar(
    project_manager: ProjectManager,
    chatbot: gr.Chatbot,
) -> gr.Column:
    """Create the sidebar with experiments content."""
    with gr.Column(scale=1) as sidebar_column:
        gr.Markdown("## Experiment Planning and Approval")
        create_experiments_tab(project_manager, chatbot)

    return sidebar_column


def toggle_sidebar(show: bool) -> gr.Column:
    """Toggle sidebar visibility"""
    return gr.Column(visible=show)
