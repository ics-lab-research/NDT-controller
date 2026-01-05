import os
from pathlib import Path
from typing import Dict

from .models import ExperimentMetadata, Mode, ModeMetadata


def get_experiments_metadata(pwd_path: Path) -> ExperimentMetadata:
    """Build experiments metadata from env vars."""
    experiments_base = os.environ.get("EXPERIMENTS_BASE", "EXPERIMENTS")
    data_dir_rel = os.environ.get("EXPERIMENTS_DATA_DIR_PATH", "data")
    plans_path = os.environ.get(
        "EXPERIMENTS_PLANS_PATH", "labview_experiment_plans.json"
    )
    vi_path_str = os.environ.get(
        "EXPERIMENTS_VI_PATH",
        "D:\\PECT LLM\\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi",
    )
    return ExperimentMetadata(
        data_dir_path=pwd_path / experiments_base / data_dir_rel,
        plans_path=pwd_path / experiments_base / plans_path,
        vi_path=Path(vi_path_str),
    )


def get_all_mode_metadata(pwd_path: Path) -> Dict[Mode, ModeMetadata]:
    """Get metadata for all modes."""
    return {Mode.EXPERIMENT: get_experiments_metadata(pwd_path)}
