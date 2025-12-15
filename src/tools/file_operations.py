import base64
import mimetypes
from pathlib import Path
from typing import List

from aider.coders import Coder
from aider.models import Model
from loguru import logger
from ..baml_client.types import ToolResult


def tool_edit_file_with_prompt(
    prompt: str,
    files: List[Path],
    model_name: str = "openrouter/anthropic/claude-sonnet-4.5",
) -> ToolResult:
    """Edit files using aider based on the given prompt."""
    name = "tool_edit_file_with_prompt"
    logger.info(
        f"Starting to edit files: {[str(f) for f in files]} with prompt: {prompt[:50]}..."
    )
    try:
        model = Model(model_name)
        coder = Coder.create(
            main_model=model,
            fnames=[str(f) for f in files],
            suggest_shell_commands=False,
            auto_lint=False,
            auto_commits=False,
            dirty_commits=False,
            stream=False,
        )
        coder.run(prompt)
        logger.info("Successfully finished editing files.")
        return ToolResult(name=name, success=True, output="Successfully finished editing files.")
    except Exception as e:
        logger.error(f"Error editing files: {e}")
        return ToolResult(name=name, success=False, error=str(e))


def tool_read_file(file_path: Path) -> ToolResult:
    """Read a file's content. If it's a PDF, return base64-encoded content; otherwise, return text."""
    name = "tool_read_file"
    logger.info(f"Reading file: {file_path}")
    try:
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
        return ToolResult(name=name, success=True, output=result)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ToolResult(name=name, success=False, error=str(e))
