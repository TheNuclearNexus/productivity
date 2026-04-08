import abc
from typing import Any, Dict, Optional, List, Callable

class BasePlatform(abc.ABC):
    @abc.abstractmethod
    def check_accessibility(self) -> bool:
        """Returns True if the application has expected OS accessibility permissions, False otherwise."""
        pass
        
    @abc.abstractmethod
    def get_keyboard_intercept(self) -> Optional[Callable]:
        """Returns the native OS intercept callback to conditionally swallow key events (e.g. for pynput), or None."""
        pass
        
    @abc.abstractmethod
    def get_active_window_info(self) -> Dict[str, Any]:
        """Fetches the foreground window metadata: app_name, active_window_title, pid, browser_tab, os."""
        pass
        
    @abc.abstractmethod
    def get_running_apps(self, include_pixmaps: bool = True) -> List[Dict[str, Any]]:
        """Returns a list of dicts mapping ['name', 'pixmap', 'app_ref'] for all open GUI applications."""
        pass
        
    @abc.abstractmethod
    def activate_app(self, app_data: Dict[str, Any]) -> None:
        """Forces the active OS window focus dynamically onto the application provided in the 'app_ref'."""
        pass
