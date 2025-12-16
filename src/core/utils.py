from pathlib import Path

from loguru import logger

import base64
import mimetypes


def read_file(file_path: Path) -> str:
    """Read a file's content. If it's a PDF, return base64-encoded content; otherwise, return text."""
    logger.info(f"Reading file: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type == "application/pdf":
        with open(file_path, "rb") as f:
            content = f.read()
        result = base64.b64encode(content).decode("utf-8")
    else:
        result = file_path.read_text()
    logger.info(f"Successfully read file: {file_path}")
    return result
