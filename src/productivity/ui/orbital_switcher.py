import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont


class OrbitalSwitcher(QWidget):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.ToolTip
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # We need this to steal top level drawing, but NOT be transparent for input if we want active focus?
        # Actually, pynput is handling the kb hook, so we CAN be transparent for input so we don't steal the true active app focus until release!
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.resize(800, 800)
        self.apps = []
        self.selected_index = 0

    def refresh_apps(self):
        from productivity.platforms import get_platform

        self.platform = get_platform()

        self.apps = self.platform.get_running_apps()

        def get_app_score(app_data):
            score = 0.5
            app_data["pretty_name"] = app_data["name"]
            if not self.engine:
                return score

            try:
                profile_name = self.engine.state.profile.name
                app_name = app_data["name"]

                # Check manual overrides
                override = self.engine.overrides.get_score(profile_name, app_name)
                if override is not None:
                    return override

                # Fallback to broad LLM classifier caching
                matches = []
                for (
                    cached_title,
                    cached_profile,
                ), entry in self.engine.classifier._cache.items():
                    if cached_profile == profile_name and app_name in cached_title:
                        # Entry natively structured as Dictionary payload!
                        if isinstance(entry, dict):
                            matches.append(entry.get("score", 0.5))
                            app_data["pretty_name"] = entry.get("pretty_name", app_name)
                        else:
                            matches.append(float(entry))

                if matches:
                    return max(matches)
            except Exception:
                pass
            return score

        # Puts highest score apps at index 0, which natively map to inner ring natively
        self.apps.sort(key=get_app_score, reverse=True)

        # Cmd+Tab orders by most recently used natively. We now dictate ordering purely by Profile relevance!
        if self.apps:
            self.selected_index = 1 % len(self.apps)  # Default select the NEXT app

        self.update()

    def showEvent(self, event):
        self.refresh_apps()
        # Center on primary screen securely
        from PySide6.QtGui import QGuiApplication

        screen_geo = QGuiApplication.primaryScreen().geometry()
        x = screen_geo.x() + (screen_geo.width() - self.width()) // 2
        y = screen_geo.y() + (screen_geo.height() - self.height()) // 2
        self.move(x, y)
        super().showEvent(event)

    def cycle(self, reverse=False):
        if not self.apps:
            return
        if reverse:
            self.selected_index = (self.selected_index - 1) % len(self.apps)
        else:
            self.selected_index = (self.selected_index + 1) % len(self.apps)
        self.update()

    def activate_selected(self):
        try:
            if self.apps and 0 <= self.selected_index < len(self.apps):
                app = self.apps[self.selected_index]["app_ref"]
                # Bypass MacOS anti-focus sandbox! Background apps (us) lose authorization to call activateWithOptions repeatedlessly.
                import subprocess

                name = app.localizedName()
                subprocess.Popen(
                    ["osascript", "-e", f'tell application "{name}" to activate']
                )
        except Exception as e:
            print(f"OrbitalSwitcher specific activation exception: {e}")
        finally:
            self.hide()

    def paintEvent(self, event):
        if not self.apps:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        center = QPointF(self.width() / 2, self.height() / 2)

        inner_ring_radius = 100
        outer_ring_radius = 180

        # Draw Orbital Rings Dark Backdrop
        painter.setBrush(QColor(0, 0, 0, 150))  # Slight dark translucent backdrop
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, outer_ring_radius + 40, outer_ring_radius + 40)

        # Draw Outlines
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 60), 4, Qt.PenStyle.SolidLine))
        painter.drawEllipse(center, inner_ring_radius, inner_ring_radius)
        painter.drawEllipse(center, outer_ring_radius, outer_ring_radius)

        ring_apps = self.apps

        # Draw the focused application explicitly in the massive center preview
        if self.apps and 0 <= self.selected_index < len(self.apps):
            app_data = self.apps[self.selected_index]
            pixmap = app_data.get("pixmap")

            # Fetch the condensed display label utilizing purely conversational LLM context
            name = app_data.get("pretty_name", app_data["name"])

            if pixmap:
                scaled = pixmap.scaled(
                    80,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                px_rect = scaled.rect()
                px_rect.moveCenter(center.toPoint())
                painter.drawPixmap(px_rect, scaled)

            painter.setPen(QColor(255, 255, 255))

            base_font_size = 18
            length_penalty = max(0, (len(name) - 12) // 2)
            font_size = max(9, base_font_size - length_penalty)

            font = QFont("Helvetica Neue", font_size, QFont.Weight.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()

            MAX_WIDTH = 140
            display_name = name
            if metrics.horizontalAdvance(display_name) > MAX_WIDTH:
                display_name = metrics.elidedText(
                    name, Qt.TextElideMode.ElideRight, MAX_WIDTH
                )

            text_width = metrics.horizontalAdvance(display_name)
            painter.drawText(
                int(center.x() - text_width / 2), int(center.y() + 60), display_name
            )

        # Draw ALL applications mathematically onto concentric orbital rings natively
        count_inner = math.ceil(len(ring_apps) / 2)

        for ring_idx, app_data in enumerate(ring_apps):
            pixmap = app_data["pixmap"]

            is_inner = ring_idx < count_inner
            count_in_this_ring = (
                count_inner if is_inner else len(ring_apps) - count_inner
            )
            my_idx_in_this_ring = ring_idx if is_inner else ring_idx - count_inner

            if count_in_this_ring > 0:
                angle = (2 * math.pi * my_idx_in_this_ring) / count_in_this_ring
            else:
                angle = 0

            # Start orbits at exactly top-dead-center crest
            angle -= math.pi / 2

            radius = inner_ring_radius if is_inner else outer_ring_radius
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)

            if pixmap:
                scaled = pixmap.scaled(
                    30,
                    30,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                px_rect = scaled.rect()
                px_rect.moveCenter(QPointF(x, y).toPoint())

                # Draw sharp targeting outline if this icon is the actively hovered selection
                if ring_idx == self.selected_index:
                    painter.setPen(
                        QPen(QColor(255, 255, 255, 220), 4, Qt.PenStyle.SolidLine)
                    )
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(px_rect.center(), 20, 20)

                painter.drawPixmap(px_rect, scaled)
