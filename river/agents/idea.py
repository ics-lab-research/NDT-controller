from typing import Generator, List

from baml_py import Collector
from loguru import logger

from ..baml_client.types import (
    ConversationMessage,
    Intent,
)
from ..core.models import AgentResponse
from ..core.project_manager import ProjectManager
from .idea_api import (
    call_intent_classifier,
)
from .idea_context import (
    fetch_data_science_plan,
    fetch_existing_idea,
    fetch_experiment_plan,
    fetch_external_docs,
    fetch_system_specs,
)
from .idea_handlers import handle_file_write, handle_discuss, handle_generate


def handle_idea_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle IDEA mode: route user message based on detected intent."""
    logger.info("Starting handle_idea_mode")

    # Fetch all existing contexts
    external_docs = fetch_external_docs(project_manager)

    existing_idea_content = fetch_existing_idea(project_manager)
    system_specs_content = fetch_system_specs(project_manager)
    existing_experiment_plan_content = fetch_experiment_plan(project_manager)
    existing_data_science_plan_content = fetch_data_science_plan(
        project_manager
    )

    # track token
    intent_classifier_collector = Collector(name="intent_classifier")
    brainstormer_collector = Collector(name="brainstormer")
    pect_expert_collector = Collector(name="pect-expert")
    file_manager_collector = Collector(name="file-manager")

    stream_intent_classifier = call_intent_classifier(
        user_message,
        conversation_history,
        project_manager,
        system_specs=system_specs_content,
        existing_experiment_plan=existing_experiment_plan_content,
        existing_data_science_plan=existing_data_science_plan_content,
        existing_idea=existing_idea_content,
        collector=intent_classifier_collector,
    )

    if stream_intent_classifier:
        for chunk in stream_intent_classifier:
            yield AgentResponse(thinking=chunk.reasoning)

        # get final intent
        final_intent_classifier = stream_intent_classifier.get_final_response()
        yield AgentResponse(thinking=final_intent_classifier.reasoning)

        if intent_classifier_collector.last:
            logger.info(
                f"Idea router usage: {intent_classifier_collector.last.usage}"
            )

        # Route to appropriate handler based on intent
        if final_intent_classifier.intent == Intent.FILE_WRITE:
            yield from handle_file_write(
                final_intent_classifier,
                project_manager,
                file_manager_collector,
            )
        elif final_intent_classifier.intent == Intent.GENERATE:
            yield from handle_generate(
                final_intent_classifier,
                user_message,
                project_manager,
                brainstormer_collector,
                existing_idea_content,
                system_specs_content,
                existing_experiment_plan_content,
                existing_data_science_plan_content,
            )
        else:  # DISCUSS
            yield from handle_discuss(
                final_intent_classifier,
                user_message,
                external_docs,
                pect_expert_collector,
            )

    logger.info("handle_idea_mode completed")
