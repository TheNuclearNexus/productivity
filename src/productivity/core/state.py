from dataclasses import dataclass
from typing import Optional
from productivity.core.profile import FocusProfile


@dataclass
class FocusState:
    profile: Optional[FocusProfile] = None
    focus_score: float = 50.0  # 0 to 100
    is_increasing: bool = True  # Tracks if the score grew this tick
    afk_ticks: int = 0

    def update_score(
        self, relevance: float, kpm: float, mpm: float, window_switched: bool
    ):
        """
        Update the focus score based on the relevance (0.0 to 1.0) and inputs.
        If relevance > 0.5, score ideally goes up. If < 0.5, score decays.
        """
        prev_score = self.focus_score

        # Base shift: relevance 1.0 -> +2.5, relevance 0.0 -> -2.5
        shift_amount = (relevance - 0.5) * 5.0

        if kpm == 0 and mpm == 0:
            self.afk_ticks += 1
        else:
            self.afk_ticks = 0

        # AFK Check: if no inputs happen for ~30 seconds (6 ticks of 5s), it is deemed AFK.
        # Without screenshots to verify otherwise, AFK strictly drains focus.
        if self.afk_ticks >= 6:
            # Overrides any positive gain, turning it into a strict drain
            # while maintaining higher penalties for being idle on distraction windows.
            shift_amount = min(shift_amount, -2.0)
        # Drain rate adjustment based on switching behavior.
        # If the user swaps to a low-relevance app, make the drain slightly harsher for this tick.
        if window_switched and relevance < 0.5:
            shift_amount *= 1.5

        self.focus_score += shift_amount
        self.focus_score = max(0.0, min(100.0, self.focus_score))

        self.is_increasing = self.focus_score >= prev_score
