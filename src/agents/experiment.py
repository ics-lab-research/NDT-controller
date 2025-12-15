from typing import Generator, List


from loguru import logger

from ..baml_client.types import ConversationMessage, ExpAction
from ..core.models import AgentResponse, ExperimentsMetadata
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
)
from ..agents.experiment_planning import save_experiment_plans
from ..core.models import ExperimentPlan


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
            yield AgentResponse(thinking="Performing single scan.")

            orchestrator_response = call_exp_orchestrator(user_message)
            yield AgentResponse(thinking="Called exp_orchestrator.")

            if orchestrator_response.number_of_scans == 1:
                yield AgentResponse(
                    thinking="Number of scans is 1, calling exp_planner..."
                )
                single_experiment = orchestrator_response.experiments[0]

                experiment_tools = call_exp_planner(
                    str(single_experiment.experiment),
                    filename=single_experiment.filename,
                )

                single_plan = ExperimentPlan(
                    filename=single_experiment.filename,
                    experiment=experiment_tools,
                )
                yield AgentResponse(response="Plan generated.")

                metadata = project_manager.get_mode_metadata(
                    project_manager.current_mode
                )
                if not isinstance(metadata, ExperimentsMetadata):
                    raise ValueError("Metadata is not ExperimentsMetadata")
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

        elif router_final.action == ExpAction.MULTIPLE_SCAN:
            yield AgentResponse(thinking="Performing multiple scan.")

            orchestrator_response = call_exp_orchestrator(user_message)
            yield AgentResponse(thinking="Called exp_orchestrator.")

            experiments = orchestrator_response.experiments
            plans_to_save: List[ExperimentPlan] = []
            for experiment in experiments:
                yield AgentResponse(
                    thinking=f"Generating plan for {experiment.filename}..."
                )
                experiment_tools = call_exp_planner(
                    user_message=str(experiment.experiment),
                    filename=experiment.filename,
                )
                experiment_plan = ExperimentPlan(
                    filename=experiment.filename,
                    experiment=experiment_tools,
                )
                plans_to_save.append(experiment_plan)

            yield AgentResponse(response="Plans generated.")

            metadata = project_manager.get_mode_metadata(
                project_manager.current_mode
            )
            if not isinstance(metadata, ExperimentsMetadata):
                raise ValueError("Metadata is not ExperimentsMetadata")
            plans_path = metadata.plans_path
            save_status = save_experiment_plans(plans_to_save, plans_path)

            if save_status["success"]:
                yield AgentResponse(
                    action="Experiment plans saved successfully."
                )
            else:
                yield AgentResponse(
                    action=f"Failed to save plans: {save_status.get('error', 'Unknown error')}"
                )

        elif router_final.action == ExpAction.ASK_CLARIFICATION:
            pass
