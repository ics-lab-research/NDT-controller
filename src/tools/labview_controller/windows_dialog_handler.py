import re
import time
from pathlib import Path
from typing import Any, Dict, Optional
  
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
  
  
def _find_uia_dialog(
    dialog_title_regex: str, timeout_seconds: float
) -> Any:
    """Find the UIA dialog window within timeout."""
    from pywinauto import Desktop  # type: ignore
  
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        desktop = Desktop(backend="uia")
        try:
            dlg_candidate = desktop.window(
                title_re=dialog_title_regex, control_type="Window"
            )
            if dlg_candidate.exists(timeout=0.2):
                return dlg_candidate
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError("Dialog not found via UIA")
  
  
def _navigate_directory_uia(dlg: Any, save_directory: str) -> None:
    """Navigate to the save directory in UIA dialog."""
    from pywinauto.keyboard import send_keys  # type: ignore
  
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
  
  
def _set_filename_uia(dlg: Any, filename: str) -> None:
    """Set the filename in UIA dialog."""
    from pywinauto.keyboard import send_keys  # type: ignore
  
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
  
  
def _click_ok_uia(dlg: Any, ok_button_regex: str) -> None:
    """Click the OK/Save button in UIA dialog."""
    from pywinauto.keyboard import send_keys  # type: ignore
  
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
  
  
def _find_win32_dialog(
    dialog_title_regex: str, timeout_seconds: float
) -> int:
    """Find the win32 dialog window handle within timeout."""
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
    return target_hwnd
  
  
def _navigate_directory_win32(target_hwnd: int, save_directory: str) -> None:
    """Navigate to the save directory in win32 dialog."""
    import win32api
    import win32clipboard
    import win32con
  
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
  
  
def _set_filename_win32(target_hwnd: int, filename: str) -> None:
    """Set the filename in win32 dialog."""
    import win32api
    import win32clipboard
    import win32con
  
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
  
  
def _click_ok_win32(target_hwnd: int, ok_button_regex: str) -> None:
    """Click the OK/Save button in win32 dialog."""
    import win32api
    import win32con
    import win32gui
  
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
  
  
def _handle_replace_prompt(full_path: str) -> Optional[Dict[str, Any]]:
    """Check for and handle replace prompt dialogs, returning success if found."""
    try:
        time.sleep(0.5)
        replace_regex = re.compile(
            r"(?i)(replace|already exists|confirm save|confirm file replace|existing file|do you want to replace)"
        )
  
        # UIA check
        try:
            from pywinauto import Desktop  # type: ignore
            from pywinauto.keyboard import send_keys  # type: ignore
  
            desktop = Desktop(backend="uia")
            for w in desktop.windows():
                try:
                    title = (w.element_info.name or "")
                    if replace_regex.search(title):
                        w.set_focus()
                        time.sleep(0.05)
                        send_keys("{ENTER}")
                        logger.info(f"Save would replace existing file: {full_path}")
                        return _success_response(
                            "Replace prompt detected and handled (UIA)",
                            path=full_path,
                            replace_prompt=True,
                        )
  
                    texts = [
                        (t.window_text() or "")
                        for t in w.descendants(control_type="Text")
                    ]
                    for txt in texts:
                        if replace_regex.search(txt):
                            w.set_focus()
                            time.sleep(0.05)
                            send_keys("{ENTER}")
                            logger.info(f"Save would replace existing file: {full_path}")
                            return _success_response(
                                "Replace prompt detected and handled (UIA)",
                                path=full_path,
                                replace_prompt=True,
                            )
                except Exception:
                    continue
        except ImportError:
            pass
  
        # Win32 check
        import win32api
        import win32con
        import win32gui
  
        def _enum_check(hwnd, _):
            try:
                title = (win32gui.GetWindowText(hwnd) or "")
                if replace_regex.search(title):
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.05)
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                    logger.info(f"Save would replace existing file: {full_path}")
                    raise StopIteration
  
                def _child_cb(ch_hwnd, _):
                    txt = (win32gui.GetWindowText(ch_hwnd) or "")
                    if replace_regex.search(txt):
                        win32gui.SetForegroundWindow(hwnd)
                        time.sleep(0.05)
                        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                        logger.info(f"Save would replace existing file: {full_path}")
                        raise StopIteration
  
                win32gui.EnumChildWindows(hwnd, _child_cb, None)
            except StopIteration:
                raise
            except Exception:
                pass
  
        win32gui.EnumWindows(_enum_check, None)
    except StopIteration:
        return _success_response(
            "Replace prompt detected and handled (win32)",
            path=full_path,
            replace_prompt=True,
        )
    except Exception:
        pass
    return None
  
  
def _handle_via_uia(
    save_directory: str,
    filename: str,
    dialog_title_regex: str,
    ok_button_regex: str,
    timeout_seconds: float,
    settle_delay_seconds: float,
) -> Dict[str, Any]:
    """Handle save dialog using UI Automation (pywinauto)."""
    logger.info("Trying UIA automation for Save File dialog")
    dlg = _find_uia_dialog(dialog_title_regex, timeout_seconds)
    dlg.set_focus()
    time.sleep(settle_delay_seconds)
  
    _navigate_directory_uia(dlg, save_directory)
    _set_filename_uia(dlg, filename)
    _click_ok_uia(dlg, ok_button_regex)
  
    full_path = str(Path(save_directory) / filename)
    replace_result = _handle_replace_prompt(full_path)
    if replace_result:
        return replace_result
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
    import win32con
    import win32gui
  
    target_hwnd = _find_win32_dialog(dialog_title_regex, timeout_seconds)
    win32gui.ShowWindow(target_hwnd, win32con.SW_SHOWNORMAL)
    win32gui.SetForegroundWindow(target_hwnd)
    time.sleep(settle_delay_seconds)
  
    _navigate_directory_win32(target_hwnd, save_directory)
    _set_filename_win32(target_hwnd, filename)
    _click_ok_win32(target_hwnd, ok_button_regex)
  
    full_path = str(Path(save_directory) / filename)
    replace_result = _handle_replace_prompt(full_path)
    if replace_result:
        return replace_result
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
