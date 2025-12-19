from typing import List

from baml_py import BamlSyncStream

from ..baml_client import b
from ..baml_client.stream_types import ExpRouterOutput as StreamExpRouterOutput
from ..baml_client.types import ConversationMessage, ExpRouterOutput
from ..core.clients import get_client_registry
from ..core.models import ExperimentTool
from ..baml_client.types import ExpOrchestratorOutput


def call_exp_router(
    user_message: str,
    conversation_history: List[ConversationMessage],
) -> BamlSyncStream[StreamExpRouterOutput, ExpRouterOutput] | None:
    # get client and collector
    cr = get_client_registry("exp-router")

    response = b.stream.ExpRouter(
        user_message,
        conversation_history,
        baml_options={"client_registry": cr},
    )

    return response


def call_exp_orchestrator(
    reformatted_message: str,
) -> ExpOrchestratorOutput:
    """Call the orchestrator agent with a reformatted message"""
    cr = get_client_registry("exp-orchestrator")

    response = b.ExpOrchestrator(
        reformatted_message,
        baml_options={"client_registry": cr},
    )

    return response


def call_exp_planner(
    user_message: str, filename: str | None = None
) -> List[ExperimentTool]:
    """Get the experiment plan tools from BAML (synchronous)."""
    cr = get_client_registry("exp-planner")

    response = b.ExpPlanner(
        user_message,
        filename,
        baml_options={"client_registry": cr},
    )
    return response


def call_exp_executor(
    user_message: str, filename: str | None = None
) -> List[ExperimentTool]:
    """Get the experiment plan tools from BAML (synchronous)."""
    cr = get_client_registry("exp-executor")
    response = b.ExpExecutor(
        user_message,
        filename,
        baml_options={"client_registry": cr},
    )
    return response
