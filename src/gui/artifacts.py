import gradio as gr

from .tab_experiment import create_experiments_tab


def create_sidebar(
    project_state: gr.State,
    chatbot: gr.Chatbot,
) -> gr.Column:
    """Create the sidebar with experiments content."""
    with gr.Column(scale=1) as sidebar_column:
        gr.Markdown("## Experiment Planning and Approval")
        create_experiments_tab(project_state, chatbot)

    return sidebar_column
