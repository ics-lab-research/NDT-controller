from pathlib import Path

import gradio as gr

from ..agents.experiment_planning import load_experiment_plans
from ..core.models import (
    ExperimentMetadata,
    ExperimentStatus,
    MessageType,
    Mode,
)
from ..core.project_manager import ProjectManager
from .experiment_utils import (
    approve_all_plans,
    convert_plan_to_table_data,
    create_message,
    delete_all_experiments,
    delete_experiment,
    get_experiment_status,
    get_experiment_statuses,
    reload_plans,
    save_experiment_changes,
    start_execution,
    update_experiment_details,
    update_experiment_status,
    update_scan_status,
)


def create_experiment_tab(
    project_state: gr.State,
    chatbot: gr.Chatbot,
) -> gr.Tabs:
    project_manager: ProjectManager = project_state.value
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENT)
    plans = []
    plans_path = None
    if isinstance(metadata, ExperimentMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path, log=True)
    filenames = [plan.filename for plan in plans]
    ids = [plan.id for plan in plans]
    initial_data = convert_plan_to_table_data(plans[0]) if plans else []
    initial_status = plans[0].status.value if plans else ""
    plans_state = gr.State(plans)
    statuses = get_experiment_statuses(plans)
    plans_path_state = gr.State(plans_path)
    log_state = gr.State(False)

    with gr.Tabs() as interface:
        # ================ Scan Status tab =============================
        with gr.TabItem("Scan Status"):
            status_df = gr.Dataframe(
                headers=["Experiment Name", "Status"],
                value=[[f, s] for f, s in zip(filenames, statuses)],
                interactive=False,
            )

            with gr.Row():
                approve_button = gr.Button("✅ Approve all plans")
                start_button = gr.Button("▶️ Start scan")

            delete_all_button = gr.Button("🗑️ Delete all experiments")

            # link to logic
            approve_button.click(
                lambda plans, plans_path, current_chatbot: (
                    approve_all_plans(plans, plans_path),
                    current_chatbot
                    + [
                        create_message(
                            content="All plans approved",
                            message_type=MessageType.STATUS,
                        )
                    ],
                ),
                inputs=[plans_state, plans_path_state, chatbot],
                outputs=[status_df, chatbot],
            )

            delete_all_button.click(
                lambda plans, plans_path, current_chatbot: (
                    delete_all_experiments(plans, plans_path),
                    [],
                    current_chatbot
                    + [
                        create_message(
                            content="All experiments deleted",
                            message_type=MessageType.STATUS,
                        )
                    ],
                ),
                inputs=[plans_state, plans_path_state, chatbot],
                outputs=[status_df, plans_state, chatbot],
            )

            start_button.click(
                start_execution,
                inputs=[
                    plans_state,
                    plans_path_state,
                    chatbot,
                    project_state,
                ],
                outputs=[status_df, chatbot],
            )

            timer = gr.Timer(0.1)
            timer.tick(
                update_scan_status,
                inputs=[plans_path_state, log_state],
                outputs=status_df,
            )

        # ================ Plan Viewer tab =============================
        with gr.TabItem("Plan Viewer"):
            with gr.Row():
                exp_dropdown = gr.Dropdown(
                    choices=[(f, i) for f, i in zip(filenames, ids)],
                    label="Select Experiment",
                    value=ids[0] if ids else None,
                )

                status_dropdown = gr.Dropdown(
                    choices=[status.value for status in ExperimentStatus],
                    label="Change Status",
                    value=initial_status,
                )

            delete_button = gr.Button("🗑️ Delete Experiment")

            details_df = gr.Dataframe(
                headers=[
                    "Step Name",
                    "Tool Name",
                    "Parameter 1",
                    "Parameter 2",
                ],
                value=initial_data,
                interactive=True,
                column_widths=[150, 100, 200, 200],
            )
            with gr.Row():
                save_button = gr.Button("💾 Save Changes")
                reload_button = gr.Button("🔄 Reload Plans")
            exp_dropdown.change(
                lambda selected_id, current_plans: (
                    update_experiment_details(current_plans, selected_id),
                    get_experiment_status(current_plans, selected_id),
                ),
                inputs=[exp_dropdown, plans_state],
                outputs=[details_df, status_dropdown],
            )

            # link to logic
            save_button.click(
                save_experiment_changes,
                inputs=[
                    plans_state,
                    plans_path_state,
                    exp_dropdown,
                    details_df,
                ],
                outputs=[plans_state],
            )
            reload_button.click(
                lambda: reload_plans(plans_path),
                inputs=[],
                outputs=[
                    exp_dropdown,
                    details_df,
                    status_dropdown,
                    plans_state,
                ],
            )

            delete_button.click(
                delete_experiment,
                inputs=[plans_state, plans_path_state, exp_dropdown],
                outputs=[
                    exp_dropdown,
                    details_df,
                    status_dropdown,
                    plans_state,
                ],
            )

            status_dropdown.change(
                update_experiment_status,
                inputs=[
                    plans_state,
                    plans_path_state,
                    exp_dropdown,
                    status_dropdown,
                ],
                outputs=[plans_state],
            )

        # ================ View Data tab =============================
        with gr.TabItem("Data Viewer"):
            pass

    return interface
