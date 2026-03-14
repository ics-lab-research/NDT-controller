import os
from pathlib import Path
from typing import List

from .metadata import get_all_mode_metadata
from .mode import ModeManager
from .models import ExperimentMetadata, Mode, ModeMetadata
from .path_manager import PathManager
from .state_manager import StateManager


class ProjectManager:
    """Unified project context for all modes (facade)."""

    def __init__(
        self, current_mode: Mode = Mode.EXPERIMENT, pwd_path: Path = Path.cwd()
    ):
        self._mode_mgr = ModeManager(current_mode, pwd_path)
        self._path_mgr = PathManager(pwd_path)
        self._state_mgr = StateManager()

    # ================ General ================
    @property
    def current_mode(self) -> Mode:
        return self._mode_mgr.current_mode

    @property
    def pwd_path(self) -> Path:
        return self._path_mgr.pwd_path

    @property
    def multimodal_uploads(self) -> List[Path]:
        return self._state_mgr.multimodal_uploads

    @property
    def get_mode_metadata(self) -> ModeMetadata:
        return self._mode_mgr.get_mode_metadata

    # ================ General function ================
    def add_multimodal_upload(self, file_path: Path):
        self._state_mgr.add_multimodal_upload(file_path)

    def set_mode(self, mode: Mode):
        self._mode_mgr.set_mode(mode)

    # ================ Experiment properties ================
    @property
    def experiment_data_path(self) -> Path:
        metadata = self._mode_mgr.get_mode_metadata
        if isinstance(metadata, ExperimentMetadata):
            return metadata.data_dir_path
        else:
            raise TypeError(
                f"Expected ExperimentMetadata, got {type(metadata)}"
            )

    @property
    def experiment_state(self):
        return self._state_mgr.experiment_state

    @property
    def experiment_dry_run(self) -> bool:
        return os.environ.get("DRY_RUN", "false").lower() == "true"

    @property
    def hardware_type(self) -> str | None:
        metadata = self._mode_mgr.get_mode_metadata
        if isinstance(metadata, ExperimentMetadata):
            return metadata.hardware_type
        return None

    # ================ Experiment functions ================
    def update_experiment_state(self, relative_offset_mm):
        self._state_mgr.update_experiment_state(relative_offset_mm)

    def set_experiment_data_path(self, path: Path):
        self._mode_mgr.set_experiment_data_path(path)

    def set_hardware_type(self, hardware_type: str):
        self._mode_mgr.set_hardware_type(hardware_type)

    # ================ init default ================
    @classmethod
    def create_default(cls, mode: Mode = Mode.EXPERIMENT) -> "ProjectManager":
        context = cls(current_mode=mode)
        all_metadata = get_all_mode_metadata(context._path_mgr.pwd_path)
        context._path_mgr.ensure_mode_specific_paths(all_metadata)
        return context


# Backward compatibility
def init_project_context(mode: Mode = Mode.EXPERIMENT) -> ProjectManager:
    return ProjectManager.create_default(mode)
