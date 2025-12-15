import time
from typing import List, Optional

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
    ExperimentsMetadata,
    ExperimentTool,
    Mode,
)
from ..core.project_manager import ProjectManager
from ..tools.labview_controller import (
    tool_connect_to_vi,
    tool_get_numeric_indicator,
    tool_handle_save_dialog,
    tool_press_button,
    tool_run_open_vi,
    tool_select_combo_box,
    tool_select_tab,
    tool_set_button_state,
    tool_set_numeric_control,
    tool_stop_vi,
)

SCAN_COMPLETION_CHECK_INTERVAL = 1
HARDWARE_SETTLE_DELAY = 5
BUTTON_STATE_DELAY = 1


def reinit_system(project_manager: ProjectManager) -> Optional[str]:
    """Reinitialize the system between experiments."""
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        raise ValueError("Not in experiments mode")

    vi_path = str(metadata.vi_path)

    logger.info("Waiting for scan to complete...")
    while True:
        connect_result = tool_connect_to_vi(vi_path=vi_path)
        if not connect_result.success:
            return connect_result.error
        status_result = tool_get_numeric_indicator("Completed")
        if not status_result.success:
            return status_result.error
        if status_result.output and status_result.output.get("value") == "1.0":
            logger.info("Scan completed!")
            break

        time.sleep(SCAN_COMPLETION_CHECK_INTERVAL)

    # --- Return home and quit ---
    result = tool_set_button_state("gohome", True)
    if not result.success:
        return result.error
    time.sleep(HARDWARE_SETTLE_DELAY)

    result = tool_stop_vi(close_labview=True)
    if not result.success:
        return result.error
    return None


def describe_tool(tool: ExperimentTool) -> str:
    """Generate a human-readable description of an experiment tool."""
    if isinstance(tool, SetNumericControlTool):
        return f"Set numeric control '{tool.control_name}' to {tool.value}"
    elif isinstance(tool, SelectTabTool):
        return f"Select tab '{tool.tab_control_name}' at index {tool.index}"
    elif isinstance(tool, RunOpenViTool):
        return f"Run open VI (run_vi={tool.run_vi})"
    elif isinstance(tool, PressButtonTool):
        return f"Press button '{tool.button_name}'"
    elif isinstance(tool, SetButtonStateTool):
        return f"Set button '{tool.button_name}' to {tool.state}"
    elif isinstance(tool, SelectComboBoxTool):
        return f"Select combo box '{tool.combo_box_name}' to '{tool.item}'"
    elif isinstance(tool, ConnectToViTool):
        return f"Connect to VI at path '{tool.vi_path}'"
    elif isinstance(tool, HandleSaveDialogTool):
        return f"Handle save dialog for file '{tool.file_name}' in directory '{tool.save_directory}'"
    else:
        return f"Unknown tool: {type(tool).__name__}"


def is_approved(tools: List[ExperimentTool]) -> bool:
    """Check if the experiment plan is approved for execution. Placeholder for GUI integration."""
    # In a real implementation, this would check a GUI state or flag set by user approval.
    # For now, return False to require manual approval.
    return False


def execute_tool(tool: ExperimentTool, project_manager: ProjectManager) -> ToolResult:
    """Execute a single experiment tool."""
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        raise ValueError("Not in experiments mode")

    logger.info(f"Executing tool: {describe_tool(tool)}")

    if isinstance(tool, SetNumericControlTool):
        return tool_set_numeric_control(tool.control_name, tool.value)
    elif isinstance(tool, SelectTabTool):
        return tool_select_tab(tool.tab_control_name, tool.index)
    elif isinstance(tool, RunOpenViTool):
        return tool_run_open_vi(tool.run_vi)
    elif isinstance(tool, PressButtonTool):
        return tool_press_button(tool.button_name)
    elif isinstance(tool, SetButtonStateTool):
        time.sleep(BUTTON_STATE_DELAY)
        return tool_set_button_state(tool.button_name, tool.state)
    elif isinstance(tool, ConnectToViTool):
        vi_path = metadata.vi_path
        if vi_path and vi_path.exists():
            return tool_connect_to_vi(str(vi_path))
        else:
            logger.warning(f"VI path {vi_path} does not exist or is None")
            return ToolResult(
                name="tool_connect_to_vi",
                success=False,
                output=None,
                error=f"VI path {vi_path} does not exist or is None",
            )
    elif isinstance(tool, HandleSaveDialogTool):
        save_directory = metadata.data_dir_path
        for existing_file in save_directory.glob(f"{tool.file_name}.*"):
            existing_file.unlink()
        return tool_handle_save_dialog(str(save_directory), tool.file_name)
    elif isinstance(tool, SelectComboBoxTool):
        return tool_select_combo_box(tool.combo_box_name, tool.item)
    else:
        logger.error(f"Unknown tool type: {type(tool).__name__}")
        return ToolResult(
            name="unknown_tool",
            success=False,
            output=None,
            error=f"Unsupported tool: {type(tool).__name__}",
        )


def execute_single_plan(
    tools: List[ExperimentTool], project_manager: ProjectManager
) -> Optional[str]:
    """Execute the experiment plan generated by the experiment planner."""
    for tool in tools:
        result = execute_tool(tool, project_manager)
        if not result.success:
            return result.error
    return None


def execute_multiple_plans(
    plans: List[List[ExperimentTool]], project_manager: ProjectManager
) -> Optional[str]:
    """Execute multiple experiment plans with system reinitialization after each plan."""
    for plan in plans:
        error = execute_single_plan(plan, project_manager)
        if error:
            return error
        reinit_error = reinit_system(project_manager)
        if reinit_error:
            return reinit_error
        time.sleep(HARDWARE_SETTLE_DELAY)
    return None
