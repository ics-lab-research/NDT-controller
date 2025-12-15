from typing import Generator, List

from baml_py import BamlSyncStream

from ..baml_client import b
from ..baml_client.types import ConversationMessage
from ..core.models import AgentResponse


def call_orchestrator(
    user_message: str, conversation_history: List[ConversationMessage]
) -> BamlSyncStream[str, str]:
    """Call the orchestrator agent with a user message and conversation history"""
    resp = b.stream.Orchestrator(user_message, conversation_history)

    return resp


def handle_chat_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
) -> Generator[AgentResponse, None, None]:
    stream = call_orchestrator(user_message, conversation_history)
    yield AgentResponse(response=stream)

    # get final response
    if stream:
        final = stream.get_final_response()
        yield AgentResponse(response=final)
