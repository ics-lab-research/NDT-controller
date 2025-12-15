from typing import Generator, List

from datetime import datetime
import time

from loguru import logger

from ..baml_client.types import ConversationMessage, ExpAction
from ..core.models import AgentResponse
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
)
from .experiment_execution import execute_single_plan, execute_multiple_plans
from ..tools.labview_controller import (
    tool_connect_to_vi,
    tool_get_vi_status,
    tool_run_open_vi,
    tool_handle_save_dialog,
)

# def process_router_action(
#     action: ExpAction,
#     user_message: str,
#     metadata: IdeaMetadata,
#     project_manager: ProjectManager,
# ) -> tuple[str, bool]:
#     """Process the router action and return message and continue flag."""
#     if action == ExpAction.BASIC_CONTROL:
#         return user_message, True
#     elif action == ExpAction.LOAD_SAVED_PLAN:
#         logger.info(f"Loading saved plan from {metadata.experiment_plan_path}")
#         return tool_read_file(metadata.experiment_plan_path), True
#     elif action == ExpAction.ASK_CLARIFICATION:
#         return "", False
#     else:
#         logger.warning(f"Unknown action: {action}")
#         return "", False


def handle_experiment_mode(
    user_message: str,
    conversation_history: List[ConversationMessage],
    project_manager: ProjectManager,
) -> Generator[AgentResponse, None, None]:
    """Handle EXPERIMENTS mode: orchestrate experiments based on user message."""
    logger.info("Handling experiment mode")

    router_response = call_exp_router(user_message, conversation_history)

    if router_response:
        for chunk in router_response:
            yield AgentResponse(response=chunk.response)

        # try to process if they want to control system
        router_final = router_response.get_final_response()

        if router_final.action == ExpAction.ASK_CLARIFICATION:
            pass

        elif router_final.action == ExpAction.BASIC_CONTROL:
            single_plan = call_exp_planner(user_message)

            tool_connect_to_vi(
                vi_path=r"D:\PECT LLM\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi"
            )
            time.sleep(5)  # wait for VI to load
            running = tool_get_vi_status()["running"]
            print(running)

            # BUG: running return False when VI is running
            if not running:
                execute_single_plan(single_plan, project_manager)
            else:
                tool_connect_to_vi(
                    vi_path=r"D:\PECT LLM\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi"
                )
                tool_run_open_vi(run_vi=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                tool_handle_save_dialog(
                    r"D:\other-repos\river\EXPERIMENTS\data", timestamp
                )

                execute_single_plan(single_plan, project_manager)

            yield AgentResponse(response="Done")

        elif router_final.action == ExpAction.SINGLE_SCAN:
            orchestrator_response = call_exp_orchestrator(user_message)

            if orchestrator_response.number_of_scans == 1:
                single_experiment = orchestrator_response.experiments[0]

                single_plan = call_exp_planner(
                    user_message, filename=single_experiment.filename
                )
                execute_single_plan(single_plan, project_manager)

            yield AgentResponse(response="Done")

        elif router_final.action == ExpAction.MULTIPLE_SCAN:
            all_plans = []

            orchestrator_response = call_exp_orchestrator(user_message)

            experiments = orchestrator_response.experiments
            for experiment in experiments:
                plan = call_exp_planner(
                    user_message=str(experiment.experiment),
                    filename=experiment.filename,
                )
                all_plans.append(plan)

            execute_multiple_plans(all_plans, project_manager)

            yield AgentResponse(response="Done")

    # router_metadata = router_response.metadata or {}
    # yield AgentResponse(response=router_response.response)

    # metadata = project_manager.get_mode_metadata(Mode.IDEA)
    # if not isinstance(metadata, IdeaMetadata):
    #     raise ValueError("Expected IdeaMetadata for experiment plan check")

    # action = router_metadata.get("action", ExpAction.ASK_CLARIFICATION)
    # message, continue_flag = process_router_action(
    #     action, user_message, metadata, project_manager
    # )

    # if action == ExpAction.LOAD_SAVED_PLAN:
    #     yield AgentResponse(
    #         actions=[
    #             f"Retrieved existing experiment plan from {metadata.experiment_plan_path.name}"
    #         ],
    #     )

    # if not continue_flag:
    #     return

    # orchestrator_response = call_exp_orchestrator(message, conversation_history)

    # if not orchestrator_response or not orchestrator_response.metadata:
    #     yield AgentResponse(response="No experiments identified.")
    #     return

    # experiments = orchestrator_response.metadata.get("experiments", [])
    # if not experiments:
    #     yield AgentResponse(response="No experiments to plan.")
    #     return

    # yield AgentResponse(
    #     actions=[f"Planning {len(experiments)} experiment(s)..."],
    # )

    # all_plans = plan_experiments(experiments, project_manager)

    # exp_metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    # if not isinstance(exp_metadata, ExperimentsMetadata):
    #     raise ValueError("Not in experiments mode")
    # save_experiment_plans(all_plans, exp_metadata.plans_path)

    # yield AgentResponse(
    #     actions=[f"Experiment plans saved to {exp_metadata.plans_path.name}"],
    # )
