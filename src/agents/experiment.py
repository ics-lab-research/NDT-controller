from typing import Generator, List

from datetime import datetime
import time

from loguru import logger

from ..baml_client.types import ConversationMessage, ExpAction
from ..core.models import AgentResponse, ExperimentsMetadata
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
)
from .experiment_execution import execute_single_plan, execute_multiple_plans
from ..agents.experiment_planning import save_experiment_plans
from ..tools.labview_controller import (
    tool_connect_to_vi,
    tool_get_vi_status,
    tool_run_open_vi,
    tool_handle_save_dialog,
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
        for chunk in router_response:
            yield AgentResponse(response=chunk.response)

        # try to process if they want to control system
        router_final = router_response.get_final_response()

        # elif router_final.action == ExpAction.BASIC_CONTROL:
        #     single_plan = call_exp_planner(user_message)

        #     tool_connect_to_vi(
        #         vi_path=r"D:\PECT LLM\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi"
        #     )
        #     time.sleep(5)  # wait for VI to load
        #     running = tool_get_vi_status()["running"]
        #     print(running)

        #     # BUG: running return False when VI is running
        #     if not running:
        #         execute_single_plan(single_plan, project_manager)
        #     else:
        #         tool_connect_to_vi(
        #             vi_path=r"D:\PECT LLM\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi"
        #         )
        #         tool_run_open_vi(run_vi=True)
        #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #         tool_handle_save_dialog(
        #             r"D:\other-repos\river\EXPERIMENTS\data", timestamp
        #         )

        #         execute_single_plan(single_plan, project_manager)

        #     yield AgentResponse(response="Done")

        if router_final.action == ExpAction.SINGLE_SCAN:
            yield AgentResponse(response="Performing single scan.")

            orchestrator_response = call_exp_orchestrator(user_message)
            yield AgentResponse(response="Called exp_orchestrator.")

            if orchestrator_response.number_of_scans == 1:
                yield AgentResponse(
                    response="Number of scans is 1, calling exp_planner..."
                )
                single_experiment = orchestrator_response.experiments[0]

                single_plan = call_exp_planner(
                    user_message, filename=single_experiment.filename
                )
                yield AgentResponse(response="Plan generated.")

                metadata = project_manager.get_mode_metadata(
                    project_manager.current_mode
                )
                if not isinstance(metadata, ExperimentsMetadata):
                    raise ValueError("Metadata is not ExperimentsMetadata")
                plans_path = metadata.plans_path
                save_experiment_plans(
                    [
                        {
                            "filename": single_experiment.filename,
                            "tools": [tool.__dict__ for tool in single_plan],
                            "approved": False,
                        }
                    ],
                    plans_path,
                )

            yield AgentResponse(action="Done")

        # elif router_final.action == ExpAction.MULTIPLE_SCAN:
        #     all_plans = []

        #     orchestrator_response = call_exp_orchestrator(user_message)

        #     experiments = orchestrator_response.experiments
        #     for experiment in experiments:
        #         plan = call_exp_planner(
        #             user_message=str(experiment.experiment),
        #             filename=experiment.filename,
        #         )
        #         all_plans.append(plan)

        #     execute_multiple_plans(all_plans, project_manager)

        #     yield AgentResponse(response="Done")

        else:
            pass
