from typing import Generator, List

from ..agents.experiment import handle_experiment_mode
from ..baml_client.types import ConversationMessage
from ..core.models import AgentResponse, Mode
from .project_manager import ProjectManager


def get_agent_response(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Get a response from the LLM"""
    if project_manager.current_mode == Mode.EXPERIMENTS:
        yield from handle_experiment_mode(
            user_message, conversation_history, project_manager
        )
    else:
        yield AgentResponse(
            response=f"Mode {project_manager.current_mode} not yet implemented"
        )
