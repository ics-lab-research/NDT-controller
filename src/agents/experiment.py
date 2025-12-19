import concurrent.futures
from typing import Generator, List

from loguru import logger

from ..baml_client.types import (
    ConversationMessage,
    Error,
    ExpAction,
    Experiment,
    RelativeOffset,
    State,
)
from ..core.models import AgentResponse
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
)

current_position = RelativeOffset(x=0, y=0, z=1)
home_position = RelativeOffset(x=0, y=0, z=1)
init_state = State(
    current_position=current_position, home_position=home_position
)


def handle_experiment_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle EXPERIMENTS mode: orchestrate experiments based on user message."""
    logger.info("Handling experiment mode")
    logger.debug(
        f"Calling ExpRouter with user_message: '{user_message}', conversation_history length: {len(conversation_history)}"
    )

    router_response = call_exp_router(user_message, conversation_history)

    if router_response:
        yield AgentResponse(response=router_response.response)

        if router_response.action == ExpAction.ASK_CLARIFICATION:
            pass

        elif router_response.action == ExpAction.BASIC_CONTROL:
            pass

        elif router_response.action == ExpAction.SINGLE_SCAN:
            yield AgentResponse(status="Performing single scan.")

            if router_response.reformatted_message:
                yield AgentResponse(
                    status=f"Calling ExpOrchestrator with message: `{router_response.reformatted_message}`"
                )
                logger.debug(
                    f"Calling ExpOrchestrator with reformatted_message: '{router_response.reformatted_message}'"
                )
                orchestrator_response = call_exp_orchestrator(
                    reformatted_message=router_response.reformatted_message
                )

                if isinstance(orchestrator_response, Error):
                    logger.error(
                        f"ExpOrchestrator error: {orchestrator_response.error}"
                    )
                    yield AgentResponse(
                        response=f"ERROR: `{orchestrator_response.error}`"
                    )
                else:
                    if orchestrator_response.number_of_scans == 1:
                        single_experiment = orchestrator_response.experiments[0]
                        yield AgentResponse(
                            status=f"Generating abstract plan for {single_experiment.filename}"
                        )
                        logger.debug(
                            f"Calling ExpPlanner with experiment: {single_experiment}, state: {init_state}"
                        )
                        planner_response = call_exp_planner(
                            single_experiment, init_state
                        )
                        if isinstance(planner_response, Error):
                            logger.error(
                                f"ExpPlanner error: {planner_response.error}"
                            )
                            yield AgentResponse(
                                response=f"ERROR: {planner_response.error}"
                            )
                        else:
                            yield AgentResponse(
                                status=f"Abstract plan:\n {planner_response}"
                            )
                            yield AgentResponse(response="Plan generated.")
                    else:
                        yield AgentResponse(
                            response="ERROR: Number of scan is not 1"
                        )

        elif router_response.action == ExpAction.MULTIPLE_SCAN:
            yield AgentResponse(status="Performing multiple scan.")

            if router_response.reformatted_message:
                yield AgentResponse(
                    status=f"Calling ExpOrchestrator with message: `{router_response.reformatted_message}`"
                )
                orchestrator_response = call_exp_orchestrator(
                    reformatted_message=router_response.reformatted_message
                )

                if isinstance(orchestrator_response, Error):
                    yield AgentResponse(
                        response=f"ERROR: `{orchestrator_response.error}`"
                    )
                else:
                    yield AgentResponse(
                        status=f"Number of scans is {orchestrator_response.number_of_scans}, generating abstract plans for each experiment."
                    )
                    logger.debug(
                        f"Generating abstract plans for experiments: {[e.filename for e in orchestrator_response.experiments]}"
                    )
                    # Use concurrent execution for I/O-bound tasks
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = {
                            executor.submit(
                                call_exp_planner,
                                experiment,
                                init_state,
                            ): experiment
                            for experiment in orchestrator_response.experiments
                        }
                        for future in concurrent.futures.as_completed(futures):
                            experiment = futures[future]
                            logger.debug(
                                f"Processing experiment: {experiment.filename}"
                            )
                            planner_response = future.result()
                            if isinstance(planner_response, Error):
                                logger.error(
                                    f"Error generating abstract plan for experiment {experiment.filename}: {planner_response.error}"
                                )
                                yield AgentResponse(
                                    response=f"ERROR: {planner_response.error}"
                                )
                            else:
                                yield AgentResponse(
                                    status=f"Abstract plan for {experiment.filename}:\n {planner_response}"
                                )
                    yield AgentResponse(response="Plans generated.")
