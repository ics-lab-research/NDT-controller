import json
import uuid
from pathlib import Path
from typing import Dict, List, Union

from loguru import logger

from ..baml_client import types as baml_types
from ..core.models import ExperimentPlan, ExperimentStatus


def save_experiment_plans(
    plans: List[ExperimentPlan],
    filepath: Path,
) -> Dict[str, Union[bool, str]]:
    """Save experiment plans to a JSON file."""
    logger.info(f"Saving experiment plans to {filepath}")
    try:
        formatted_plans = [
            {
                "id": plan.id,
                "experiment": plan.filename,
                "tools": [
                    {"type": type(tool).__name__, **tool.__dict__}
                    for tool in plan.experiment
                ],
                "status": plan.status.value,
            }
            for plan in plans
        ]
        with filepath.open("w") as f:
            json.dump(formatted_plans, f, indent=4)
        logger.info(
            f"Successfully saved {len(plans)} experiment plans to {filepath}"
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to save experiment plans to {filepath}: {e}")
        return {"success": False, "error": str(e)}


def append_experiment_plans(
    plans: List[ExperimentPlan],
    filepath: Path,
) -> Dict[str, Union[bool, str]]:
    """Append experiment plans to an existing JSON file."""
    logger.info(f"Appending experiment plans to {filepath}")
    try:
        existing_plans = load_experiment_plans(filepath, log=True)
        combined_plans = existing_plans + plans
        return save_experiment_plans(combined_plans, filepath)
    except Exception as e:
        logger.error(f"Failed to append experiment plans to {filepath}: {e}")
        return {"success": False, "error": str(e)}


def load_experiment_plans(
    filepath: Path, log: bool = False
) -> List[ExperimentPlan]:
    """Load experiment plans from a JSON file."""
    if log:
        logger.info(f"Loading experiment plans from {filepath}")
    if not filepath.exists():
        if log:
            logger.error(f"Experiment plans file {filepath} does not exist")
        return []
    try:
        with filepath.open("r") as f:
            plans_data = json.load(f)
        if log:
            logger.info(
                f"Successfully loaded {len(plans_data)} experiment plans from {filepath}"
            )
        plans = []
        for plan_data in plans_data:
            tools = []
            for tool_dict in plan_data.get("tools", []):
                type_name = tool_dict.pop("type", None)
                if type_name and hasattr(baml_types, type_name):
                    tool_class = getattr(baml_types, type_name)
                    try:
                        tool = tool_class(**tool_dict)
                        tools.append(tool)
                    except Exception as e:
                        if log:
                            logger.error(
                                f"Failed to instantiate {type_name}: {e}"
                            )
                        tools.append("unknown")
                else:
                    tools.append("unknown")
            plans.append(
                ExperimentPlan(
                    id=plan_data.get("id", str(uuid.uuid4())),
                    filename=plan_data["experiment"],
                    experiment=tools,
                    status=ExperimentStatus(
                        plan_data.get(
                            "status", ExperimentStatus.NOT_APPROVED.value
                        )
                    ),
                )
            )
        return plans
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to load experiment plans from {filepath}: {e}")
        return []
