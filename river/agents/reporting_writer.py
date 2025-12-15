from pathlib import Path
from typing import Generator, List

from loguru import logger

from ..baml_client import b
from ..baml_client.types import (
    ConversationMessage,
    EditFileTool,
)
from ..core.project_manager import ProjectManager
from ..core.models import AgentResponse, IdeaMetadata, Mode, ReportingMetadata
from ..tools.file_operations import tool_edit_file_with_prompt, tool_read_file
from ..tools.latex_compiler import tool_compile_latex_to_pdf


def call_editor(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
) -> EditFileTool:
    """Generate editor instructions from user message and history."""
    logger.info("Calling ReportingEditor for user message")
    result = b.ReportingEditor(
        user_message,
        conversation_history=conversation_history,
        available_files=project_manager.get_available_files(),
    )
    logger.info("ReportingEditor call completed")
    return result


def handle_reporting_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle REPORTING mode: edit files and compile LaTeX to PDF."""
    logger.info("Starting handle_reporting_mode")
    edit_result = call_editor(
        user_message, conversation_history, project_manager
    )

    file_paths = [Path(f) for f in edit_result.files]

    # Indicate starting edits
    yield AgentResponse(
        response="",
        thinking="",
        actions=["Applying edits to files..."],
    )

    # Perform the edit
    logger.info("Applying edits to files")
    tool_edit_file_with_prompt(edit_result.instruction, file_paths)
    logger.info("Edits applied successfully")

    # Indicate starting compilation
    yield AgentResponse(
        response="",
        thinking="",
        actions=["Compiling LaTeX to PDF..."],
    )

    # Compile to PDF
    logger.info("Compiling LaTeX to PDF")
    tool_compile_latex_to_pdf()
    logger.info("LaTeX compilation completed")

    # Indicate completion
    yield AgentResponse(
        response="",
        thinking="",
        actions=["Report generated successfully."],
    )
    logger.info("handle_reporting_mode completed")


def edit_abstract_tex(project_manager: ProjectManager) -> None:
    """Edit abstract.tex using the provided context_manager, including image descriptions for visualizations after training models."""
    logger.info("Starting edit_abstract_tex")
    idea_metadata = project_manager.get_mode_metadata(Mode.IDEA)
    if not isinstance(idea_metadata, IdeaMetadata):
        logger.error("Expected IdeaMetadata, got {}", type(idea_metadata))
        raise ValueError("Expected IdeaMetadata")
    reporting_metadata = project_manager.get_mode_metadata(Mode.REPORTING)
    if not isinstance(reporting_metadata, ReportingMetadata):
        logger.error(
            "Expected ReportingMetadata, got {}", type(reporting_metadata)
        )
        raise ValueError("Expected ReportingMetadata")
    logger.info("Reading experiment plan for abstract")
    idea = (
        tool_read_file(idea_metadata.experiment_plan_path)
        if idea_metadata.experiment_plan_path.exists()
        else ""
    )
    results = None
    instruction = f"""
    Update the abstract.tex file with a concise abstract based on the following idea and results.
    Idea: {idea}
    Results: {results}
    Include descriptions of images that visualize the results after training models, such as plots or charts showing performance metrics, comparisons, or key insights.
    Ensure the abstract is written in LaTeX format, is engaging, and highlights the main contributions and outcomes.
    """
    logger.info("Editing abstract.tex")
    tool_edit_file_with_prompt(
        instruction, [reporting_metadata.abstract_tex_path]
    )
    logger.info("edit_abstract_tex completed")


def edit_intro_tex(project_manager: ProjectManager) -> None:
    """Edit introduction.tex using the provided context_manager to create an introduction section."""
    logger.info("Starting edit_intro_tex")
    idea_metadata = project_manager.get_mode_metadata(Mode.IDEA)
    if not isinstance(idea_metadata, IdeaMetadata):
        logger.error("Expected IdeaMetadata, got {}", type(idea_metadata))
        raise ValueError("Expected IdeaMetadata")
    reporting_metadata = project_manager.get_mode_metadata(Mode.REPORTING)
    if not isinstance(reporting_metadata, ReportingMetadata):
        logger.error(
            "Expected ReportingMetadata, got {}", type(reporting_metadata)
        )
        raise ValueError("Expected ReportingMetadata")
    logger.info("Reading experiment plan for introduction")
    idea = (
        tool_read_file(idea_metadata.experiment_plan_path)
        if idea_metadata.experiment_plan_path.exists()
        else ""
    )
    instruction = f"""
    Update the introduction.tex file with an introduction section based on the following idea.
    Idea: {idea}
    Write an engaging introduction that sets the context, explains the motivation, and outlines the structure of the report.
    Ensure the introduction is written in LaTeX format and is concise yet informative.
    """
    logger.info("Editing introduction.tex")
    tool_edit_file_with_prompt(
        instruction, [reporting_metadata.introduction_tex_path]
    )
    logger.info("edit_intro_tex completed")


def edit_experimental_setup_tex(project_manager: ProjectManager) -> None:
    """Edit experimental_setup.tex using the provided context_manager to create a detailed experimental setup section."""
    logger.info("Starting edit_experimental_setup_tex")
    idea_metadata = project_manager.get_mode_metadata(Mode.IDEA)
    if not isinstance(idea_metadata, IdeaMetadata):
        logger.error("Expected IdeaMetadata, got {}", type(idea_metadata))
        raise ValueError("Expected IdeaMetadata")
    reporting_metadata = project_manager.get_mode_metadata(Mode.REPORTING)
    if not isinstance(reporting_metadata, ReportingMetadata):
        logger.error(
            "Expected ReportingMetadata, got {}", type(reporting_metadata)
        )
        raise ValueError("Expected ReportingMetadata")
    logger.info("Reading experiment plan for experimental setup")
    experiment_plan = (
        tool_read_file(idea_metadata.experiment_plan_path)
        if idea_metadata.experiment_plan_path.exists()
        else ""
    )
    instruction = f"""
    Update the experimental_setup.tex file with a detailed experimental setup section based on the following experiment plan.
    Experiment Plan: {experiment_plan}
    Ensure the section is written in LaTeX format, is clear and structured, and highlights the methodology, data, and setup details.
    """
    logger.info("Editing experimental_setup.tex")
    tool_edit_file_with_prompt(
        instruction, [reporting_metadata.experimental_setup_tex_path]
    )
    logger.info("edit_experimental_setup_tex completed")


def edit_results_tex(project_manager: ProjectManager) -> None:
    """Edit results.tex using the provided context_manager to create a detailed results section."""
    logger.info("Starting edit_results_tex")
    reporting_metadata = project_manager.get_mode_metadata(Mode.REPORTING)
    if not isinstance(reporting_metadata, ReportingMetadata):
        logger.error(
            "Expected ReportingMetadata, got {}", type(reporting_metadata)
        )
        raise ValueError("Expected ReportingMetadata")
    data_analysis_results = None
    training_results = None
    instruction = f"""
    Update the results.tex file with a detailed results section based on the following data analysis results and training results.
    Data Analysis Results: {data_analysis_results}
    Training Results: {training_results}
    Include descriptions of images that visualize the results, such as plots or charts showing performance metrics, comparisons, or key insights from the data analysis and model training.
    Ensure the section is written in LaTeX format, is clear and structured, and highlights the outcomes and findings.
    """
    logger.info("Editing results.tex")
    tool_edit_file_with_prompt(
        instruction, [reporting_metadata.results_tex_path]
    )
    logger.info("edit_results_tex completed")


def edit_conclusion_tex(project_manager: ProjectManager) -> None:
    """Edit main.tex to update the conclusion section based on the introduction content from context_manager, without editing introduction.tex."""
    logger.info("Starting edit_conclusion_tex")
    reporting_metadata = project_manager.get_mode_metadata(Mode.REPORTING)
    if not isinstance(reporting_metadata, ReportingMetadata):
        logger.error(
            "Expected ReportingMetadata, got {}", type(reporting_metadata)
        )
        raise ValueError("Expected ReportingMetadata")
    logger.info("Reading introduction.tex for conclusion")
    introduction_content = (
        tool_read_file(reporting_metadata.introduction_tex_path)
        if reporting_metadata.introduction_tex_path.exists()
        else ""
    )
    instruction = f"""
    Update the conclusion section in main.tex based on the following introduction content.
    Introduction Content: {introduction_content}
    Do not edit introduction.tex. Edit only main.tex to create or update a conclusion that summarizes the key points, reflects on the introduction, and provides final thoughts.
    Ensure the conclusion is written in LaTeX format, is concise, and ties back to the motivation and structure outlined in the introduction.
    """
    logger.info("Editing main.tex for conclusion")
    tool_edit_file_with_prompt(instruction, [reporting_metadata.main_tex_path])
    logger.info("edit_conclusion_tex completed")
