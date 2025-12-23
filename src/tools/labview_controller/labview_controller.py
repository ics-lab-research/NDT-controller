import subprocess
import sys
import time
from os import environ
from pathlib import Path
from typing import Any, Dict, Union

try:
    import win32com.client  # type: ignore
except ImportError:
    win32com = None

from loguru import logger

from .windows_dialog_handler import handle_save_file_dialog


class LabVIEWController:
    """A controller class to manage LabVIEW VI interactions for controls and indicators."""

    def __init__(self):
        self.labview_app = None
        self.vi_reference = None
        self.vi_path: Path | None = None

    def handle_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Standardized error handling."""
        error_msg = f"Failed to {operation}: {error}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    def success_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """Standardized success response."""
        response = {"success": True, "message": message}
        response.update(kwargs)
        return response

    def run_open_vi_subprocess(self, run_vi: bool = True) -> Dict[str, Any]:
        """Run open_vi.py in a subprocess to open and run the VI"""
        try:
            # If not running the VI and no path is set, just return success
            if not run_vi and self.vi_path is None:
                return self.success_response(
                    "No VI path set and run_vi=False, skipping subprocess",
                    process_id=None,
                    run_vi=False,
                    vi_path=None,
                )

            current_dir = Path(__file__).parent
            open_vi_path = current_dir / "open_vi.py"
            if not open_vi_path.exists():
                return self.handle_error(
                    "find open_vi.py",
                    FileNotFoundError(
                        f"open_vi.py not found at {open_vi_path}"
                    ),
                )

            if self.vi_path is None:
                return self.handle_error(
                    "run open_vi.py subprocess",
                    ValueError(
                        "VI path must be set in controller (use connect_to_existing_vi or set vi_path manually)"
                    ),
                )

            env = environ.copy()
            env["PYTHONIOENCODING"] = "ascii:replace"
            env["PYTHONLEGACYWINDOWSSTDIO"] = "1"

            cmd = [sys.executable, str(open_vi_path), str(self.vi_path)]
            if not run_vi:
                cmd.append("--no-run")
            logger.debug(f"Running command: {' '.join(cmd)}")
            popen_kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "encoding": "ascii",
                "errors": "replace",
                "env": env,
            }
            if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
                popen_kwargs["creationflags"] = (
                    subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
                )
            process = subprocess.Popen(cmd, **popen_kwargs)
            return self.success_response(
                f"Started open_vi.py in subprocess with PID: {process.pid} (run_vi={run_vi})",
                process_id=process.pid,
                run_vi=run_vi,
                vi_path=self.vi_path,
            )
        except Exception as e:
            return self.handle_error("run open_vi.py subprocess", e)

    def _validate_existing_connection(self, vi_path: Path | None) -> bool:
        """Validate and update existing VI connection if valid."""
        if not self.labview_app or not self.vi_reference:
            return False
        try:
            test_state = self.vi_reference.ExecState
            logger.debug(
                f"Existing connection is valid, VI state: {test_state}"
            )
            if vi_path and vi_path != self.vi_path:
                logger.debug(
                    f"Updating VI path from {self.vi_path} to {vi_path}"
                )
                self.vi_reference = self.labview_app.GetVIReference(
                    str(vi_path)
                )
                self.vi_path = vi_path
            if not self.vi_reference.FPWinOpen:
                self.vi_reference.FPWinOpen = True
                logger.debug("Reopened front panel for existing connection")
            return True
        except Exception as validation_error:
            logger.warning(f"Existing connection is invalid: {validation_error}")
            self.labview_app = None
            self.vi_reference = None
            self.vi_path = None
            return False

    def _create_new_connection(self, vi_path: Path | None) -> bool:
        """Create a new LabVIEW connection."""
        logger.debug("Creating new LabVIEW connection...")
        if win32com is None:
            logger.warning(
                "win32com is not available (likely on non-Windows platform)"
            )
            return False
        try:
            self.labview_app = win32com.client.Dispatch("LabVIEW.Application")
        except Exception as e:
            logger.error(f"Failed to dispatch LabVIEW application: {e}")
            self.labview_app = None
            return False
        if vi_path:
            logger.debug(f"Connecting to VI: {vi_path}")
            try:
                self.vi_reference = self.labview_app.GetVIReference(
                    str(vi_path)
                )
                self.vi_path = vi_path
            except Exception as vi_error:
                logger.error(
                    f"Failed to get VI reference for {vi_path}: {vi_error}"
                )
                self.vi_reference = None
                self.vi_path = None
                return False
            try:
                self.vi_reference.FPWinOpen = True
                time.sleep(0.5)
                self.vi_reference.FPWinOpen = True
                logger.debug(f"Front panel opened for VI: {vi_path}")
            except Exception as fp_error:
                logger.error(f"Could not open front panel: {fp_error}")
            try:
                exec_state = self.vi_reference.ExecState
                logger.debug(
                    f"VI connection successful, execution state: {exec_state}"
                )
            except Exception as state_error:
                logger.error(
                    f"VI connection failed - cannot get execution state: {state_error}"
                )
                return False
        else:
            logger.error("No VI path provided - connected to LabVIEW app only")
        logger.debug("Successfully connected to LabVIEW application")
        return True

    def connect_to_existing_vi(self, vi_path: Path | None = None) -> bool:
        """Connect to an already opened LabVIEW VI."""
        if win32com is None:
            logger.warning(
                "win32com is not available (likely on non-Windows platform)"
            )
            return False
        try:
            if self._validate_existing_connection(vi_path):
                return True
            return self._create_new_connection(vi_path)
        except Exception as e:
            logger.error(f"Failed to connect to LabVIEW: {e}")
            self.labview_app = None
            self.vi_reference = None
            self.vi_path = None
            return False

    def get_control_value(self, control_name: str) -> Any:
        """Get the value of a control on the front panel."""
        try:
            if not self.vi_reference:
                return None
            value = self.vi_reference.GetControlValue(control_name)
            logger.debug(f"Got control value - {control_name}: {value}")
            return value
        except Exception as e:
            logger.error(f"Failed to get control value '{control_name}': {e}")
            return None

    def set_control_value(self, control_name: str, value: Any) -> bool:
        """Set the value of a control on the front panel."""
        try:
            if not self.vi_reference:
                return False
            self.vi_reference.SetControlValue(control_name, value)
            logger.debug(f"Set control value - {control_name}: {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set control value '{control_name}': {e}")
            return False

    def press_button(
        self, button_name: str, press_duration: float = 0.1
    ) -> bool:
        """Press a button on the front panel."""
        try:
            if not self.vi_reference:
                return False
            self.vi_reference.SetControlValue(button_name, True)
            time.sleep(press_duration)
            self.vi_reference.SetControlValue(button_name, False)
            logger.debug(f"Pressed button: {button_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to press button '{button_name}': {e}")
            return False

    def set_button_state(self, button_name: str, state: bool) -> bool:
        """Set the state of a button on the front panel."""
        try:
            if not self.vi_reference:
                return False
            self.vi_reference.SetControlValue(button_name, state)
            state_text = "pressed/on" if state else "released/off"
            logger.debug(f"Set button '{button_name}' to {state_text}")
            return True
        except Exception as e:
            logger.error(f"Failed to set button state '{button_name}': {e}")
            return False

    def select_combo_box(self, combo_box_name: str, index: int) -> bool:
        """Select an item in a combo box control by index (int) or string value."""
        try:
            if not self.vi_reference:
                return False
            self.vi_reference.SetControlValue(combo_box_name, index)
            logger.debug(
                f"Selected combo box '{combo_box_name}' to index: {index}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to select combo box '{combo_box_name}': {e}")
            return False

    def _get_additional_info(self) -> Dict[str, Any]:
        """Retrieve additional VI information."""
        info = {}
        if not self.vi_reference:
            info["front_panel_open"] = "Unknown"
            info["vi_name"] = "Unknown"
            info["is_running"] = None
            return info
        try:
            info["front_panel_open"] = self.vi_reference.FPWinOpen
        except Exception:
            info["front_panel_open"] = "Unknown"
        try:
            info["vi_name"] = self.vi_reference.Name
        except Exception:
            info["vi_name"] = "Unknown"
        try:
            info["is_running"] = self.vi_reference.IsRunning
        except Exception:
            info["is_running"] = None
        return info

    def get_vi_status(self) -> Dict[str, Any]:
        """Get detailed status information about the current VI connection and state."""
        try:
            if not self.labview_app:
                return {
                    "connected": False,
                    "error": "No LabVIEW application connection",
                }
            if not self.vi_reference:
                return {
                    "connected": False,
                    "labview_app_connected": True,
                    "error": "No VI reference",
                }
            try:
                exec_state = self.vi_reference.ExecState
            except Exception as ref_error:
                return {
                    "connected": False,
                    "labview_app_connected": True,
                    "vi_reference_valid": False,
                    "error": f"VI reference is invalid: {ref_error}",
                }
            status_map = {0: "Idle", 1: "Running", 2: "Stopped", 3: "Bad VI"}
            additional_info = self._get_additional_info()
            return {
                "connected": True,
                "labview_app_connected": True,
                "vi_reference_valid": True,
                # "running": additional_info.get("is_running", exec_state == 1),
                "running": exec_state == 1,
                "exec_state": exec_state,
                "status_text": status_map.get(
                    exec_state, f"Unknown({exec_state})"
                ),
                "vi_path": str(self.vi_path) if self.vi_path else None,
                **additional_info,
            }
        except Exception as e:
            logger.error(f"Failed to get VI status: {e}")
            return {"connected": False, "error": str(e)}

    def set_tab_index(self, control_name: str, tab_index: int) -> bool:
        """Select a page in a LabVIEW Tab control by zero-based index."""
        try:
            if not self.vi_reference:
                return False
            if tab_index is None:
                return False
            numeric_index = int(tab_index)
            if numeric_index < 0:
                raise ValueError("tab_index must be >= 0")
            self.vi_reference.SetControlValue(control_name, numeric_index)
            logger.debug(f"Set tab '{control_name}' to index {numeric_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to set tab index for '{control_name}': {e}")
            return False

    def _try_abort(self, methods_tried: list[str]) -> bool:
        """Attempt to abort the VI."""
        try:
            if not self.vi_reference:
                logger.warning("VI reference is None, cannot abort")
                return False
            self.vi_reference.Abort()
            methods_tried.append("Abort()")
            time.sleep(0.2)
            if self.vi_reference.ExecState != 1:
                logger.debug(
                    f"VI stopped successfully with Abort() - new state: {self.vi_reference.ExecState}"
                )
                return True
        except Exception as e:
            logger.warning(f"Abort() method failed: {e}")
        return False

    def _try_stop(self, methods_tried: list[str]) -> bool:
        """Attempt to stop the VI using Stop method."""
        try:
            if not self.vi_reference:
                logger.warning("VI reference is None, cannot stop")
                return False
            if hasattr(self.vi_reference, "Stop"):
                self.vi_reference.Stop()
                methods_tried.append("Stop()")
                time.sleep(0.2)
                if self.vi_reference.ExecState != 1:
                    logger.debug(
                        f"VI stopped successfully with Stop() - new state: {self.vi_reference.ExecState}"
                    )
                    return True
        except Exception as e:
            logger.warning(f"Stop() method failed: {e}")
        return False

    def _try_multiple_aborts(self, methods_tried: list[str]) -> bool:
        """Attempt multiple abort calls if needed."""
        if not self.vi_reference:
            logger.error("VI reference is None, cannot perform multiple aborts")
            return False
        for attempt in range(3):
            try:
                self.vi_reference.Abort()
                methods_tried.append(f"Abort() attempt {attempt + 1}")
                time.sleep(0.3)
                logger.debug(
                    f"After abort attempt {attempt + 1}: state = {self.vi_reference.ExecState}"
                )
                if self.vi_reference.ExecState != 1:
                    logger.debug(
                        f"VI stopped after {attempt + 1} abort attempts"
                    )
                    return True
            except Exception as e:
                logger.error(f"Abort attempt {attempt + 1} failed: {e}")
        return False

    def _close_labview(self) -> bool:
        """Close the LabVIEW application."""
        try:
            logger.debug("Attempting to close LabVIEW application...")
            try:
                if self.vi_reference:
                    self.vi_reference.FPWinOpen = False
                    time.sleep(0.2)
            except Exception as e:
                logger.warning(f"Could not close VI front panel: {e}")
            try:
                if self.labview_app:
                    self.labview_app.Quit()
                    time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Could not quit LabVIEW application: {e}")
            self.vi_reference, self.labview_app, self.vi_path = None, None, None
            logger.debug("LabVIEW application closed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to close LabVIEW application: {e}")
            return False

    def stop_vi(self, close_labview: bool = False) -> bool:
        """Stop the currently running VI, optionally close LabVIEW."""
        try:
            if not self.vi_reference:
                return False
            initial_state = self.vi_reference.ExecState
            logger.debug(
                f"Initial VI state: {initial_state} (0=Idle, 1=Running, 2=Stopped)"
            )
            methods_tried = []
            vi_stopped = self._try_abort(methods_tried)
            if not vi_stopped:
                vi_stopped = self._try_stop(methods_tried)
            if not vi_stopped:
                vi_stopped = self._try_multiple_aborts(methods_tried)
            final_state = self.vi_reference.ExecState
            logger.debug(f"Final VI state after all attempts: {final_state}")
            logger.debug(f"Methods tried: {methods_tried}")
            if initial_state == 1 and final_state != 1:
                logger.debug(
                    "VI state changed from running - considering it stopped"
                )
                vi_stopped = True
            elif initial_state != 1:
                logger.debug("VI was not running initially - no action needed")
                vi_stopped = True
            else:
                logger.error(
                    "VI appears to still be running after all stop attempts"
                )
            if close_labview and self.labview_app:
                return self._close_labview()
            return vi_stopped
        except Exception as e:
            logger.error(f"Failed to stop VI: {e}")
            return False

    def handle_save_file_dialog(self, *args, **kwargs) -> Dict[str, Any]:
        """
        A wrapper that calls the dedicated save file dialog handler.
        This keeps the implementation separate while maintaining the method on the controller.
        """
        try:
            # Delegate the call to the imported function
            return handle_save_file_dialog(*args, **kwargs)
        except Exception as e:
            return self.handle_error("handle save dialog", e)
