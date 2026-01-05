import os
from pathlib import Path
from typing import Dict

from .models import ExperimentMetadata, Mode, ModeMetadata


def get_experiment_metadata(pwd_path: Path) -> ExperimentMetadata:
    """Build experiments metadata from env vars."""
    experiments_base = os.environ.get("EXPERIMENT_BASE")
    vi_path = os.environ.get("EXPERIMENT_VI_PATH")
    plans_path = os.environ.get("EXPERIMENT_PLANS_PATH")
    data_path = os.environ.get("EXPERIMENT_DATA_PATH")

    if experiments_base is None:
        raise ValueError("Environment variables EXPERIMENT_BASE must be set")
    if vi_path is None:
        raise ValueError("Environment variables EXPERIMENT_VI_PATH must be set")
    if data_path is None:
        raise ValueError(
            "Environment variables EXPERIMENT_DATA_PATH must be set"
        )
    if plans_path is None:
        raise ValueError(
            "Environment variables EXPERIMENT_PLANS_PATH must be set"
        )

    return ExperimentMetadata(
        data_dir_path=pwd_path / experiments_base / data_path,
        plans_path=pwd_path / experiments_base / plans_path,
        vi_path=Path(vi_path),
    )


def get_all_mode_metadata(pwd_path: Path) -> Dict[Mode, ModeMetadata]:
    """Get metadata for all modes."""
    return {Mode.EXPERIMENT: get_experiment_metadata(pwd_path)}
