from pathlib import Path
from typing import List, Tuple

import gradio as gr

from ...agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ...core.models import (
    ChatMessage,
    ExperimentPlan,
    ExperimentStatus,
    MessageType,
)
from ..chat_utils import create_message


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
    plans_path: Path | None,
    chatbot: List[ChatMessage],
) -> Tuple[List[ExperimentPlan], List[ChatMessage]]:
    if not (selected_scan_image and plans_path):
        return [], chatbot

    # Reload plans to get latest state
    plans = load_experiment_plans(plans_path, log=True)

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
