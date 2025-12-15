import json
from pathlib import Path
from typing import Generator, List

from baml_py import Collector
from baml_py.baml_py import BamlPdfPy
from loguru import logger

from ..baml_client.types import (
    ContextType,
    IntentClassifierOutput,
)
from ..core.models import AgentResponse
from ..core.project_manager import ProjectManager
from ..tools.search_and_replace import tool_search_and_replace
from .idea_api import (
    call_brainstormer,
    call_file_manager,
    call_PECT_expert,
)


def handle_file_write(
    router_final: IntentClassifierOutput,
    project_manager: ProjectManager,
    collector: Collector,
) -> Generator[AgentResponse, None, None]:
    """Handle file write intent by managing file operations."""
    logger.info("Handling file write intent")
    if not router_final.content_to_save or not router_final.target_files:
        yield AgentResponse(
            actions=["No content to save or target files specified"]
        )
        logger.info("File write handling completed")
        return
    final = call_file_manager(
        content_to_save=router_final.content_to_save,
        target_files=router_final.target_files,
        operation_type=router_final.operation_type,
        collector=collector,
    )

    if collector.last:
        logger.info(f"File manager usage: {collector.last.usage}")

    if final and final.files_to_change:
        result = tool_search_and_replace(final, project_manager.pwd_path)

        if result.success and result.output and isinstance(result.output, str):
            output_dict = json.loads(result.output)
            files_changed = [
                str(
                    Path(r.split(" to ")[1]).relative_to(
                        project_manager.pwd_path
                    )
                )
                for r in output_dict["results"]
                if "Successfully applied" in r
            ]
            yield AgentResponse(
                actions=[f"Applied changes: {', '.join(files_changed)}"]
            )
        else:
            error_msg = result.error if result.error else "Unknown error"
            yield AgentResponse(
                actions=[f"Failed to apply changes: {error_msg}"]
            )
    logger.info("File write handling completed")


def handle_generate(
    router_final: IntentClassifierOutput,
    user_message: str,
    project_manager: ProjectManager,
    collector: Collector,
    existing_idea_content: str | None,
    system_specs_content: str | None,
    existing_experiment_plan_content: str | None,
    existing_data_science_plan_content: str | None,
) -> Generator[AgentResponse, None, None]:
    """Handle generate intent by calling brainstormer with filtered contexts."""
    logger.info("Handling generate intent")
    required_contexts = router_final.required_context_types

    filtered_system_specs = (
        system_specs_content
        if required_contexts and ContextType.SYSTEM_SPECS in required_contexts
        else None
    )
    filtered_experiment_plan = (
        existing_experiment_plan_content
        if required_contexts
        and ContextType.EXPERIMENT_PLAN in required_contexts
        else None
    )
    filtered_data_science_plan = (
        existing_data_science_plan_content
        if required_contexts
        and ContextType.DATA_SCIENCE_PLAN in required_contexts
        else None
    )
    filtered_existing_idea = (
        existing_idea_content
        if required_contexts and ContextType.EXISTING_IDEA in required_contexts
        else None
    )

    stream_brainstormer = call_brainstormer(
        user_message,
        relevant_context=router_final.extracted_context,
        system_specs=filtered_system_specs,
        existing_experiment_plan=filtered_experiment_plan,
        existing_data_science_plan=filtered_data_science_plan,
        existing_idea=filtered_existing_idea,
        collector=collector,
    )

    if stream_brainstormer:
        for chunk in stream_brainstormer:
            yield AgentResponse(response=chunk)

            # get final response
            final_brainstormer = stream_brainstormer.get_final_response()
            yield AgentResponse(response=final_brainstormer)

        if collector.last:
            logger.info(f"Brainstormer usage: {collector.last.usage}")
    logger.info("Generate handling completed")


def handle_discuss(
    router_final: IntentClassifierOutput,
    user_message: str,
    external_docs: List[BamlPdfPy] | None,
    collector: Collector,
) -> Generator[AgentResponse, None, None]:
    """Handle discuss intent by calling PECT expert."""
    logger.info("Handling discuss intent")
    stream_pect_expert = call_PECT_expert(
        user_message,
        relevant_context=router_final.extracted_context,
        external_docs=external_docs,
        collector=collector,
    )

    if stream_pect_expert:
        for chunk in stream_pect_expert:
            yield AgentResponse(response=chunk)

        # get final response
        final_pect_expert = stream_pect_expert.get_final_response()
        yield AgentResponse(response=final_pect_expert)

        if collector.last:
            logger.info(f"PECT expert usage: {collector.last.usage}")
    logger.info("Discuss handling completed")
