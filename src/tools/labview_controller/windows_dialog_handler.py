import re
import time
from pathlib import Path
from typing import Any, Dict

from loguru import logger


def _handle_error(operation: str, error: Exception) -> Dict[str, Any]:
    """Standardized error handling for this module."""
    error_msg = f"Failed to {operation}: {error}"
    logger.error(error_msg)
    return {"success": False, "error": error_msg}


def _success_response(message: str, **kwargs) -> Dict[str, Any]:
    """Standardized success response for this module."""
    response = {"success": True, "message": message}
    response.update(kwargs)
    return response


def _ensure_tdms_extension(filename: str) -> str:
    """Ensure filename has .tdms extension."""
    if not filename.lower().endswith(".tdms"):
        return f"{filename}.tdms"
    return filename


def _handle_via_uia(
    save_directory: str,
    filename: str,
    dialog_title_regex: str,
    ok_button_regex: str,
    timeout_seconds: float,
    settle_delay_seconds: float,
) -> Dict[str, Any]:
    """Handle save dialog using UI Automation (pywinauto)."""
    from pywinauto import Desktop  # type: ignore
    from pywinauto.keyboard import send_keys  # type: ignore

    logger.info("Trying UIA automation for Save File dialog")
    deadline = time.time() + timeout_seconds
    dlg = None
    while time.time() < deadline:
        desktop = Desktop(backend="uia")
        try:
            dlg_candidate = desktop.window(
                title_re=dialog_title_regex, control_type="Window"
            )
            if dlg_candidate.exists(timeout=0.2):
                dlg = dlg_candidate
                break
        except Exception:
            pass
        time.sleep(0.2)

    if dlg is None:
        raise RuntimeError("Dialog not found via UIA")

    dlg.set_focus()
    time.sleep(settle_delay_seconds)

    # Navigate to directory
    try:
        send_keys("^l")  # Ctrl+L to focus address bar
        time.sleep(0.3)
        send_keys("^a")  # Select all
        time.sleep(0.1)
        send_keys("{DELETE}")  # Delete content
        time.sleep(0.1)
        send_keys(save_directory)
        send_keys("{ENTER}")
        time.sleep(0.8)
    except Exception as nav_error:
        logger.warning(f"Directory navigation failed: {nav_error}")

    # Set filename
    filename_edit = None
    edits = dlg.descendants(control_type="Edit")
    if len(edits) >= 2:
        for edit in reversed(edits):
            try:
                rect = edit.rectangle()
                dlg_rect = dlg.rectangle()
                if rect.top > (dlg_rect.top + dlg_rect.height() * 0.6):
                    filename_edit = edit
                    break
            except Exception:
                continue
    if filename_edit is None and edits:
        filename_edit = edits[-1]

    if filename_edit:
        try:
            filename_edit.click_input()
            time.sleep(0.3)
            send_keys("^a")
            time.sleep(0.1)
            send_keys("{DELETE}")
            time.sleep(0.1)
            filename_edit.type_keys(
                filename, with_spaces=True, set_foreground=True
            )
        except Exception as e:
            logger.warning(f"Failed to set filename in edit control: {e}")
            send_keys("%n^a{DELETE}" + filename)
    else:
        send_keys("%n^a{DELETE}" + filename)

    # Click OK/Save
    btn = None
    for b in dlg.descendants(control_type="Button"):
        name = (b.window_text() or "").strip()
        if re.match(ok_button_regex, name):
            btn = b
            break
    if btn is None:
        send_keys("{ENTER}")
    else:
        btn.click()

    full_path = str(Path(save_directory) / filename)
    return _success_response("Save dialog handled (UIA)", path=full_path)


def _handle_via_win32(
    save_directory: str,
    filename: str,
    dialog_title_regex: str,
    ok_button_regex: str,
    timeout_seconds: float,
    settle_delay_seconds: float,
) -> Dict[str, Any]:
    """Handle save dialog using win32 APIs."""
    import win32api
    import win32clipboard
    import win32con
    import win32gui

    deadline = time.time() + timeout_seconds
    target_hwnd = None

    def _enum_handler(hwnd, _):
        nonlocal target_hwnd
        if target_hwnd is not None:
            return
        title = win32gui.GetWindowText(hwnd) or ""
        if re.search(dialog_title_regex, title):
            target_hwnd = hwnd

    while time.time() < deadline and target_hwnd is None:
        win32gui.EnumWindows(_enum_handler, None)
        if target_hwnd is None:
            time.sleep(0.2)

    if target_hwnd is None:
        raise RuntimeError("Dialog not found")

    win32gui.ShowWindow(target_hwnd, win32con.SW_SHOWNORMAL)
    win32gui.SetForegroundWindow(target_hwnd)
    time.sleep(settle_delay_seconds)

    # Navigate to directory
    try:
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord("L"), 0, 0, 0)
        win32api.keybd_event(ord("L"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(
            win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0
        )
        time.sleep(0.3)

        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(save_directory)  # type: ignore
        finally:
            win32clipboard.CloseClipboard()

        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(
            win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0
        )
        time.sleep(0.2)
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.8)
    except Exception as nav_error:
        logger.warning(f"Directory navigation failed: {nav_error}")

    # Set filename
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(filename)  # type: ignore
    finally:
        win32clipboard.CloseClipboard()

    try:
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32api.keybd_event(ord("N"), 0, 0, 0)
        win32api.keybd_event(ord("N"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.3)

        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, 0, 0)
        win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(
            win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0
        )
        logger.info("Used Alt+N method to set filename")
    except Exception as alt_error:
        logger.warning(f"Alt+N method failed: {alt_error}")

    time.sleep(0.2)

    # Confirm dialog
    ok_btn = None
    child = 0
    while True:
        child = win32gui.FindWindowEx(target_hwnd, child, "Button", None)
        if not child:
            break
        text = (win32gui.GetWindowText(child) or "").strip()
        if re.match(ok_button_regex, text):
            ok_btn = child
            break

    if ok_btn:
        win32gui.SendMessage(ok_btn, win32con.BM_CLICK, 1, 0)
    else:
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)

    full_path = str(Path(save_directory) / filename)
    return _success_response("Save dialog handled (win32)", path=full_path)


def handle_save_file_dialog(
    save_directory: str,
    filename: str,
    dialog_title_regex: str = r"(?i)(choose|save).*file.*",
    ok_button_regex: str = r"(?i)^(ok|save)$",
    timeout_seconds: float = 15.0,
    settle_delay_seconds: float = 0.3,
) -> Dict[str, Any]:
    """Handle a Windows "Save File" dialog by navigating to directory and entering filename.

    Args:
        save_directory: The directory path where to save the file
        filename: Just the filename (without extension, .tdms will be added automatically)
        dialog_title_regex: Regex to match dialog title
        ok_button_regex: Regex to match OK/Save button
        timeout_seconds: How long to wait for dialog
        settle_delay_seconds: Delay between actions

    The method first tries UI Automation via pywinauto for robustness. If unavailable,
    it falls back to a lightweight win32 approach using window handles and keystrokes.
    """
    try:
        filename = _ensure_tdms_extension(filename)
        full_path = str(Path(save_directory) / filename)

        # Try UIA first
        try:
            return _handle_via_uia(
                save_directory,
                filename,
                dialog_title_regex,
                ok_button_regex,
                timeout_seconds,
                settle_delay_seconds,
            )
        except ImportError:
            logger.info("pywinauto not installed; falling back to win32")
        except Exception as uia_error:
            logger.warning(
                f"UIA path failed: {uia_error}; falling back to win32"
            )

        # Fallback to win32
        return _handle_via_win32(
            save_directory,
            filename,
            dialog_title_regex,
            ok_button_regex,
            timeout_seconds,
            settle_delay_seconds,
        )
    except Exception as e:
        return _handle_error("handle save dialog", e)
