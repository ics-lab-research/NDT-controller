import dataclasses
import shutil
from pathlib import Path

from loguru import logger


class PathManager:
    """Manages paths, directories, and file creation."""

    def __init__(self, pwd_path: Path):
        self._pwd_path = pwd_path

    @property
    def pwd_path(self) -> Path:
        return self._pwd_path

    def ensure_mode_specific_paths(self, all_metadata: dict):
        """Ensure paths exist for all modes."""
        logger.info("Ensuring mode-specific paths exist")
        for metadata in all_metadata.values():
            for field in dataclasses.fields(metadata):
                if field.name == "vi_path":
                    continue
                paths = getattr(metadata, field.name)
                if isinstance(paths, Path):
                    paths = [paths]
                for path in paths:
                    if path.suffix:  # File
                        self._ensure_file_exists(path)
                    else:  # Directory
                        self._ensure_directory_exists(path)
        logger.info("Mode-specific paths ensured")

    def _ensure_file_exists(self, file_path: Path):
        if not file_path.exists():
            logger.debug(f"Ensuring file exists: {file_path}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            template_path = (
                self._pwd_path
                / "templates"
                / file_path.relative_to(self._pwd_path)
            )
            if template_path.exists():
                shutil.copy(template_path, file_path)
            else:
                file_path.touch()

    def _ensure_directory_exists(self, dir_path: Path):
        if dir_path:
            logger.debug(f"Ensuring directory exists: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
