from pathlib import Path
from typing import List, Tuple, Dict, Any
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


def tool_to_table_row(tool: ExperimentTool) -> List[str]:
    if tool == "unknown":
        return []
    tool_name = str(tool.tool_name)
    params = {k: v for k, v in vars(tool).items() if k != "tool_name"}
    param_list = [f"{k}={v}" for k, v in params.items()]
    param1 = param_list[0] if param_list else ""
    param2 = param_list[1] if len(param_list) > 1 else ""
    return [tool_name, param1, param2]


def convert_plan_to_table_data(plan: ExperimentPlan) -> List[List[str]]:
    return [
        row
        for tool in plan.experiment
        for row in [tool_to_table_row(tool)]
        if row
    ]


def parse_param(param_str: str) -> Tuple[str, str]:
    if not param_str or "=" not in param_str:
        return "", ""
    key, value = param_str.split("=", 1)
    return key.strip(), value.strip()


def extract_params_from_row(row: pd.Series) -> Dict[str, str]:
    params = {}
    for i in range(1, len(row)):
        param_str = str(row.iloc[i]) if pd.notna(row.iloc[i]) else ""
        if param_str and param_str != "nan":
            key, value = parse_param(param_str)
            if key:
                params[key] = value
    return params


def create_tool_from_row(
    row: pd.Series, tool_map: Dict[str, Any]
) -> ExperimentTool:
    tool_name = str(row.iloc[0]).strip() if len(row) > 0 else ""
    if not tool_name or tool_name == "nan":
        return "unknown"
    params = extract_params_from_row(row)
    tool_class = tool_map.get(tool_name)
    if tool_class:
        try:
            return tool_class(tool_name=tool_name, **params)
        except Exception as e:
            logger.error(f"Failed to create tool {tool_name}: {e}")
            return "unknown"
    logger.warning(f"Unknown tool type: {tool_name}")
    return "unknown"


def convert_table_data_to_tools(
    table_data: pd.DataFrame,
) -> List[ExperimentTool]:
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
    return [
        create_tool_from_row(row, tool_map) for _, row in table_data.iterrows()
    ]


def find_plan_by_filename(
    plans: List[ExperimentPlan], filename: str
) -> ExperimentPlan | None:
    return next((p for p in plans if p.filename == filename), None)


def update_experiment_details(
    plans: List[ExperimentPlan], selected_filename: str
) -> List[List[str]]:
    if not selected_filename:
        return []
    plan = find_plan_by_filename(plans, selected_filename)
    if not plan:
        logger.warning(f"Plan not found for filename: {selected_filename}")
        return [["Error", "", ""]]
    return convert_plan_to_table_data(plan)


def save_experiment_changes(
    plans: List[ExperimentPlan],
    plans_path: Path | None,
    selected_filename: str,
    table_data: pd.DataFrame,
) -> str:
    if not selected_filename:
        return "Error: No experiment selected"
    if not plans_path:
        return "Error: Plans path not configured"
    plan = find_plan_by_filename(plans, selected_filename)
    if not plan:
        return f"Error: Plan not found for {selected_filename}"
    try:
        plan.experiment = convert_table_data_to_tools(table_data)
        save_experiment_plans(plans, plans_path)
        return f"Successfully saved changes to {selected_filename}"
    except Exception as e:
        error_msg = f"Error saving changes: {str(e)}"
        logger.error(error_msg)
        return error_msg


def create_experiments_tab(project_manager: ProjectManager) -> gr.Tab:
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    plans = []
    plans_path = None
    if isinstance(metadata, ExperimentsMetadata):
        plans_path = metadata.plans_path
        if isinstance(plans_path, Path):
            plans = load_experiment_plans(plans_path)
    filenames = [plan.filename for plan in plans]
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
