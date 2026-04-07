import sys
import time
from typing import Dict, Any, Optional

from pynput import keyboard, mouse
from productivity.monitors.base import Monitor
from productivity.platforms import get_platform

try:
    _ = get_platform().check_accessibility()
except Exception:
    pass


class InputMonitor(Monitor):
    def __init__(self):
        self.keystroke_count = 0
        self.mouse_move_count = 0
        self.start_time = time.time()

        self.modifier_held = False
        self.shift_held = False
        self.on_alt_tab_pressed = None
        self.on_alt_released = None

        self.platform = get_platform()

        # Start listeners before Qt event loop to prevent CGEvent clashes
        self.m_listener = mouse.Listener(on_move=self.on_move, on_scroll=self.on_scroll)

        self.k_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            darwin_intercept=self.platform.get_keyboard_intercept(),
        )
        self.k_listener.start()
        self.m_listener.start()

    def on_press(self, key):
        self.keystroke_count += 1

        key_name = getattr(key, "name", str(key))
        if (
            key
            in (
                keyboard.Key.alt,
                keyboard.Key.alt_l,
                keyboard.Key.alt_r,
                keyboard.Key.cmd,
                keyboard.Key.cmd_l,
                keyboard.Key.cmd_r,
            )
            or "alt" in key_name
            or "cmd" in key_name
        ):
            # For max compatibility handle Cmd or Option as the trigger anchor
            self.modifier_held = True
        elif (
            key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r)
            or "shift" in key_name
        ):
            self.shift_held = True
        elif key == keyboard.Key.tab and self.modifier_held:
            if self.on_alt_tab_pressed:
                self.on_alt_tab_pressed(self.shift_held)

    def on_release(self, key):
        key_name = getattr(key, "name", str(key))
        if (
            key
            in (
                keyboard.Key.alt,
                keyboard.Key.alt_l,
                keyboard.Key.alt_r,
                keyboard.Key.cmd,
                keyboard.Key.cmd_l,
                keyboard.Key.cmd_r,
            )
            or "alt" in key_name
            or "cmd" in key_name
        ):
            self.modifier_held = False
            if self.on_alt_released:
                self.on_alt_released()
        elif (
            key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r)
            or "shift" in key_name
        ):
            self.shift_held = False

    def on_move(self, x, y):
        self.mouse_move_count += 1

    def on_scroll(self, x, y, dx, dy):
        self.mouse_move_count += 1

    def start(self):
        pass

    def stop(self):
        self.k_listener.stop()
        self.m_listener.stop()

    def get_state(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start_time
        if elapsed < 1:
            elapsed = 1

        kpm = (self.keystroke_count / elapsed) * 60
        mpm = (self.mouse_move_count / elapsed) * 60

        # Reset counters to get discrete windows of time
        self.keystroke_count = 0
        self.mouse_move_count = 0
        self.start_time = time.time()

        return {"kpm": round(kpm, 2), "mouse_moves_pm": round(mpm, 2)}
