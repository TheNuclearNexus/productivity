import sys
from typing import Any, Dict, Optional
from productivity.monitors.base import Monitor
from productivity.platforms import get_platform


class WindowMonitor(Monitor):
    """Monitors the active window title and application name cleanly using Platform abstractions."""

    def __init__(self):
        self.last_active_title: Optional[str] = None
        self.platform = get_platform()

    def start(self):
        pass

    def stop(self):
        pass

    def get_state(self) -> Dict[str, Any]:
        """Fetch the currently active window title and process context."""

        info = self.platform.get_active_window_info()
        title = info.get("active_window_title")

        if not title or title == "Unknown":
            title = self.last_active_title or "Unknown"
        else:
            self.last_active_title = title

        info["active_window_title"] = title
        return info
