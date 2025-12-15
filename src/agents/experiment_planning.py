from typing import Dict, List, Union

import json
from pathlib import Path

from loguru import logger
from ..core.models import ExperimentTool


def save_experiment_plans(
    plans: List[dict], filepath: Path
) -> Dict[str, Union[bool, str]]:
    """Save experiment plans to a JSON file."""
    logger.info(f"Saving experiment plans to {filepath}")
    try:
        with filepath.open("w") as f:
            json.dump(plans, f, indent=4)
        logger.info(
            f"Successfully saved {len(plans)} experiment plans to {filepath}"
        )
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to save experiment plans to {filepath}: {e}")
        return {"success": False, "error": str(e)}


def load_experiment_plans(filepath: Path) -> List[dict]:
    """Load experiment plans from a JSON file."""
    logger.info(f"Loading experiment plans from {filepath}")
    if not filepath.exists():
        logger.warning(f"Experiment plans file {filepath} does not exist")
        return []
    try:
        with filepath.open("r") as f:
            plans = json.load(f)
        logger.info(
            f"Successfully loaded {len(plans)} experiment plans from {filepath}"
        )
        return plans
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to load experiment plans from {filepath}: {e}")
        return []
