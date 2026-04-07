import sys

_PLATFORM_INSTANCE = None

def get_platform():
    """Lazily load and build the cross-architecture driver explicitly tuned to the running OS"""
    global _PLATFORM_INSTANCE
    if _PLATFORM_INSTANCE is not None:
        return _PLATFORM_INSTANCE
        
    if sys.platform == "darwin":
        from .macos import MacOSPlatform
        _PLATFORM_INSTANCE = MacOSPlatform()
    elif sys.platform == "win32":
        from .windows import WindowsPlatform
        _PLATFORM_INSTANCE = WindowsPlatform()
    elif sys.platform.startswith("linux"):
        from .linux import LinuxPlatform
        _PLATFORM_INSTANCE = LinuxPlatform()
    else:
        from .base import BasePlatform
        class DummyPlatform(BasePlatform):
            def check_accessibility(self): return True
            def get_keyboard_intercept(self): return None
            def get_active_window_info(self): return {"os": "unknown"}
            def get_running_apps(self): return []
            def activate_app(self, app_data): pass
        _PLATFORM_INSTANCE = DummyPlatform()
        
    return _PLATFORM_INSTANCE
