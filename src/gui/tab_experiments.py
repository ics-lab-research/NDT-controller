from pathlib import Path
from typing import List, Tuple

import gradio as gr
import pandas as pd
from loguru import logger

from ..baml_client.types import (
    ConnectToViTool,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
)
from ..core.models import (
    ExperimentPlan,
    ExperimentsMetadata,
    ExperimentTool,
    Mode,
)
from ..core.project_manager import ProjectManager
from ..core.utils import load_experiment_plans, save_experiment_plans


def convert_plan_to_table_data(plan: ExperimentPlan) -> List[List[str]]:
    """Convert an experiment plan's tools to table data format."""
    data = []
    for tool in plan.experiment:
        if tool == "unknown":
            continue
        tool_name = str(tool.tool_name)
        params = dict(vars(tool))
        params.pop("tool_name", None)
        param_list = [f"{k}={v}" for k, v in params.items()]
        param1 = param_list[0] if len(param_list) > 0 else ""
        param2 = param_list[1] if len(param_list) > 1 else ""
        data.append([tool_name, param1, param2])
    return data


def parse_param(param_str: str) -> Tuple[str, str]:
    """Parse a parameter string like 'key=value' into (key, value)."""
    if not param_str or "=" not in param_str:
        return "", ""
    parts = param_str.split("=", 1)
    return parts[0].strip(), parts[1].strip()


def convert_table_data_to_tools(
    table_data: pd.DataFrame,
) -> List[ExperimentTool]:
    """Convert table data back to experiment tools."""
    logger.debug(f"Converting table_data to tools: {table_data}")
    logger.debug(f"Table data type: {type(table_data)}")
    logger.debug(f"Table data shape: {table_data.shape}")

    tools: List[ExperimentTool] = []

    tool_map = {
        "set_numeric_control": SetNumericControlTool,
        "select_tab": SelectTabTool,
        "run_open_vi": RunOpenViTool,
        "connect_to_vi": ConnectToViTool,
        "handle_save_dialog": HandleSaveDialogTool,
        "press_button": PressButtonTool,
        "set_button_state": SetButtonStateTool,
        "select_combo_box": SelectComboBoxTool,
    }

    for idx, row in table_data.iterrows():
        logger.debug(f"Processing row {idx}: {row.to_dict()}")
        print(f"Row {idx}: {row.to_dict()}")

        tool_name = str(row.iloc[0]).strip() if len(row) > 0 else ""
        param1_str = (
            str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        )
        param2_str = (
            str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
        )

        if not tool_name or tool_name == "nan":
            continue

        params = {}
        if param1_str and param1_str != "nan":
            key, value = parse_param(param1_str)
            if key:
                params[key] = value
        if param2_str and param2_str != "nan":
            key, value = parse_param(param2_str)
            if key:
                params[key] = value

        tool_class = tool_map.get(tool_name)
        if tool_class:
            try:
                tool = tool_class(tool_name=tool_name, **params)
                tools.append(tool)
            except Exception as e:
                logger.error(f"Failed to create tool {tool_name}: {e}")
                tools.append("unknown")
        else:
            logger.warning(f"Unknown tool type: {tool_name}")
            tools.append("unknown")

    return tools


def update_experiment_details(
    plans: List[ExperimentPlan], selected_filename: str
) -> List[List[str]]:
    """Update the details table for a selected experiment."""
    logger.info(
        f"Updating details for selected experiment: {selected_filename}"
    )
    if not selected_filename:
        return []
    plan = next((p for p in plans if p.filename == selected_filename), None)
    if not plan:
        logger.warning(f"Plan not found for filename: {selected_filename}")
        return [["Error", "", ""]]
    data = convert_plan_to_table_data(plan)
    logger.info(f"Details updated with {len(data)} tools")
    return data


def save_experiment_changes(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_filename: str,
    table_data: pd.DataFrame,
) -> str:
    """Save changes from the table back to the experiment plan."""
    logger.info(f"Saving changes for experiment: {selected_filename}")
    logger.debug(f"Received table_data:\n{table_data}")
    logger.debug(f"Table data type: {type(table_data)}")
    logger.debug(f"Table data shape: {table_data.shape}")

    if not selected_filename:
        return "Error: No experiment selected"
    if not plans_path:
        return "Error: Plans path not configured"

    plan = next((p for p in plans if p.filename == selected_filename), None)
    if not plan:
        return f"Error: Plan not found for {selected_filename}"

    try:
        new_tools = convert_table_data_to_tools(table_data)
        logger.debug(f"Converted tools: {new_tools}")
        print(new_tools)
        plan.experiment = new_tools
        save_experiment_plans(plans, plans_path)
        logger.info(f"Successfully saved changes to {selected_filename}")
        return f"Successfully saved changes to {selected_filename}"
    except Exception as e:
        error_msg = f"Error saving changes: {str(e)}"
        logger.error(error_msg)
        return error_msg


def create_experiments_tab(project_manager: ProjectManager) -> gr.Tab:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans: List[ExperimentPlan] = []
    plans_path = None
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path)

    filenames = [plan.filename for plan in plans] if plans else []

    initial_data = convert_plan_to_table_data(plans[0]) if plans else []

    with gr.Tab("Plans Viewer") as tab:
        dropdown = gr.Dropdown(
            choices=filenames,
            label="Select Experiment",
            value=filenames[0] if filenames else None,
        )
        details_df = gr.Dataframe(
            headers=["Tool Name", "Parameter 1", "Parameter 2"],
            value=initial_data,
            interactive=True,
        )
        save_button = gr.Button("Save Changes")
        save_status = gr.Textbox(label="Status", interactive=False)

        dropdown.change(
            lambda filename: update_experiment_details(plans, filename),
            inputs=dropdown,
            outputs=details_df,
        )
        save_button.click(
            lambda filename, data: save_experiment_changes(
                plans, plans_path, filename, data
            ),
            inputs=[dropdown, details_df],
            outputs=save_status,
        )
    return tab
