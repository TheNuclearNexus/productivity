import os
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QDialog,
    QListWidget,
    QSlider,
    QHBoxLayout,
    QLineEdit,
)
from PySide6.QtCore import Qt, QTimer, QPointF, QObject, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QGuiApplication

from productivity.core.engine import TrackerEngine
from productivity.core.state import FocusState
from productivity.core.profile import ProfileManager, FocusProfile


class OrbitalSignals(QObject):
    alt_tab_pressed = Signal(bool)
    alt_released = Signal()

class SurveyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Post-Session Analysis Survey")
        self.resize(400, 450)

        layout = QVBoxLayout()
        
        # 1. Productivity Slider
        layout.addWidget(QLabel("How productive did you feel? (1: Low, 7: High)"))
        self.prod_slider = QSlider(Qt.Orientation.Horizontal)
        self.prod_slider.setRange(1, 7)
        self.prod_slider.setValue(4)
        self.prod_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.prod_slider.setTickInterval(1)
        layout.addWidget(self.prod_slider)

        # 2. Distracted Slider
        layout.addWidget(QLabel("How distracted did you feel? (1: Low, 7: High)"))
        self.dist_slider = QSlider(Qt.Orientation.Horizontal)
        self.dist_slider.setRange(1, 7)
        self.dist_slider.setValue(4)
        self.dist_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.dist_slider.setTickInterval(1)
        layout.addWidget(self.dist_slider)

        # 3. Distraction Length
        layout.addWidget(QLabel("How long did your distractions feel? (1: Short, 7: Long)"))
        self.len_slider = QSlider(Qt.Orientation.Horizontal)
        self.len_slider.setRange(1, 7)
        self.len_slider.setValue(4)
        self.len_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.len_slider.setTickInterval(1)
        layout.addWidget(self.len_slider)

        # 4. Tracking Accuracy
        layout.addWidget(QLabel("How accurate did automated tracking feel? (1: Inaccurate, 7: Accurate)"))
        self.acc_slider = QSlider(Qt.Orientation.Horizontal)
        self.acc_slider.setRange(1, 7)
        self.acc_slider.setValue(4)
        self.acc_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.acc_slider.setTickInterval(1)
        layout.addWidget(self.acc_slider)

        # 5. Profile Adherence
        layout.addWidget(QLabel("Did you stick to your Profile Context? (1: Diverged, 7: Perfectly)"))
        self.prof_slider = QSlider(Qt.Orientation.Horizontal)
        self.prof_slider.setRange(1, 7)
        self.prof_slider.setValue(4)
        self.prof_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.prof_slider.setTickInterval(1)
        layout.addWidget(self.prof_slider)

        # 6. Fatigue
        layout.addWidget(QLabel("How mentally fatigued do you feel? (1: Refreshed, 7: Exhausted)"))
        self.fatigue_slider = QSlider(Qt.Orientation.Horizontal)
        self.fatigue_slider.setRange(1, 7)
        self.fatigue_slider.setValue(4)
        self.fatigue_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.fatigue_slider.setTickInterval(1)
        layout.addWidget(self.fatigue_slider)

        self.submit_btn = QPushButton("Complete & View Final Report")
        self.submit_btn.clicked.connect(self.accept)
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)

    def get_results(self):
        return {
            "productivity": self.prod_slider.value(),
            "distraction_level": self.dist_slider.value(),
            "distraction_length": self.len_slider.value(),
            "tracking_accuracy": self.acc_slider.value(),
            "profile_adherence": self.prof_slider.value(),
            "mental_fatigue": self.fatigue_slider.value()
        }


class OverrideEditorDialog(QDialog):
    def __init__(self, engine, target_profile_name, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.current_profile_name = target_profile_name
        self.setWindowTitle(f"Overrides: {self.current_profile_name}")
        self.resize(500, 300)

        main_layout = QVBoxLayout()

        # List of applications seen this session
        self.app_list = QListWidget()
        main_layout.addWidget(QLabel("Saved & Active Contexts:"))
        main_layout.addWidget(self.app_list)

        # Populate list
        self.titles = []
        seen = set()

        # 1. Load persistently saved historical overrides
        if self.engine and self.engine.overrides:
            profile_saves = self.engine.overrides.overrides.get(
                self.current_profile_name, {}
            )
            for title, entry in profile_saves.items():
                score = (
                    entry.get("score", 0.5) if isinstance(entry, dict) else float(entry)
                )
                pretty_name = (
                    entry.get("pretty_name", title)
                    if isinstance(entry, dict)
                    else title
                )
                self.titles.append(
                    (title, {"score": score, "pretty_name": pretty_name})
                )
                seen.add(title)

        # 2. Merge any new active windows from this session's cache
        if self.engine and self.engine.classifier:
            for (title, profile_name), entry in self.engine.classifier._cache.items():
                if profile_name == self.current_profile_name and title not in seen:
                    score = (
                        entry.get("score", 0.5)
                        if isinstance(entry, dict)
                        else float(entry)
                    )
                    pretty_name = (
                        entry.get("pretty_name", title)
                        if isinstance(entry, dict)
                        else title
                    )
                    self.titles.append(
                        (title, {"score": score, "pretty_name": pretty_name})
                    )
                    seen.add(title)

        self.titles.sort(key=lambda x: x[0])
        for t, entry in self.titles:
            s = entry["score"]
            self.app_list.addItem(f"{t} (Current: {s:.2f})")

        self.app_list.currentRowChanged.connect(self.on_selection)

        slider_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.on_slider_change)

        self.score_label = QLabel("0.50")
        self.score_label.setEnabled(False)

        slider_layout.addWidget(QLabel("Score:"))
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.score_label)

        # Add Rename App input
        rename_layout = QHBoxLayout()
        self.rename_input = QLineEdit()
        self.rename_input.setEnabled(False)
        rename_layout.addWidget(QLabel("Display Name:"))
        rename_layout.addWidget(self.rename_input)

        main_layout.addLayout(slider_layout)
        main_layout.addLayout(rename_layout)

        self.save_btn = QPushButton("Save Override")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_override)
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)

    def on_selection(self, idx):
        if idx < 0 or idx >= len(self.titles):
            return
        title, entry = self.titles[idx]
        score = entry["score"]
        pretty_name = entry["pretty_name"]

        if self.engine.overrides:
            saved = self.engine.overrides.get_override(self.current_profile_name, title)
            if saved is not None:
                score = saved.get("score", score)
                pretty_name = saved.get("pretty_name", pretty_name)

        self.slider.setEnabled(True)
        self.score_label.setEnabled(True)
        self.rename_input.setEnabled(True)
        self.save_btn.setEnabled(True)

        self.slider.setValue(int(score * 100))
        self.score_label.setText(f"{score:.2f}")
        self.rename_input.setText(pretty_name)

    def on_slider_change(self, val):
        self.score_label.setText(f"{val / 100.0:.2f}")

    def save_override(self):
        idx = self.app_list.currentRow()
        if idx < 0:
            return

        title, entry = self.titles[idx]
        new_score = self.slider.value() / 100.0
        new_name = self.rename_input.text()

        if self.engine and self.engine.overrides:
            self.engine.overrides.set_score(
                self.current_profile_name, title, new_score, new_name
            )
            self.engine.classifier._cache[(title, self.current_profile_name)] = {
                "score": new_score,
                "pretty_name": new_name,
            }

        self.titles[idx] = (title, {"score": new_score, "pretty_name": new_name})
        self.app_list.item(idx).setText(f"{title} (Current: {new_score:.2f})")


from PySide6.QtWidgets import QTextEdit, QMessageBox


class ProfileEditorDialog(QDialog):
    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setWindowTitle("Edit Focus Profiles")
        self.resize(600, 400)

        main_layout = QHBoxLayout()
        # Left Side - List
        left_layout = QVBoxLayout()
        self.profile_list = QListWidget()
        left_layout.addWidget(QLabel("Profiles:"))
        left_layout.addWidget(self.profile_list)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("New")
        self.add_btn.clicked.connect(self.add_profile)
        self.del_btn = QPushButton("Delete")
        self.del_btn.clicked.connect(self.delete_profile)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        left_layout.addLayout(btn_layout)

        main_layout.addLayout(left_layout, 1)

        # Right Side - Editor
        right_layout = QVBoxLayout()
        self.name_input = QLineEdit()
        right_layout.addWidget(QLabel("Name:"))
        right_layout.addWidget(self.name_input)

        self.desc_input = QTextEdit()
        right_layout.addWidget(QLabel("Context Description:"))
        right_layout.addWidget(self.desc_input)

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_current)
        right_layout.addWidget(self.save_btn)

        main_layout.addLayout(right_layout, 2)

        self.setLayout(main_layout)

        self.profile_keys = []
        self.current_key = None

        self.refresh_list()
        self.profile_list.currentRowChanged.connect(self.on_selection)

    def refresh_list(self):
        self.profile_list.clear()
        self.profile_keys = list(self.profile_manager.profiles.keys())
        for key in self.profile_keys:
            self.profile_list.addItem(self.profile_manager.profiles[key].name)

    def on_selection(self, idx):
        if idx < 0 or idx >= len(self.profile_keys):
            self.current_key = None
            self.name_input.clear()
            self.desc_input.clear()
            return

        self.current_key = self.profile_keys[idx]
        profile = self.profile_manager.profiles[self.current_key]
        self.name_input.setText(profile.name)
        self.desc_input.setPlainText(profile.description)

    def add_profile(self):
        self.profile_list.clearSelection()
        self.current_key = None
        self.name_input.setText("New Profile")
        self.desc_input.setPlainText("Description here...")
        self.name_input.setFocus()
        self.name_input.selectAll()

    def save_current(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        if not name or not desc:
            QMessageBox.warning(self, "Error", "Name and Description cannot be empty.")
            return

        if self.current_key is None:
            self.current_key = self.profile_manager.generate_key(name)

        self.profile_manager.profiles[self.current_key] = FocusProfile(
            name=name, description=desc
        )
        self.profile_manager.save()
        self.refresh_list()

        if self.current_key in self.profile_keys:
            self.profile_list.setCurrentRow(self.profile_keys.index(self.current_key))

    def delete_profile(self):
        if not self.current_key:
            return
        if len(self.profile_manager.profiles) <= 1:
            QMessageBox.warning(self, "Error", "Cannot delete the last profile.")
            return

        del self.profile_manager.profiles[self.current_key]
        self.profile_manager.save()
        self.refresh_list()





class FocusRingOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.ToolTip
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.target_score = -1.0
        self.score = 50.0
        self.is_increasing = True

        self.resize(150, 150)

        # Position at Bottom Right
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(
            screen.width() - self.width() - 30, screen.height() - self.height() - 30
        )

        # Timer to hide after period of no score change
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.trigger_fade_out)

        self.target_opacity = 0.0
        self.setWindowOpacity(0.0)

        # 60fps interpolation timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._lerp_step)
        self.anim_timer.start(16)

    def trigger_fade_out(self):
        self.target_opacity = 0.0

    def _lerp_step(self):
        if self.target_score >= 0:
            diff = self.target_score - self.score
            if abs(diff) > 0.05:
                self.score += diff * 0.02
                self.update()

        current_opacity = self.windowOpacity()
        opacity_diff = self.target_opacity - current_opacity
        if abs(opacity_diff) > 0.01:
            self.setWindowOpacity(current_opacity + opacity_diff * 0.05)
        elif self.target_opacity <= 0.0 and self.isVisible():
            self.hide()

    def update_state(self, state: FocusState):
        if abs(state.focus_score - self.target_score) > 0.01:
            self.target_score = state.focus_score
            self.is_increasing = state.is_increasing
            self.target_opacity = 1.0
            self.show()
            self.fade_timer.start(8000)  # Hide after stagnation

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 20
        rect = event.rect().adjusted(margin, margin, -margin, -margin)

        # Draw faint background ring
        painter.setPen(
            QPen(
                QColor(0, 0, 0, 80), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
            )
        )
        painter.drawArc(rect, 0, 360 * 16)

        # Draw white outline backdrop for contrast
        painter.setPen(
            QPen(
                QColor(255, 255, 255, 60),
                16,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawArc(rect, 0, 360 * 16)

        # Draw filled orbital arc based on focus score
        start_angle = 90 * 16  # 12 O'clock position
        span_angle = int(-(self.score / 100.0) * 360 * 16)  # Clockwise sweep

        color = QColor(144, 238, 144) if self.is_increasing else QColor(255, 99, 71)

        painter.setPen(QPen(color, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, start_angle, span_angle)

        # Draw a small inner pulsating/orbiting dot representing the core focus
        center = rect.center()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(center, int(self.score / 10.0), int(self.score / 10.0))


class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Global Settings")
        self.resize(400, 200)

        layout = QVBoxLayout()

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("Ollama (Local Models)", "ollama")
        self.provider_combo.addItem("Google Gemini (REST API)", "gemini")

        idx = self.provider_combo.findData(self.config_manager.config.provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        layout.addWidget(QLabel("LLM Provider:"))
        layout.addWidget(self.provider_combo)

        self.model_input = QLineEdit()
        self.model_input.setText(self.config_manager.config.ollama_model)
        layout.addWidget(QLabel("Ollama Model String (e.g. llama3.1:8b):"))
        layout.addWidget(self.model_input)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(self.config_manager.config.gemini_api_key)
        layout.addWidget(QLabel("Gemini API Key:"))
        layout.addWidget(self.api_key_input)

        self.save_btn = QPushButton("Save Config")
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def save_config(self):
        self.config_manager.config.provider = self.provider_combo.currentData()
        self.config_manager.config.ollama_model = self.model_input.text().strip()
        self.config_manager.config.gemini_api_key = self.api_key_input.text().strip()
        self.config_manager.save()
        self.accept()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Productivity Tracker")
        self.resize(300, 150)

        from productivity.core.config import ConfigManager

        self.config_manager = ConfigManager()

        # Check if first launch explicitly
        if not os.path.exists("config.json"):
            dlg = SettingsDialog(self.config_manager, self)
            dlg.exec()

        self.engine = TrackerEngine(config=self.config_manager.config)
        self.profile_manager = ProfileManager()

        self.engine_thread = None
        self.overlay = None
        self.orbital_switcher = None

        self.shared_state_container = {"state": None}

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_overlay)

        # Setup custom signals to bridge background pynput to main Qt thread safely
        self.orbital_signals = OrbitalSignals()
        self.orbital_signals.alt_tab_pressed.connect(self.handle_alt_tab)
        self.orbital_signals.alt_released.connect(self.handle_alt_released)

        # Hook standard overlay signals
        self.engine.input_monitor.on_alt_tab_pressed = lambda reverse: (
            self.orbital_signals.alt_tab_pressed.emit(reverse)
        )
        self.engine.input_monitor.on_alt_released = lambda: (
            self.orbital_signals.alt_released.emit()
        )

        self.init_ui()

    def handle_alt_tab(self, reverse=False):
        if self.overlay_combo.currentData() == "orbital" and self.engine._running:
            if not self.orbital_switcher:
                from productivity.ui.orbital_switcher import OrbitalSwitcher

                self.orbital_switcher = OrbitalSwitcher(self.engine)

            self.orbital_switcher.is_actively_switching = True

            if not self.orbital_switcher.isVisible():
                self.orbital_switcher.show()
                # UI rendering will trigger internally but we optionally force refresh here
            else:
                self.orbital_switcher.cycle(reverse)

    def handle_alt_released(self):
        if self.orbital_switcher and getattr(
            self.orbital_switcher, "is_actively_switching", False
        ):
            self.orbital_switcher.activate_selected()
            self.orbital_switcher.is_actively_switching = False
            if self.engine:
                self.engine._switcher_used = True

    def init_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Select Focus Profile:")
        layout.addWidget(label)

        self.profile_combo = QComboBox()
        self.refresh_profile_combo()
        layout.addWidget(self.profile_combo)

        self.edit_profiles_btn = QPushButton("Edit Profiles")
        self.edit_profiles_btn.clicked.connect(self.open_profile_editor)
        layout.addWidget(self.edit_profiles_btn)

        # Append Global Settings inherently explicitly
        self.app_settings_btn = QPushButton("Global Settings")
        self.app_settings_btn.clicked.connect(self.open_global_settings)
        layout.addWidget(self.app_settings_btn)

        # Add Overlay Toggle Data
        overlay_label = QLabel("Select Active Overlay:")
        layout.addWidget(overlay_label)

        self.overlay_combo = QComboBox()
        self.overlay_combo.addItem("Focus Meter (Ring)", "focus_ring")
        self.overlay_combo.addItem("Orbital App Switcher", "orbital")
        self.overlay_combo.addItem("None", "none")
        layout.addWidget(self.overlay_combo)

        self.toggle_btn = QPushButton("Start Session")
        self.toggle_btn.clicked.connect(self.toggle_session)
        layout.addWidget(self.toggle_btn)

        self.settings_btn = QPushButton("Overrides Editor")
        self.settings_btn.clicked.connect(self.open_editor)
        layout.addWidget(self.settings_btn)

        self.setLayout(layout)

    def refresh_profile_combo(self):
        self.profile_combo.clear()
        for key, profile in self.profile_manager.profiles.items():
            self.profile_combo.addItem(profile.name, key)

    def open_profile_editor(self):
        dlg = ProfileEditorDialog(self.profile_manager, self)
        dlg.exec()
        self.refresh_profile_combo()

    def open_global_settings(self):
        dlg = SettingsDialog(self.config_manager, self)
        dlg.exec()

        # Inject config actively to the live engine
        self.engine.classifier.config = self.config_manager.config

        cfg = self.config_manager.config
        if cfg.provider == "gemini" and cfg.gemini_api_key.strip():
            from productivity.llm.client import GeminiClient

            self.engine.classifier.client = GeminiClient(
                api_key=cfg.gemini_api_key.strip()
            )
            self.engine.classifier.model = "gemini-2.5-flash"
        else:
            from productivity.llm.client import OllamaClient

            self.engine.classifier.client = OllamaClient()
            self.engine.classifier.model = cfg.ollama_model

    def open_editor(self):
        if not self.engine:
            return

        current_profile_key = self.profile_combo.currentData()
        if not current_profile_key:
            return
        current_profile_name = self.profile_manager.profiles[current_profile_key].name

        dlg = OverrideEditorDialog(self.engine, current_profile_name, self)
        dlg.exec()

    def toggle_session(self):
        if self.engine is None or not self.engine._running:
            selected_key = self.profile_combo.currentData()
            self.start_session(selected_key)
            self.toggle_btn.setText("Stop Session & View Report")
            self.profile_combo.setEnabled(False)
            self.edit_profiles_btn.setEnabled(False)
            self.overlay_combo.setEnabled(False)
        else:
            self.stop_session()
            self.toggle_btn.setText("Start Session")
            self.profile_combo.setEnabled(True)
            self.edit_profiles_btn.setEnabled(True)
            self.overlay_combo.setEnabled(True)

    def on_state_change(self, new_state: FocusState):
        self.shared_state_container["state"] = new_state

    def start_session(self, profile_key: str):
        self.engine.state.profile = self.profile_manager.profiles[profile_key]
        self.engine.on_state_change = self.on_state_change

        # Critical Fix: Execute OS routines on main GUI thread!
        self.engine.start()

        overlay_selection = self.overlay_combo.currentData()
        if overlay_selection == "focus_ring":
            if self.overlay is None:
                self.overlay = FocusRingOverlay()
        else:
            self.overlay = None

        self.engine_timer = QTimer()
        self.engine_timer.timeout.connect(self.engine_tick)
        self.engine_timer.start(5000)  # Fire engine every 5 seconds

        self.timer.start(1000)  # Fast UI updater

    def engine_tick(self):
        if self.engine and self.engine._running:
            self.engine.tick()

    def stop_session(self):
        self.timer.stop()
        if hasattr(self, "engine_timer") and self.engine_timer:
            self.engine_timer.stop()

        if self.engine:
            overlay_selection = self.overlay_combo.currentData()
            
            # Open blocking survey capturing explicitly
            survey_results = None
            if self.engine._running:
                dlg = SurveyDialog(self)
                if dlg.exec():
                    survey_results = dlg.get_results()

            self.engine.stop(overlay_name=overlay_selection, survey_results=survey_results)  # This blocks while matplotlib is shown

        if self.overlay:
            self.overlay.close()
            self.overlay = None

    def update_overlay(self):
        state = self.shared_state_container.get("state")
        if self.overlay and state:
            self.overlay.update_state(state)

    def closeEvent(self, event):
        self.stop_session()
        super().closeEvent(event)
