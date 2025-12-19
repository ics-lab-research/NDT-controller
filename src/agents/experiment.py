from typing import Generator, List

from loguru import logger

from ..agents.experiment_planning import save_experiment_plans
from ..baml_client.types import (
    ConversationMessage,
    ExpAction,
    Error,
    ExpRouterOutput,
)
from ..core.models import AgentResponse, ExperimentPlan, ExperimentsMetadata
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
)


def handle_experiment_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle EXPERIMENTS mode: orchestrate experiments based on user message."""
    logger.info("Handling experiment mode")

    router_response = call_exp_router(user_message, conversation_history)

    if router_response:
        yield AgentResponse(response=router_response.response)

        if router_response.action == ExpAction.SINGLE_SCAN:
            yield AgentResponse(thinking="Performing single scan.")

            if router_response.reformatted_message:
                # orchestrator_response = call_exp_orchestrator(
                #     router_response.reformatted_message
                # )
                orchestrator_response = call_exp_orchestrator(
                    "fasdfds fadsf fsdf"
                )

                # yield error here AI!
                if isinstance(orchestrator_response, Error):
                    yield AgentResponse(response=orchestrator_response.error)
