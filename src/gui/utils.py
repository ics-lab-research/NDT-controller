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


def convert_table_data_to_experiment_steps(
    table_data: pd.DataFrame,
) -> List[ExperimentStep]:
    """Converts table data back into a list of experiment steps."""
    steps: List[ExperimentStep] = []
    current_step_name: str | None = None
    current_tools: List[ExperimentTool] = []
    for _, row in table_data.iterrows():
        if len(row) < 4:
            continue  # Skip invalid rows
        step_name: str = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        tool_name: str = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
        param1: str = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
        param2: str = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""

        if step_name:
            if current_step_name:
                steps.append(
                    ExperimentStep(
                        step_name=current_step_name, tool_sequence=current_tools
                    )
                )
            current_step_name = step_name
            current_tools = []
        # Parse parameters
        params: Dict[str, Any] = {}
        for param in [param1, param2]:
            if param:
                try:
                    key: str
                    value: Any
                    key, value = param.split("=", 1)
                    # Attempt to convert to int if possible, otherwise keep as str
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    params[key] = value
                except ValueError:
                    continue  # Skip malformed params
        # Add tool_name if available
        if tool_name in tool_name_map:
            params["tool_name"] = tool_name_map[tool_name]
        # Instantiate tool
        tool_class: Any | None = tool_map.get(tool_name)
        if tool_class:
            try:
                tool: ExperimentTool = tool_class(**params)
                current_tools.append(tool)
            except Exception:
                logger.warning(
                    f"Failed to instantiate {tool_name} with params {params}"
                )
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


def save_experiment_changes(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_id: str,
    table_data: pd.DataFrame,
) -> List[ExperimentPlan]:
    """Saves changes to the selected experiment plan from table data."""
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
