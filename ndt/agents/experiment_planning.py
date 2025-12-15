from typing import List

from loguru import logger

import json
from pathlib import Path

from ..core.project_manager import ProjectManager
from .experiment_api import call_exp_planner


def plan_experiments(
    experiments: List[dict], project_manager: ProjectManager
) -> List[dict]:
    """Plan experiments and return list of plans."""
    logger.info(f"Planning {len(experiments)} experiments")

    def plan_single_experiment(exp: dict) -> dict:
        exp_description = exp.get("experiment", "")
        filename = exp.get("filename", "")
        tools = call_exp_planner(
            str(exp_description),
            project_manager,
            filename,
        )
        return {
            "filename": filename,
            "tools": [tool.__dict__ for tool in tools],
            "approved": False,
        }

    return [plan_single_experiment(exp) for exp in experiments]


def save_experiment_plans(plans: List[dict], filepath: Path) -> None:
    """Save experiment plans to a JSON file."""
    with filepath.open("w") as f:
        json.dump(plans, f, indent=4)


def load_experiment_plans(filepath: Path) -> List[dict]:
    """Load experiment plans from a JSON file."""
    if not filepath.exists():
        return []
    try:
        with filepath.open("r") as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return []
