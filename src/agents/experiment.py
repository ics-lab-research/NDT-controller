from typing import Generator, List

from loguru import logger

from ..baml_client.types import (
    ConversationMessage,
    Error,
    ExpAction,
    Experiment,
    ExpOrchestratorOutput,
)
from ..core.models import AgentResponse, ExperimentPlan, ExperimentsMetadata
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_basic_executor,
    call_exp_executor,
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
)
from .experiment_execution import execute_tool
from .experiment_planning import append_experiment_plans


def yield_error(error: Error) -> Generator[AgentResponse, None, None]:
    """Yield an error response."""
    logger.error(f"Error: {error.error}")
    yield AgentResponse(status=f"ERROR: {error.error}")


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
    save_result = append_experiment_plans(plans, metadata.plans_path)

    if save_result["success"]:
        message = (
            "Plan generated and saved."
            if len(plans) == 1
            else "Plans generated and saved."
        )
        yield AgentResponse(action=message)
    else:
        error_msg = save_result.get("error", "Unknown error")
        yield AgentResponse(
            action=f"ERROR: Plans generated but save failed: {error_msg}"
        )


def process_single_experiment(
    experiment: Experiment,
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, ExperimentPlan | Error]:
    """Process a single experiment through planning and execution."""
    yield AgentResponse(
        intermediate_step=f"Generating abstract plan for `{experiment.filename}`"
    )
    logger.debug(
        f"Calling ExpPlanner with experiment: {experiment}, experiment_state: {project_manager.experiment_state}"
    )

    plan = call_exp_planner(experiment, project_manager.experiment_state)
    if isinstance(plan, Error):
        yield from yield_error(plan)
        return plan

    yield AgentResponse(
        intermediate_step=f"Calling ExpExecutor with filename: `{experiment.filename}` and abstract plan:\n {plan}"
    )
    logger.debug(
        f"Calling ExpExecutor with plan: '{plan}', filename: '{experiment.filename}'"
    )

    tools = call_exp_executor(plan, experiment.filename)
    if isinstance(tools, Error):
        yield from yield_error(tools)
        return tools

    return ExperimentPlan(
        id=str(uuid.uuid4()), filename=experiment.filename, experiment=tools
    )


def handle_single_scan(
    orchestrator_output: ExpOrchestratorOutput,
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle single scan experiment workflow."""
    if orchestrator_output.number_of_scans != 1:
        yield AgentResponse(status="ERROR: Number of scan is not 1")

    experiment = orchestrator_output.experiments[0]
    result = yield from process_single_experiment(
        experiment,
        project_manager,
    )

    # NOTE: each scan will return home position
    if isinstance(result, ExperimentPlan):
        new_position = project_manager.experiment_state.home_position
        project_manager.update_experiment_state(new_position)
        yield from save_plans([result], project_manager)


def handle_multiple_scan(
    orchestrator_output: ExpOrchestratorOutput,
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle multiple scan experiments workflow."""
    yield AgentResponse(
        intermediate_step=f"Number of scans is {orchestrator_output.number_of_scans}, generating abstract plans for each experiment."
    )
    logger.debug(
        f"Generating abstract plans for experiments: {[e.filename for e in orchestrator_output.experiments]}"
    )

    def process_experiment(
        experiment: Experiment,
    ) -> Generator[AgentResponse, None, ExperimentPlan | None]:
        logger.debug(f"Processing experiment: {experiment.filename}")

        plan = call_exp_planner(experiment, project_manager.experiment_state)
        if isinstance(plan, Error):
            yield from yield_error(plan)
            return None

        yield AgentResponse(
            intermediate_step=f"Calling ExpExecutor with filename: `{experiment.filename}` and abstract plan:\n {plan}"
        )
        logger.debug(
            f"Calling ExpExecutor with plan: '{plan}', filename: '{experiment.filename}'"
        )

        tools = call_exp_executor(plan, experiment.filename)
        if isinstance(tools, Error):
            yield from yield_error(tools)
            return None

        # NOTE: each scan will return home position
        new_position = project_manager.experiment_state.home_position
        project_manager.update_experiment_state(new_position)

        exp_plan = ExperimentPlan(
            id=str(uuid.uuid4()), filename=experiment.filename, experiment=tools
        )
        return exp_plan

    plans_to_save = []
    for experiment in orchestrator_output.experiments:
        gen = process_experiment(experiment)
        try:
            while True:
                msg = next(gen)
                yield msg
        except StopIteration as e:
            plan = e.value
            if plan:
                plans_to_save.append(plan)

    if plans_to_save:
        yield from save_plans(plans_to_save, project_manager)
    else:
        yield AgentResponse(status="No plans generated.")


def orchestrate_experiments(
    reformatted_message: str, project_manager: ProjectManager, action: ExpAction
) -> Generator[AgentResponse, None, None]:
    """Orchestrate experiment workflow based on action type."""
    yield AgentResponse(
        intermediate_step=f"Calling ExpOrchestrator with message: `{reformatted_message}`"
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
    logger.debug(f"Calling ExpRouter with user_message: '{user_message}'")

    router_response = call_exp_router(user_message, conversation_history)
    if not router_response:
        return

    yield AgentResponse(response=router_response.response)

    # Determine next steps based on router action
    if router_response.action == ExpAction.ASK_CLARIFICATION:
        return

    elif router_response.action == ExpAction.BASIC_CONTROL:
        yield AgentResponse(intermediate_step="Performing basic control")

        tools = call_exp_basic_executor(user_message)
        if isinstance(tools, Error):
            yield from yield_error(tools)
            return

        for tool in tools:
            result = execute_tool(tool, project_manager)
            if not result.success:
                yield AgentResponse(status=f"ERROR: {result.error}")

    elif router_response.action == ExpAction.SINGLE_SCAN:
        yield AgentResponse(intermediate_step="Performing single scan")

    elif router_response.action == ExpAction.MULTIPLE_SCAN:
        yield AgentResponse(intermediate_step="Performing multiple scan")

    if router_response.reformatted_message:
        yield from orchestrate_experiments(
            router_response.reformatted_message,
            project_manager,
            router_response.action,
        )
