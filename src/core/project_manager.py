import os
from pathlib import Path
from typing import List

from .metadata_utils import get_all_mode_metadata
from .mode_utils import ModeManager
from .models import Mode
from .path_utils import PathManager
from .state_utils import StateManager


class ProjectManager:
    """Unified project context for all modes (facade)."""

    def __init__(
        self, current_mode: Mode = Mode.EXPERIMENT, pwd_path: Path = Path.cwd()
    ):
        self._mode_mgr = ModeManager(current_mode)
        self._path_mgr = PathManager(pwd_path)
        self._state_mgr = StateManager()

    @property
    def current_mode(self) -> Mode:
        return self._mode_mgr.current_mode

    @property
    def pwd_path(self) -> Path:
        return self._path_mgr.pwd_path

    @property
    def experiment_data_path(self) -> Path:
        return self._path_mgr.experiment_data_path

    @property
    def experiment_state(self):
        return self._state_mgr.experiment_state

    @property
    def multimodal_uploads(self) -> List[Path]:
        return self._state_mgr.multimodal_uploads

    @property
    def experiment_dry_run(self) -> bool:
        return os.environ.get("DRY_RUN", "false").lower() == "true"

    def add_multimodal_upload(self, file_path: Path) -> None:
        self._state_mgr.add_multimodal_upload(file_path)

    def update_experiment_state(self, relative_offset_mm):
        self._state_mgr.update_experiment_state(relative_offset_mm)

    def get_mode_metadata(self, mode: Mode):
        all_metadata = get_all_mode_metadata(self._path_mgr.pwd_path)
        return self._mode_mgr.get_mode_metadata(mode, all_metadata)

    def set_mode(self, mode: Mode) -> None:
        self._mode_mgr.set_mode(mode)

    def set_data_dir_path(self, path: Path) -> None:
        self._path_mgr.set_data_dir_path(path)

    @classmethod
    def create_default(cls, mode: Mode = Mode.EXPERIMENT) -> "ProjectManager":
        context = cls(current_mode=mode)
        all_metadata = get_all_mode_metadata(context._path_mgr.pwd_path)
        context._path_mgr.ensure_mode_specific_paths(all_metadata)
        return context


# Backward compatibility
def init_project_context(mode: Mode = Mode.EXPERIMENT) -> ProjectManager:
    return ProjectManager.create_default(mode)
