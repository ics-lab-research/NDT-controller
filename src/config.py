import os
import tomllib
from pathlib import Path
from typing import Any
from loguru import logger


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return Path.cwd() / "config.toml"


def load_config_dict(config_path: Path) -> dict[str, Any]:
    """Load and parse the TOML configuration file."""
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Error parsing TOML config: {e}")
        raise


def set_env_vars_from_section(config: dict[str, Any], section: str) -> None:
    """Set environment variables from a specific config section, uppercasing keys."""
    vars_dict = config.get(section, {})
    for key, value in vars_dict.items():
        os.environ[key.upper()] = str(value)


def load_toml_config():
    """Load configuration and set environment variables."""
    config_path = get_config_path()
    config = load_config_dict(config_path)

    # Set environment variables for the paths section.
    paths = config.get("paths", {})
    if "experiment_dir" in paths:
        os.environ["EXPERIMENT_BASE"] = paths["experiment_dir"]

    # Set environment variables for the experiment section.
    experiments = config.get("experiment", {})
    if "data_dir" in experiments:
        os.environ["EXPERIMENT_DATA_PATH"] = experiments["data_dir"]
    if "plans" in experiments:
        os.environ["EXPERIMENT_PLANS_PATH"] = experiments["plans"]
    if "vi_path" in experiments:
        os.environ["EXPERIMENT_VI_PATH"] = experiments["vi_path"]
    if "plots_dir" in experiments:
        os.environ["EXPERIMENT_PLOTS_PATH"] = experiments["plots_dir"]

    set_env_vars_from_section(config, "models")
    set_env_vars_from_section(config, "logging")
    logger.info("Configuration loaded and environment variables set.")
