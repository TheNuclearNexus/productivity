import subprocess
import psutil
from typing import Any, Dict, Optional, List, Callable

from .base import BasePlatform

class LinuxPlatform(BasePlatform):
    def check_accessibility(self) -> bool:
        return True

    def get_keyboard_intercept(self) -> Optional[Callable]:
        return None

    def get_active_window_info(self) -> Dict[str, Any]:
        title, app_name, pid, browser_tab = None, None, None, None
        try:
            import pygetwindow as gw
            active_win = gw.getActiveWindow()
            if active_win is not None:
                if isinstance(active_win, str):
                    title = active_win
                elif hasattr(active_win, "title"):
                    title = active_win.title
                
            pid_bytes = subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowpid'])
            pid = int(pid_bytes.decode().strip())
            app_name = psutil.Process(pid).name()
        except Exception:
            pass
            
        return {
            "active_window_title": title or "Unknown",
            "app_name": app_name,
            "pid": pid,
            "browser_tab": browser_tab,
            "os": "linux"
        }

    def __init__(self):
        super().__init__()
        self._icon_cache = {}

    def get_running_apps(self, include_pixmaps: bool = True) -> List[Dict[str, Any]]:
        apps = []
        try:
            import pygetwindow as gw
            import psutil
            import subprocess
            from PySide6.QtGui import QPixmap
            
            # Simple fallback mapping for Linux environments
            for window in gw.getAllWindows():
                if not window.title:
                    continue
                    
                pixmap = None
                safe_title = window.title[:20] + "..." if len(window.title) > 20 else window.title
                apps.append({
                    "name": safe_title,
                    "app_ref": window,
                    "pixmap": pixmap
                })
        except Exception as e:
            print("Failed to pull raw Linux apps natively:", e)
            
        return apps

    def activate_app(self, app_data: Dict[str, Any]) -> None:
        try:
            window = app_data["app_ref"]
            if hasattr(window, "activate"):
                window.activate()
        except Exception as e:
            print(f"Linux specific activation exception: {e}")
