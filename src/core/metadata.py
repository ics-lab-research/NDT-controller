import os
from pathlib import Path
from typing import Dict

from .models import ExperimentMetadata, Mode, ModeMetadata


def get_experiment_metadata(pwd_path: Path) -> ExperimentMetadata:
    """Build experiments metadata from env vars."""
    experiments_base = os.environ.get("EXPERIMENT_BASE")
    vi_file = os.environ.get("EXPERIMENT_VI_PATH")
    plans_file = os.environ.get("EXPERIMENT_PLANS_PATH")
    data_dir = os.environ.get("EXPERIMENT_DATA_PATH")
    plot_dir = os.environ.get("EXPERIMENT_PLOTS_PATH")

    if experiments_base is None:
        raise ValueError("Environment variables EXPERIMENT_BASE must be set")
    if vi_file is None:
        raise ValueError("Environment variables EXPERIMENT_VI_PATH must be set")
    if data_dir is None:
        raise ValueError(
            "Environment variables EXPERIMENT_DATA_PATH must be set"
        )
    if plans_file is None:
        raise ValueError(
            "Environment variables EXPERIMENT_PLANS_PATH must be set"
        )
    if plot_dir is None:
        raise ValueError(
            "Environment variables EXPERIMENT_PLOTS_PATH must be set"
        )

    return ExperimentMetadata(
        data_dir_path=pwd_path / experiments_base / data_dir,
        plans_path=pwd_path / experiments_base / plans_file,
        vi_path=Path(vi_file),
        plots_dir_path=pwd_path / experiments_base / plot_dir,
    )


def get_all_mode_metadata(pwd_path: Path) -> Dict[Mode, ModeMetadata]:
    """Get metadata for all modes."""
    return {Mode.EXPERIMENT: get_experiment_metadata(pwd_path)}
