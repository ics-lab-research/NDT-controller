from typing import List


from ..baml_client.types import ConversationMessage
from ..core.models import (
    ChatHistory,
)


def build_conversation_history(
    history: ChatHistory,
) -> List[ConversationMessage]:
    """Convert chat history to conversation messages."""
    conversation = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        if (
            (role == "user" or role == "assistant")
            and isinstance(role, str)
            and isinstance(content, str)
        ):
            conversation.append(ConversationMessage(role=role, content=content))
    return conversation
