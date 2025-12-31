from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import gradio as gr
import pandas as pd
from loguru import logger

from ..agents.experiment_planning import save_experiment_plans
from ..baml_client.types import (
    ConnectToViTool,
    ConversationMessage,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
    StopViTool,
    WaitForOperationCompleteTool,
)
from ..core.models import (
    ChatHistory,
    ChatMessage,
    ExperimentPlan,
    ExperimentStep,
    ExperimentTool,
    MessageType,
)

tool_map = {
    "ConnectToViTool": ConnectToViTool,
    "HandleSaveDialogTool": HandleSaveDialogTool,
    "PressButtonTool": PressButtonTool,
    "RunOpenViTool": RunOpenViTool,
    "SelectComboBoxTool": SelectComboBoxTool,
    "SelectTabTool": SelectTabTool,
    "SetButtonStateTool": SetButtonStateTool,
    "SetNumericControlTool": SetNumericControlTool,
    "StopViTool": StopViTool,
    "WaitForOperationCompleteTool": WaitForOperationCompleteTool,
}

tool_name_map: Dict[str, str] = {
    "ConnectToViTool": "connect_to_vi",
    "HandleSaveDialogTool": "handle_save_dialog",
    "PressButtonTool": "press_button",
    "RunOpenViTool": "run_open_vi",
    "SelectComboBoxTool": "select_combo_box",
    "SelectTabTool": "select_tab",
    "SetButtonStateTool": "set_button_state",
    "SetNumericControlTool": "set_numeric_control",
    "StopViTool": "stop_vi",
    "WaitForOperationCompleteTool": "wait_for_operation_complete",
}


def _tool_to_table_row(tool: ExperimentTool) -> List[str]:
    tool_name = type(tool).__name__
    params = {k: v for k, v in vars(tool).items() if k != "tool_name"}
    param_list = [
        f"{k}={v.value if isinstance(v, Enum) else str(v)}"
        for k, v in params.items()
    ]
    param1 = param_list[0] if param_list else ""
    param2 = param_list[1] if len(param_list) > 1 else ""
    return [tool_name, param1, param2]


def convert_plan_to_table_data(plan: ExperimentPlan) -> List[List[str]]:
    rows = []
    for step in plan.experiment:
        tool_sequence = step.tool_sequence
        for i, tool in enumerate(tool_sequence):
            row = _tool_to_table_row(tool)
            if row:
                step_name = step.step_name if i == 0 else ""
                rows.append([step_name] + row)
    return rows


def _parse_row_params(param1: str, param2: str) -> Dict[str, Any]:
    params = {}
    for param in [param1, param2]:
        if not param:
            continue
        try:
            key, value = param.split("=", 1)
            try:
                value = int(value)
            except ValueError:
                pass
            params[key] = value
        except ValueError:
            continue
    return params


def _instantiate_tool(
    tool_name: str, params: Dict[str, Any]
) -> ExperimentTool | None:
    if tool_name in tool_name_map:
        params["tool_name"] = tool_name_map[tool_name]
    tool_class = tool_map.get(tool_name)
    if not tool_class:
        return None
    try:
        return tool_class(**params)
    except Exception:
        logger.warning(
            f"Failed to instantiate {tool_name} with params {params}"
        )
        return None


def _process_table_row(
    row: pd.Series,
    current_step_name: str | None,
    current_tools: List[ExperimentTool],
) -> tuple[str | None, List[ExperimentTool]]:
    if len(row) < 4:
        return current_step_name, current_tools
    step_name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
    tool_name = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
    param1 = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
    param2 = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""
    if step_name:
        return step_name, []
    params = _parse_row_params(param1, param2)
    tool = _instantiate_tool(tool_name, params)
    if tool:
        current_tools.append(tool)
    return current_step_name, current_tools


def convert_table_data_to_experiment_steps(
    table_data: pd.DataFrame,
) -> List[ExperimentStep]:
    steps = []
    current_step_name = None
    current_tools = []
    for _, row in table_data.iterrows():
        current_step_name, current_tools = _process_table_row(
            row, current_step_name, current_tools
        )
        if current_step_name and not current_tools:
            continue
        if current_step_name and current_tools:
            steps.append(
                ExperimentStep(
                    step_name=current_step_name,
                    tool_sequence=current_tools.copy(),
                )
            )
            current_step_name = None
            current_tools = []
    if current_step_name:
        steps.append(
            ExperimentStep(
                step_name=current_step_name, tool_sequence=current_tools
            )
        )
    return steps


def update_experiment_details(
    plans: List[ExperimentPlan], selected_id: str
) -> List[List[str]]:
    if not selected_id:
        return []
    plan = next((p for p in plans if p.id == selected_id), None)
    if not plan:
        logger.warning(f"Plan not found for id: {selected_id}")
        return [["Error", "", ""]]
    return convert_plan_to_table_data(plan)


def build_conversation_history(
    history: ChatHistory,
) -> List[ConversationMessage]:
    conversation = []
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if (
            (role == "user" or role == "assistant")
            and isinstance(role, str)
            and isinstance(content, str)
        ):
            conversation.append(ConversationMessage(role=role, content=content))
    return conversation


def save_experiment_changes(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_id: str,
    table_data: pd.DataFrame,
) -> List[ExperimentPlan]:
    if not plans_path:
        gr.Info("Error: Plans path not configured", title="⚠️ Warning")
        return plans
    try:
        steps = convert_table_data_to_experiment_steps(table_data)
        plan = next((p for p in plans if p.id == selected_id), None)
        if not plan:
            gr.Info("Error: Plan not found", title="⚠️ Warning")
            return plans
        plan.experiment = steps
        save_experiment_plans(plans, plans_path)
        gr.Info(
            "Experiment changes saved successfully", duration=1, title="✅ Info"
        )
        return plans
    except Exception as e:
        error_msg = f"Error saving changes: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg, title="❌ Error")
        return plans


def create_message(
    content: str, message_type: MessageType = MessageType.NORMAL
) -> ChatMessage:
    metadata = None
    if message_type == MessageType.ACTION:
        metadata = {"title": "⚡ Action"}
    elif message_type == MessageType.STATUS:
        metadata = {"title": "📊 Status"}
    elif message_type == MessageType.INTERMEDIATE_STEP:
        metadata = {"title": "🔄 Intermediate step"}
    return ChatMessage(role="assistant", content=content, metadata=metadata)
