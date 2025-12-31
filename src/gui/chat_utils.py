from typing import List

from ..baml_client.types import (
    ConversationMessage,
)
from ..core.models import (
    ChatHistory,
    ChatMessage,
    MessageType,
)


def create_message(
    content: str, message_type: MessageType = MessageType.NORMAL
) -> ChatMessage:
    """Creates a chat message with optional type-based metadata."""
    metadata = None
    if message_type == MessageType.ACTION:
        metadata = {"title": "⚡ Action"}
    elif message_type == MessageType.STATUS:
        metadata = {"title": "📊 Status"}
    elif message_type == MessageType.INTERMEDIATE_STEP:
        metadata = {"title": "🔄 Intermediate step"}
    # For NORMAL, no metadata
    return ChatMessage(role="assistant", content=content, metadata=metadata)


def build_conversation_history(
    history: ChatHistory,
) -> List[ConversationMessage]:
    """Builds a list of conversation messages from chat history."""
    conversation = []
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if (
            (role == "user" or role == "assistant")
            and isinstance(role, str)
            and isinstance(content, str)
        ):
            conversation.append(ConversationMessage(role=role, content=content))
    return conversation
