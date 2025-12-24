from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr
import pandas as pd
from loguru import logger


class MessageType(Enum):
    NORMAL = "normal"
    ACTION = "action"
    STATUS = "status"
    INTERMEDIATE_STEP = "intermediate_step"

from ..agents.experiment_planning import (
    save_experiment_plans,
)
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
    ExperimentPlan,
    ExperimentTool,
    ChatMessage,
)


def _tool_to_table_row(tool: ExperimentTool) -> List[str]:
    tool_name = str(tool.tool_name)
    params = {k: v for k, v in vars(tool).items() if k != "tool_name"}
    param_list = [
        f"{k}={v.value if isinstance(v, Enum) else str(v)}"
        for k, v in params.items()
    ]
    param1 = param_list[0] if param_list else ""
    param2 = param_list[1] if len(param_list) > 1 else ""
    return [tool_name, param1, param2]


def convert_plan_to_table_data(plan: ExperimentPlan) -> List[List[str]]:
    return [
        row
        for tool in plan.experiment
        for row in [_tool_to_table_row(tool)]
        if row
    ]


def _parse_param(param_str: str) -> Tuple[str, str]:
    if not param_str or "=" not in param_str:
        return "", ""
    key, value = param_str.split("=", 1)
    return key.strip(), value.strip()


def _extract_params_from_row(row: pd.Series) -> Dict[str, str]:
    params = {}
    for i in range(1, len(row)):
        param_str = str(row.iloc[i]) if pd.notna(row.iloc[i]) else ""
        if param_str and param_str != "nan":
            key, value = _parse_param(param_str)
            if key:
                params[key] = value
    return params


def _create_tool_from_row(
    row: pd.Series, tool_map: Dict[str, Any]
) -> ExperimentTool | None:
    tool_name = str(row.iloc[0]).strip() if len(row) > 0 else ""
    if not tool_name or tool_name == "nan":
        return None
    params = _extract_params_from_row(row)
    tool_class = tool_map.get(tool_name)
    if tool_class:
        try:
            return tool_class(tool_name=tool_name, **params)
        except Exception as e:
            logger.error(f"Failed to create tool {tool_name}: {e}")
            return None
    logger.warning(f"Unknown tool type: {tool_name}")
    return None


def _convert_table_data_to_tools(
    table_data: pd.DataFrame,
) -> List[ExperimentTool]:
    tool_map = {
        "connect_to_vi": ConnectToViTool,
        "handle_save_dialog": HandleSaveDialogTool,
        "press_button": PressButtonTool,
        "run_open_vi": RunOpenViTool,
        "select_combo_box": SelectComboBoxTool,
        "select_tab": SelectTabTool,
        "set_button_state": SetButtonStateTool,
        "set_numeric_control": SetNumericControlTool,
        "stop_vi": StopViTool,
        "wait_for_operation_complete": WaitForOperationCompleteTool,
    }
    tools = [
        _create_tool_from_row(row, tool_map) for _, row in table_data.iterrows()
    ]
    return [tool for tool in tools if tool is not None]


def update_experiment_details(
    plans: List[ExperimentPlan], selected_filename: str
) -> List[List[str]]:
    if not selected_filename:
        return []
    plan = next((p for p in plans if p.filename == selected_filename), None)
    if not plan:
        logger.warning(f"Plan not found for filename: {selected_filename}")
        return [["Error", "", ""]]
    return convert_plan_to_table_data(plan)


def save_experiment_changes(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_filename: str,
    table_data: pd.DataFrame,
):
    if not selected_filename:
        gr.Info("Error: No experiment selected")
        return
    if not plans_path:
        gr.Info("Error: Plans path not configured")
        return
    plan = next((p for p in plans if p.filename == selected_filename), None)
    if not plan:
        gr.Info(f"Error: Plan not found for {selected_filename}")
        return
    try:
        plan.experiment = _convert_table_data_to_tools(table_data)
        save_experiment_plans(plans, plans_path)
        gr.Info(f"Successfully saved changes to {selected_filename}")
    except Exception as e:
        error_msg = f"Error saving changes: {str(e)}"
        logger.error(error_msg)
        gr.Info(error_msg)


def build_conversation_history(
    history: ChatHistory,
) -> List[ConversationMessage]:
    """Convert chat history to baml conversation messages models"""
    conversation = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content")
        if (
            (role == "user" or role == "assistant")
            and isinstance(role, str)
            and isinstance(content, str)
        ):
            conversation.append(ConversationMessage(role=role, content=content))
    return conversation


def create_message(content: str, message_type: MessageType = MessageType.NORMAL) -> ChatMessage:
    """Create a message dictionary with optional type-based metadata."""
    msg = {
        "role": "assistant",
        "content": content,
    }
    if message_type == MessageType.ACTION:
        msg["metadata"] = {"title": "⚡ Action"}
    elif message_type == MessageType.STATUS:
        msg["metadata"] = {"title": "📊 Status"}
    elif message_type == MessageType.INTERMEDIATE_STEP:
        msg["metadata"] = {"title": "🔄 Intermediate step"}
    # For NORMAL, no metadata
    return msg
