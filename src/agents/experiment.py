from typing import Generator, List, Tuple

from loguru import logger

from ..agents.experiment_planning import save_experiment_plans
from ..baml_client.types import (
    ConversationMessage,
    Error,
    ExpAction,
    Experiment,
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


def generate_plan_for_experiment(
    experiment: Experiment, state: State
) -> Tuple[ExperimentPlan | None, Error | None]:
    """Generate a plan for a single experiment, returning the plan or an error."""
    planner_response = call_exp_planner(experiment, state)
    if isinstance(planner_response, Error):
        return None, planner_response
    
    experiment_tools = call_exp_executor(
        plan=planner_response, filename=experiment.filename
    )
    if isinstance(experiment_tools, Error):
        return None, experiment_tools
    
    plan = ExperimentPlan(filename=experiment.filename, experiment=experiment_tools)
    return plan, None


def save_experiment_plans_to_project(
    plans: List[ExperimentPlan], project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Save experiment plans to the project and yield responses."""
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if not isinstance(metadata, ExperimentsMetadata):
        raise ValueError("Metadata is not ExperimentsMetadata")
    plans_path = metadata.plans_path
    save_status = save_experiment_plans(plans, plans_path)
    if save_status["success"]:
        yield AgentResponse(action="Experiment plans saved successfully.")
    else:
        yield AgentResponse(
            action=f"Failed to save plans: {save_status.get('error', 'Unknown error')}"
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

                if isinstance(orchestrator_response, Error):
                    yield AgentResponse(
                        response=f"ERROR: `{orchestrator_response.error}`"
                    )
                else:
                    if orchestrator_response.number_of_scans == 1:
                        single_experiment = orchestrator_response.experiments[0]
                        yield AgentResponse(
                            status=f"Number of scans is 1, calling ExpPlanner with this experiment {single_experiment}"
                        )
                        plan, error = generate_plan_for_experiment(
                            single_experiment, init_state
                        )
                        if error:
                            yield AgentResponse(
                                response=f"ERROR: {error.error}"
                            )
                        else:
                            yield AgentResponse(
                                status=f"Calling ExpExecutor with file name is `{single_experiment.filename}` and this abstract plan:\n {plan}"
                            )
                            yield AgentResponse(response="Plan generated.")
                            yield from save_experiment_plans_to_project(
                                [plan], project_manager
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
                    plans = []
                    # TODO: change for loop later
                    # TODO: have to update state between scans
                    for experiment in orchestrator_response.experiments:
                        yield AgentResponse(
                            status=f"Calling ExpPlanner with this experiment {experiment}"
                        )
                        plan, error = generate_plan_for_experiment(
                            experiment, init_state
                        )
                        if error:
                            yield AgentResponse(
                                response=f"ERROR: {error.error}"
                            )
                        else:
                            yield AgentResponse(
                                status=f"Calling ExpExecutor with file name is `{experiment.filename}` and this abstract plan:\n {plan}"
                            )
                            plans.append(plan)
                    yield AgentResponse(response="Plans generated.")
                    yield from save_experiment_plans_to_project(
                        plans, project_manager
                    )
