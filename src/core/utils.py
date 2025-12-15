from typing import List

import json
from pathlib import Path

from loguru import logger
from ..baml_client import types
from ..core.models import ExperimentPlan

import base64
import mimetypes


def load_experiment_plans(filepath: Path) -> List[ExperimentPlan]:
    """Load experiment plans from a JSON file."""
    logger.info(f"Loading experiment plans from {filepath}")
    if not filepath.exists():
        logger.warning(f"Experiment plans file {filepath} does not exist")
        return []
    try:
        with filepath.open("r") as f:
            plans_data = json.load(f)
        logger.info(
            f"Successfully loaded {len(plans_data)} experiment plans from {filepath}"
        )
        plans = []
        for plan_data in plans_data:
            tools = []
            for tool_dict in plan_data.get("tools", []):
                type_name = tool_dict.pop("type", None)
                if type_name and hasattr(types, type_name):
                    tool_class = getattr(types, type_name)
                    try:
                        tool = tool_class(**tool_dict)
                        tools.append(tool)
                    except Exception as e:
                        logger.warning(
                            f"Failed to instantiate {type_name}: {e}"
                        )
                        tools.append("unknown")
                else:
                    tools.append("unknown")
            plans.append(
                ExperimentPlan(
                    filename=plan_data["experiment"], experiment=tools
                )
            )
        return plans
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to load experiment plans from {filepath}: {e}")
        return []


def read_file(file_path: Path) -> str:
    """Read a file's content. If it's a PDF, return base64-encoded content; otherwise, return text."""
    logger.info(f"Reading file: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type == "application/pdf":
        with open(file_path, "rb") as f:
            content = f.read()
        result = base64.b64encode(content).decode("utf-8")
    else:
        result = file_path.read_text()
    logger.info(f"Successfully read file: {file_path}")
    return result
