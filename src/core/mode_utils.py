from pathlib import Path
from typing import Dict
from .metadata_utils import get_all_mode_metadata
from .models import Mode, ModeMetadata, ExperimentMetadata


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

    def get_mode_metadata(self, mode: Mode) -> ModeMetadata:
        if mode not in self._metadata:
            all_metadata = get_all_mode_metadata(self._pwd_path)
            self._metadata.update(all_metadata)
        if mode not in self._metadata:
            raise ValueError(f"Unknown mode: {mode}")
        return self._metadata[mode]

    def set_experiment_data_path(self, path: Path) -> None:
        metadata = self.get_mode_metadata(Mode.EXPERIMENT)
        if not isinstance(metadata, ExperimentMetadata):
            raise ValueError("Metadata is not ExperimentMetadata")

        metadata.data_dir_path = path
