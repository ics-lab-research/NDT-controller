import dataclasses
import os
import shutil
from pathlib import Path
from typing import Dict
from loguru import logger
from ..baml_client.types import RelativeOffset, State
from .models import (
    ExperimentsMetadata,
    Mode,
    ModeMetadata,
)


class ProjectManager:
    """Unified project context for all modes."""

    def __init__(
        self,
        current_mode: Mode = Mode.EXPERIMENTS,
        pwd_path: Path = Path.cwd(),
    ):
        """Initialize project context."""
        self._current_mode = current_mode
        self._pwd_path = pwd_path
        self._experiment_state = self.create_initial_experiment_state()

    @property
    def current_mode(self) -> Mode:
        """Get the current mode."""
        return self._current_mode

    @property
    def pwd_path(self) -> Path:
        """Get the present working directory path."""
        return self._pwd_path

    @property
    def experiment_state(self) -> State:
        """Get the current experiment state."""
        return self._experiment_state

    def create_initial_experiment_state(self) -> State:
        """Create the initial experiment state for experiments."""
        position = RelativeOffset(x=0, y=0, z=1)
        return State(current_position=position, home_position=position)

    def update_experiment_state(self, relative_offset_mm: RelativeOffset) -> None:
        """Update the experiment state based on executed tools."""
        new_x = relative_offset_mm.x
        new_y = relative_offset_mm.y
        new_z = relative_offset_mm.z
        new_position = RelativeOffset(x=new_x, y=new_y, z=new_z)
        self._experiment_state = State(
            current_position=new_position,
            home_position=self._experiment_state.home_position,
        )

    def _get_experiments_metadata(self) -> ExperimentsMetadata:
        experiments_base = os.environ.get("EXPERIMENTS_BASE", "EXPERIMENTS")
        data_dir_path = os.environ.get("EXPERIMENTS_DATA_DIR_PATH", "data")
        plans_path = os.environ.get(
            "EXPERIMENTS_PLANS_PATH", "labview_experiment_plans.json"
        )
        vi_path_str = os.environ.get(
            "EXPERIMENTS_VI_PATH",
            "D:\\PECT LLM\\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi",
        )
        return ExperimentsMetadata(
            data_dir_path=self._pwd_path / experiments_base / data_dir_path,
            plans_path=self._pwd_path / experiments_base / plans_path,
            vi_path=Path(vi_path_str),
        )

    def _get_all_mode_metadata(self) -> Dict[Mode, ModeMetadata]:
        """Get metadata for all modes, with paths loaded from environment variables."""
        return {
            Mode.EXPERIMENTS: self._get_experiments_metadata(),
        }

    def get_mode_metadata(self, mode: Mode) -> ModeMetadata:
        """Get metadata for the specified mode."""
        if mode != Mode.EXPERIMENTS:
            raise ValueError(f"Only EXPERIMENTS mode is supported: {mode}")

        all_metadata = self._get_all_mode_metadata()
        return all_metadata[mode]

    def set_mode(self, mode: Mode):
        """Set the mode for the current context."""
        logger.info(f"Setting mode to {mode}")
        self._current_mode = mode

    def _ensure_file_exists(self, file_path: Path):
        """Ensure a file exists, copying from template if available."""
        if not file_path.exists():
            logger.debug(f"Ensuring file exists: {file_path}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            template_path = (
                self._pwd_path
                / "templates"
                / file_path.relative_to(self._pwd_path)
            )
            if template_path.exists():
                logger.debug(
                    f"Copying from template: {template_path} to {file_path}"
                )
                shutil.copy(template_path, file_path)
            else:
                logger.debug(
                    f"Template not found, creating empty file: {file_path}"
                )
                file_path.touch()

    def _ensure_directory_exists(self, dir_path: Path):
        """Ensure a directory exists, creating it if necessary."""
        if dir_path:
            logger.debug(f"Ensuring directory exists: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create_default(
        cls,
        mode: Mode = Mode.EXPERIMENTS,
    ) -> "ProjectManager":
        """Create a default project context with all necessary files and directories."""
        context = cls(
            current_mode=mode,
        )

        context.ensure_mode_specific_paths()

        return context

    def ensure_mode_specific_paths(self):
        """Ensure all mode-specific directories and files exist."""
        logger.info("Ensuring mode-specific paths exist")
        metadata = self._get_experiments_metadata()
        for field in dataclasses.fields(metadata):
            if field.name == "vi_path":
                continue
            paths = getattr(metadata, field.name)
            # Normalize to a list if it's a single Path
            if isinstance(paths, Path):
                paths = [paths]
            for path in paths:
                if path.suffix:  # It's a file (has extension)
                    self._ensure_file_exists(path)
                else:  # It's a directory
                    self._ensure_directory_exists(path)
        logger.info("Mode-specific paths ensured")


# Backward compatibility function
def init_project_context(
    mode: Mode = Mode.EXPERIMENTS,
) -> ProjectManager:
    """Initialize a new project context with all necessary files and directories."""
    return ProjectManager.create_default(mode)
