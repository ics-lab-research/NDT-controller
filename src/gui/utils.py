from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr
import pandas as pd
from loguru import logger


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
    ExperimentStep,
    ExperimentTool,
    ChatMessage,
    MessageType,
)


def _tool_to_table_row(tool: ExperimentTool) -> List[str]:
    """Converts an experiment tool into a list of strings for table display."""
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
    """Converts an experiment plan into a list of table data rows."""
    rows = []
    for step in plan.experiment:
        tool_sequence = step.tool_sequence
        for i, tool in enumerate(tool_sequence):
            row = _tool_to_table_row(tool)
            if row:
                step_name = step.step_name if i == 0 else ""
                rows.append([step_name] + row)
    return rows


def _parse_param(param_str: str) -> Tuple[str, str]:
    """Parses a parameter string into key and value."""
    if not param_str or "=" not in param_str:
        return "", ""
    key, value = param_str.split("=", 1)
    return key.strip(), value.strip()


def _extract_params_from_row(row: pd.Series) -> Dict[str, str]:
    """Extracts parameters from a pandas Series row."""
    params = {}
    for i in range(2, len(row)):
        param_str = str(row.iloc[i]) if pd.notna(row.iloc[i]) else ""
        if param_str and param_str != "nan":
            key, value = _parse_param(param_str)
            if key:
                params[key] = value
    return params


def _create_tool_from_row(
    row: pd.Series, tool_map: Dict[str, Any]
) -> ExperimentTool | None:
    """Creates an experiment tool from a pandas Series row using a tool map."""
    tool_name = str(row.iloc[1]).strip() if len(row) > 1 else ""
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
) -> List[ExperimentStep]:
    """Converts table data into a list of experiment steps."""
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
    # Fill in empty step names with the last non-empty step name
    filled_data = table_data.copy()
    last_step_name = ""
    for idx in filled_data.index:
        step_name = str(filled_data.at[idx, 0]).strip()
        if step_name:
            last_step_name = step_name
        else:
            filled_data.at[idx, 0] = last_step_name
    steps = []
    for step_name, group in filled_data.groupby(0):
        tools = [
            _create_tool_from_row(row, tool_map) for _, row in group.iterrows()
        ]
        tools = [tool for tool in tools if tool is not None]
        if tools:
            steps.append(
                ExperimentStep(step_name=str(step_name), tool_sequence=tools)
            )
    return steps


def update_experiment_details(
    plans: List[ExperimentPlan], selected_id: str
) -> List[List[str]]:
    """Updates and returns table data for the selected experiment plan."""
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
    """Builds a list of conversation messages from chat history."""
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


def create_message(
    content: str, message_type: MessageType = MessageType.NORMAL
) -> ChatMessage:
    """Creates a chat message with optional type-based metadata."""
    metadata = None
    if message_type == MessageType.ACTION:
        metadata = {"title": "⚡ Action"}
    elif message_type == MessageType.STATUS:
        metadata = {"title": "📊 Status"}
    elif message_type == MessageType.INTERMEDIATE_STEP:
        metadata = {"title": "🔄 Intermediate step"}
    # For NORMAL, no metadata
    return ChatMessage(role="assistant", content=content, metadata=metadata)
