import time
from datetime import datetime
from pathlib import Path
from typing import Generator, List

from loguru import logger

from ..agents.experiment_dry_run import execute_tool_dry_run
from ..agents.experiment_planning import (
    load_experiment_plans,
    save_experiment_plans,
)
from ..baml_client.types import (
    ConnectToViTool,
    ExpType,
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
from ..core.models import (
    BasicExpTool,
    ExperimentExecutionError,
    ExperimentMetadata,
    ExperimentPlan,
    ExperimentStatus,
    ExperimentTool,
)
from ..core.project_manager import ProjectManager
from ..tools.labview_controller import (
    tool_connect_to_vi,
    tool_get_numeric_indicator,
    tool_get_vi_status,
    tool_handle_save_dialog,
    tool_press_button,
    tool_run_open_vi,
    tool_select_combo_box,
    tool_select_tab,
    tool_set_button_state,
    tool_set_numeric_control,
    tool_stop_vi,
)
from ..utils.heatmap_plotter import generate_heatmaps

# BUTTON_STATE_DELAY = 1
# SCAN_COMPLETION_CHECK_INTERVAL = 1
HARDWARE_SETTLE_DELAY = 5


def wait_for_scan_complete(project_manager: ProjectManager) -> ToolResult:
    """Wait for a scan operation to complete by polling the 'Completed' indicator."""
    metadata = project_manager.get_mode_metadata
    if not isinstance(metadata, ExperimentMetadata):
        return ToolResult(
            name="wait_for_operation_complete",
            success=False,
            output=None,
            error="Not in experiment mode",
        )

    vi_path = metadata.vi_path
    logger.info("Waiting for scan to complete...")
    while True:
        connect_result = tool_connect_to_vi(vi_path, log=False)
        if not connect_result.success:
            return ToolResult(
                name="wait_for_operation_complete",
                success=False,
                output=None,
                error=connect_result.error,
            )
        status_result = tool_get_numeric_indicator("Completed", log=False)
        if not status_result.success:
            return ToolResult(
                name="wait_for_operation_complete",
                success=False,
                output=None,
                error=status_result.error,
            )
        if (
            status_result.output
            and isinstance(status_result.output, dict)
            and status_result.output.get("value") == "1.0"
        ):
            logger.info("Scan completed!")
            break
        # time.sleep(SCAN_COMPLETION_CHECK_INTERVAL)

    return ToolResult(
        name="wait_for_operation_complete",
        success=True,
        output=None,
        error=None,
    )


def wait_for_movement_complete() -> ToolResult:
    """Wait for a movement operation to complete by calculating and sleeping for movement time."""
    x_result = tool_get_numeric_indicator("X Distance")
    if not x_result.success:
        return ToolResult(
            name="wait_for_operation_complete",
            success=False,
            output=None,
            error=x_result.error,
        )
    if not x_result.output or not isinstance(x_result.output, dict):
        return ToolResult(
            name="wait_for_operation_complete",
            success=False,
            output=None,
            error="Invalid output format for X Distance",
        )
    y_result = tool_get_numeric_indicator("Y Distance")
    if not y_result.success:
        return ToolResult(
            name="wait_for_operation_complete",
            success=False,
            output=None,
            error=y_result.error,
        )
    if not y_result.output or not isinstance(y_result.output, dict):
        return ToolResult(
            name="wait_for_operation_complete",
            success=False,
            output=None,
            error="Invalid output format for Y Distance",
        )
    speed_result = tool_get_numeric_indicator("Speed (mm/s)")
    if not speed_result.success:
        return ToolResult(
            name="wait_for_operation_complete",
            success=False,
            output=None,
            error=speed_result.error,
        )
    if not speed_result.output or not isinstance(speed_result.output, dict):
        return ToolResult(
            name="wait_for_operation_complete",
            success=False,
            output=None,
            error="Invalid output format for Speed (mm/s)",
        )
    x = float(x_result.output["value"])
    y = float(y_result.output["value"])
    speed = float(speed_result.output["value"])

    distance = max(abs(x), abs(y))
    movement_time = distance / speed
    logger.info(f"Calculated movement time: {movement_time} seconds")
    time.sleep(movement_time + HARDWARE_SETTLE_DELAY)
    return ToolResult(
        name="wait_for_operation_complete",
        success=True,
        output=None,
        error=None,
    )


def tool_wait_for_operation_complete(
    exp_type: ExpType, project_manager: ProjectManager
) -> ToolResult:
    """Wait for the specified experiment operation to complete."""
    if exp_type == ExpType.SCAN:
        return wait_for_scan_complete(project_manager)
    elif exp_type == ExpType.MOVEMENT:
        return wait_for_movement_complete()


def execute_tool(
    tool: BasicExpTool | ExperimentTool, project_manager: ProjectManager
) -> ToolResult:
    """Execute a single experiment tool."""
    metadata = project_manager.get_mode_metadata
    if not isinstance(metadata, ExperimentMetadata):
        raise ValueError("Not in experiment mode")

    if project_manager.experiment_dry_run:
        return execute_tool_dry_run(tool, metadata)

    if isinstance(tool, ConnectToViTool):
        vi_path = metadata.vi_path
        if vi_path and vi_path.exists():
            return tool_connect_to_vi(vi_path)
        else:
            logger.error(f"VI path {vi_path} does not exist or is None")
            return ToolResult(
                name="tool_connect_to_vi",
                success=False,
                output=None,
                error=f"VI path {vi_path} does not exist or is None",
            )

    elif isinstance(tool, GetViStatusTool):
        return tool_get_vi_status()

    elif isinstance(tool, GetNumericIndicatorTool):
        return tool_get_numeric_indicator(indicator_name=tool.indicator_name)

    elif isinstance(tool, HandleSaveDialogTool):
        save_directory = metadata.data_dir_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(tool.file_name).stem
        filename = f"{base_name}_{timestamp}"
        return tool_handle_save_dialog(save_directory, filename=filename)

    elif isinstance(tool, PressButtonTool):
        return tool_press_button(button_name=tool.button_name)

    elif isinstance(tool, RunOpenViTool):
        return tool_run_open_vi(run_vi=tool.run_vi)

    elif isinstance(tool, SelectComboBoxTool):
        return tool_select_combo_box(
            combo_box_name=tool.combo_box_name, index=tool.index
        )

    elif isinstance(tool, SelectTabTool):
        return tool_select_tab(
            tab_control_name=tool.tab_control_name, tab=tool.index
        )

    elif isinstance(tool, SetButtonStateTool):
        # time.sleep(BUTTON_STATE_DELAY)
        return tool_set_button_state(
            button_name=tool.button_name, state=tool.state
        )

    elif isinstance(tool, SetNumericControlTool):
        return tool_set_numeric_control(
            control_name=tool.control_name, value=tool.value
        )

    elif isinstance(tool, StopViTool):
        return tool_stop_vi(close_labview=tool.close_labview)

    elif isinstance(tool, WaitForOperationCompleteTool):
        return tool_wait_for_operation_complete(
            exp_type=tool.exp_type, project_manager=project_manager
        )


def execute_single_plan(plan: ExperimentPlan, project_manager: ProjectManager):
    """Execute the experiment plan generated by the experiment planner."""
    saved_tdms_file = None
    metadata = project_manager.get_mode_metadata

    for step in plan.experiment:
        for tool in step.tool_sequence:
            result = execute_tool(tool, project_manager)

            # NOTE: just tricky using output, we should find out other solution
            if (
                isinstance(tool, HandleSaveDialogTool)
                and result.success
                and isinstance(result.output, str)
            ):
                saved_tdms_file = result.output
            if not result.success:
                plan.status = ExperimentStatus.ERROR
                raise ExperimentExecutionError(
                    filename=plan.filename,
                    error_message=result.error or "Unknown error",
                )

    # Generate heatmaps for check data quality
    if (
        saved_tdms_file
        and isinstance(saved_tdms_file, str)
        and isinstance(metadata, ExperimentMetadata)
    ):
        generate_heatmaps(
            metadata.data_dir_path / saved_tdms_file,
            plan.id,
            metadata.plots_dir_path,
        )


# BUG: can be bug, check carefully
# TODO: we should check error during scan
def execute_multiple_plans(
    plans: List[ExperimentPlan], project_manager: ProjectManager
) -> Generator[str, None, ExperimentExecutionError | None]:
    """Execute multiple experiment plans with system reinitialization after each plan."""
    metadata = project_manager.get_mode_metadata
    runnable_statuses = [
        ExperimentStatus.APPROVED,
        ExperimentStatus.SCANNING,
        ExperimentStatus.PENDING,
        ExperimentStatus.ERROR,
    ]
    while any(p.status in runnable_statuses for p in plans):
        # Find the next plan to execute
        plan = next((p for p in plans if p.status in runnable_statuses), None)
        if not plan:
            break
        yield f"Executing plan: `{plan.filename}`"
        plan.status = ExperimentStatus.SCANNING
        # Save progress before execution
        if isinstance(metadata, ExperimentMetadata):
            save_experiment_plans(plans, metadata.plans_path)
        try:
            execute_single_plan(plan, project_manager)
            yield f"Plan `{plan.filename}` completed"
            plan.status = ExperimentStatus.COMPLETED
        except ExperimentExecutionError as e:
            error_message = f"Plan {plan.filename} errored: {e.error_message}"
            yield error_message
            plan.status = ExperimentStatus.ERROR
            # Save error state
            if isinstance(metadata, ExperimentMetadata):
                save_experiment_plans(plans, metadata.plans_path)
            return e
        # Save completion state
        if isinstance(metadata, ExperimentMetadata):
            save_experiment_plans(plans, metadata.plans_path)
            # Reload plans to check for status updates (e.g., rescan requests)
            plans = load_experiment_plans(metadata.plans_path, log=False)

    # Final save of all plans
    if isinstance(metadata, ExperimentMetadata):
        save_experiment_plans(plans, metadata.plans_path)
