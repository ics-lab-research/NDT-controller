from typing import List

from ..baml_client import b
from ..baml_client.types import (
    ConversationMessage,
    Error,
    Experiment,
    ExpOrchestratorOutput,
    ExpRouterOutput,
    State,
)
from ..core.clients import get_client_registry
from ..core.models import ExperimentTool


def call_exp_router(
    user_message: str,
    conversation_history: List[ConversationMessage],
) -> ExpRouterOutput:
    # get client and collector
    cr = get_client_registry("exp-router")

    response = b.ExpRouter(
        user_message,
        conversation_history,
        baml_options={"client_registry": cr},
    )

    return response


def call_exp_orchestrator(
    reformatted_message: str,
) -> ExpOrchestratorOutput | Error:
    """Call the orchestrator agent with a reformatted message"""
    cr = get_client_registry("exp-orchestrator")

    response = b.ExpOrchestrator(
        reformatted_message,
        baml_options={"client_registry": cr},
    )

    return response


def call_exp_planner(experiment: Experiment, state: State) -> str | Error:
    """Get the experiment plan tools from BAML (synchronous)."""
    cr = get_client_registry("exp-planner")

    response = b.ExpPlanner(
        experiment,
        state,
        baml_options={"client_registry": cr},
    )
    return response


def call_exp_executor(plan: str, filename: str) -> List[ExperimentTool] | Error:
    """Get the experiment plan tools from BAML (synchronous)."""
    cr = get_client_registry("exp-executor")
    response = b.ExpExecutor(
        plan,
        filename,
        baml_options={"client_registry": cr},
    )
    return response
