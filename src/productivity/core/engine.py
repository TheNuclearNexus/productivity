import asyncio
from typing import Callable, Optional
from productivity.monitors.window import WindowMonitor
from productivity.monitors.input import InputMonitor
from productivity.core.state import FocusState
from productivity.core.profile import FocusProfile
from productivity.llm.classifier import WindowClassifier

from productivity.core.logger import SessionLogger
from productivity.core.overrides import OverridesManager

from productivity.core.config import AppConfig

import threading


class TrackerEngine:
    def __init__(self, config: AppConfig):
        self.window_monitor = WindowMonitor()
        self.input_monitor = InputMonitor()
        self.overrides = OverridesManager()
        self.classifier = WindowClassifier(config=config, overrides_mgr=self.overrides)
        self.state = FocusState(profile=FocusProfile(name="Idle", description="Idle"))

        self.logger = SessionLogger()
        self.last_window_title = ""
        self.on_state_change: Optional[Callable[[FocusState], None]] = None
        self._running = False

    def start(self):
        # Keep OS monitors inside main thread constraints
        print("window monitor")
        self.window_monitor.start()
        print("input monitor")
        self.input_monitor.start()
        print("session logger")
        self.logger = SessionLogger()  # Fresh logger on start
        self._running = True

        # Async bootstrapper to mass-evaluate all existing OS apps proactively
        threading.Thread(target=self._bootstrap_classifications, daemon=True).start()

    def _bootstrap_classifications(self):
        """Asynchronously runs through all currently active Desktop Applications across the OS
        and pre-warms the LLM evaluation cache natively without user switching."""
        from productivity.platforms import get_platform

        apps = get_platform().get_running_apps(include_pixmaps=False)

        if not apps:
            return

        print(
            f"Bootstrapping {len(apps)} background applications against Profile Context: {self.state.profile.name}"
        )

        # We sequentially resolve them locally to prevent flooding local CPU RAM via massive concurrently generated tensors
        async def evaluate_all():
            for app_data in apps:
                title = app_data.get("name")
                if title and self._running:
                    # Leverage the active classifier (which natively skips if overridden or deeply cached)
                    _, _ = await self.classifier.classify(title, self.state.profile)

        try:
            asyncio.run(evaluate_all())
            print("Background Application Bootstrap Mass Mapping Complete.")
        except Exception as e:
            print(f"Bootstrap evaluation skipped/failed: {e}")

    def stop(self):
        if not self._running:
            return

        self._running = False
        self.window_monitor.stop()
        self.input_monitor.stop()
        df = self.logger.end_session()
        self.logger.plot_session(df)

    def tick(self):
        """Called periodically by the main GUI thread/timer."""
        if not self._running:
            return

        win_state = self.window_monitor.get_state()
        input_state = self.input_monitor.get_state()  # KPM, Mouse Moves

        title = win_state.get("active_window_title", "Unknown")
        app_name = win_state.get("app_name")
        pid = win_state.get("pid")
        browser_tab = win_state.get("browser_tab")

        target_title = title
        if app_name:
            pid_str = f" [PID: {pid}]" if pid else ""
            if browser_tab:
                target_title = f"{browser_tab} - {app_name}{pid_str}"
            else:
                target_title = f"{title} - {app_name}{pid_str}"

        kpm = input_state.get("kpm", 0.0)
        mpm = input_state.get("mouse_moves_pm", 0.0)

        # Dispatch the LLM evaluation to a daemon thread
        def background_classify():
            self._is_classifying = True
            try:
                relevance, pretty_title = asyncio.run(
                    self.classifier.classify(target_title, self.state.profile)
                )

                window_switched = (
                    target_title != self.last_window_title
                ) and self.last_window_title != ""
                self.last_window_title = target_title

                self.state.update_score(relevance, kpm, mpm, window_switched)

                # Natively storing verbose title to logs logically per explicit fallback
                self.logger.log(
                    profile=self.state.profile.name,
                    window_title=target_title,
                    relevance=relevance,
                    kpm=kpm,
                    mpm=mpm,
                    focus_score=self.state.focus_score,
                )

                if self.on_state_change:
                    self.on_state_change(self.state)
            finally:
                self._is_classifying = False

        if not getattr(self, "_is_classifying", False):
            threading.Thread(target=background_classify, daemon=True).start()
