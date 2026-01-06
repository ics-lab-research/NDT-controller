from pathlib import Path
from typing import List

from loguru import logger

from ..baml_client.types import RelativeOffset, State


class StateManager:
    """Manages experiment state and multimodal uploads."""

    def __init__(self):
        self._experiment_state = self._create_init_experiment_state()
        self._multimodal_uploads: List[Path] = []

    @property
    def experiment_state(self) -> State:
        return self._experiment_state

    @property
    def multimodal_uploads(self) -> List[Path]:
        return self._multimodal_uploads

    def add_multimodal_upload(self, file_path: Path):
        logger.info(f"Added multimodal upload: {file_path}")
        self._multimodal_uploads.append(file_path)

    def update_experiment_state(
        self, relative_offset_mm: RelativeOffset
    ) -> None:
        new_position = RelativeOffset(
            x=relative_offset_mm.x,
            y=relative_offset_mm.y,
            z=relative_offset_mm.z,
        )
        self._experiment_state = State(
            current_position=new_position,
            home_position=self._experiment_state.home_position,
        )

    def _create_init_experiment_state(self) -> State:
        position = RelativeOffset(x=0, y=0, z=1)
        return State(current_position=position, home_position=position)
