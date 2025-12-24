from pathlib import Path
from typing import Generator, List, Tuple

import gradio as gr
from loguru import logger

from ..agents.experiment_execution import execute_multiple_plans
from ..agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ..core.models import (
    ChatHistory,
    ExperimentPlan,
    ExperimentsMetadata,
    ExperimentStatus,
    MessageType,
    Mode,
)
from ..core.project_manager import ProjectManager
from .utils import (
    convert_plan_to_table_data,
    create_message,
    save_experiment_changes,
    update_experiment_details,
)


def get_experiment_status(
    plans: List[ExperimentPlan], selected_filename: str
) -> str:
    """Gets the status value for the selected experiment."""
    plan = next((p for p in plans if p.filename == selected_filename), None)
    return plan.status.value if plan else ""


def update_scan_status(
    plans_path: Path | None, log: bool = False
) -> gr.Dataframe:
    if not plans_path:
        return gr.Dataframe(value=[])
    try:
        plans = load_experiment_plans(plans_path, log=log)
        filenames = [plan.filename for plan in plans]
        statuses = _get_experiment_statuses(plans)
        return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])
    except Exception as e:
        if log:
            logger.error(f"Error updating scan status: {e}")
        return gr.Dataframe(value=[])


def _get_experiment_statuses(
    plans: List[ExperimentPlan],
) -> List[str]:
    return [plan.status.value for plan in plans]


def approve_all_plans(
    plans: List[ExperimentPlan], plans_path: Path | None
) -> gr.Dataframe:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return gr.Dataframe(value=[])
    for plan in plans:
        if plan.status == ExperimentStatus.NOT_APPROVED:
            plan.status = ExperimentStatus.APPROVED
    try:
        save_experiment_plans(plans, plans_path)
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        gr.Info(error_msg)
    filenames = [plan.filename for plan in plans]
    statuses = _get_experiment_statuses(plans)
    return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])


def start_all_approved_plans(
    plans: List[ExperimentPlan], plans_path: Path | None
) -> gr.Dataframe:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return gr.Dataframe(value=[])
    for plan in plans:
        if plan.status == ExperimentStatus.APPROVED:
            plan.status = ExperimentStatus.PENDING
    try:
        save_experiment_plans(plans, plans_path)
    except Exception as e:
        error_msg = f"Error saving plans: {e}"
        logger.error(error_msg)
        gr.Info(error_msg)
    filenames = [plan.filename for plan in plans]
    statuses = _get_experiment_statuses(plans)
    return gr.Dataframe(value=[[f, s] for f, s in zip(filenames, statuses)])


def reload_plans(
    plans_path: Path | None,
) -> Tuple[gr.Dropdown, gr.Dataframe, str, List[ExperimentPlan]]:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []
    try:
        plans = load_experiment_plans(plans_path, log=True)
        filenames = [plan.filename for plan in plans]
        initial_data = convert_plan_to_table_data(plans[0]) if plans else []
        initial_status = plans[0].status.value if plans else ""
        gr.Info("Successfully reloaded experiment plans")
        return (
            gr.Dropdown(
                choices=filenames, value=filenames[0] if filenames else None
            ),
            gr.Dataframe(value=initial_data),
            initial_status,
            plans,
        )
    except Exception as e:
        error_msg = f"Error reloading plans: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg)
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []


def delete_experiment(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_filename: str,
) -> Tuple[gr.Dropdown, gr.Dataframe, str, List[ExperimentPlan]]:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []
    try:
        # Find and remove the plan
        plans = [p for p in plans if p.filename != selected_filename]
        save_experiment_plans(plans, plans_path)
        filenames = [plan.filename for plan in plans]
        initial_data = convert_plan_to_table_data(plans[0]) if plans else []
        initial_status = plans[0].status.value if plans else ""
        gr.Info("Experiment deleted successfully")
        return (
            gr.Dropdown(
                choices=filenames, value=filenames[0] if filenames else None
            ),
            gr.Dataframe(value=initial_data),
            initial_status,
            plans,
        )
    except Exception as e:
        error_msg = f"Error deleting experiment: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg)
        return gr.Dropdown(choices=[]), gr.Dataframe(value=[]), "", []


def update_experiment_status(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_filename: str,
    new_status: str,
) -> List[ExperimentPlan]:
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return plans
    try:
        for plan in plans:
            if plan.filename == selected_filename:
                plan.status = ExperimentStatus(new_status)
                break
        save_experiment_plans(plans, plans_path)
        gr.Info("Experiment status updated successfully")
        return plans
    except Exception as e:
        error_msg = f"Error updating experiment status: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg)
        return plans


def start_execution(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    current_chatbot: ChatHistory,
    project_manager: ProjectManager,
) -> Generator[Tuple[gr.Dataframe, ChatHistory], None, None]:
    if not plans_path:
        yield (
            gr.Dataframe(value=[]),
            current_chatbot
            + [
                create_message(
                    content="Error: Plans path not configured",
                    message_type=MessageType.STATUS,
                )
            ],
        )
        return
    approved_plans = [p for p in plans if p.status == ExperimentStatus.APPROVED]
    if approved_plans:
        # Set to PENDING
        for plan in approved_plans:
            plan.status = ExperimentStatus.PENDING
        try:
            save_experiment_plans(plans, plans_path)
        except Exception as e:
            error_msg = f"Error saving plans: {e}"
            logger.error(error_msg)
            yield (
                update_scan_status(plans_path),
                current_chatbot
                + [
                    create_message(
                        content=error_msg, message_type=MessageType.STATUS
                    )
                ],
            )
            return

    # Execute all plans
    execution_gen = execute_multiple_plans(plans, project_manager)
    status_index = None
    try:
        for message in execution_gen:
            if status_index is None:
                current_chatbot = current_chatbot + [
                    create_message(
                        content=message, message_type=MessageType.STATUS
                    )
                ]
                status_index = len(current_chatbot) - 1
            else:
                current_chatbot[status_index]["content"] = message
            yield update_scan_status(plans_path), current_chatbot
    except StopIteration as e:
        error = e.value
        if error:
            if status_index is None:
                current_chatbot = current_chatbot + [
                    create_message(
                        content=f"Execution error: {error.error_message}",
                        message_type=MessageType.STATUS,
                    )
                ]
            else:
                current_chatbot[status_index]["content"] = (
                    f"Execution error: {error.error_message}"
                )
            yield update_scan_status(plans_path), current_chatbot


def create_experiments_tab(
    project_manager: ProjectManager,
    chatbot: gr.Chatbot,
) -> gr.Tabs:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans = []
    plans_path = None
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path, log=True)
    filenames = [plan.filename for plan in plans]
    initial_data = convert_plan_to_table_data(plans[0]) if plans else []
    initial_status = plans[0].status.value if plans else ""
    plans_state = gr.State(plans)
    statuses = _get_experiment_statuses(plans)
    plans_path_state = gr.State(plans_path)
    log_state = gr.State(False)
    project_manager_state = gr.State(project_manager)

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

            start_button.click(
                start_execution,
                inputs=[
                    plans_state,
                    plans_path_state,
                    chatbot,
                    project_manager_state,
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
                    choices=filenames,
                    label="Select Experiment",
                    value=filenames[0] if filenames else None,
                )

                status_dropdown = gr.Dropdown(
                    choices=[status.value for status in ExperimentStatus],
                    label="Change Status",
                    value=initial_status,
                )

            delete_button = gr.Button("🗑️ Delete Experiment")

            details_df = gr.Dataframe(
                headers=["Tool Name", "Parameter 1", "Parameter 2"],
                value=initial_data,
                interactive=True,
            )
            with gr.Row():
                save_button = gr.Button("💾 Save Changes")
                reload_button = gr.Button("🔄 Reload Plans")
            exp_dropdown.change(
                lambda filename, current_plans: (
                    update_experiment_details(current_plans, filename),
                    get_experiment_status(current_plans, filename),
                ),
                inputs=[exp_dropdown, plans_state],
                outputs=[details_df, status_dropdown],
            )
            save_button.click(
                lambda filename, data, current_plans: save_experiment_changes(
                    current_plans, plans_path, filename, data
                ),
                inputs=[exp_dropdown, details_df, plans_state],
                outputs=[],
            )
            reload_button.click(
                lambda: reload_plans(plans_path),
                inputs=[],
                outputs=[exp_dropdown, details_df, status_dropdown, plans_state],
            )

            delete_button.click(
                delete_experiment,
                inputs=[plans_state, plans_path_state, exp_dropdown],
                outputs=[exp_dropdown, details_df, status_dropdown, plans_state],
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

    return interface
