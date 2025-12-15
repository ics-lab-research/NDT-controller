

import os
import tomllib
from pathlib import Path
from loguru import logger


def load_config():
    """Load configuration from config.toml and set environment variables."""
    config_path = Path(__file__).parent.parent / "config.toml"
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        logger.error(f"Error parsing TOML config: {e}")
        raise
    
    # Set paths section
    paths = config.get("paths", {})
    if "experiments" in paths:
        os.environ["RIVER_EXPERIMENTS_BASE"] = paths["experiments"]
    
    # Set experiments section
    experiments = config.get("experiments", {})
    if "exp_constraint_path" in experiments:
        os.environ["RIVER_EXPERIMENTS_EXP_CONSTRAINT_PATH"] = experiments["exp_constraint_path"]
    if "data_dir_path" in experiments:
        os.environ["RIVER_EXPERIMENTS_DATA_DIR_PATH"] = experiments["data_dir_path"]
    if "plans_path" in experiments:
        os.environ["RIVER_EXPERIMENTS_PLANS_PATH"] = experiments["plans_path"]
    if "vi_path" in experiments:
        os.environ["RIVER_EXPERIMENTS_VI_PATH"] = experiments["vi_path"]
    
    logger.info("Configuration loaded and environment variables set.")
