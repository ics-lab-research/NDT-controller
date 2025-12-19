import concurrent.futures
import random
from typing import Generator, List

from loguru import logger

from ..baml_client.types import (
    ConversationMessage,
    Error,
    Experiment,
    ExpAction,
    ExpOrchestratorOutput,
    RelativeOffset,
    State,
)
from ..core.models import AgentResponse, ExperimentPlan, ExperimentsMetadata
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_executor,
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
)
from .experiment_planning import save_experiment_plans


def create_initial_state() -> State:
    """Create the initial state for experiments."""
    position = RelativeOffset(x=0, y=0, z=1)
    return State(current_position=position, home_position=position)


def update_state(
    current_state: State, metadata: ExpOrchestratorOutput
) -> State:
    """Update the state based on executed tools. Placeholder with random values."""
    new_x = random.randint(-10, 10)
    new_y = random.randint(-10, 10)
    new_z = random.randint(0, 5)
    new_position = RelativeOffset(x=new_x, y=new_y, z=new_z)
    return State(
        current_position=new_position, home_position=current_state.home_position
    )


def yield_error(error: Error) -> Generator[AgentResponse, None, None]:
    """Yield an error response."""
    logger.error(f"Error: {error.error}")
    yield AgentResponse(response=f"ERROR: {error.error}")


def get_experiments_metadata(
    project_manager: ProjectManager,
) -> ExperimentsMetadata:
    """Get and validate experiments metadata from project manager."""
    metadata = project_manager.get_mode_metadata(project_manager.current_mode)
    if not isinstance(metadata, ExperimentsMetadata):
        raise ValueError("Metadata is not ExperimentsMetadata")
    return metadata


def save_plans(
    plans: List[ExperimentPlan], project_manager: ProjectManager
) -> Generator[AgentResponse, None, None]:
    """Save experiment plans and yield appropriate response."""
    metadata = get_experiments_metadata(project_manager)
    save_result = save_experiment_plans(plans, metadata.plans_path)

    if save_result["success"]:
        message = (
            "Plan generated and saved."
            if len(plans) == 1
            else "Plans generated and saved."
        )
        yield AgentResponse(response=message)
    else:
        error_msg = save_result.get("error", "Unknown error")
        yield AgentResponse(
            response=f"Plans generated but save failed: {error_msg}"
        )


def process_single_experiment(
    experiment: Experiment, state: State
) -> Generator[AgentResponse, None, ExperimentPlan | Error]:
    """Process a single experiment through planning and execution."""
    yield AgentResponse(
        status=f"Generating abstract plan for {experiment.filename}"
    )
    logger.debug(
        f"Calling ExpPlanner with experiment: {experiment}, state: {state}"
    )

    plan = call_exp_planner(experiment, state)
    if isinstance(plan, Error):
        yield from yield_error(plan)
        return plan

    yield AgentResponse(
        status=f"Calling ExpExecutor with filename: {experiment.filename} and abstract plan:\n {plan}"
    )
    logger.debug(
        f"Calling ExpExecutor with plan: '{plan}', filename: '{experiment.filename}'"
    )

    tools = call_exp_executor(plan, experiment.filename)
    if isinstance(tools, Error):
        yield from yield_error(tools)
        return tools

    return ExperimentPlan(filename=experiment.filename, experiment=tools)


def handle_single_scan(
    orchestrator_output: ExpOrchestratorOutput,
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle single scan experiment workflow."""
    if orchestrator_output.number_of_scans != 1:
        yield AgentResponse(response="ERROR: Number of scan is not 1")
        return

    state = create_initial_state()
    experiment = orchestrator_output.experiments[0]
    result = yield from process_single_experiment(experiment, state)

    if isinstance(result, ExperimentPlan):
        yield from save_plans([result], project_manager)


def handle_multiple_scan(
    orchestrator_output: ExpOrchestratorOutput,
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle multiple scan experiments workflow with concurrent execution."""
    yield AgentResponse(
        status=f"Number of scans is {orchestrator_output.number_of_scans}, generating abstract plans for each experiment."
    )
    logger.debug(
        f"Generating abstract plans for experiments: {[e.filename for e in orchestrator_output.experiments]}"
    )

    state = create_initial_state()
    plans_to_save = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(call_exp_planner, experiment, state): experiment
            for experiment in orchestrator_output.experiments
        }

        for future in concurrent.futures.as_completed(futures):
            experiment = futures[future]
            logger.debug(f"Processing experiment: {experiment.filename}")

            plan = future.result()
            if isinstance(plan, Error):
                yield from yield_error(plan)
                continue

            yield AgentResponse(
                status=f"Calling ExpExecutor with filename: {experiment.filename} and abstract plan:\n {plan}"
            )
            logger.debug(
                f"Calling ExpExecutor with plan: '{plan}', filename: '{experiment.filename}'"
            )

            tools = call_exp_executor(plan, experiment.filename)
            if isinstance(tools, Error):
                yield from yield_error(tools)
                continue

            plans_to_save.append(
                ExperimentPlan(filename=experiment.filename, experiment=tools)
            )

    if plans_to_save:
        yield from save_plans(plans_to_save, project_manager)
    else:
        yield AgentResponse(response="No plans generated.")


def orchestrate_experiments(
    reformatted_message: str, project_manager: ProjectManager, action: ExpAction
) -> Generator[AgentResponse, None, None]:
    """Orchestrate experiment workflow based on action type."""
    yield AgentResponse(
        status=f"Calling ExpOrchestrator with message: `{reformatted_message}`"
    )
    logger.debug(
        f"Calling ExpOrchestrator with reformatted_message: '{reformatted_message}'"
    )

    orchestrator_output = call_exp_orchestrator(reformatted_message)
    if isinstance(orchestrator_output, Error):
        yield from yield_error(orchestrator_output)
        return

    if action == ExpAction.SINGLE_SCAN:
        yield from handle_single_scan(orchestrator_output, project_manager)
    elif action == ExpAction.MULTIPLE_SCAN:
        yield from handle_multiple_scan(orchestrator_output, project_manager)


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
    if not router_response:
        return

    yield AgentResponse(response=router_response.response)

    if router_response.action in (
        ExpAction.ASK_CLARIFICATION,
        ExpAction.BASIC_CONTROL,
    ):
        return

    if router_response.action == ExpAction.SINGLE_SCAN:
        yield AgentResponse(status="Performing single scan.")
    elif router_response.action == ExpAction.MULTIPLE_SCAN:
        yield AgentResponse(status="Performing multiple scan.")

    if router_response.reformatted_message:
        yield from orchestrate_experiments(
            router_response.reformatted_message,
            project_manager,
            router_response.action,
        )
