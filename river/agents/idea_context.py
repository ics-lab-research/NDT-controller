from pathlib import Path
from typing import List

from baml_py import Pdf
from loguru import logger

from ..core.models import IdeaMetadata
from ..core.project_manager import ProjectManager
from ..tools.file_operations import tool_read_file


def fetch_system_specs(project_manager: ProjectManager) -> str | None:
    """Fetch system specs, return content."""
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if (
        not isinstance(metadata, IdeaMetadata)
        or not metadata.system_spec_path
        or not metadata.system_spec_path.exists()
    ):
        logger.warning("System spec path not available or does not exist")
        return None
    spec_content = tool_read_file(metadata.system_spec_path)
    if not spec_content.strip():
        return None
    return spec_content


def fetch_external_docs(project_manager: ProjectManager) -> List[Pdf] | None:
    """Fetch external docs, return baml docs."""
    if not project_manager.uploaded_docs:
        return None
    baml_docs = []
    for doc_path_str in project_manager.uploaded_docs:
        doc_path = Path(doc_path_str)
        if doc_path.exists():
            doc_content_str = tool_read_file(doc_path)
            if not doc_content_str.strip():
                continue
            doc_content = Pdf.from_base64(doc_content_str)
            baml_docs.append(doc_content)
        else:
            logger.warning(f"External doc path {doc_path} does not exist")
    if not baml_docs:
        return None
    return baml_docs


def fetch_experiment_plan(project_manager: ProjectManager) -> str | None:
    """Fetch existing experiment plan, return content."""
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if (
        not isinstance(metadata, IdeaMetadata)
        or not metadata.experiment_plan_path
        or not metadata.experiment_plan_path.exists()
    ):
        logger.warning("Experiment plan path not available or does not exist")
        return None
    plan_content = tool_read_file(metadata.experiment_plan_path)
    if not plan_content.strip():
        return None
    return plan_content


def fetch_data_science_plan(project_manager: ProjectManager) -> str | None:
    """Fetch existing data science plan, return content."""
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if (
        not isinstance(metadata, IdeaMetadata)
        or not metadata.data_science_plan_path
        or not metadata.data_science_plan_path.exists()
    ):
        logger.warning("Data science plan path not available or does not exist")
        return None
    plan_content = tool_read_file(metadata.data_science_plan_path)
    if not plan_content.strip():
        return None
    return plan_content


def fetch_existing_idea(project_manager: ProjectManager) -> str | None:
    """Fetch existing idea, return content."""
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if (
        not isinstance(metadata, IdeaMetadata)
        or not metadata.idea_output_path
        or not metadata.idea_output_path.exists()
    ):
        logger.warning("Idea output path not available or does not exist")
        return None
    idea_content = tool_read_file(metadata.idea_output_path)
    if not idea_content.strip():
        return None
    return idea_content
