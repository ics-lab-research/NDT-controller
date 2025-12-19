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
    logger.info("Generating plan for experiment")
    planner_response = call_exp_planner(experiment, state)
    if isinstance(planner_response, Error):
        logger.error(f"Planner error: {planner_response.error}")
        return None, planner_response

    experiment_tools = call_exp_executor(
        plan=planner_response, filename=experiment.filename
    )
    if isinstance(experiment_tools, Error):
        logger.error(f"Executor error: {experiment_tools.error}")
        return None, experiment_tools

    plan = ExperimentPlan(
        filename=experiment.filename, experiment=experiment_tools
    )
    logger.info("Plan generated successfully")
    return plan, None


def save_experiment_plans_to_project(
    plans: List[ExperimentPlan], project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Save experiment plans to the project and yield responses."""
    logger.info("Saving experiment plans to project")
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if not isinstance(metadata, ExperimentsMetadata):
        error_msg = "Metadata is not ExperimentsMetadata"
        logger.error(error_msg)
        raise ValueError(error_msg)
    plans_path = metadata.plans_path
    save_status = save_experiment_plans(plans, plans_path)
    if save_status["success"]:
        logger.info("Experiment plans saved successfully")
        yield AgentResponse(action="Experiment plans saved successfully.")
    else:
        error = save_status.get("error", "Unknown error")
        logger.error(f"Failed to save plans: {error}")
        yield AgentResponse(action=f"Failed to save plans: {error}")


def handle_ask_clarification() -> Generator[AgentResponse, None, None]:
    """Handle ask clarification action: no operation."""
    logger.info("Handling ask clarification")
    # No specific action required for clarification


def handle_basic_control() -> Generator[AgentResponse, None, None]:
    """Handle basic control action: no operation."""
    logger.info("Handling basic control")
    # No specific action required for basic control


def handle_single_scan(
    reformatted_message: str, project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Handle single scan action."""
    logger.info("Handling single scan")
    yield AgentResponse(status="Performing single scan.")

    if reformatted_message:
        yield AgentResponse(
            status=f"Calling ExpOrchestrator with message: `{reformatted_message}`"
        )
        orchestrator_response = call_exp_orchestrator(
            reformatted_message=reformatted_message
        )

        if isinstance(orchestrator_response, Error):
            logger.error(f"Orchestrator error: {orchestrator_response.error}")
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
                    yield AgentResponse(response=f"ERROR: {error.error}")
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
                error_msg = "ERROR: Number of scan is not 1"
                logger.error(error_msg)
                yield AgentResponse(response=error_msg)


def handle_multiple_scan(
    reformatted_message: str, project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Handle multiple scan action."""
    logger.info("Handling multiple scan")
    yield AgentResponse(status="Performing multiple scan.")

    if reformatted_message:
        yield AgentResponse(
            status=f"Calling ExpOrchestrator with message: `{reformatted_message}`"
        )
        orchestrator_response = call_exp_orchestrator(
            reformatted_message=reformatted_message
        )

        if isinstance(orchestrator_response, Error):
            logger.error(f"Orchestrator error: {orchestrator_response.error}")
            yield AgentResponse(
                response=f"ERROR: `{orchestrator_response.error}`"
            )
        else:
            yield AgentResponse(
                status=f"Number of scans is {orchestrator_response.number_of_scans}, calling ExpPlanner for each experiment."
            )
            plans: List[ExperimentPlan] = []
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
                    yield AgentResponse(response=f"ERROR: {error.error}")
                else:
                    yield AgentResponse(
                        status=f"Calling ExpExecutor with file name is `{experiment.filename}` and this abstract plan:\n {plan}"
                    )
                    if plan:
                        plans.append(plan)
            yield AgentResponse(response="Plans generated.")
            yield from save_experiment_plans_to_project(plans, project_manager)


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

        action_handlers = {
            ExpAction.ASK_CLARIFICATION: handle_ask_clarification,
            ExpAction.BASIC_CONTROL: handle_basic_control,
            ExpAction.SINGLE_SCAN: lambda: handle_single_scan(
                router_response.reformatted_message, project_manager
            ),
            ExpAction.MULTIPLE_SCAN: lambda: handle_multiple_scan(
                router_response.reformatted_message, project_manager
            ),
        }

        handler = action_handlers.get(router_response.action)
        if handler:
            yield from handler()
        else:
            logger.warning(f"Unknown action: {router_response.action}")
