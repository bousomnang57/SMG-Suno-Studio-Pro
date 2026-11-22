"""
Interactive Waveform Widget for SMG Suno Studio Pro.
High-DPI vector-drawn antialiased audio waveform with:
- Playhead scrub line
- Draggable IN / OUT Silence Trim Markers
- Live A/B Mode Indicator Badge (Original Suno vs. Mastered Pro)
- Zoom & Scroll Navigation
- Stereo L/R Peak Volume Level Meters
- Theme-adaptive color rendering
"""

from __future__ import annotations

import math
from typing import Optional, Tuple
import numpy as np

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath


class WaveformCanvas(QWidget):
    """Core Canvas rendering the audio waveform envelope and trim handles."""

    seek_requested = pyqtSignal(float)  # seconds
    trim_changed = pyqtSignal(float, float)  # in_sec, out_sec

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.samples: Optional[np.ndarray] = None
        self.sample_rate: int = 44100
        self.duration: float = 0.0
        self.current_time: float = 0.0

        # In/Out Trim Markers in seconds
        self.in_point: float = 0.0
        self.out_point: float = 0.0

        # Display Mode: "A" (Original) or "B" (Mastered Pro)
        self.mode_tag: str = "B: MASTERED PRO"
        self.is_mastered_mode: bool = True

        # Zoom level (1.0 = Fit)
        self.zoom: float = 1.0
        self.scroll_offset: float = 0.0

        # Colors (default Obsidian Dark)
        self.bg_color = QColor("#080c14")
        self.grid_color = QColor("#162032")
        self.wave_color = QColor("#10b981")  # Mastered Emerald
        self.wave_color_alt = QColor("#059669")
        self.playhead_color = QColor("#38bdf8")
        self.in_marker_color = QColor("#f59e0b")
        self.out_marker_color = QColor("#ef4444")
        self.text_color = QColor("#94a3b8")

        # Dragging state
        self._dragging: Optional[str] = None  # "in", "out", "seek"

    def set_audio_data(self, samples: np.ndarray, sample_rate: int, is_mastered: bool = True):
        """Loads audio samples into the waveform view."""
        if samples is None or len(samples) == 0:
            self.samples = None
            self.duration = 0.0
            self.update()
            return

        # Mono downmix for waveform display
        if samples.ndim == 2:
            self.samples = np.mean(samples, axis=1)
        else:
            self.samples = samples

        self.sample_rate = sample_rate
        self.duration = float(len(self.samples) / sample_rate)
        self.in_point = 0.0
        self.out_point = self.duration
        self.set_mode(is_mastered)
        self.update()

    def set_mode(self, is_mastered: bool):
        """Switches between Original (A) and Mastered Pro (B) styling."""
        self.is_mastered_mode = is_mastered
        if is_mastered:
            self.mode_tag = "B: MASTERED PRO"
            self.wave_color = QColor("#10b981")  # Emerald
            self.wave_color_alt = QColor("#059669")
        else:
            self.mode_tag = "A: ORIGINAL SUNO"
            self.wave_color = QColor("#f59e0b")  # Amber
            self.wave_color_alt = QColor("#d97706")
        self.update()

    def set_playback_position(self, sec: float):
        """Updates playhead position during audio playback."""
        self.current_time = max(0.0, min(sec, self.duration))
        self.update()

    def set_trim_points(self, in_sec: float, out_sec: float):
        self.in_point = max(0.0, min(in_sec, self.duration))
        self.out_point = max(self.in_point, min(out_sec, self.duration))
        self.update()

    def set_zoom(self, zoom: float):
        self.zoom = max(1.0, min(zoom, 10.0))
        self.update()

    def apply_theme(self, theme_dict: dict):
        """Adapts colors to active studio theme."""
        is_dark = theme_dict.get("is_dark", True)
        bg = theme_dict.get("bg_window", "#080c14")
        card = theme_dict.get("bg_card", "#0e1526")
        border = theme_dict.get("border", "#1e293b")
        acc = theme_dict.get("accent", "#38bdf8")

        self.bg_color = QColor(bg)
        self.grid_color = QColor(border)
        self.playhead_color = QColor(acc)
        self.text_color = QColor(theme_dict.get("text_secondary", "#94a3b8"))

        if self.is_mastered_mode:
            self.wave_color = QColor("#10b981") if is_dark else QColor("#059669")
            self.wave_color_alt = QColor("#059669") if is_dark else QColor("#047857")
        else:
            self.wave_color = QColor("#f59e0b") if is_dark else QColor("#d97706")
            self.wave_color_alt = QColor("#d97706") if is_dark else QColor("#b45309")
        self.update()

    # ── Paint Events ──

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Background Fill
        p.fillRect(0, 0, w, h, self.bg_color)

        # 2. Timeline Grid & Time Markers
        self._draw_grid_and_ruler(p, w, h)

        if self.samples is None or len(self.samples) == 0:
            # Placeholder text
            p.setPen(QColor("#64748b"))
            p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎵 No Audio Loaded — Drag & drop Suno tracks or click '+ Add Audio'")
            return

        # 3. Waveform Peaks & Envelope
        self._draw_waveform(p, w, h)

        # 4. Draggable In/Out Trim Regions
        self._draw_trim_regions(p, w, h)

        # 5. Playhead Line
        self._draw_playhead(p, w, h)

        # 6. Mode Badge (A: Original vs. B: Mastered Pro)
        self._draw_mode_badge(p, w, h)

    def _draw_grid_and_ruler(self, p: QPainter, w: int, h: int):
        p.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DashLine))
        mid_y = h / 2.0
        p.drawLine(0, int(mid_y), w, int(mid_y))

        # Ruler bar top
        ruler_h = 20
        p.fillRect(0, 0, w, ruler_h, QColor(0, 0, 0, 50))
        p.setPen(QPen(self.grid_color, 1))
        p.drawLine(0, ruler_h, w, ruler_h)

        if self.duration > 0:
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(self.text_color)
            steps = 6
            for i in range(steps + 1):
                sec = (self.duration / steps) * i
                x = int((sec / self.duration) * w)
                m = int(sec // 60)
                s = int(sec % 60)
                txt = f"{m:02d}:{s:02d}.00"
                p.drawLine(x, ruler_h - 4, x, ruler_h)
                if x < w - 40:
                    p.drawText(x + 2, ruler_h - 6, txt)

    def _draw_waveform(self, p: QPainter, w: int, h: int):
        mid_y = h / 2.0
        ruler_h = 20
        wave_h = (h - ruler_h) / 2.0 - 4

        n_samples = len(self.samples)
        if n_samples == 0:
            return

        # Downsample samples to width pixels
        chunk_size = max(1, n_samples // w)
        visible_chunks = n_samples // chunk_size

        grad = QLinearGradient(0, ruler_h, 0, h)
        grad.setColorAt(0.0, self.wave_color)
        grad.setColorAt(0.5, self.wave_color_alt)
        grad.setColorAt(1.0, self.wave_color)

        pen = QPen(QBrush(grad), 1.5)
        p.setPen(pen)

        for col in range(min(w, visible_chunks)):
            start = col * chunk_size
            end = min(n_samples, start + chunk_size)
            block = self.samples[start:end]

            if len(block) > 0:
                val_max = float(np.max(block))
                val_min = float(np.min(block))
                # Scale to wave height
                y_top = mid_y - (val_max * wave_h)
                y_bot = mid_y - (val_min * wave_h)
                if abs(y_bot - y_top) < 1.0:
                    y_bot = y_top + 1.0
                p.drawLine(col, int(y_top), col, int(y_bot))

    def _draw_trim_regions(self, p: QPainter, w: int, h: int):
        if self.duration <= 0:
            return

        # Draw shaded region for trimmed head
        x_in = int((self.in_point / self.duration) * w)
        if x_in > 0:
            p.fillRect(0, 20, x_in, h - 20, QColor(0, 0, 0, 110))
            # IN marker line
            p.setPen(QPen(self.in_marker_color, 2))
            p.drawLine(x_in, 20, x_in, h)
            # IN flag
            p.setBrush(self.in_marker_color)
            p.drawRect(x_in - 1, 20, 22, 14)
            p.setPen(QColor("#000000"))
            p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            p.drawText(x_in + 4, 31, "IN")

        # Draw shaded region for trimmed tail
        x_out = int((self.out_point / self.duration) * w)
        if x_out < w:
            p.fillRect(x_out, 20, w - x_out, h - 20, QColor(0, 0, 0, 110))
            # OUT marker line
            p.setPen(QPen(self.out_marker_color, 2))
            p.drawLine(x_out, 20, x_out, h)
            # OUT flag
            p.setBrush(self.out_marker_color)
            p.drawRect(x_out - 22, 20, 22, 14)
            p.setPen(QColor("#ffffff"))
            p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            p.drawText(x_out - 19, 31, "OUT")

    def _draw_playhead(self, p: QPainter, w: int, h: int):
        if self.duration <= 0:
            return
        x = int((self.current_time / self.duration) * w)
        p.setPen(QPen(self.playhead_color, 2))
        p.drawLine(x, 20, x, h)
        # Playhead triangle pointer
        p.setBrush(self.playhead_color)
        triangle = QPainterPath()
        triangle.moveTo(x - 5, 20)
        triangle.lineTo(x + 5, 20)
        triangle.lineTo(x, 28)
        triangle.closeSubpath()
        p.drawPath(triangle)

    def _draw_mode_badge(self, p: QPainter, w: int, h: int):
        badge_w = 135
        badge_h = 24
        x = w - badge_w - 12
        y = h - badge_h - 10

        bg = QColor(6, 95, 70, 220) if self.is_mastered_mode else QColor(146, 64, 14, 220)
        border = QColor("#10b981") if self.is_mastered_mode else QColor("#f59e0b")

        p.setPen(QPen(border, 1.5))
        p.setBrush(bg)
        p.drawRoundedRect(x, y, badge_w, badge_h, 6, 6)

        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.drawText(QRectF(x, y, badge_w, badge_h), Qt.AlignmentFlag.AlignCenter, self.mode_tag)

    # ── Mouse Interaction (Seek & Trim Dragging) ──

    def mousePressEvent(self, event):
        if self.duration <= 0:
            return
        w = self.width()
        pos_sec = (event.pos().x() / float(w)) * self.duration

        x_in = int((self.in_point / self.duration) * w)
        x_out = int((self.out_point / self.duration) * w)

        if abs(event.pos().x() - x_in) < 10:
            self._dragging = "in"
        elif abs(event.pos().x() - x_out) < 10:
            self._dragging = "out"
        else:
            self._dragging = "seek"
            self.current_time = max(0.0, min(pos_sec, self.duration))
            self.seek_requested.emit(self.current_time)
            self.update()

    def mouseMoveEvent(self, event):
        if self.duration <= 0 or not self._dragging:
            return
        w = self.width()
        pos_sec = max(0.0, min((event.pos().x() / float(w)) * self.duration, self.duration))

        if self._dragging == "in":
            self.in_point = min(pos_sec, self.out_point - 0.5)
            self.trim_changed.emit(self.in_point, self.out_point)
            self.update()
        elif self._dragging == "out":
            self.out_point = max(pos_sec, self.in_point + 0.5)
            self.trim_changed.emit(self.in_point, self.out_point)
            self.update()
        elif self._dragging == "seek":
            self.current_time = pos_sec
            self.seek_requested.emit(self.current_time)
            self.update()

    def mouseReleaseEvent(self, event):
        self._dragging = None


class StereoLevelMeter(QWidget):
    """High-speed L/R Level Peak & RMS dBFS visual meter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(44)
        self.setMinimumHeight(120)
        self.level_l: float = -60.0  # dBFS
        self.level_r: float = -60.0
        self.peak_db: float = -60.0
        self.bg_color = QColor("#080c14")
        self.border_color = QColor("#1e293b")

    def set_levels(self, l_db: float, r_db: float):
        self.level_l = max(-60.0, min(l_db, 0.0))
        self.level_r = max(-60.0, min(r_db, 0.0))
        self.peak_db = max(self.level_l, self.level_r)
        self.update()

    def apply_theme(self, theme_dict: dict):
        self.bg_color = QColor(theme_dict.get("bg_card", "#080c14"))
        self.border_color = QColor(theme_dict.get("border", "#1e293b"))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        p.fillRect(0, 0, w, h, self.bg_color)
        p.setPen(self.border_color)
        p.drawRect(0, 0, w - 1, h - 1)

        # Header readout
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.setPen(QColor("#10b981") if self.peak_db < -0.5 else QColor("#ef4444"))
        p.drawText(QRectF(0, 2, w, 14), Qt.AlignmentFlag.AlignCenter, f"{self.peak_db:.1f}")

        # Two vertical meters: L and R
        bar_w = 12
        meter_top = 18
        meter_h = h - meter_top - 6

        # Left Bar
        norm_l = (self.level_l + 60.0) / 60.0
        fill_h_l = int(norm_l * meter_h)
        self._draw_meter_bar(p, 6, meter_top, bar_w, meter_h, fill_h_l)

        # Right Bar
        norm_r = (self.level_r + 60.0) / 60.0
        fill_h_r = int(norm_r * meter_h)
        self._draw_meter_bar(p, 24, meter_top, bar_w, meter_h, fill_h_r)

    def _draw_meter_bar(self, p: QPainter, x: int, y: int, w: int, h: int, fill_h: int):
        # Background bar
        p.fillRect(x, y, w, h, QColor(15, 23, 42, 180))

        if fill_h > 0:
            fill_y = y + (h - fill_h)
            grad = QLinearGradient(x, y, x, y + h)
            grad.setColorAt(0.0, QColor("#ef4444"))  # 0 dB (Red)
            grad.setColorAt(0.15, QColor("#f59e0b"))  # -3 dB (Amber)
            grad.setColorAt(0.4, QColor("#10b981"))  # -12 dB (Emerald)
            grad.setColorAt(1.0, QColor("#065f46"))  # -60 dB (Deep green)
            p.fillRect(x, fill_y, w, fill_h, QBrush(grad))


class WaveformEditorPane(QWidget):
    """Complete Top-Right Waveform Container with Controls, Timeline & L/R Meter."""

    seek_requested = pyqtSignal(float)
    ab_mode_toggled = pyqtSignal(bool)  # True = Mastered B, False = Original A

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("waveformEditorPane")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # Left: Canvas
        self.canvas = WaveformCanvas(self)
        self.canvas.seek_requested.connect(self.seek_requested)
        root.addWidget(self.canvas, stretch=1)

        # Right: Stereo Level Meter
        self.meter = StereoLevelMeter(self)
        root.addWidget(self.meter)

    def set_audio_data(self, samples: np.ndarray, sample_rate: int, is_mastered: bool = True):
        self.canvas.set_audio_data(samples, sample_rate, is_mastered)

    def set_mode(self, is_mastered: bool):
        self.canvas.set_mode(is_mastered)

    def set_playback_position(self, sec: float):
        self.canvas.set_playback_position(sec)

    def set_levels(self, l_db: float, r_db: float):
        self.meter.set_levels(l_db, r_db)

    def apply_theme(self, theme_dict: dict):
        self.canvas.apply_theme(theme_dict)
        self.meter.apply_theme(theme_dict)
