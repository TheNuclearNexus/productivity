import psutil
from typing import Any, Dict, Optional, List, Callable

from .base import BasePlatform

class WindowsPlatform(BasePlatform):
    def check_accessibility(self) -> bool:
        return True # Windows doesn't universally throttle listener permissions like MacOS

    def get_keyboard_intercept(self) -> Optional[Callable]:
        # Utilizing win32_event_filter natively inside pynput is complex, return None to allow the listener to safely default
        return None

    def get_active_window_info(self) -> Dict[str, Any]:
        title, app_name, pid, browser_tab = None, None, None, None
        try:
            import ctypes
            import pygetwindow as gw
            
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd:
                pid_c = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_c))
                pid = pid_c.value
                app_name = psutil.Process(pid).name()
                
            active_win = gw.getActiveWindow()
            if active_win is not None:
                if isinstance(active_win, str):
                    title = active_win
                elif hasattr(active_win, "title"):
                    title = active_win.title
        except Exception:
            pass
            
        return {
            "active_window_title": title or "Unknown",
            "app_name": app_name,
            "pid": pid,
            "browser_tab": browser_tab,
            "os": "win32"
        }

    def get_running_apps(self) -> List[Dict[str, Any]]:
        apps = []
        try:
            from PySide6.QtGui import QImage, QPixmap
            from PySide6.QtWidgets import QFileIconProvider
            from PySide6.QtCore import QFileInfo
            import ctypes
            import psutil
            import pygetwindow as gw
            
            provider = QFileIconProvider()
            seen_apps = set()
            
            for window in gw.getAllWindows():
                if not window.title or window.isMinimized:
                    continue
                        
                hwnd = window._hWnd
                pid_c = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_c))
                pid = pid_c.value
                
                try:
                    proc = psutil.Process(pid)
                    exe_path = proc.exe()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
                # Only map one window per executable to mimic MacOS behavior
                if exe_path in seen_apps:
                    continue
                seen_apps.add(exe_path)
                
                pixmap = None
                if exe_path:
                    try:
                        icon = provider.icon(QFileInfo(exe_path))
                        if not icon.isNull():
                            pixmap = icon.pixmap(128, 128)
                    except Exception:
                        pass
                
                safe_title = window.title[:20] + "..." if len(window.title) > 20 else window.title
                
                apps.append({
                    "name": safe_title,
                    "app_ref": hwnd,
                    "pixmap": pixmap
                })
        except Exception as e:
            print("Failed to pull raw Windows apps natively:", e)
            
        return apps

    def activate_app(self, app_data: Dict[str, Any]) -> None:
        try:
            import ctypes
            hwnd = app_data["app_ref"]
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"Windows specific activation exception: {e}")
