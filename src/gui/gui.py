import gradio as gr
from .chat import (
    create_chat_interface,
    handle_mode_change,
    clear_chat,
    respond_stream,
)
from .artifacts import create_sidebar, toggle_sidebar
from ..core.project_manager import init_project_context
from ..core.models import Mode

custom_css = """
.gradio-container {
    height: 100vh !important;
    display: flex;
    flex-direction: column;
    overflow: auto;
}
  
/* --- Chat area --- */
.chatbot-container {
    flex: 1 1 auto;
    height: 65vh !important;       /* ⚖️ good balance */
    max-height: 65vh !important;
    overflow-y: auto !important;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 4px;
}
    
/* --- PDF viewer area --- */
.scrollable-pdf {
    overflow-y: auto !important;
    height: 75vh !important;       /* PDF scrolls internally */
    max-height: 75vh !important;
    border: 1px solid #444;
    border-radius: 8px;
    background-color: #1e1e1e;
    padding: 4px;
}
  
.scrollable-pdf iframe {
    width: 100%;
    height: 100%;
    display: block;
    border: none;
}
"""


def create_main_interface() -> gr.Blocks:
    """Create the main GUI interface with tabs."""
    with gr.Blocks(
        title="River Chat",
        fill_width=True,
        fill_height=True,
        css=custom_css,
    ) as iface:
        # State
        project_manager = init_project_context()

        # NOTE: set mode to test
        project_manager.set_mode(Mode.EXPERIMENTS)
        current_context = gr.State(project_manager)

        with gr.Row():
            with gr.Column():
                with gr.Row():
                    with gr.Column(scale=3):
                        gr.Markdown("# River Chat")

                    with gr.Column(scale=1):
                        show_sidebar = gr.Checkbox(
                            label="Show Sidebar",
                            value=False,
                            elem_classes="checkbox-group",
                            min_width=100,
                        )

                with gr.Row():
                    # Chat Column
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        - Choose your interaction mode from the dropdown menu
                        - Type your message and press Enter to send
                        """)

                        (
                            chatbot,
                            msg,
                            mode_dropdown,
                            clear,
                        ) = create_chat_interface(project_manager)

                    # Sidebar with tabs (hidden by default)
                    sidebar = gr.Sidebar(label="Sidebar", open=False)
                    with sidebar:
                        gr.Markdown("Dummy text for important information")

        # Wire up events (only for Chat tab)
        msg.submit(
            respond_stream,
            inputs=[msg, chatbot, current_context],
            outputs=[
                chatbot,
                msg,
            ],
        )

        clear.click(clear_chat, outputs=[chatbot, msg])

        mode_dropdown.select(
            handle_mode_change,
            inputs=[mode_dropdown, current_context],
            outputs=[current_context],
        )

        show_sidebar.change(
            lambda x: gr.update(open=x),
            inputs=[show_sidebar],
            outputs=[sidebar],
        )

    return iface
