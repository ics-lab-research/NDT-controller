from datetime import datetime
from pathlib import Path
import time

from loguru import logger
from tqdm import tqdm

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
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Connecting to VI"):
            time.sleep(1)
        return ToolResult(
            name="tool_connect_to_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, GetViStatusTool):
        logger.debug("Dry run: Would call tool_get_vi_status with no inputs")
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Getting VI status"):
            time.sleep(1)
        return ToolResult(
            name="tool_get_vi_status", success=True, output=None, error=None
        )

    elif isinstance(tool, GetNumericIndicatorTool):
        logger.debug(
            f"Dry run: Would call tool_get_numeric_indicator with indicator_name={tool.indicator_name}"
        )
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Getting numeric indicator"):
            time.sleep(1)
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
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Handling save dialog"):
            time.sleep(1)
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
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Pressing button"):
            time.sleep(1)
        return ToolResult(
            name="tool_press_button", success=True, output=None, error=None
        )

    elif isinstance(tool, RunOpenViTool):
        logger.debug(
            f"Dry run: Would call tool_run_open_vi with run_vi={tool.run_vi}"
        )
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Running/opening VI"):
            time.sleep(1)
        return ToolResult(
            name="tool_run_open_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, SelectComboBoxTool):
        logger.debug(
            f"Dry run: Would call tool_select_combo_box with combo_box_name={tool.combo_box_name}, index={tool.index}"
        )
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Selecting combo box"):
            time.sleep(1)
        return ToolResult(
            name="tool_select_combo_box", success=True, output=None, error=None
        )

    elif isinstance(tool, SelectTabTool):
        logger.debug(
            f"Dry run: Would call tool_select_tab with tab_control_name={tool.tab_control_name}, tab={tool.index}"
        )
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Selecting tab"):
            time.sleep(1)
        return ToolResult(
            name="tool_select_tab", success=True, output=None, error=None
        )

    elif isinstance(tool, SetButtonStateTool):
        logger.debug(
            f"Dry run: Would call tool_set_button_state with button_name={tool.button_name}, state={tool.state} (after BUTTON_STATE_DELAY={BUTTON_STATE_DELAY}s)"
        )
        for _ in tqdm(range(BUTTON_STATE_DELAY), desc="Setting button state"):
            time.sleep(1)
        return ToolResult(
            name="tool_set_button_state", success=True, output=None, error=None
        )

    elif isinstance(tool, SetNumericControlTool):
        logger.debug(
            f"Dry run: Would call tool_set_numeric_control with control_name={tool.control_name}, value={tool.value}"
        )
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Setting numeric control"):
            time.sleep(1)
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
        for _ in tqdm(range(DRY_RUN_DELAY), desc="Stopping VI"):
            time.sleep(1)
        return ToolResult(
            name="tool_stop_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, WaitForOperationCompleteTool):
        logger.debug(
            f"Dry run: Would call tool_wait_for_operation_complete with exp_type={tool.exp_type}"
        )
        for _ in tqdm(
            range(DRY_RUN_DELAY), desc="Waiting for operation complete"
        ):
            time.sleep(1)
        return ToolResult(
            name="tool_wait_for_operation_complete",
            success=True,
            output=None,
            error=None,
        )
