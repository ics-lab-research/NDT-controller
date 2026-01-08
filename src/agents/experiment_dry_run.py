from datetime import datetime
from pathlib import Path
import time

from loguru import logger

from ..baml_client.types import (
    ConnectToViTool,
    GetNumericIndicatorTool,
    GetViStatusTool,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
    StopViTool,
    ToolResult,
    WaitForOperationCompleteTool,
)
from ..core.models import BasicExpTool, ExperimentMetadata, ExperimentTool

BUTTON_STATE_DELAY = 1
DRY_RUN_DELAY = 2


def execute_tool_dry_run(
    tool: BasicExpTool | ExperimentTool, metadata: ExperimentMetadata
) -> ToolResult:
    """Simulate execution of a single experiment tool by logging inputs and returning a mock success."""
    if isinstance(tool, ConnectToViTool):
        vi_path = metadata.vi_path
        logger.debug(
            f"Dry run: Would call tool_connect_to_vi with vi_path={vi_path}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_connect_to_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, GetViStatusTool):
        logger.debug("Dry run: Would call tool_get_vi_status with no inputs")
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_get_vi_status", success=True, output=None, error=None
        )

    elif isinstance(tool, GetNumericIndicatorTool):
        logger.debug(
            f"Dry run: Would call tool_get_numeric_indicator with indicator_name={tool.indicator_name}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_get_numeric_indicator",
            success=True,
            output=None,
            error=None,
        )

    elif isinstance(tool, HandleSaveDialogTool):
        save_directory = metadata.data_dir_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(tool.file_name).stem
        filename = f"{base_name}_{timestamp}"
        logger.debug(
            f"Dry run: Would call tool_handle_save_dialog with save_directory={save_directory}, filename={filename}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_handle_save_dialog",
            success=True,
            output=None,
            error=None,
        )

    elif isinstance(tool, PressButtonTool):
        logger.debug(
            f"Dry run: Would call tool_press_button with button_name={tool.button_name}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_press_button", success=True, output=None, error=None
        )

    elif isinstance(tool, RunOpenViTool):
        logger.debug(
            f"Dry run: Would call tool_run_open_vi with run_vi={tool.run_vi}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_run_open_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, SelectComboBoxTool):
        logger.debug(
            f"Dry run: Would call tool_select_combo_box with combo_box_name={tool.combo_box_name}, index={tool.index}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_select_combo_box", success=True, output=None, error=None
        )

    elif isinstance(tool, SelectTabTool):
        logger.debug(
            f"Dry run: Would call tool_select_tab with tab_control_name={tool.tab_control_name}, tab={tool.index}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_select_tab", success=True, output=None, error=None
        )

    elif isinstance(tool, SetButtonStateTool):
        logger.debug(
            f"Dry run: Would call tool_set_button_state with button_name={tool.button_name}, state={tool.state} (after BUTTON_STATE_DELAY={BUTTON_STATE_DELAY}s)"
        )
        time.sleep(BUTTON_STATE_DELAY)
        return ToolResult(
            name="tool_set_button_state", success=True, output=None, error=None
        )

    elif isinstance(tool, SetNumericControlTool):
        logger.debug(
            f"Dry run: Would call tool_set_numeric_control with control_name={tool.control_name}, value={tool.value}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_set_numeric_control",
            success=True,
            output=None,
            error=None,
        )

    elif isinstance(tool, StopViTool):
        logger.debug(
            f"Dry run: Would call tool_stop_vi with close_labview={tool.close_labview}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_stop_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, WaitForOperationCompleteTool):
        logger.debug(
            f"Dry run: Would call tool_wait_for_operation_complete with exp_type={tool.exp_type}"
        )
        time.sleep(DRY_RUN_DELAY)
        return ToolResult(
            name="tool_wait_for_operation_complete",
            success=True,
            output=None,
            error=None,
        )
