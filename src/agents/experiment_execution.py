import time
from datetime import datetime
from typing import Generator, List

from loguru import logger

from ..agents.experiment_planning import save_experiment_plans
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
    ExperimentExecutionError,
    ExperimentPlan,
    ExperimentsMetadata,
    ExperimentStatus,
    ExperimentTool,
    BasicExpTool,
    Mode,
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

BUTTON_STATE_DELAY = 1
SCAN_COMPLETION_CHECK_INTERVAL = 1
HARDWARE_SETTLE_DELAY = 5


def tool_wait_for_operation_complete(
    exp_type: ExpType, project_manager: ProjectManager
) -> ToolResult:
    if exp_type == ExpType.SCAN:
        metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
        if not isinstance(metadata, ExperimentsMetadata):
            return ToolResult(
                name="wait_for_operation_complete",
                success=False,
                output=None,
                error="Not in experiments mode",
            )

        vi_path = metadata.vi_path
        logger.info("Waiting for scan to complete...")
        while True:
            connect_result = tool_connect_to_vi(vi_path)
            if not connect_result.success:
                return ToolResult(
                    name="wait_for_operation_complete",
                    success=False,
                    output=None,
                    error=connect_result.error,
                )
            status_result = tool_get_numeric_indicator("Completed")
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

            time.sleep(SCAN_COMPLETION_CHECK_INTERVAL)

        return ToolResult(
            name="wait_for_operation_complete",
            success=True,
            output=None,
            error=None,
        )

    elif exp_type == ExpType.MOVEMENT:
        time.sleep(HARDWARE_SETTLE_DELAY)
        return ToolResult(
            name="wait_for_operation_complete",
            success=True,
            output=None,
            error=None,
        )


def execute_tool(
    tool: BasicExpTool | ExperimentTool, project_manager: ProjectManager
) -> ToolResult:
    """Execute a single experiment tool."""
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        raise ValueError("Not in experiments mode")

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
        filename = f"{tool.file_name}_{timestamp}"
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
        time.sleep(BUTTON_STATE_DELAY)
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


def execute_tool_dry_run(
    tool: BasicExpTool | ExperimentTool, project_manager: ProjectManager
) -> ToolResult:
    """Simulate execution of a single experiment tool by logging inputs and returning a mock success."""
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    if not isinstance(metadata, ExperimentsMetadata):
        raise ValueError("Not in experiments mode")

    if isinstance(tool, ConnectToViTool):
        vi_path = metadata.vi_path
        logger.info(
            f"Dry run: Would call tool_connect_to_vi with vi_path={vi_path}"
        )
        return ToolResult(
            name="tool_connect_to_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, GetViStatusTool):
        logger.info("Dry run: Would call tool_get_vi_status with no inputs")
        return ToolResult(
            name="tool_get_vi_status", success=True, output=None, error=None
        )

    elif isinstance(tool, GetNumericIndicatorTool):
        logger.info(
            f"Dry run: Would call tool_get_numeric_indicator with indicator_name={tool.indicator_name}"
        )
        return ToolResult(
            name="tool_get_numeric_indicator",
            success=True,
            output=None,
            error=None,
        )

    elif isinstance(tool, HandleSaveDialogTool):
        save_directory = metadata.data_dir_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{tool.file_name}_{timestamp}"
        logger.info(
            f"Dry run: Would call tool_handle_save_dialog with save_directory={save_directory}, filename={filename}"
        )
        return ToolResult(
            name="tool_handle_save_dialog",
            success=True,
            output=None,
            error=None,
        )

    elif isinstance(tool, PressButtonTool):
        logger.info(
            f"Dry run: Would call tool_press_button with button_name={tool.button_name}"
        )
        return ToolResult(
            name="tool_press_button", success=True, output=None, error=None
        )

    elif isinstance(tool, RunOpenViTool):
        logger.info(
            f"Dry run: Would call tool_run_open_vi with run_vi={tool.run_vi}"
        )
        return ToolResult(
            name="tool_run_open_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, SelectComboBoxTool):
        logger.info(
            f"Dry run: Would call tool_select_combo_box with combo_box_name={tool.combo_box_name}, index={tool.index}"
        )
        return ToolResult(
            name="tool_select_combo_box", success=True, output=None, error=None
        )

    elif isinstance(tool, SelectTabTool):
        logger.info(
            f"Dry run: Would call tool_select_tab with tab_control_name={tool.tab_control_name}, tab={tool.index}"
        )
        return ToolResult(
            name="tool_select_tab", success=True, output=None, error=None
        )

    elif isinstance(tool, SetButtonStateTool):
        logger.info(
            f"Dry run: Would call tool_set_button_state with button_name={tool.button_name}, state={tool.state} (after BUTTON_STATE_DELAY={BUTTON_STATE_DELAY}s)"
        )
        return ToolResult(
            name="tool_set_button_state", success=True, output=None, error=None
        )

    elif isinstance(tool, SetNumericControlTool):
        logger.info(
            f"Dry run: Would call tool_set_numeric_control with control_name={tool.control_name}, value={tool.value}"
        )
        return ToolResult(
            name="tool_set_numeric_control",
            success=True,
            output=None,
            error=None,
        )

    elif isinstance(tool, StopViTool):
        logger.info(
            f"Dry run: Would call tool_stop_vi with close_labview={tool.close_labview}"
        )
        return ToolResult(
            name="tool_stop_vi", success=True, output=None, error=None
        )

    elif isinstance(tool, WaitForOperationCompleteTool):
        logger.info(
            f"Dry run: Would call tool_wait_for_operation_complete with exp_type={tool.exp_type}"
        )
        return ToolResult(
            name="tool_wait_for_operation_complete",
            success=True,
            output=None,
            error=None,
        )


def execute_single_plan(
    plan: ExperimentPlan, project_manager: ProjectManager, dry_run: bool = False
):
    """Execute the experiment plan generated by the experiment planner."""
    for step in plan.experiment:
        for tool in step.tool_sequence:
            result = (
                execute_tool_dry_run(tool, project_manager)
                if dry_run
                else execute_tool(tool, project_manager)
            )
            if not result.success:
                plan.status = ExperimentStatus.ERROR
                raise ExperimentExecutionError(
                    filename=plan.filename,
                    error_message=result.error or "Unknown error",
                )


def execute_multiple_plans(
    plans: List[ExperimentPlan],
    project_manager: ProjectManager,
    dry_run: bool = False,
) -> Generator[str, None, ExperimentExecutionError | None]:
    """Execute multiple experiment plans with system reinitialization after each plan."""
    metadata = project_manager.get_mode_metadata(Mode.EXPERIMENTS)
    for plan in plans:
        # Only execute plans that are pending or previously errored
        if plan.status in (ExperimentStatus.ERROR, ExperimentStatus.PENDING):
            yield f"Executing plan: `{plan.filename}`"
            plan.status = ExperimentStatus.SCANNING
            # Save progress before execution
            if isinstance(metadata, ExperimentsMetadata):
                save_experiment_plans(plans, metadata.plans_path)
            try:
                execute_single_plan(plan, project_manager, dry_run)
            except ExperimentExecutionError as e:
                error_message = (
                    f"Plan {plan.filename} errored: {e.error_message}"
                )
                yield error_message
                # Save error state
                if isinstance(metadata, ExperimentsMetadata):
                    save_experiment_plans(plans, metadata.plans_path)
                return e
            yield f"Plan `{plan.filename}` completed"
            plan.status = ExperimentStatus.COMPLETED
            # Save completion state
            if isinstance(metadata, ExperimentsMetadata):
                save_experiment_plans(plans, metadata.plans_path)
            # Allow hardware to settle before next plan
            time.sleep(HARDWARE_SETTLE_DELAY)
    # Final save of all plans
    if isinstance(metadata, ExperimentsMetadata):
        save_experiment_plans(plans, metadata.plans_path)
