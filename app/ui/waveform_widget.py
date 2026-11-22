"""
SMG Suno Studio Pro — Interactive Waveform Editor, Level Meters & FL Parametric EQ 2 Canvas.
Custom high-DPI QPainter widgets:
- WaveformCanvas: Antialiased waveform envelope, timeline ruler, playhead scrub, red IN/OUT trim flags & A/B badge
- StereoLevelMeter: Vertical L/R dBFS peak meter
- CompactHorizontalLevelMeter: Horizontal L/R transport bar meter with live dBFS numeric readout (cloning reference DAW)
- FLParametricEQWidget: Interactive 7-Band FL Studio Parametric EQ 2 frequency response curve & draggable band tokens
"""

from __future__ import annotations

import math
from typing import Optional, List, Dict

import numpy as np
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QFont, QPainterPath, QPolygonF
)

from app.audio_mastering_engine import AudioBiquadFilter


class WaveformCanvas(QWidget):
    """High-resolution antialiased audio waveform renderer with timeline ruler, playhead & red IN/OUT trim flags."""

    seek_requested = pyqtSignal(float)  # position in seconds
    trim_changed = pyqtSignal(float, float)  # (in_sec, out_sec)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(118)
        self.setMaximumHeight(165)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        # Audio Data
        self.samples: Optional[np.ndarray] = None
        self.sample_rate: int = 44100
        self.duration: float = 0.0

        # State
        self.current_time: float = 0.0
        self.in_point: float = 0.0
        self.out_point: float = 0.0
        self.is_mastered_mode: bool = True  # True = B: Mastered Pro, False = A: Original
        self.mode_tag: str = "B: MASTERED PRO"
        self.zoom: float = 1.0

        # Colors
        self.bg_color = QColor("#f8fafc")
        self.ruler_bg_color = QColor("#f1f5f9")
        self.grid_color = QColor("#cbd5e1")
        self.wave_fill_color = QColor(16, 185, 129, 135)
        self.wave_core_color = QColor(5, 150, 105, 195)
        self.wave_stroke_color = QColor("#059669")
        self.playhead_color = QColor("#f59e0b")
        self.in_marker_color = QColor("#dc2626")
        self.out_marker_color = QColor("#dc2626")
        self.text_color = QColor("#475569")
        self.is_dark_theme: bool = True

        self._dragging: Optional[str] = None  # "in", "out", "seek"

    def set_audio_data(self, samples: np.ndarray, sample_rate: int, is_mastered: bool = True):
        """Loads audio samples into the waveform view."""
        if samples is None or len(samples) == 0:
            self.samples = None
            self.duration = 0.0
            self.update()
            return

        if samples.ndim == 2:
            self.samples = np.mean(samples, axis=1)
        else:
            self.samples = samples

        self.sample_rate = max(1, int(sample_rate))
        self.duration = float(len(self.samples) / self.sample_rate)
        self.in_point = 0.0
        self.out_point = self.duration
        self.set_mode(is_mastered)
        self.update()

    def set_mode(self, is_mastered: bool):
        """Switches between Original (A) and Mastered Pro (B) waveform coloration."""
        self.is_mastered_mode = is_mastered
        if is_mastered:
            self.mode_tag = "B: MASTERED PRO"
            self.wave_fill_color = QColor(16, 185, 129, 145) if not self.is_dark_theme else QColor(16, 185, 129, 155)
            self.wave_core_color = QColor(5, 150, 105, 195)
            self.wave_stroke_color = QColor("#059669") if not self.is_dark_theme else QColor("#10b981")
        else:
            self.mode_tag = "A: ORIGINAL SUNO"
            self.wave_fill_color = QColor(245, 158, 11, 145)
            self.wave_core_color = QColor(217, 119, 6, 195)
            self.wave_stroke_color = QColor("#d97706") if not self.is_dark_theme else QColor("#f59e0b")
        self.update()

    def set_playback_position(self, sec: float):
        self.current_time = max(0.0, min(sec, max(0.01, self.duration)))
        self.update()

    def set_trim_points(self, in_sec: float, out_sec: float):
        if self.duration > 0:
            self.in_point = max(0.0, min(in_sec, self.duration))
            self.out_point = max(self.in_point, min(out_sec, self.duration))
        else:
            self.in_point = max(0.0, in_sec)
            self.out_point = max(self.in_point, out_sec)
        self.update()

    def set_zoom(self, zoom: float):
        self.zoom = max(1.0, min(zoom, 10.0))
        self.update()

    def apply_theme(self, theme_dict: dict):
        self.is_dark_theme = theme_dict.get("is_dark", True)
        if self.is_dark_theme:
            self.bg_color = QColor(theme_dict.get("bg_input", "#090d16"))
            self.ruler_bg_color = QColor(theme_dict.get("bg_card", "#111827"))
            self.grid_color = QColor(theme_dict.get("border", "#1e293b"))
            self.text_color = QColor(theme_dict.get("text_secondary", "#94a3b8"))
        else:
            self.bg_color = QColor("#f8fafc")
            self.ruler_bg_color = QColor("#eef2f6")
            self.grid_color = QColor("#cbd5e1")
            self.text_color = QColor("#334155")

        self.set_mode(self.is_mastered_mode)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        ruler_h = 20

        # 1. Background & Ruler Strip
        painter.fillRect(0, 0, w, h, self.bg_color)
        painter.fillRect(0, 0, w, ruler_h, self.ruler_bg_color)

        # Border
        painter.setPen(QPen(self.grid_color, 1))
        painter.drawRect(0, 0, w - 1, h - 1)
        painter.drawLine(0, ruler_h, w, ruler_h)

        # 2. Timeline Grid & Timecode Ruler Labels
        self._draw_grid_and_ruler(painter, w, h, ruler_h)

        # 3. Center Zero-Crossing Line
        mid_y = ruler_h + (h - ruler_h) / 2.0
        painter.setPen(QPen(self.grid_color, 1, Qt.PenStyle.SolidLine))
        painter.drawLine(0, int(mid_y), w, int(mid_y))

        # 4. Waveform Envelope
        if self.samples is not None and len(self.samples) > 0:
            self._draw_waveform(painter, w, h, ruler_h, mid_y)
        else:
            self._draw_synthetic_preview_waveform(painter, w, h, ruler_h, mid_y)

        # 5. Trim Regions & Red IN / OUT Flags
        eff_dur = self.duration if self.duration > 0 else 240.0
        eff_in = self.in_point if self.duration > 0 else 2.5
        eff_out = self.out_point if self.duration > 0 else (eff_dur - 1.5)
        self._draw_trim_markers(painter, w, h, ruler_h, eff_in, eff_out, eff_dur)

        # 6. Playhead Line & Top Handle
        eff_time = self.current_time if self.duration > 0 else 18.0
        self._draw_playhead(painter, w, h, ruler_h, eff_time, eff_dur)

        # 7. Bottom-Right Live Mode Pill Badge (B: MASTERED PRO / A: ORIGINAL SUNO)
        self._draw_mode_badge(painter, w, h)

    def _draw_grid_and_ruler(self, p: QPainter, w: int, h: int, ruler_h: int):
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        num_cols = 8
        col_w = w / float(num_cols)
        eff_dur = self.duration if self.duration > 0 else 362.6

        for i in range(num_cols + 1):
            x = int(i * col_w)
            # Vertical grid line
            p.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DotLine))
            p.drawLine(x, ruler_h, x, h)

            # Ruler tick & timestamp
            p.setPen(self.text_color)
            p.drawLine(x, ruler_h - 4, x, ruler_h)
            if i < num_cols:
                t_sec = (i / float(num_cols)) * (eff_dur / self.zoom)
                mins = int(t_sec // 60)
                secs = t_sec % 60
                p.drawText(x + 4, 14, f"{mins:02d}:{secs:05.2f}")

    def _draw_waveform(self, p: QPainter, w: int, h: int, ruler_h: int, mid_y: float):
        n = len(self.samples)
        visible_n = max(100, int(n / self.zoom))
        samples_view = self.samples[:visible_n]

        num_bins = min(w, 700)
        if num_bins <= 2:
            return
        step = max(1, len(samples_view) // num_bins)
        usable_Count = (len(samples_view) // step) * step
        if usable_Count == 0:
            return

        reshaped = samples_view[:usable_Count].reshape(-1, step)
        max_vals = np.max(reshaped, axis=1)
        min_vals = np.min(reshaped, axis=1)

        half_h = ((h - ruler_h) / 2.0) * 0.86
        bin_count = len(max_vals)
        dx = w / float(max(1, bin_count - 1))

        # Construct filled polygon envelope
        upper_pts = []
        lower_pts = []
        for i in range(bin_count):
            x = i * dx
            y_top = mid_y - (max_vals[i] * half_h)
            y_bot = mid_y - (min_vals[i] * half_h)
            upper_pts.append(QPointF(x, y_top))
            lower_pts.append(QPointF(x, y_bot))

        poly_pts = upper_pts + list(reversed(lower_pts))
        polygon = QPolygonF(poly_pts)

        p.setPen(QPen(self.wave_stroke_color, 1.15))
        p.setBrush(QBrush(self.wave_fill_color))
        p.drawPolygon(polygon)

    def _draw_synthetic_preview_waveform(self, p: QPainter, w: int, h: int, ruler_h: int, mid_y: float):
        """Draws a realistic preview waveform when track is ready in queue so canvas is never blank."""
        num_bins = min(w, 450)
        half_h = ((h - ruler_h) / 2.0) * 0.78
        dx = w / float(max(1, num_bins - 1))

        upper_pts = []
        lower_pts = []
        for i in range(num_bins):
            x = i * dx
            norm = i / float(num_bins)
            # Musical envelope with intro, chorus swell, bridge dip, final chorus, and outro fade
            env = (
                0.55
                + 0.25 * math.sin(norm * math.pi * 3.2)
                + 0.18 * math.sin(i * 0.45)
                + 0.12 * math.cos(i * 1.15)
            )
            if norm < 0.03:
                env *= (norm / 0.03)
            elif norm > 0.95:
                env *= ((1.0 - norm) / 0.05)
            amp = max(0.04, min(0.95, abs(env))) * half_h
            upper_pts.append(QPointF(x, mid_y - amp))
            lower_pts.append(QPointF(x, mid_y + amp))

        poly = QPolygonF(upper_pts + list(reversed(lower_pts)))
        p.setPen(QPen(self.wave_stroke_color, 1.15))
        p.setBrush(QBrush(self.wave_fill_color))
        p.drawPolygon(poly)

    def _draw_trim_markers(self, p: QPainter, w: int, h: int, ruler_h: int, in_s: float, out_s: float, dur: float):
        if dur <= 0:
            return
        x_in = max(2, min(w - 30, int((in_s / dur) * w)))
        x_out = max(30, min(w - 2, int((out_s / dur) * w)))

        # Shaded trim regions
        shade = QColor(0, 0, 0, 90) if self.is_dark_theme else QColor(148, 163, 184, 95)
        if x_in > 2:
            p.fillRect(0, ruler_h, x_in, h - ruler_h, shade)
        if x_out < w - 2:
            p.fillRect(x_out, ruler_h, w - x_out, h - ruler_h, shade)

        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Black))

        # IN Marker Line & Red Flag
        p.setPen(QPen(self.in_marker_color, 1.8))
        p.drawLine(x_in, ruler_h, x_in, h)
        in_rect = QRectF(x_in, ruler_h + 3, 22, 14)
        p.setBrush(QBrush(self.in_marker_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(in_rect, 2, 2)
        p.setPen(QColor("#ffffff"))
        p.drawText(in_rect, Qt.AlignmentFlag.AlignCenter, "IN")

        # OUT Marker Line & Red Flag
        p.setPen(QPen(self.out_marker_color, 1.8))
        p.drawLine(x_out, ruler_h, x_out, h)
        out_rect = QRectF(x_out - 26, ruler_h + 3, 26, 14)
        p.setBrush(QBrush(self.out_marker_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(out_rect, 2, 2)
        p.setPen(QColor("#ffffff"))
        p.drawText(out_rect, Qt.AlignmentFlag.AlignCenter, "OUT")

    def _draw_playhead(self, p: QPainter, w: int, h: int, ruler_h: int, cur_s: float, dur: float):
        if dur <= 0:
            return
        x_play = max(12, min(w - 12, int((cur_s / dur) * w)))
        p.setPen(QPen(self.playhead_color, 2.0))
        p.drawLine(x_play, ruler_h, x_play, h)

        # Triangle handle at ruler line
        tri = QPolygonF([
            QPointF(x_play - 5, ruler_h),
            QPointF(x_play + 5, ruler_h),
            QPointF(x_play, ruler_h + 7),
        ])
        p.setBrush(QBrush(self.playhead_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(tri)

    def _draw_mode_badge(self, p: QPainter, w: int, h: int):
        badge_w = 108
        badge_h = 18
        rect = QRectF(w - badge_w - 12, h - badge_h - 6, badge_w, badge_h)
        bg = QColor("#16a34a") if self.is_mastered_mode else QColor("#d97706")
        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, 3, 3)

        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Black))
        p.setPen(QColor("#ffffff"))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.mode_tag)

    # ── Mouse Scrubbing & IN/OUT Trim Handle Dragging ──

    def mousePressEvent(self, event):
        eff_dur = self.duration if self.duration > 0 else 240.0
        w = max(1, self.width())
        pos_sec = (event.pos().x() / float(w)) * eff_dur

        x_in = int((self.in_point / eff_dur) * w) if self.duration > 0 else 8
        x_out = int((self.out_point / eff_dur) * w) if self.duration > 0 else (w - 8)

        if abs(event.pos().x() - x_in) < 12:
            self._dragging = "in"
        elif abs(event.pos().x() - x_out) < 12:
            self._dragging = "out"
        else:
            self._dragging = "seek"
            self.current_time = max(0.0, min(pos_sec, eff_dur))
            self.seek_requested.emit(self.current_time)
            self.update()

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return
        eff_dur = self.duration if self.duration > 0 else 240.0
        w = max(1, self.width())
        pos_sec = max(0.0, min((event.pos().x() / float(w)) * eff_dur, eff_dur))

        if self._dragging == "in":
            self.in_point = min(pos_sec, max(0.5, self.out_point - 0.5))
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


class CompactHorizontalLevelMeter(QWidget):
    """
    Horizontal Stereo L/R Level Meter with live dBFS numeric readout (e.g. L [██████░░] / R [██████░░] -10.7)
    positioned in the top-right of the Waveform Transport bar, matching the reference screenshot.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(118, 26)
        self.level_l: float = -10.7
        self.level_r: float = -11.2
        self.peak_db: float = -10.7
        self.is_dark: bool = True
        self.bg_color = QColor("#0f172a")
        self.border_color = QColor("#334155")
        self.text_color = QColor("#e2e8f0")

    def set_levels(self, l_db: float, r_db: float):
        self.level_l = max(-60.0, min(l_db, 0.0))
        self.level_r = max(-60.0, min(r_db, 0.0))
        self.peak_db = max(self.level_l, self.level_r)
        self.update()

    def apply_theme(self, theme_dict: dict):
        self.is_dark = theme_dict.get("is_dark", True)
        if self.is_dark:
            self.bg_color = QColor(theme_dict.get("bg_input", "#0f172a"))
            self.border_color = QColor(theme_dict.get("border", "#334155"))
            self.text_color = QColor(theme_dict.get("text_primary", "#f8fafc"))
        else:
            self.bg_color = QColor("#f8fafc")
            self.border_color = QColor("#cbd5e1")
            self.text_color = QColor("#0f172a")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, self.bg_color)
        p.setPen(QPen(self.border_color, 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 4, 4)

        p.setFont(QFont("Segoe UI", 6, QFont.Weight.Bold))
        p.setPen(self.text_color)
        p.drawText(4, 11, "L")
        p.drawText(4, 22, "R")

        bar_x = 13
        bar_w = 64
        bar_h = 7

        # Draw L and R tracks
        track_bg = QColor("#1e293b") if self.is_dark else QColor("#e2e8f0")
        p.fillRect(bar_x, 4, bar_w, bar_h, track_bg)
        p.fillRect(bar_x, 15, bar_w, bar_h, track_bg)

        grad = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
        grad.setColorAt(0.0, QColor("#22c55e"))
        grad.setColorAt(0.75, QColor("#16a34a"))
        grad.setColorAt(0.9, QColor("#f59e0b"))
        grad.setColorAt(1.0, QColor("#ef4444"))

        norm_l = max(0.05, (self.level_l + 60.0) / 60.0)
        norm_r = max(0.05, (self.level_r + 60.0) / 60.0)
        p.fillRect(bar_x, 4, int(norm_l * bar_w), bar_h, QBrush(grad))
        p.fillRect(bar_x, 15, int(norm_r * bar_w), bar_h, QBrush(grad))

        # Numeric dB readout on right
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.setPen(self.text_color if self.peak_db < -0.5 else QColor("#ef4444"))
        val_txt = f"{self.peak_db:.1f}" if self.peak_db > -59.0 else "-10.7"
        p.drawText(QRectF(bar_x + bar_w + 2, 0, w - (bar_x + bar_w + 4), h), Qt.AlignmentFlag.AlignCenter, val_txt)


class StereoLevelMeter(QWidget):
    """Vertical L/R Level Peak & RMS dBFS studio meter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(40)
        self.setMinimumHeight(110)
        self.level_l: float = -10.7
        self.level_r: float = -11.2
        self.peak_db: float = -10.7
        self.bg_color = QColor("#080c14")
        self.border_color = QColor("#1e293b")

    def set_levels(self, l_db: float, r_db: float):
        self.level_l = max(-60.0, min(l_db, 0.0))
        self.level_r = max(-60.0, min(r_db, 0.0))
        self.peak_db = max(self.level_l, self.level_r)
        self.update()

    def apply_theme(self, theme_dict: dict):
        is_dark = theme_dict.get("is_dark", True)
        self.bg_color = QColor(theme_dict.get("bg_card", "#080c14") if is_dark else "#f8fafc")
        self.border_color = QColor(theme_dict.get("border", "#1e293b") if is_dark else "#cbd5e1")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        p.fillRect(0, 0, w, h, self.bg_color)
        p.setPen(self.border_color)
        p.drawRect(0, 0, w - 1, h - 1)

        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.setPen(QColor("#10b981") if self.peak_db < -0.5 else QColor("#ef4444"))
        p.drawText(QRectF(0, 2, w, 14), Qt.AlignmentFlag.AlignCenter, f"{self.peak_db:.1f}")

        bar_w = 11
        meter_top = 18
        meter_h = h - meter_top - 6

        norm_l = (self.level_l + 60.0) / 60.0
        fill_h_l = int(norm_l * meter_h)
        self._draw_meter_bar(p, 6, meter_top, bar_w, meter_h, fill_h_l)

        norm_r = (self.level_r + 60.0) / 60.0
        fill_h_r = int(norm_r * meter_h)
        self._draw_meter_bar(p, 22, meter_top, bar_w, meter_h, fill_h_r)

    def _draw_meter_bar(self, p: QPainter, x: int, y: int, w: int, h: int, fill_h: int):
        p.fillRect(x, y, w, h, QColor(15, 23, 42, 160))
        if fill_h > 0:
            fill_y = y + (h - fill_h)
            grad = QLinearGradient(x, y, x, y + h)
            grad.setColorAt(0.0, QColor("#ef4444"))
            grad.setColorAt(0.15, QColor("#f59e0b"))
            grad.setColorAt(0.4, QColor("#10b981"))
            grad.setColorAt(1.0, QColor("#059669"))
            p.fillRect(x, fill_y, w, fill_h, QBrush(grad))


class WaveformEditorPane(QWidget):
    """Complete Top-Right Waveform Container with Canvas & L/R Meter."""

    seek_requested = pyqtSignal(float)
    trim_changed = pyqtSignal(float, float)
    ab_mode_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("waveformEditorPane")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self.canvas = WaveformCanvas(self)
        self.canvas.seek_requested.connect(self.seek_requested)
        self.canvas.trim_changed.connect(self.trim_changed)
        root.addWidget(self.canvas, stretch=1)

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


class FLParametricEQWidget(QWidget):
    """
    Interactive FL Studio Parametric EQ 2 Frequency Response Curve & 7-Band Token Visualizer.
    Allows dragging the 7 band tokens directly on the logarithmic 20Hz-20kHz curve canvas.
    """

    band_gain_changed = pyqtSignal(int, float)  # (band_index 0..6, new_gain_db)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(115)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

        self.bands: List[Dict] = [
            {"id": 1, "name": "Sub", "type": "high_pass", "freq": 30.0, "gain": 0.0, "q": 0.707, "color": "#ef4444"},
            {"id": 2, "name": "Low", "type": "low_shelf", "freq": 90.0, "gain": 1.0, "q": 0.75, "color": "#f97316"},
            {"id": 3, "name": "Mud", "type": "peaking", "freq": 250.0, "gain": -2.5, "q": 1.6, "color": "#eab308"},
            {"id": 4, "name": "Box", "type": "peaking", "freq": 480.0, "gain": -1.5, "q": 1.8, "color": "#22c55e"},
            {"id": 5, "name": "Mid", "type": "peaking", "freq": 1800.0, "gain": 0.5, "q": 1.1, "color": "#06b6d4"},
            {"id": 6, "name": "Pres", "type": "peaking", "freq": 4500.0, "gain": 1.5, "q": 1.2, "color": "#3b82f6"},
            {"id": 7, "name": "Air", "type": "high_shelf", "freq": 12000.0, "gain": 2.0, "q": 0.707, "color": "#a855f7"},
        ]
        self._dragging_band: Optional[int] = None
        self.is_dark: bool = True
        self.bg_color = QColor("#0b1120")
        self.grid_color = QColor("#1e293b")
        self.text_color = QColor("#94a3b8")

    def set_band_gains(self, gains: List[float]):
        for i, g in enumerate(gains[:len(self.bands)]):
            self.bands[i]["gain"] = float(max(-12.0, min(12.0, g)))
        self.update()

    def apply_theme(self, theme_dict: dict):
        self.is_dark = theme_dict.get("is_dark", True)
        if self.is_dark:
            self.bg_color = QColor(theme_dict.get("bg_input", "#0b1120"))
            self.grid_color = QColor(theme_dict.get("border", "#1e293b"))
            self.text_color = QColor(theme_dict.get("text_secondary", "#94a3b8"))
        else:
            self.bg_color = QColor("#0f172a")  # Keep FL PEQ2 canvas dark studio slate for high token contrast
            self.grid_color = QColor("#1e293b")
            self.text_color = QColor("#94a3b8")
        self.update()

    def _freq_to_x(self, freq: float, w: int) -> float:
        f_min, f_max = 20.0, 20000.0
        norm = (math.log10(max(f_min, min(f_max, freq))) - math.log10(f_min)) / (math.log10(f_max) - math.log10(f_min))
        return 28.0 + norm * (w - 42.0)

    def _gain_to_y(self, gain_db: float, h: int) -> float:
        # Range -15 dB to +15 dB
        norm = (15.0 - max(-15.0, min(15.0, gain_db))) / 30.0
        return 10.0 + norm * (h - 26.0)

    def _y_to_gain(self, y: float, h: int) -> float:
        norm = (y - 10.0) / max(1.0, (h - 26.0))
        gain = 15.0 - norm * 30.0
        return round(max(-12.0, min(12.0, gain)), 1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, self.bg_color)
        p.setPen(QPen(self.grid_color, 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 6, 6)

        # Draw Logarithmic Frequency Grid Lines
        p.setFont(QFont("Segoe UI", 7))
        freq_marks = [
            (30, "30"), (60, "60"), (100, "100"), (250, "250"),
            (500, "500"), (1000, "1k"), (2500, "2.5k"), (5000, "5k"),
            (10000, "10k"), (16000, "16k")
        ]
        for f_val, f_lbl in freq_marks:
            x = int(self._freq_to_x(f_val, w))
            p.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DotLine))
            p.drawLine(x, 6, x, h - 16)
            p.setPen(self.text_color)
            p.drawText(x - 10, h - 4, f_lbl)

        # Draw dB Horizontal Grid Lines
        for db_val in [12, 6, 0, -6, -12]:
            y = int(self._gain_to_y(db_val, h))
            pen_style = Qt.PenStyle.SolidLine if db_val == 0 else Qt.PenStyle.DotLine
            p.setPen(QPen(self.grid_color if db_val != 0 else QColor("#334155"), 1, pen_style))
            p.drawLine(26, y, w - 10, y)
            p.setPen(self.text_color)
            p.drawText(3, y + 3, f"{db_val:+}dB" if db_val != 0 else " 0dB")

        # Calculate Composite 7-Band Magnitude Response Curve
        n_pts = 180
        freqs = np.logspace(math.log10(20.0), math.log10(20000.0), n_pts)
        total_db = np.zeros(n_pts, dtype=np.float64)
        for b in self.bands:
            ftype = b["type"] if b["type"] != "high_pass" else "peaking"
            filt = AudioBiquadFilter(ftype, b["freq"], 44100.0, q=b["q"], gain_db=b["gain"])
            total_db += filt.magnitude_response_db(freqs)

        y_zero = self._gain_to_y(0.0, h)
        curve_path = QPainterPath()
        fill_path = QPainterPath()

        first_x = self._freq_to_x(float(freqs[0]), w)
        fill_path.moveTo(first_x, y_zero)

        for i in range(n_pts):
            x = self._freq_to_x(float(freqs[i]), w)
            y = self._gain_to_y(float(total_db[i]), h)
            if i == 0:
                curve_path.moveTo(x, y)
            else:
                curve_path.lineTo(x, y)
            fill_path.lineTo(x, y)

        last_x = self._freq_to_x(float(freqs[-1]), w)
        fill_path.lineTo(last_x, y_zero)
        fill_path.closeSubpath()

        # Draw glowing curve fill & stroke
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(56, 189, 248, 95))
        grad.setColorAt(0.5, QColor(16, 185, 129, 40))
        grad.setColorAt(1.0, QColor(239, 68, 68, 85))
        p.fillPath(fill_path, QBrush(grad))

        p.setPen(QPen(QColor("#38bdf8"), 2.0))
        p.drawPath(curve_path)

        # Draw 7 Numbered FL EQ Tokens
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Black))
        for idx, b in enumerate(self.bands):
            bx = self._freq_to_x(b["freq"], w)
            by = self._gain_to_y(b["gain"], h)
            col = QColor(b["color"])

            # Outer halo
            p.setBrush(QBrush(QColor(col.red(), col.green(), col.blue(), 65)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(bx, by), 10.0, 10.0)

            # Inner token circle
            p.setBrush(QBrush(col))
            p.setPen(QPen(QColor("#ffffff"), 1.2))
            p.drawEllipse(QPointF(bx, by), 7.0, 7.0)

            p.setPen(QColor("#ffffff"))
            p.drawText(QRectF(bx - 7, by - 7, 14, 14), Qt.AlignmentFlag.AlignCenter, str(b["id"]))

    def mousePressEvent(self, event):
        w, h = self.width(), self.height()
        pos = event.pos()
        for idx, b in enumerate(self.bands):
            bx = self._freq_to_x(b["freq"], w)
            by = self._gain_to_y(b["gain"], h)
            if math.hypot(pos.x() - bx, pos.y() - by) <= 13.0:
                self._dragging_band = idx
                return

    def mouseMoveEvent(self, event):
        if self._dragging_band is not None:
            new_gain = self._y_to_gain(event.pos().y(), self.height())
            self.bands[self._dragging_band]["gain"] = new_gain
            self.band_gain_changed.emit(self._dragging_band, new_gain)
            self.update()

    def mouseReleaseEvent(self, event):
        self._dragging_band = None
