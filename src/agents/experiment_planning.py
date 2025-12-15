from typing import Dict, List, Union

import json
from pathlib import Path

from loguru import logger
from ..core.models import ExperimentPlan


def save_experiment_plans(
    plans: List[ExperimentPlan],
    filepath: Path,
) -> Dict[str, Union[bool, str]]:
    """Save experiment plans to a JSON file."""
    logger.info(f"Saving experiment plans to {filepath}")
    try:
        formatted_plans = [
            {
                "experiment": plan.filename,
                "tools": [
                    {"type": type(tool).__name__, **tool.__dict__}
                    for tool in plan.experiment
                ],
                "approved": False,
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
