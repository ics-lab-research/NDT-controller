import dataclasses
import os
import shutil
from pathlib import Path
from typing import Dict, List
from loguru import logger
from .models import (
    ExperimentsMetadata,
    Mode,
    ModeMetadata,
)
from ..tools.file_operations import tool_read_file


class ProjectManager:
    """Unified project context for all modes."""

    def __init__(
        self,
        current_mode: Mode = Mode.EXPERIMENTS,
        pwd_path: Path = Path.cwd(),
        uploaded_docs: List[str] | None = None,
    ):
        """Initialize project context."""
        self._current_mode = current_mode
        self._pwd_path = pwd_path
        self._uploaded_docs = uploaded_docs or []

    @property
    def current_mode(self) -> Mode:
        """Get the current mode."""
        return self._current_mode

    @property
    def pwd_path(self) -> Path:
        """Get the present working directory path."""
        return self._pwd_path

    @property
    def uploaded_docs(self) -> List[str]:
        """Get the uploaded document paths."""
        return self._uploaded_docs

    def _get_experiments_metadata(self) -> ExperimentsMetadata:
        experiments_base = os.environ.get(
            "RIVER_EXPERIMENTS_BASE", "EXPERIMENTS"
        )
        exp_constraint_path = os.environ.get(
            "RIVER_EXPERIMENTS_EXP_CONSTRAINT_PATH", "LABVIEW.md"
        )
        data_dir_path = os.environ.get(
            "RIVER_EXPERIMENTS_DATA_DIR_PATH", "data"
        )
        plans_path = os.environ.get(
            "RIVER_EXPERIMENTS_PLANS_PATH", "labview_experiment_plans.json"
        )
        vi_path_str = os.environ.get(
            "RIVER_EXPERIMENTS_VI_PATH",
            "D:\\PECT LLM\\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi",
        )
        return ExperimentsMetadata(
            exp_constraint_path=self._pwd_path
            / experiments_base
            / exp_constraint_path,
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

    # TODO: should contain description of file
    def get_available_files(self) -> List[str]:
        """Get available files based on current mode."""
        files = []
        metadata = self.get_mode_metadata(self.current_mode)
        for field in dataclasses.fields(metadata):
            value = getattr(metadata, field.name)
            # Normalize to a list if it's a single Path
            if isinstance(value, Path):
                value = [value]
            for item in value:
                if isinstance(item, Path) and item.is_file() and item.exists():
                    files.append(str(item))

        return files

    # TODO: should add docs with mode
    def add_docs(self, docs: List[str]):
        """Add additional uploaded doc paths to the current context."""
        self._uploaded_docs.extend(docs)

    def set_uploaded_docs(self, docs: List[str]):
        """Set the uploaded document paths, replacing any existing ones."""
        self._uploaded_docs = docs

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


def get_exp_constraint_content(project_manager: ProjectManager) -> str:
    """Get the content of the experiment constraint file."""
    logger.debug("Retrieving experiment constraint content")
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        logger.error(
            "Attempted to get exp constraint content not in experiments mode"
        )
        raise ValueError("Not in experiments mode")
    path = metadata.exp_constraint_path
    if path.exists():
        content = tool_read_file(path)
        logger.debug(f"Read content from {path}")
        return content
    logger.warning(f"Experiment constraint file does not exist: {path}")
    return ""


# Backward compatibility function
def init_project_context(
    mode: Mode = Mode.EXPERIMENTS,
) -> ProjectManager:
    """Initialize a new project context with all necessary files and directories."""
    return ProjectManager.create_default(mode)
