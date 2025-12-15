from typing import Any, Dict, Optional, Union

from ...baml_client.types import ToolResult
from .labview_controller import LabVIEWController

# --- Global controller instance ---
# This is the single instance that manages the connection
controller = LabVIEWController()


# --- LLM Function Calling Interface ---


def tool_run_open_vi(run_vi: bool = True) -> ToolResult:
    """
    Run open_vi.py in a subprocess to open and run the VI file.
    """
    result = controller.run_open_vi_subprocess(run_vi=run_vi)
    return ToolResult(
        name="tool_run_open_vi",
        success=result["success"],
        output={
            k: str(v)
            for k, v in result.items()
            if k not in ["success", "error"]
        },
        error=result.get("error"),
    )


def tool_connect_to_vi(vi_path: str | None = None) -> ToolResult:
    """
    Connect to an existing LabVIEW VI that is already open.
    """
    if controller.connect_to_existing_vi(vi_path):
        return ToolResult(
            name="tool_connect_to_vi",
            success=True,
            output={
                "message": "Connected to LabVIEW VI successfully",
                "ready_for_control": "True",
            },
            error=None,
        )
    else:
        return ToolResult(
            name="tool_connect_to_vi",
            success=False,
            output=None,
            error="Connection failed",
        )


def tool_press_button(button_name: str) -> ToolResult:
    """Press a button on the LabVIEW front panel."""
    if not controller.vi_reference:
        return ToolResult(
            name="tool_press_button",
            success=False,
            output=None,
            error="No VI connection. Use connect_to_vi() first",
        )
    if controller.press_button(button_name):
        return ToolResult(
            name="tool_press_button",
            success=True,
            output={"message": f"Button '{button_name}' pressed successfully"},
            error=None,
        )
    else:
        return ToolResult(
            name="tool_press_button",
            success=False,
            output=None,
            error=f"Button '{button_name}' press failed",
        )


def tool_set_button_state(button_name: str, state: bool) -> ToolResult:
    """Set the state of a button (True=pressed/on, False=released/off)."""
    if not controller.vi_reference:
        return ToolResult(
            name="tool_set_button_state",
            success=False,
            output=None,
            error="No VI connection. Use connect_to_vi() first",
        )
    if controller.set_button_state(button_name, state):
        state_text = "pressed/on" if state else "released/off"
        return ToolResult(
            name="tool_set_button_state",
            success=True,
            output={"message": f"Button '{button_name}' set to {state_text}"},
            error=None,
        )
    else:
        return ToolResult(
            name="tool_set_button_state",
            success=False,
            output=None,
            error=f"Failed to set button '{button_name}' state",
        )


def tool_set_numeric_control(control_name: str, value: float) -> ToolResult:
    """Set a numeric control value on the front panel."""
    if not controller.vi_reference:
        return ToolResult(
            name="tool_set_numeric_control",
            success=False,
            output=None,
            error="No VI connection. Use connect_to_vi() first",
        )
    if controller.set_control_value(control_name, float(value)):
        return ToolResult(
            name="tool_set_numeric_control",
            success=True,
            output={
                "message": f"Control '{control_name}' set to {value}",
                "value_set": str(float(value)),
            },
            error=None,
        )
    else:
        return ToolResult(
            name="tool_set_numeric_control",
            success=False,
            output=None,
            error=f"Failed to set '{control_name}'",
        )


def tool_get_numeric_indicator(indicator_name: str) -> ToolResult:
    """Get a numeric indicator value from the front panel."""
    if not controller.vi_reference:
        return ToolResult(
            name="tool_get_numeric_indicator",
            success=False,
            output=None,
            error="No VI connection. Use connect_to_vi() first",
        )
    value = controller.get_control_value(indicator_name)
    if value is not None:
        return ToolResult(
            name="tool_get_numeric_indicator",
            success=True,
            output={
                "message": f"Retrieved indicator '{indicator_name}'",
                "value": str(float(value)),
            },
            error=None,
        )
    else:
        return ToolResult(
            name="tool_get_numeric_indicator",
            success=False,
            output=None,
            error=f"Failed to get '{indicator_name}'",
        )


def tool_get_vi_status() -> ToolResult:
    """Get the current status of the connected VI."""
    result = controller.get_vi_status()
    return ToolResult(
        name="tool_get_vi_status",
        success=result.get("connected", False),
        output={
            k: str(v)
            for k, v in result.items()
            if k not in ["connected", "error"]
        },
        error=result.get("error"),
    )


def tool_select_combo_box(
    combo_box_name: str, item: Union[str, int]
) -> ToolResult:
    """Select an item in a combo box control by index or string value."""
    if not controller.vi_reference:
        return ToolResult(
            name="tool_select_combo_box",
            success=False,
            output=None,
            error="No VI connection. Use connect_to_vi() first",
        )
    if controller.select_combo_box(combo_box_name, item):
        return ToolResult(
            name="tool_select_combo_box",
            success=True,
            output={
                "message": f"Combo box '{combo_box_name}' selected to {item}",
                "selection": str(item),
            },
            error=None,
        )
    else:
        return ToolResult(
            name="tool_select_combo_box",
            success=False,
            output=None,
            error=f"Failed to select '{combo_box_name}'",
        )


def tool_select_tab(
    tab_control_name: str,
    tab: Any,
    name_to_index: Optional[Dict[str, int]] = None,
) -> ToolResult:
    """Select a page in a LabVIEW Tab control by index or name."""
    # ... (keep existing implementation)
    if not controller.vi_reference:
        return ToolResult(
            name="tool_select_tab",
            success=False,
            output=None,
            error="No VI connection. Use connect_to_vi() first",
        )
    resolved_index: Optional[int] = None
    if isinstance(tab, int):
        resolved_index = tab
    elif isinstance(tab, str):
        if name_to_index and tab in name_to_index:
            resolved_index = name_to_index[tab]
        else:
            return ToolResult(
                name="tool_select_tab",
                success=False,
                output=None,
                error="Page name not found in mapping",
            )
    else:
        return ToolResult(
            name="tool_select_tab",
            success=False,
            output=None,
            error="'tab' must be int or str",
        )
    if controller.set_tab_index(tab_control_name, int(resolved_index)):
        return ToolResult(
            name="tool_select_tab",
            success=True,
            output={
                "message": f"Tab '{tab_control_name}' set to index {int(resolved_index)}"
            },
            error=None,
        )
    else:
        return ToolResult(
            name="tool_select_tab",
            success=False,
            output=None,
            error="Failed to set tab index",
        )


def tool_stop_vi(close_labview: bool = True) -> ToolResult:
    """Stop the VI, and optionally close LabVIEW."""
    if not controller.vi_reference:
        return ToolResult(
            name="tool_stop_vi",
            success=False,
            output=None,
            error="No VI connection. Use connect_to_vi() first",
        )
    if controller.stop_vi(close_labview=close_labview):
        msg = (
            "VI stopped and LabVIEW application closed"
            if close_labview
            else "VI stopped successfully"
        )
        return ToolResult(
            name="tool_stop_vi",
            success=True,
            output={"message": msg},
            error=None,
        )
    else:
        return ToolResult(
            name="tool_stop_vi",
            success=False,
            output=None,
            error="Failed to stop VI",
        )


def tool_handle_save_dialog(
    save_directory: str, filename: str, **kwargs
) -> ToolResult:
    """Handle the Windows Save File dialog."""
    result = controller.handle_save_file_dialog(
        save_directory=save_directory, filename=filename, **kwargs
    )
    return ToolResult(
        name="tool_handle_save_dialog",
        success=result["success"],
        output={
            k: str(v)
            for k, v in result.items()
            if k not in ["success", "error"]
        },
        error=result.get("error"),
    )
