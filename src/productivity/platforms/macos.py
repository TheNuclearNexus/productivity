import sys
import subprocess
from typing import Any, Dict, Optional, List, Callable

from .base import BasePlatform

class MacOSPlatform(BasePlatform):
    def check_accessibility(self) -> bool:
        try:
            import ApplicationServices
            return ApplicationServices.AXIsProcessTrusted()
        except ImportError:
            return False

    def get_keyboard_intercept(self) -> Optional[Callable]:
        def darwin_intercept_callback(event_type, event):
            try:
                if not getattr(self, "suppress_alt_tab", False):
                    return event
                import Quartz
                if event_type == 10: # kCGEventKeyDown
                    keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
                    flags = Quartz.CGEventGetFlags(event)
                    # kCGEventFlagMaskAlternate = 524288, kCGEventFlagMaskCommand = 1048576
                    is_modifier = (flags & 524288) or (flags & 1048576)
                    if keycode == 48 and is_modifier: # 48 is Tab
                        return None
            except Exception:
                pass
            return event
        return darwin_intercept_callback

    def get_active_window_info(self) -> Dict[str, Any]:
        title, app_name, pid, browser_tab = None, None, None, None
        try:
            from AppKit import NSWorkspace
            import pygetwindow as gw
            
            # Use pygetwindow for precise active window title string
            active_win = gw.getActiveWindow()
            if active_win is not None:
                if isinstance(active_win, str):
                    title = active_win
                elif hasattr(active_win, "title"):
                    title = active_win.title
                
            # Use AppKit for deep mapping (AppName, PID and DOM Browser Tab queries via AppleScript)
            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if app:
                app_name = app.localizedName()
                pid = app.processIdentifier()
                
                if app_name in ["Google Chrome", "Brave Browser", "Microsoft Edge"]:
                    script = f'tell application "{app_name}" to return title of active tab of front window'
                    res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                    if res.returncode == 0:
                        browser_tab = res.stdout.strip()
                elif app_name == "Safari":
                    script = 'tell application "Safari" to return name of front document'
                    res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                    if res.returncode == 0:
                        browser_tab = res.stdout.strip()
        except Exception:
            pass
            
        return {
            "active_window_title": title or "Unknown",
            "app_name": app_name,
            "pid": pid,
            "browser_tab": browser_tab,
            "os": "darwin"
        }

    def __init__(self):
        super().__init__()
        self._icon_cache = {}

    def get_running_apps(self, include_pixmaps: bool = True) -> List[Dict[str, Any]]:
        apps = []
        try:
            import AppKit
            from PySide6.QtGui import QImage, QPixmap
            
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            for app in running_apps:
                # NSApplicationActivationPolicyRegular ensures we only fetch true desktop applications (like dock apps)
                if app.activationPolicy() == 0:
                    name = app.localizedName()
                    icon = app.icon()
                    
                    pixmap = None
                    if include_pixmaps and icon:
                        if name in self._icon_cache:
                            pixmap = self._icon_cache[name]
                        else:
                            tiff = icon.TIFFRepresentation()
                            if tiff:
                                byte_str = tiff.bytes()
                                if byte_str:
                                    qimg = QImage()
                                    if qimg.loadFromData(bytes(byte_str)):
                                        pixmap = QPixmap.fromImage(qimg)
                                        self._icon_cache[name] = pixmap
                                    
                    apps.append({
                        "name": name,
                        "app_ref": app,
                        "pixmap": pixmap
                    })
        except Exception as e:
            print("Failed to pull raw macOS apps natively:", e)
            
        return apps

    def activate_app(self, app_data: Dict[str, Any]) -> None:
        try:
            # Bypass MacOS anti-focus sandbox! Background apps lose authorization to call activateWithOptions repeatedly.
            import subprocess
            name = app_data["name"]
            subprocess.Popen(["osascript", "-e", f'tell application "{name}" to activate'])
        except Exception as e:
            print(f"macOS specific activation exception: {e}")
