from pathlib import Path
from typing import List, Tuple

import gradio as gr

from ..agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ..core.models import (
    ChatMessage,
    ExperimentMetadata,
    ExperimentPlan,
    ExperimentStatus,
    MessageType,
)
from ..core.project_manager import ProjectManager
from .experiment_utils import (
    # approve_all_plans,
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


def get_scan_images(plots_dir: Path | None) -> Tuple[List[str], List[str]]:
    images = []
    if isinstance(plots_dir, Path) and plots_dir.exists():
        images = [
            str(plots_dir / f)
            for f in plots_dir.iterdir()
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif")
        ]
    return images, images


# def approve_scan(
#     selected_scan_image: str,
#     plans: List[ExperimentPlan],
#     plans_path: Path | None,
#     chatbot: List[ChatMessage],
# ) -> Tuple[List[ExperimentPlan], List[ChatMessage]]:
#     if not (selected_scan_image and plans and plans_path):
#         return plans, chatbot

#     filename = Path(selected_scan_image).stem
#     plan = next((p for p in plans if p.id == filename), None)
#     if plan:
#         plan.status = ExperimentStatus.COMPLETED
#         save_experiment_plans(plans, plans_path)
#         return plans, chatbot + [
#             create_message(
#                 content=f"Scan approved for `{plan.filename}`",
#                 message_type=MessageType.STATUS,
#             )
#         ]
#     return plans, chatbot


def reject_scan(
    selected_scan_image: str,
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    chatbot: List[ChatMessage],
) -> Tuple[List[ExperimentPlan], List[ChatMessage]]:
    if not (selected_scan_image and plans and plans_path):
        return plans, chatbot

    filename = Path(selected_scan_image).stem
    plan = next((p for p in plans if p.id == filename), None)
    if plan:
        plan.status = ExperimentStatus.RESCAN
        save_experiment_plans(plans, plans_path)
        return plans, chatbot + [
            create_message(
                content=f"Scan rejected for `{plan.filename}`",
                message_type=MessageType.STATUS,
            )
        ]
    return plans, chatbot


def select_scan_image(evt: gr.SelectData, images):
    return images[evt.index] if evt.index is not None else None


def create_experiment_tab(
    project_state: gr.State,
    chatbot: gr.Chatbot,
) -> gr.Tabs:
    plans, plans_path, plots_dir = [], None, None

    project_manager: ProjectManager = project_state.value
    metadata = project_manager.get_mode_metadata
    if isinstance(metadata, ExperimentMetadata):
        plans_path = metadata.plans_path
        plots_dir = metadata.plots_dir_path

        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path, log=True)

    filenames = [plan.filename for plan in plans]
    ids = [plan.id for plan in plans]
    initial_data = convert_plan_to_table_data(plans[0]) if plans else []
    initial_status = plans[0].status.value if plans else ""
    statuses = get_experiment_statuses(plans)

    # gradio states
    plans_state = gr.State(plans)
    plans_path_state = gr.State(plans_path)
    plots_dir_state = gr.State(plots_dir)
    log_state = gr.State(False)

    with gr.Tabs() as interface:
        # ================ Scan Status tab =============================
        with gr.TabItem("Scan Status"):
            scan_status_table = gr.Dataframe(
                headers=["Experiment Name", "Status"],
                value=[[f, s] for f, s in zip(filenames, statuses)],
                interactive=False,
            )

            with gr.Row():
                # approve_all_button = gr.Button("✅ Approve all plans")
                start_scan_button = gr.Button("▶️ Start scan")
                delete_all_experiments_button = gr.Button(
                    "🗑️ Delete all experiments"
                )

            # link to logic
            # approve_all_button.click(
            #     lambda plans, plans_path, current_chatbot: (
            #         approve_all_plans(plans, plans_path),
            #         current_chatbot
            #         + [
            #             create_message(
            #                 content="All plans approved",
            #                 message_type=MessageType.STATUS,
            #             )
            #         ],
            #     ),
            #     inputs=[plans_state, plans_path_state, chatbot],
            #     outputs=[scan_status_table, chatbot],
            # )

            delete_all_experiments_button.click(
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
                outputs=[scan_status_table, plans_state, chatbot],
            )

            start_scan_button.click(
                start_execution,
                inputs=[
                    plans_path_state,
                    chatbot,
                    project_state,
                ],
                outputs=[scan_status_table, chatbot],
            )

            timer = gr.Timer(0.1)
            timer.tick(
                update_scan_status,
                inputs=[plans_path_state, log_state],
                outputs=scan_status_table,
            )

        # ================ Plan Viewer tab =============================
        with gr.TabItem("Plan Viewer"):
            with gr.Row():
                experiment_dropdown = gr.Dropdown(
                    choices=[(f, i) for f, i in zip(filenames, ids)],
                    label="Select Experiment",
                    value=ids[0] if ids else None,
                )

                experiment_status_dropdown = gr.Dropdown(
                    choices=[status.value for status in ExperimentStatus],
                    label="Change Status",
                    value=initial_status,
                )

            delete_experiment_button = gr.Button("🗑️ Delete Experiment")

            experiment_details_table = gr.Dataframe(
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
                save_changes_button = gr.Button("💾 Save Changes")
                reload_plans_button = gr.Button("🔄 Reload Plans")
            experiment_dropdown.change(
                lambda selected_id, current_plans: (
                    update_experiment_details(current_plans, selected_id),
                    get_experiment_status(current_plans, selected_id),
                ),
                inputs=[experiment_dropdown, plans_state],
                outputs=[experiment_details_table, experiment_status_dropdown],
            )

            # link to logic
            save_changes_button.click(
                save_experiment_changes,
                inputs=[
                    plans_state,
                    plans_path_state,
                    experiment_dropdown,
                    experiment_details_table,
                ],
                outputs=[plans_state],
            )
            reload_plans_button.click(
                lambda: reload_plans(plans_path),
                inputs=[],
                outputs=[
                    experiment_dropdown,
                    experiment_details_table,
                    experiment_status_dropdown,
                    plans_state,
                ],
            )

            delete_experiment_button.click(
                delete_experiment,
                inputs=[plans_state, plans_path_state, experiment_dropdown],
                outputs=[
                    experiment_dropdown,
                    experiment_details_table,
                    experiment_status_dropdown,
                    plans_state,
                ],
            )

            experiment_status_dropdown.change(
                update_experiment_status,
                inputs=[
                    plans_state,
                    plans_path_state,
                    experiment_dropdown,
                    experiment_status_dropdown,
                ],
                outputs=[plans_state],
            )

        # ================ View Data tab =============================
        with gr.TabItem("Data Viewer"):
            initial_scan_images, _ = get_scan_images(plots_dir)

            scan_images_state = gr.State(initial_scan_images)
            selected_scan_image_state = gr.State(None)

            scan_image_gallery = gr.Gallery(
                value=initial_scan_images,
                label="Image Gallery",
                height=400,
                columns=3,
                allow_preview=True,
            )

            scan_image_gallery.select(
                select_scan_image,
                inputs=[scan_images_state],
                outputs=selected_scan_image_state,
            )

            with gr.Row():
                approve_scan_button = gr.Button("✅ Approve Scan")
                reject_scan_button = gr.Button("❌ Reject Scan")

            # approve_scan_button.click(
            #     approve_scan,
            #     inputs=[
            #         selected_scan_image_state,
            #         plans_state,
            #         plans_path_state,
            #         chatbot,
            #     ],
            #     outputs=[plans_state, chatbot],
            # )

            reject_scan_button.click(
                reject_scan,
                inputs=[
                    selected_scan_image_state,
                    plans_state,
                    plans_path_state,
                    chatbot,
                ],
                outputs=[plans_state, chatbot],
            )

            timer_data = gr.Timer(1)
            timer_data.tick(
                get_scan_images,
                inputs=[plots_dir_state],
                outputs=[scan_image_gallery, scan_images_state],
            )

    return interface
