import gradio as gr


def create_quick_actions_ui(
    chatbot: gr.Chatbot, msg: gr.Textbox, ctx: gr.State
):
    """
    Creates a set of buttons for quick actions that send predefined messages to the chatbot.
    """
    with gr.Column():
        gr.Markdown("## Quick Actions")
        gr.Markdown("Click a button to send a predefined message to the agent.")

        with gr.Walkthrough(selected=1) as walkthrough:
            with gr.Step("Idea", id=1):
                gr.Markdown("## Idea")
                gr.Markdown(
                    "This tab is for managing idea, plans, and system specifications."
                )
                next_btn = gr.Button("Next: Experiments")
                next_btn.click(
                    lambda: gr.Walkthrough(selected=2), outputs=walkthrough
                )

            with gr.Step("Experiments", id=2):
                gr.Markdown("## Experiments")
                gr.Markdown("This tab is for experiment planning and approval.")
                with gr.Row():
                    prev_btn = gr.Button("Prev: Idea")
                    next_btn = gr.Button("Next: Data Science")
                prev_btn.click(
                    lambda: gr.Walkthrough(selected=1), outputs=walkthrough
                )
                next_btn.click(
                    lambda: gr.Walkthrough(selected=3), outputs=walkthrough
                )

            with gr.Step("Data Science", id=3):
                gr.Markdown("## Data Science")
                gr.Markdown("This tab is for data science tasks.")
                with gr.Row():
                    prev_btn = gr.Button("Prev: Experiments")
                    next_btn = gr.Button("Next: Reporting")
                prev_btn.click(
                    lambda: gr.Walkthrough(selected=2), outputs=walkthrough
                )
                next_btn.click(
                    lambda: gr.Walkthrough(selected=4), outputs=walkthrough
                )

            with gr.Step("Reporting", id=4):
                gr.Markdown("## Reporting")
                gr.Markdown("This tab is for generating reports.")
                prev_btn = gr.Button("Prev: Data Science")
                prev_btn.click(
                    lambda: gr.Walkthrough(selected=3), outputs=walkthrough
                )

    return
