from typing import Generator, List

from loguru import logger

from ..agents.experiment_planning import save_experiment_plans
from ..baml_client.types import (
    ConversationMessage,
    ExpAction,
    Error,
    ExpRouterOutput,
)
from ..core.models import AgentResponse, ExperimentPlan, ExperimentsMetadata
from ..core.project_manager import ProjectManager
from .experiment_api import (
    call_exp_orchestrator,
    call_exp_planner,
    call_exp_router,
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

        # try to process if they want to control system

        # yield AgentResponse(response="Done again")

        # if router_final.action == ExpAction.BASIC_CONTROL:
        #     single_plan = call_exp_planner(user_message)

        # tool_connect_to_vi(
        #     vi_path=r"D:\PECT LLM\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi"
        # )
        # time.sleep(5)  # wait for VI to load
        # running = tool_get_vi_status()["running"]
        # print(running)

        # # BUG: running return False when VI is running
        # if not running:
        #     execute_single_plan(single_plan, project_manager)
        # else:
        #     tool_connect_to_vi(
        #         vi_path=r"D:\PECT LLM\MAIN - PECT - Autonics - Pulses - encoder_TCP1.vi"
        #     )
        #     tool_run_open_vi(run_vi=True)
        #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #     tool_handle_save_dialog(
        #         r"D:\other-repos\river\EXPERIMENTS\data", timestamp
        #     )

        #     execute_single_plan(single_plan, project_manager)

        #     yield AgentResponse(response="Done")

        if router_response.action == ExpAction.SINGLE_SCAN:
            yield AgentResponse(thinking="Performing single scan.")

            if router_response.reformatted_message:
                # orchestrator_response = call_exp_orchestrator(
                #     router_response.reformatted_message
                # )
                orchestrator_response = call_exp_orchestrator(
                    "fasdfds fadsf fsdf"
                )

                if isinstance(orchestrator_response, Error):
                    yield AgentResponse(response=orchestrator_response.error)
        #     yield AgentResponse(thinking="Called exp_orchestrator.")

        #     if orchestrator_response.number_of_scans == 1:
        #         yield AgentResponse(
        #             thinking="Number of scans is 1, calling exp_planner..."
        #         )
        #         single_experiment = orchestrator_response.experiments[0]

        #         experiment_tools = call_exp_planner(
        #             str(single_experiment.experiment),
        #             filename=single_experiment.filename,
        #         )

        #         single_plan = ExperimentPlan(
        #             filename=single_experiment.filename,
        #             experiment=experiment_tools,
        #         )
        #         yield AgentResponse(response="Plan generated.")

        #         metadata = project_manager.get_mode_metadata(
        #             project_manager.current_mode
        #         )
        #         if not isinstance(metadata, ExperimentsMetadata):
        #             raise ValueError("Metadata is not ExperimentsMetadata")
        #         plans_path = metadata.plans_path
        #         save_status = save_experiment_plans(
        #             [single_plan],
        #             plans_path,
        #         )

        #         if save_status["success"]:
        #             yield AgentResponse(
        #                 action="Experiment plans saved successfully."
        #             )
        #         else:
        #             yield AgentResponse(
        #                 action=f"Failed to save plans: {save_status.get('error', 'Unknown error')}"
        #             )

        # elif router_final.action == ExpAction.MULTIPLE_SCAN:
        #     yield AgentResponse(thinking="Performing multiple scan.")

        #     orchestrator_response = call_exp_orchestrator(user_message)
        #     yield AgentResponse(thinking="Called exp_orchestrator.")

        #     experiments = orchestrator_response.experiments
        #     plans_to_save: List[ExperimentPlan] = []
        #     for experiment in experiments:
        #         yield AgentResponse(
        #             thinking=f"Generating plan for {experiment.filename}..."
        #         )
        #         experiment_tools = call_exp_planner(
        #             user_message=str(experiment.experiment),
        #             filename=experiment.filename,
        #         )
        #         experiment_plan = ExperimentPlan(
        #             filename=experiment.filename,
        #             experiment=experiment_tools,
        #         )
        #         plans_to_save.append(experiment_plan)

        #     yield AgentResponse(response="Plans generated.")

        #     metadata = project_manager.get_mode_metadata(
        #         project_manager.current_mode
        #     )
        #     if not isinstance(metadata, ExperimentsMetadata):
        #         raise ValueError("Metadata is not ExperimentsMetadata")
        #     plans_path = metadata.plans_path
        #     save_status = save_experiment_plans(plans_to_save, plans_path)

        #     if save_status["success"]:
        #         yield AgentResponse(
        #             action="Experiment plans saved successfully."
        #         )
        #     else:
        #         yield AgentResponse(
        #             action=f"Failed to save plans: {save_status.get('error', 'Unknown error')}"
        #         )

        # elif router_final.action == ExpAction.ASK_CLARIFICATION:
        #     pass


def respond_stream(
    message: str,
    history: ChatHistory,
    ctx: ProjectManager,
) -> Generator[Tuple[ChatHistory, str], None, None]:
    """Handle chat responses with streaming."""
    # Add user message to history
    history.append({"role": "user", "content": message})
    # Add response placeholder
    history.append({"role": "assistant", "content": ""})
    yield history, ""

    thinking_added = False
    action_added = False

    # Convert history to conversation messages, excluding the new messages
    conversation_history = build_conversation_history(history[:-2])

    for agent_response in get_agent_response(
        message, conversation_history, ctx
    ):
        if agent_response.response:
            # Update response message
            history[-1]["content"] = agent_response.response
            yield history, ""

        if agent_response.thinking and agent_response.thinking.strip():
            if not thinking_added:
                # Append thinking message
                history.append(
                    {
                        "role": "assistant",
                        "content": agent_response.thinking,
                        "metadata": {"title": "🧠 Thinking"},
                    },
                )
                thinking_added = True
                yield history, ""
            else:
                # Update existing thinking message
                history[-1]["content"] = agent_response.thinking
                yield history, ""

        if agent_response.action and agent_response.action.strip():
            if not action_added:
                # Append action message
                history.append(
                    {
                        "role": "assistant",
                        "content": agent_response.action,
                        "metadata": {"title": "⚡ Action"},
                    },
                )
                action_added = True
                yield history, ""
            else:
                # Update existing action message
                history[-1]["content"] = agent_response.action
                yield history, ""
