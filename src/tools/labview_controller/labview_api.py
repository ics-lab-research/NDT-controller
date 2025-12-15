from typing import Any, Dict, Optional, Union

from ...baml_client.types import ToolResult
from .labview_controller import LabVIEWController

# --- Global controller instance ---
# This is the single instance that manages the connection
controller = LabVIEWController()


# --- LLM Function Calling Interface ---


def tool_run_open_vi(run_vi: bool = True) -> Dict[str, Any]:
    """
    Run open_vi.py in a subprocess to open and run the VI file.
    """
    return controller.run_open_vi_subprocess(run_vi=run_vi)


def tool_connect_to_vi(vi_path: str | None = None) -> Dict[str, Any]:
    """
    Connect to an existing LabVIEW VI that is already open.
    """
    if controller.connect_to_existing_vi(vi_path):
        return controller.success_response(
            "Connected to LabVIEW VI successfully", ready_for_control=True
        )
    else:
        return controller.handle_error(
            "connect to VI", RuntimeError("Connection failed")
        )


def tool_press_button(button_name: str) -> Dict[str, Any]:
    """Press a button on the LabVIEW front panel."""
    if not controller.vi_reference:
        return controller.handle_error(
            "press button",
            RuntimeError("No VI connection. Use connect_to_vi() first"),
        )
    if controller.press_button(button_name):
        return controller.success_response(
            f"Button '{button_name}' pressed successfully"
        )
    else:
        return controller.handle_error(
            "press button", RuntimeError(f"Button '{button_name}' press failed")
        )


def tool_set_button_state(button_name: str, state: bool) -> Dict[str, Any]:
    """Set the state of a button (True=pressed/on, False=released/off)."""
    if not controller.vi_reference:
        return controller.handle_error(
            "set button state",
            RuntimeError("No VI connection. Use connect_to_vi() first"),
        )
    if controller.set_button_state(button_name, state):
        state_text = "pressed/on" if state else "released/off"
        return controller.success_response(
            f"Button '{button_name}' set to {state_text}"
        )
    else:
        return controller.handle_error(
            "set button state",
            RuntimeError(f"Failed to set button '{button_name}' state"),
        )


def tool_set_numeric_control(control_name: str, value: float) -> Dict[str, Any]:
    """Set a numeric control value on the front panel."""
    if not controller.vi_reference:
        return controller.handle_error(
            "set control",
            RuntimeError("No VI connection. Use connect_to_vi() first"),
        )
    if controller.set_control_value(control_name, float(value)):
        return controller.success_response(
            f"Control '{control_name}' set to {value}", value_set=float(value)
        )
    else:
        return controller.handle_error(
            "set control", RuntimeError(f"Failed to set '{control_name}'")
        )


def tool_get_numeric_indicator(indicator_name: str) -> Dict[str, Any]:
    """Get a numeric indicator value from the front panel."""
    if not controller.vi_reference:
        return controller.handle_error(
            "get indicator",
            RuntimeError("No VI connection. Use connect_to_vi() first"),
        )
    value = controller.get_control_value(indicator_name)
    if value is not None:
        return controller.success_response(
            f"Retrieved indicator '{indicator_name}'", value=float(value)
        )
    else:
        return controller.handle_error(
            "get indicator", RuntimeError(f"Failed to get '{indicator_name}'")
        )


def tool_get_vi_status() -> Dict[str, Any]:
    """Get the current status of the connected VI."""
    return controller.get_vi_status()


def tool_select_combo_box(
    combo_box_name: str, item: Union[str, int]
) -> Dict[str, Any]:
    """Select an item in a combo box control by index or string value."""
    if not controller.vi_reference:
        return controller.handle_error(
            "select combo box",
            RuntimeError("No VI connection. Use connect_to_vi() first"),
        )
    if controller.select_combo_box(combo_box_name, item):
        return controller.success_response(
            f"Combo box '{combo_box_name}' selected to {item}", selection=item
        )
    else:
        return controller.handle_error(
            "select combo box",
            RuntimeError(f"Failed to select '{combo_box_name}'"),
        )


def tool_select_tab(
    tab_control_name: str,
    tab: Any,
    name_to_index: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Select a page in a LabVIEW Tab control by index or name."""
    # ... (keep existing implementation)
    if not controller.vi_reference:
        return controller.handle_error(
            "select tab",
            RuntimeError("No VI connection. Use connect_to_vi() first"),
        )
    resolved_index: Optional[int] = None
    if isinstance(tab, int):
        resolved_index = tab
    elif isinstance(tab, str):
        if name_to_index and tab in name_to_index:
            resolved_index = name_to_index[tab]
        else:
            return controller.handle_error(
                "select tab", ValueError("Page name not found in mapping")
            )
    else:
        return controller.handle_error(
            "select tab", TypeError("'tab' must be int or str")
        )
    if controller.set_tab_index(tab_control_name, int(resolved_index)):
        return controller.success_response(
            f"Tab '{tab_control_name}' set to index {int(resolved_index)}"
        )
    else:
        return controller.handle_error(
            "select tab", RuntimeError("Failed to set tab index")
        )


def tool_stop_vi(close_labview: bool = True) -> Dict[str, Any]:
    """Stop the VI, and optionally close LabVIEW."""
    if not controller.vi_reference:
        return controller.handle_error(
            "stop VI",
            RuntimeError("No VI connection. Use connect_to_vi() first"),
        )
    if controller.stop_vi(close_labview=close_labview):
        msg = (
            "VI stopped and LabVIEW application closed"
            if close_labview
            else "VI stopped successfully"
        )
        return controller.success_response(msg)
    else:
        return controller.handle_error(
            "stop VI", RuntimeError("Failed to stop VI")
        )


def tool_handle_save_dialog(
    save_directory: str, filename: str, **kwargs
) -> Dict[str, Any]:
    """Handle the Windows Save File dialog."""
    return controller.handle_save_file_dialog(
        save_directory=save_directory, filename=filename, **kwargs
    )
