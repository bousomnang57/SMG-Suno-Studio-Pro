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
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton
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
    Supports dragging tokens on the logarithmic 20Hz-20kHz grid, mouse-wheel Q-width control,
    dual Before/After FFT heatmaps, and Commercial Reference Curve overlay.
    """

    band_gain_changed = pyqtSignal(int, float)  # (band_index 0..6, new_gain_db)
    band_q_changed = pyqtSignal(int, float)     # (band_index 0..6, new_q)

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
        self._hover_band: Optional[int] = None
        self.spectrum_db: Optional[np.ndarray] = None
        self.after_spectrum_db: Optional[np.ndarray] = None
        self.ref_spectrum_db: Optional[np.ndarray] = None
        self.linear_phase: bool = False
        self.eq_mode_label: str = "Stereo"
        self.is_dark: bool = True
        self.bg_color = QColor("#0b1120")
        self.grid_color = QColor("#1e293b")
        self.text_color = QColor("#94a3b8")

    def set_spectrum_data(self, spec_db: Optional[np.ndarray]):
        """Sets source FFT spectrum profile for background overlay."""
        self.spectrum_db = spec_db
        self.update()

    def set_after_spectrum_data(self, spec_db: Optional[np.ndarray]):
        """Sets post-mastered FFT spectrum profile for Before vs After comparison."""
        self.after_spectrum_db = spec_db
        self.update()

    def set_reference_spectrum_data(self, spec_db: Optional[np.ndarray]):
        """Sets commercial reference track spectral overlay curve."""
        self.ref_spectrum_db = spec_db
        self.update()

    def set_eq_badges(self, linear_phase: bool, eq_mode_label: str):
        self.linear_phase = bool(linear_phase)
        self.eq_mode_label = str(eq_mode_label)
        self.update()

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

    def _draw_spectrum_bars(self, p: QPainter, spec: Optional[np.ndarray], w: int, h: int, fill_col: QColor):
        if spec is None or len(spec) == 0:
            return
        n_bars = len(spec)
        bar_freqs = np.logspace(math.log10(22.0), math.log10(19500.0), n_bars)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fill_col))
        for bi in range(n_bars):
            bx = int(self._freq_to_x(float(bar_freqs[bi]), w))
            by = int(self._gain_to_y(float(spec[bi]), h))
            bh = max(2, (h - 18) - by)
            p.drawRoundedRect(bx - 2, by, 4, bh, 1, 1)

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

        # Draw Background Before & After FFT Spectrum Analyzer Heatmaps
        spec = self.spectrum_db
        if spec is None or len(spec) == 0:
            t_idx = np.linspace(0.0, 1.0, 72)
            spec = -4.0 + 5.5 * np.sin(t_idx * math.pi * 1.1) - 3.5 * (t_idx ** 1.6) + 1.4 * np.cos(t_idx * 18.0)
        self._draw_spectrum_bars(p, spec, w, h, QColor(245, 158, 11, 28) if self.after_spectrum_db is not None else QColor(16, 185, 129, 34))
        if self.after_spectrum_db is not None and len(self.after_spectrum_db) > 0:
            self._draw_spectrum_bars(p, self.after_spectrum_db, w, h, QColor(16, 185, 129, 44))

        # Optional Commercial Reference Track Curve Overlay
        if self.ref_spectrum_db is not None and len(self.ref_spectrum_db) > 2:
            ref_freqs = np.logspace(math.log10(22.0), math.log10(19500.0), len(self.ref_spectrum_db))
            ref_path = QPainterPath()
            for ri, rv in enumerate(self.ref_spectrum_db):
                rx = self._freq_to_x(float(ref_freqs[ri]), w)
                ry = self._gain_to_y(float(rv), h)
                ref_path.moveTo(rx, ry) if ri == 0 else ref_path.lineTo(rx, ry)
            p.setPen(QPen(QColor("#c084fc"), 1.4, Qt.PenStyle.DashLine))
            p.drawPath(ref_path)

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

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(56, 189, 248, 95))
        grad.setColorAt(0.5, QColor(16, 185, 129, 40))
        grad.setColorAt(1.0, QColor(239, 68, 68, 85))
        p.fillPath(fill_path, QBrush(grad))

        p.setPen(QPen(QColor("#38bdf8"), 2.0))
        p.drawPath(curve_path)

        # Top-right Mode & Phase HUD Pill
        badge_txt = f"{'LIN-PHASE' if self.linear_phase else 'MIN-PHASE'} · {self.eq_mode_label.upper()}"
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.setBrush(QColor(15, 23, 42, 200))
        p.setPen(QPen(QColor("#38bdf8" if self.linear_phase else "#334155"), 1))
        b_rect = QRectF(w - 152, 5, 144, 16)
        p.drawRoundedRect(b_rect, 4, 4)
        p.setPen(QColor("#38bdf8" if self.linear_phase else "#94a3b8"))
        p.drawText(b_rect, Qt.AlignmentFlag.AlignCenter, badge_txt)

        # Active Band Telemetry HUD when hovered or dragged
        active_b = self._dragging_band if self._dragging_band is not None else self._hover_band
        if active_b is not None and 0 <= active_b < len(self.bands):
            ab = self.bands[active_b]
            hud = f"B{ab['id']} {ab['name']} · {int(ab['freq'])}Hz · {ab['gain']:+.1f}dB · Q:{ab['q']:.2f} (Wheel=Q)"
            p.setBrush(QColor(15, 23, 42, 220))
            p.setPen(QPen(QColor(ab["color"]), 1))
            h_rect = QRectF(32, 5, 250, 16)
            p.drawRoundedRect(h_rect, 4, 4)
            p.setPen(QColor("#f8fafc"))
            p.drawText(h_rect, Qt.AlignmentFlag.AlignCenter, hud)

        # Draw 7 Numbered FL EQ Tokens
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Black))
        for idx, b in enumerate(self.bands):
            bx = self._freq_to_x(b["freq"], w)
            by = self._gain_to_y(b["gain"], h)
            col = QColor(b["color"])

            p.setBrush(QBrush(QColor(col.red(), col.green(), col.blue(), 80 if idx == active_b else 55)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(bx, by), 11.5 if idx == active_b else 10.0, 11.5 if idx == active_b else 10.0)

            p.setBrush(QBrush(col))
            p.setPen(QPen(QColor("#ffffff"), 1.6 if idx == active_b else 1.2))
            p.drawEllipse(QPointF(bx, by), 7.0, 7.0)

            p.setPen(QColor("#ffffff"))
            p.drawText(QRectF(bx - 7, by - 7, 14, 14), Qt.AlignmentFlag.AlignCenter, str(b["id"]))

    def _hit_test_band(self, pos) -> Optional[int]:
        w, h = self.width(), self.height()
        for idx, b in enumerate(self.bands):
            bx = self._freq_to_x(b["freq"], w)
            by = self._gain_to_y(b["gain"], h)
            if math.hypot(pos.x() - bx, pos.y() - by) <= 13.5:
                return idx
        return None

    def mousePressEvent(self, event):
        hit = self._hit_test_band(event.pos())
        if hit is not None:
            self._dragging_band = hit

    def mouseMoveEvent(self, event):
        if self._dragging_band is not None:
            new_gain = self._y_to_gain(event.pos().y(), self.height())
            self.bands[self._dragging_band]["gain"] = new_gain
            self.band_gain_changed.emit(self._dragging_band, new_gain)
            self.update()
        else:
            hit = self._hit_test_band(event.pos())
            if hit != self._hover_band:
                self._hover_band = hit
                self.update()

    def mouseReleaseEvent(self, event):
        self._dragging_band = None

    def wheelEvent(self, event):
        target = self._dragging_band if self._dragging_band is not None else self._hover_band
        if target is not None and 0 <= target < len(self.bands):
            delta = 0.15 if event.angleDelta().y() > 0 else -0.15
            new_q = round(max(0.4, min(6.0, self.bands[target]["q"] + delta)), 2)
            self.bands[target]["q"] = new_q
            self.band_q_changed.emit(target, new_q)
            self.update()
            event.accept()
            return
        super().wheelEvent(event)


class RibbonTileButton(QPushButton):
    """
    Professional DAW Ribbon Action Tile with a colored rounded-square badge on top
    (e.g. '+', 'F+', 'AI', 'AN', 'T', 'TR', 'EX', 'OD') and a crisp label below,
    matching the reference image's Auto Studio ribbon.
    """

    def __init__(self, badge_text: str, badge_color: str, label_text: str, parent=None):
        super().__init__(parent)
        self.badge_text = badge_text
        self.badge_color = QColor(badge_color)
        self.label_text = label_text
        self.is_dark = True
        self._hovered = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(84, 46)
        self.setToolTip(f"{label_text}")

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self._hovered or self.isDown():
            bg = QColor(56, 189, 248, 28) if self.is_dark else QColor(37, 99, 235, 18)
            border = self.badge_color
            p.setBrush(QBrush(bg))
            p.setPen(QPen(border, 1.2))
            p.drawRoundedRect(1, 1, w - 2, h - 2, 6, 6)

        # Top Colored Rounded-Square Badge
        bw, bh = 22, 18
        bx = (w - bw) / 2.0
        by = 4.0
        badge_rect = QRectF(bx, by, bw, bh)
        p.setBrush(QBrush(self.badge_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(badge_rect, 4, 4)

        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Black))
        p.setPen(QColor("#ffffff"))
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, self.badge_text)

        # Bottom Label
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        txt_col = QColor("#e2e8f0") if self.is_dark else QColor("#1e293b")
        if not self.isEnabled():
            txt_col = QColor("#64748b")
        p.setPen(txt_col)
        lbl_rect = QRectF(2, 24, w - 4, 20)
        p.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, self.label_text)


class StereoPhaseCorrelationMeter(QWidget):
    """
    Visual Stereo Phase Correlation & Mono-Compatibility Bar (-1.0 Out-of-Phase to +1.0 Mono-Safe)
    for Tab 4 (Stereo, Reverb & Trim).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.correlation: float = 0.84
        self.is_dark: bool = True

    def set_correlation(self, corr: float):
        self.correlation = max(-1.0, min(1.0, float(corr)))
        self.update()

    def apply_theme(self, theme_dict: dict):
        self.is_dark = theme_dict.get("is_dark", True)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        bg = QColor("#0f172a") if self.is_dark else QColor("#f1f5f9")
        border = QColor("#334155") if self.is_dark else QColor("#cbd5e1")
        txt_col = QColor("#e2e8f0") if self.is_dark else QColor("#0f172a")

        p.fillRect(0, 0, w, h, bg)
        p.setPen(QPen(border, 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 5, 5)

        # Center 0.0 mark
        mid_x = w // 2
        p.setPen(QPen(border, 1, Qt.PenStyle.DashLine))
        p.drawLine(mid_x, 3, mid_x, h - 3)

        # Draw Correlation Fill Bar from center
        norm = (self.correlation + 1.0) / 2.0  # 0..1
        pos_x = int(28 + norm * (w - 56))
        bar_col = QColor("#16a34a") if self.correlation >= 0.15 else (QColor("#f59e0b") if self.correlation >= -0.1 else QColor("#ef4444"))

        fill_left = min(mid_x, pos_x)
        fill_w = max(4, abs(pos_x - mid_x))
        p.fillRect(fill_left, 6, fill_w, h - 12, bar_col)

        # Marker thumb
        p.setBrush(QBrush(QColor("#ffffff")))
        p.setPen(QPen(bar_col, 2))
        p.drawEllipse(QPointF(pos_x, h / 2.0), 5.0, 5.0)

        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.setPen(txt_col)
        p.drawText(6, h - 9, "-1.0")
        p.drawText(w - 30, h - 9, "+1.0")
        status = f"Phase: {self.correlation:+.2f} (Mono-Safe)" if self.correlation >= 0.0 else f"Phase: {self.correlation:+.2f} (Wide/Cancel)"
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, status)


class MaximusDynamicsWidget(QWidget):
    """
    FL Studio Maximus-inspired 4-Panel Multiband Transfer Curve & Gain-Reduction Visualizer
    (LOW <140Hz, MID 140-3.5kHz, HIGH >3.5kHz, MASTER) with clickable Solo selection.
    """

    band_solo_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(88)
        self.setMaximumHeight(112)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.thresholds = {"LOW": -18.0, "MID": -16.0, "HIGH": -15.0, "MASTER": -1.0}
        self.ratios = {"LOW": 2.8, "MID": 2.2, "HIGH": 2.5, "MASTER": 8.0}
        self.gr_values = {"LOW": 1.4, "MID": 1.1, "HIGH": 0.9, "MASTER": 1.8}
        self.solo_band = "None"
        self.is_dark = True

    def set_telemetry(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        ratios: Optional[Dict[str, float]] = None,
        gr_values: Optional[Dict[str, float]] = None,
        solo_band: Optional[str] = None,
    ):
        if thresholds:
            self.thresholds.update(thresholds)
        if ratios:
            self.ratios.update(ratios)
        if gr_values:
            self.gr_values.update(gr_values)
        if solo_band is not None:
            self.solo_band = solo_band
        self.update()

    def apply_theme(self, theme_dict: dict):
        self.is_dark = theme_dict.get("is_dark", True)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        bg = QColor("#090f1d") if self.is_dark else QColor("#0f172a")
        p.fillRect(0, 0, w, h, bg)

        panels = [
            ("LOW", "#f97316"),
            ("MID", "#22c55e"),
            ("HIGH", "#38bdf8"),
            ("MASTER", "#a855f7"),
        ]
        gap = 6
        card_w = (w - gap * 5) / 4.0
        card_h = h - 8

        for idx, (name, col_hex) in enumerate(panels):
            cx = gap + idx * (card_w + gap)
            cy = 4
            rect = QRectF(cx, cy, card_w, card_h)
            col = QColor(col_hex)
            is_solo = (self.solo_band.upper() == name)

            p.setBrush(QColor(15, 23, 42))
            p.setPen(QPen(col if is_solo else QColor("#334155"), 2.0 if is_solo else 1.0))
            p.drawRoundedRect(rect, 5, 5)

            # Inner graph area (left 78% curve, right 22% GR meter)
            gx, gy = cx + 6, cy + 16
            gw, gh = card_w - 22, card_h - 22
            p.setPen(QPen(QColor("#1e293b"), 1, Qt.PenStyle.DotLine))
            p.drawRect(QRectF(gx, gy, gw, gh))
            p.drawLine(QPointF(gx, gy + gh), QPointF(gx + gw, gy))  # 1:1 unity ref

            # Compression Transfer Curve
            th = float(self.thresholds.get(name, -16.0))
            rat = max(1.0, float(self.ratios.get(name, 2.5)))
            curve = QPainterPath()
            for s_i in range(25):
                in_db = -36.0 + (36.0 * s_i / 24.0)
                out_db = in_db if in_db <= th else th + (in_db - th) / rat
                px = gx + ((in_db + 36.0) / 36.0) * gw
                py = gy + gh - ((out_db + 36.0) / 36.0) * gh
                curve.moveTo(px, py) if s_i == 0 else curve.lineTo(px, py)
            p.setPen(QPen(col, 1.8))
            p.drawPath(curve)

            # Threshold knee marker
            kx = gx + ((th + 36.0) / 36.0) * gw
            ky = gy + gh - ((th + 36.0) / 36.0) * gh
            p.setBrush(col)
            p.setPen(QPen(QColor("#ffffff"), 1))
            p.drawEllipse(QPointF(kx, ky), 3.0, 3.0)

            # Right vertical Gain-Reduction meter bar (drops downward from top)
            gr = min(12.0, abs(float(self.gr_values.get(name, 0.0))))
            mx = cx + card_w - 11
            p.fillRect(QRectF(mx, gy, 6, gh), QColor("#1e293b"))
            gr_h = (gr / 12.0) * gh
            if gr_h > 1.0:
                p.fillRect(QRectF(mx, gy, 6, gr_h), col)

            # Title & GR badge
            p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            p.setPen(col)
            lbl = f"{name} · -{gr:.1f}dB" if not is_solo else f"SOLO {name}"
            p.drawText(QRectF(cx + 4, cy + 2, card_w - 8, 13), Qt.AlignmentFlag.AlignCenter, lbl)

    def mousePressEvent(self, event):
        w = max(1, self.width())
        idx = int(min(3, max(0, (event.pos().x() / w) * 4)))
        names = ["LOW", "MID", "HIGH", "None"]
        chosen = names[idx]
        self.solo_band = "None" if self.solo_band == chosen else chosen
        self.band_solo_requested.emit(self.solo_band)
        self.update()


class FruityLimiterGraphWidget(QWidget):
    """
    FL Studio Fruity Limiter Gain-Reduction & True-Peak Envelope Visualizer.
    Draws input transient peaks (amber), output limiting envelope (emerald),
    true-peak ceiling (red dashed), and gain reduction drop curve (violet).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(76)
        self.setMaximumHeight(96)
        self.telemetry: Dict = {
            "in_env": [-8.0, -5.0, -2.0, 0.5, -3.5, -1.0, 1.2, -4.0, -2.5, -6.0, -1.5, 0.2, -5.0],
            "out_env": [-8.0, -5.0, -2.0, -1.0, -3.5, -1.1, -1.0, -4.0, -2.5, -6.0, -1.5, -1.0, -5.0],
            "gr_curve": [0.0, 0.0, 0.0, -1.5, 0.0, -0.1, -2.2, 0.0, 0.0, 0.0, 0.0, -1.2, 0.0],
            "max_gr_db": 2.2,
            "ceiling_db": -1.0,
        }
        self.is_dark = True

    def set_telemetry(self, telemetry: Dict):
        if telemetry and telemetry.get("gr_curve"):
            self.telemetry = telemetry
            self.update()

    def apply_theme(self, theme_dict: dict):
        self.is_dark = theme_dict.get("is_dark", True)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, QColor("#090f1d"))
        p.setPen(QPen(QColor("#1e293b"), 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 5, 5)

        def _db_to_y(db_val: float) -> float:
            # Top=+3 dB, Bottom=-18 dB
            norm = (3.0 - max(-18.0, min(3.0, db_val))) / 21.0
            return 14.0 + norm * (h - 20.0)

        # Ceiling Dashed Line
        ceil_db = float(self.telemetry.get("ceiling_db", -1.0))
        cy = _db_to_y(ceil_db)
        p.setPen(QPen(QColor("#ef4444"), 1.2, Qt.PenStyle.DashLine))
        p.drawLine(4, int(cy), w - 4, int(cy))

        in_env = self.telemetry.get("in_env") or []
        out_env = self.telemetry.get("out_env") or []
        gr_c = self.telemetry.get("gr_curve") or []
        n = min(len(in_env), len(out_env), len(gr_c))
        if n >= 2:
            xs = np.linspace(6.0, w - 6.0, n)
            in_path, out_path, gr_path = QPainterPath(), QPainterPath(), QPainterPath()
            gr_path.moveTo(xs[0], 14.0)
            for i in range(n):
                iy, oy = _db_to_y(in_env[i]), _db_to_y(out_env[i])
                gy = 14.0 + min(h - 20.0, abs(gr_c[i]) * ((h - 20.0) / 10.0))
                in_path.moveTo(xs[i], iy) if i == 0 else in_path.lineTo(xs[i], iy)
                out_path.moveTo(xs[i], oy) if i == 0 else out_path.lineTo(xs[i], oy)
                gr_path.lineTo(xs[i], gy)
            gr_path.lineTo(xs[-1], 14.0)
            gr_path.closeSubpath()

            p.fillPath(gr_path, QBrush(QColor(168, 85, 247, 70)))
            p.setPen(QPen(QColor("#f59e0b"), 1.2))
            p.drawPath(in_path)
            p.setPen(QPen(QColor("#10b981"), 1.8))
            p.drawPath(out_path)
            p.setPen(QPen(QColor("#c084fc"), 1.5))
            p.drawLine(QPointF(xs[0], 14.0), QPointF(xs[-1], 14.0))

        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.setPen(QColor("#94a3b8"))
        max_gr = float(self.telemetry.get("max_gr_db", 0.0))
        p.drawText(8, 12, f"FRUITY 4x LOOKAHEAD LIMITER · Ceiling: {ceil_db:.1f} dBTP · Max GR: -{max_gr:.2f} dB")


class WaveCandyVectorscopeWidget(QWidget):
    """
    FL Studio Wave Candy Goniometer / Polar Vectorscope + Loudness Range (LRA / Crest) Meter.
    Visualizes real Mid/Side Lissajous stereo field during analysis and after mastering.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(112, 112)
        self.points: List[List[float]] = []
        self.lra_lu: float = 4.2
        self.crest_db: float = 9.8
        self.is_dark: bool = True

    def set_telemetry(self, telemetry: Dict):
        if not telemetry:
            return
        self.points = telemetry.get("vectorscope_points") or []
        self.lra_lu = float(telemetry.get("lra_lu", self.lra_lu))
        self.crest_db = float(telemetry.get("crest_db", self.crest_db))
        self.update()

    def apply_theme(self, theme_dict: dict):
        self.is_dark = theme_dict.get("is_dark", True)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, QColor("#090f1d"))
        p.setPen(QPen(QColor("#334155"), 1))
        p.drawRoundedRect(0, 0, w - 1, h - 1, 6, 6)

        cx, cy = w / 2.0, (h - 14) / 2.0
        rad = min(w, h - 18) * 0.42

        # Polar circle + L/R diagonal grid
        p.setPen(QPen(QColor("#1e293b"), 1, Qt.PenStyle.DotLine))
        p.drawEllipse(QPointF(cx, cy), rad, rad)
        p.drawLine(QPointF(cx - rad, cy - rad), QPointF(cx + rad, cy + rad))
        p.drawLine(QPointF(cx - rad, cy + rad), QPointF(cx + rad, cy - rad))
        p.drawLine(QPointF(cx, cy - rad), QPointF(cx, cy + rad))

        # Vectorscope phosphor trace (s=horizontal width, m=vertical energy)
        pts = self.points
        if not pts:
            t = np.linspace(0, 2 * math.pi, 48)
            pts = [[round(0.32 * math.sin(a * 3), 3), round(0.75 * math.cos(a), 3)] for a in t]

        p.setPen(QPen(QColor(56, 189, 248, 175), 1.4))
        for i in range(len(pts)):
            sx, my = pts[i][0], pts[i][1]
            px = cx + sx * rad * 0.92
            py = cy - my * rad * 0.92
            p.drawPoint(QPointF(px, py))
            if i > 0:
                px0 = cx + pts[i - 1][0] * rad * 0.92
                py0 = cy - pts[i - 1][1] * rad * 0.92
                if math.hypot(px - px0, py - py0) < rad * 0.85:
                    p.drawLine(QPointF(px0, py0), QPointF(px, py))

        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.setPen(QColor("#64748b"))
        p.drawText(4, 10, "L")
        p.drawText(w - 10, 10, "R")
        p.setPen(QColor("#38bdf8"))
        p.drawText(QRectF(0, h - 14, w, 13), Qt.AlignmentFlag.AlignCenter, f"LRA {self.lra_lu:.1f} · DR {self.crest_db:.1f}")

