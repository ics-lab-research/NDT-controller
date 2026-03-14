from typing import List

from ..baml_client import b
from ..baml_client.types import (
    ConversationMessage,
    ResponseError,
    Experiment,
    ExpOrchestratorOutput,
    ExpRouterOutput,
    State,
    ExperimentStep,
)
from ..core.clients import get_client_registry
from ..core.models import BasicExpTool


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


def call_exp_basic_executor(
    user_message: str,
) -> List[BasicExpTool] | ResponseError:
    """Call the basic experiment executor with a user message."""
    cr = get_client_registry("exp-basic-executor")

    response = b.ExpBasicExecutor(
        user_message,
        baml_options={"client_registry": cr},
    )
    return response


def call_exp_orchestrator(
    reformatted_message: str,
) -> ExpOrchestratorOutput | ResponseError:
    """Call the orchestrator agent with a reformatted message"""
    cr = get_client_registry("exp-orchestrator")

    response = b.ExpOrchestrator(
        reformatted_message,
        baml_options={"client_registry": cr},
    )

    return response


def call_exp_planner(
    experiment: Experiment, state: State
) -> str | ResponseError:
    """Get the experiment plan tools from BAML (synchronous)."""
    cr = get_client_registry("exp-planner")

    response = b.ExpPlanner(
        experiment,
        state,
        baml_options={"client_registry": cr},
    )
    return response


def call_exp_orchestrator_dual_sensor(
    reformatted_message: str,
) -> ExpOrchestratorOutput | ResponseError:
    """Call the dual-sensor orchestrator agent with a reformatted message."""
    cr = get_client_registry("exp-orchestrator")

    response = b.ExpOrchestratorDualSensor(
        reformatted_message,
        baml_options={"client_registry": cr},
    )

    return response


def call_exp_executor(
    plan: str,
    filename: str,
    hardware_type: str = "single_sensor",
    filename_2: str | None = None,
) -> List[ExperimentStep] | ResponseError:
    """Call the experiment executor with a plan and filename(s)."""
    cr = get_client_registry("exp-executor")
    if hardware_type == "dual_sensor":
        response = b.ExpExecutorDualSensor(
            plan, filename, filename_2, baml_options={"client_registry": cr}
        )
    else:
        response = b.ExpExecutorSingleSensor(
            plan, filename, baml_options={"client_registry": cr}
        )
    return response
