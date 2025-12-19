from typing import Generator, List

from loguru import logger

from ..agents.experiment_planning import save_experiment_plans
from ..baml_client.types import (
    ConversationMessage,
    Error,
    ExpAction,
    RelativeOffset,
    State,
)
from ..core.models import AgentResponse, ExperimentPlan, ExperimentsMetadata
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
    call_exp_executor,
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
                orchestrator_response = call_exp_orchestrator(
                    reformatted_message=router_response.reformatted_message
                )

                # check if error
                if isinstance(orchestrator_response, Error):
                    yield AgentResponse(
                        response=f"ERROR: `{orchestrator_response.error}`"
                    )
                else:
                    # check number of scans again
                    if orchestrator_response.number_of_scans == 1:
                        yield AgentResponse(
                            status=f"Number of scans is 1, calling ExpPlanner with this experiment {orchestrator_response.experiments[0]}"
                        )
                        single_experiment = orchestrator_response.experiments[0]

                        planner_response = call_exp_planner(
                            experiment=single_experiment, state=init_state
                        )

                        if isinstance(planner_response, Error):
                            yield AgentResponse(
                                response=f"ERROR: {planner_response.error}"
                            )
                        else:
                            yield AgentResponse(
                                status=f"Calling ExpExecutor with file name is `{single_experiment.filename}` and this abstract plan:\n {planner_response}"
                            )

                            experiment_tools = call_exp_executor(
                                plan=planner_response,
                                filename=single_experiment.filename,
                            )

                            if isinstance(experiment_tools, Error):
                                yield AgentResponse(
                                    response=f"ERROR: {experiment_tools.error}"
                                )
                            else:
                                single_plan = ExperimentPlan(
                                    filename=single_experiment.filename,
                                    experiment=experiment_tools,
                                )
                                yield AgentResponse(response="Plan generated.")

                                metadata = project_manager.get_mode_metadata(
                                    project_manager.current_mode
                                )
                                if not isinstance(
                                    metadata, ExperimentsMetadata
                                ):
                                    raise ValueError(
                                        "Metadata is not ExperimentsMetadata"
                                    )
                                plans_path = metadata.plans_path
                                save_status = save_experiment_plans(
                                    [single_plan],
                                    plans_path,
                                )

                                if save_status["success"]:
                                    yield AgentResponse(
                                        action="Experiment plans saved successfully."
                                    )
                                else:
                                    yield AgentResponse(
                                        action=f"Failed to save plans: {save_status.get('error', 'Unknown error')}"
                                    )
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
                    # TODO: change for loop later
                    # TODO: have to update state between scans
                    for experiment in orchestrator_response.experiments:
                        planner_response = call_exp_planner(
                            experiment, state=init_state
                        )

                        if isinstance(planner_response, Error):
                            yield AgentResponse(
                                response=f"ERROR: {planner_response.error}"
                            )

                        else:
                            yield AgentResponse(
                                status=f"Calling ExpExecutor with file name is `{experiment.filename}` and this abstract plan:\n {planner_response}"
                            )

                            experiment_tools = call_exp_executor(
                                plan=planner_response,
                                filename=experiment.filename,
                            )

                            if isinstance(experiment_tools, Error):
                                yield AgentResponse(
                                    response=f"ERROR: {experiment_tools.error}"
                                )
                            else:
                                single_plan = ExperimentPlan(
                                    filename=experiment.filename,
                                    experiment=experiment_tools,
                                )
