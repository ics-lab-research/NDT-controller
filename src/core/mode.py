from pathlib import Path
from typing import Dict

from .metadata import get_all_mode_metadata
from .models import ExperimentMetadata, Mode, ModeMetadata


class ModeManager:
    """Manages current mode and metadata retrieval."""

    def __init__(self, initial_mode: Mode, pwd_path: Path):
        self._current_mode = initial_mode
        self._pwd_path = pwd_path
        self._metadata: Dict[Mode, ModeMetadata] = {}

    @property
    def current_mode(self) -> Mode:
        return self._current_mode

    def set_mode(self, mode: Mode) -> None:
        from loguru import logger

        logger.info(f"Setting mode to {mode}")
        self._current_mode = mode

    @property
    def get_mode_metadata(self) -> ModeMetadata:
        current_mode = self.current_mode

        if current_mode not in self._metadata:
            all_metadata = get_all_mode_metadata(self._pwd_path)
            self._metadata.update(all_metadata)
        if current_mode not in self._metadata:
            raise ValueError(f"Unknown mode: {current_mode}")
        return self._metadata[current_mode]

    def set_experiment_data_path(self, path: Path) -> None:
        metadata = self.get_mode_metadata
        if not isinstance(metadata, ExperimentMetadata):
            raise ValueError("Metadata is not ExperimentMetadata")

        metadata.data_dir_path = path
