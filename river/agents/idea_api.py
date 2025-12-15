from typing import List

from baml_py import BamlSyncStream, Collector
from baml_py.baml_py import BamlPdfPy
from baml_py.errors import BamlAbortError
from loguru import logger

from ..baml_client.stream_types import (
    IntentClassifierOutput as StreamIntentClassifierOutput,
)
from ..baml_client.sync_client import b
from ..baml_client.types import (
    ConversationMessage,
    ConversationState,
    CachedContexts,
    IntentClassifierOutput,
    SearchReplaceTool,
)
from ..core.clients import get_client_registry
from ..core.project_manager import ProjectManager


def call_intent_classifier(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
    system_specs: str | None,
    existing_experiment_plan: str | None,
    existing_data_science_plan: str | None,
    existing_idea: str | None,
    collector: Collector,
) -> (
    BamlSyncStream[StreamIntentClassifierOutput, IntentClassifierOutput] | None
):
    try:
        logger.info("Calling intent classifier")

        # get client and collector
        cr = get_client_registry("intent-classifier")

        # Limit conversation_history to the last 3 messages
        conversation_history = conversation_history[-3:]

        # set context for intent classifier
        conversation_state = ConversationState(
            available_files=project_manager.get_available_files(),
            cached_contexts=CachedContexts(
                system_specs=system_specs is not None,
                experiment_plan=existing_experiment_plan is not None,
                data_science_plan=existing_data_science_plan is not None,
                existing_idea=existing_idea is not None,
            ),
        )

        # call baml
        resp = b.stream.IntentClassifier(
            user_message,
            conversation_history,
            conversation_state,
            baml_options={"client_registry": cr, "collector": collector},
        )
        logger.info("Intent classifier call completed")
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


def call_PECT_expert(
    user_message: str,
    relevant_context: str | None,
    external_docs: List[BamlPdfPy] | None,
    collector: Collector,
) -> BamlSyncStream[str, str] | None:
    try:
        logger.info("Calling PECT Exper")

        # get client and collector
        cr = get_client_registry("pect-expert")

        # call baml
        resp = b.stream.PECTExpert(
            user_message,
            relevant_context,
            external_docs,
            baml_options={"client_registry": cr, "collector": collector},
        )
        logger.info("PECT Expert call completed")
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


def call_file_manager(
    content_to_save: str,
    target_files: List[str],
    operation_type: str | None,
    collector: Collector,
) -> SearchReplaceTool | None:
    """Call the appropriate brainstormer API based on next_agent."""
    try:
        logger.info("Calling File manager")

        # get client from config
        cr = get_client_registry("file-manager")

        # call baml
        resp = b.FileManager(
            content_to_save,
            target_files,
            operation_type,
            baml_options={"client_registry": cr, "collector": collector},
        )
        logger.info("Brainstormer call completed")
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")


def call_brainstormer(
    user_message: str,
    relevant_context: str | None,
    system_specs: str | None,
    existing_experiment_plan: str | None,
    existing_data_science_plan: str | None,
    existing_idea: str | None,
    collector: Collector,
) -> BamlSyncStream[str, str] | None:
    """Call the appropriate brainstormer API based on next_agent."""
    try:
        logger.info("Calling brainstormer")

        # get client from config
        cr = get_client_registry("brainstormer")

        # call baml
        resp = b.stream.Brainstormer(
            user_message,
            relevant_context,
            system_specs,
            existing_experiment_plan,
            existing_data_science_plan,
            existing_idea,
            baml_options={"client_registry": cr, "collector": collector},
        )
        logger.info("Brainstormer call completed")
        return resp
    except BamlAbortError:
        logger.error("Operation was cancelled")
