import gradio as gr

from ..core.project_manager import ProjectManager
from .tab_data_science import create_data_science_tab
from .tab_experiments import create_experiments_tab
from .tab_idea import create_idea_tab
from .tab_quick_actions import create_quick_actions_ui
from .tab_reporting import create_reporting_tab


def create_sidebar(
    project_manager: ProjectManager,
    chatbot: gr.Chatbot,
    msg: gr.Textbox,
    ctx: gr.State,
) -> gr.Column:
    """Create the sidebar with tabs for different content areas."""
    with gr.Column(scale=1) as sidebar_column:
        with gr.Tabs():
            with gr.TabItem("Quick Actions"):
                create_quick_actions_ui(chatbot, msg, ctx)

            with gr.TabItem("Idea"):
                gr.Markdown("## Idea, Plans, and System Specifications")
                create_idea_tab(project_manager)

            with gr.TabItem("Experiments"):
                gr.Markdown("## Experiment Planning and Approval")
                create_experiments_tab(project_manager)

            with gr.TabItem("Data Science"):
                gr.Markdown("## Data Science")
                create_data_science_tab()

            with gr.TabItem("Reporting"):
                gr.Markdown("## Reporting")
                create_reporting_tab(project_manager)

    return sidebar_column


def toggle_sidebar(show: bool) -> gr.Column:
    """Toggle sidebar visibility"""
    return gr.Column(visible=show)
