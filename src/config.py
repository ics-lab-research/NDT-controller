import os
import tomllib
from pathlib import Path
from loguru import logger


def load_config():
    """Load configuration from config.toml and set environment variables."""
    config_path = Path.cwd() / "config.toml"
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
        os.environ["EXPERIMENTS_BASE"] = paths["experiments"]

    # Set experiments section
    experiments = config.get("experiments", {})
    if "data_dir_path" in experiments:
        os.environ["EXPERIMENTS_DATA_DIR_PATH"] = experiments["data_dir_path"]
    if "plans_path" in experiments:
        os.environ["EXPERIMENTS_PLANS_PATH"] = experiments["plans_path"]
    if "vi_path" in experiments:
        os.environ["EXPERIMENTS_VI_PATH"] = experiments["vi_path"]

    # Set models section
    models = config.get("models", {})
    for key, value in models.items():
        os.environ[key.upper()] = str(value)

    # Set logging section
    logging = config.get("logging", {})
    for key, value in logging.items():
        os.environ[key.upper()] = str(value)

    logger.info("Configuration loaded and environment variables set.")
