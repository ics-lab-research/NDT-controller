from typing import List


import json
from pathlib import Path


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
