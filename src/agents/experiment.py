import concurrent.futures
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
    logger.debug(
        f"Generating plan for experiment: {experiment.filename}, state: {state}"
    )
    logger.debug(
        f"Calling ExpPlanner with experiment: {experiment}, state: {state}"
    )
    planner_response = call_exp_planner(experiment, state)
    if isinstance(planner_response, Error):
        logger.error(f"ExpPlanner error: {planner_response.error}")
        return None, planner_response

    logger.debug(
        f"Calling ExpExecutor with plan: '{planner_response}', filename: '{experiment.filename}'"
    )
    experiment_tools = call_exp_executor(
        plan=planner_response, filename=experiment.filename
    )
    if isinstance(experiment_tools, Error):
        logger.error(f"ExpExecutor error: {experiment_tools.error}")
        return None, experiment_tools

    plan = ExperimentPlan(
        filename=experiment.filename, experiment=experiment_tools
    )
    return plan, None


def save_experiment_plans_to_project(
    plans: List[ExperimentPlan], project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Save experiment plans to the project and yield responses."""
    logger.debug(f"Saving {len(plans)} experiment plans")
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if not isinstance(metadata, ExperimentsMetadata):
        raise ValueError("Metadata is not ExperimentsMetadata")
    plans_path = metadata.plans_path
    save_status = save_experiment_plans(plans, plans_path)
    if save_status["success"]:
        yield AgentResponse(action="Experiment plans saved successfully.")
    else:
        logger.error(
            f"Failed to save plans: {save_status.get('error', 'Unknown error')}"
        )
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
                            status=f"Number of scans is 1, calling ExpPlanner with this experiment {single_experiment}"
                        )
                        logger.debug(
                            f"Generating plan for single experiment: {single_experiment.filename}"
                        )
                        plan, error = generate_plan_for_experiment(
                            single_experiment, init_state
                        )
                        if error:
                            logger.error(
                                f"Error generating plan for single experiment: {error.error}"
                            )
                            yield AgentResponse(
                                response=f"ERROR: {error.error}"
                            )
                        else:
                            yield AgentResponse(
                                status=f"Calling ExpExecutor with file name is `{single_experiment.filename}` and this abstract plan:\n {plan}"
                            )
                            yield AgentResponse(response="Plan generated.")

                            if plan:
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
                    yield AgentResponse(
                        status=f"Number of scans is {orchestrator_response.number_of_scans}, calling ExpPlanner for each experiment."
                    )
                    logger.debug(
                        f"Generating plans for experiments: {[e.filename for e in orchestrator_response.experiments]}"
                    )
                    plans: List[ExperimentPlan] = []
                    # Use concurrent execution for I/O-bound tasks
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = {
                            executor.submit(
                                generate_plan_for_experiment, experiment, init_state
                            ): experiment
                            for experiment in orchestrator_response.experiments
                        }
                        for future in concurrent.futures.as_completed(futures):
                            experiment = futures[future]
                            logger.debug(
                                f"Processing experiment: {experiment.filename}"
                            )
                            plan, error = future.result()
                            if error:
                                logger.error(
                                    f"Error generating plan for experiment {experiment.filename}: {error.error}"
                                )
                                yield AgentResponse(
                                    response=f"ERROR: {error.error}"
                                )
                            else:
                                yield AgentResponse(
                                    status=f"Processed experiment {experiment.filename} with plan: {plan}"
                                )
                                if plan:
                                    plans.append(plan)
                    yield AgentResponse(response="Plans generated.")
                    yield from save_experiment_plans_to_project(
                        plans, project_manager
                    )
