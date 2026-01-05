from typing import Dict
from .models import Mode, ModeMetadata


class ModeManager:
    """Manages current mode and metadata retrieval."""

    def __init__(self, initial_mode: Mode):
        self._current_mode = initial_mode

    @property
    def current_mode(self) -> Mode:
        return self._current_mode

    def set_mode(self, mode: Mode) -> None:
        from loguru import logger

        logger.info(f"Setting mode to {mode}")
        self._current_mode = mode

    def get_mode_metadata(
        self, mode: Mode, all_metadata: Dict[Mode, ModeMetadata]
    ) -> ModeMetadata:
        if mode not in all_metadata:
            raise ValueError(f"Unknown mode: {mode}")
        return all_metadata[mode]
