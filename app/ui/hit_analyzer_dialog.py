"""
Hit Potential & AI Vocal Safety Inspector Dialog.
Presents interactive gauges, energy curve breakdown, and actionable hit recommendations.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QWidget, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from app.hit_analyzer import HitAnalyzer
from app.ui.styles import get_theme


class HitAnalyzerDialog(QDialog):
    def __init__(self, lyrics: str, bpm: int = 120, theme_or_dark=True, parent=None):
        super().__init__(parent)
        self.lyrics = lyrics
        self.bpm = bpm
        self.theme = get_theme(theme_or_dark)
        self.is_dark = self.theme.get("is_dark", True)
        self.setWindowTitle("🌟 Commercial Hit Potential & AI Vocal Safety Inspector")
        self.setFixedSize(620, 560)
        self._init_ui()

    def _init_ui(self):
        analysis = HitAnalyzer.analyze(self.lyrics, self.bpm)
        t = getattr(self, "theme", get_theme(self.is_dark))
        is_dark = t.get("is_dark", True)

        bg_col = t["bg_window"]
        card_bg = t["bg_card"]
        border_col = t["border"]
        text_primary = t["text_primary"]
        text_muted = t["text_muted"]

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_col};
                color: {text_primary};
                font-family: 'Segoe UI', sans-serif;
            }}
            QFrame#card {{
                background-color: {card_bg};
                border: 1px solid {border_col};
                border-radius: 8px;
                padding: 10px;
            }}
            QLabel {{
                background: transparent;
                color: {text_primary};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # ── 1. Header with Big Composite Hit Score ──
        score_card = QFrame()
        score_card.setObjectName("card")
        score_layout = QHBoxLayout(score_card)

        # Left: Score badge
        badge_box = QVBoxLayout()
        score_val = analysis["hit_score"]
        lbl_num = QLabel(f"{score_val}%")
        lbl_num.setStyleSheet(f"font-size: 34px; font-weight: 900; color: {t['accent']};")
        lbl_badge = QLabel("Commercial Hit Index")
        lbl_badge.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {text_muted};")
        badge_box.addWidget(lbl_num)
        badge_box.addWidget(lbl_badge)
        score_layout.addLayout(badge_box)

        score_layout.addSpacing(16)

        # Right: Sub-scores
        sub_layout = QGridLayout()
        sub_layout.setVerticalSpacing(4)
        sub_layout.setHorizontalSpacing(10)

        # Hook Score
        sub_layout.addWidget(QLabel("🎯 Hook & Earworm Retention:"), 0, 0)
        lbl_h = QLabel(f"{analysis['hook_score']}%")
        lbl_h.setStyleSheet("font-weight: 800; color: #38bdf8;")
        sub_layout.addWidget(lbl_h, 0, 1)

        # AI Vocal Safety
        sub_layout.addWidget(QLabel("🎙️ Suno AI Vocal Safety:"), 1, 0)
        lbl_s = QLabel(f"{analysis['safety_score']}% ({analysis['safety_grade']})")
        lbl_s.setStyleSheet(f"font-weight: 800; color: {analysis['safety_color']};")
        sub_layout.addWidget(lbl_s, 1, 1)

        # Meter Balance
        sub_layout.addWidget(QLabel("⚖️ Syllable Cadence Balance:"), 2, 0)
        lbl_m = QLabel(f"{analysis['meter_score']}% (Avg {analysis['avg_syllables']}s/line)")
        lbl_m.setStyleSheet("font-weight: 800; color: #10b981;")
        sub_layout.addWidget(lbl_m, 2, 1)

        score_layout.addLayout(sub_layout)
        layout.addWidget(score_card)

        # ── 2. Dynamic Energy Curve ──
        energy_card = QFrame()
        energy_card.setObjectName("card")
        e_layout = QVBoxLayout(energy_card)
        e_layout.setSpacing(4)

        lbl_e_title = QLabel("📈 Song Dynamic Energy & Arrangement Curve")
        lbl_e_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #a855f7;")
        e_layout.addWidget(lbl_e_title)

        sec_bars = QHBoxLayout()
        sec_bars.setSpacing(6)
        sections = analysis.get("sections", [])
        if sections:
            for s in sections[:7]:
                col_box = QVBoxLayout()
                col_box.setSpacing(2)
                col_box.setAlignment(Qt.AlignmentFlag.AlignBottom)

                val = s["energy"]
                bar = QFrame()
                bar.setFixedWidth(45)
                bar.setFixedHeight(int(max(15, val * 0.65)))
                bar.setStyleSheet(f"background: qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 #4f46e5, stop:1 #ec4899); border-radius: 4px;")

                lbl_val = QLabel(f"{val}%")
                lbl_val.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {text_muted};")
                lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)

                sec_name = s.get("name", "Sec")
                lbl_sec = QLabel(sec_name[:11])
                lbl_sec.setToolTip(s.get("full_name", sec_name))
                lbl_sec.setStyleSheet(f"font-size: 9.5px; font-weight: 600; color: {text_primary};")
                lbl_sec.setAlignment(Qt.AlignmentFlag.AlignCenter)

                col_box.addWidget(lbl_val)
                col_box.addWidget(bar)
                col_box.addWidget(lbl_sec)
                sec_bars.addLayout(col_box)
        else:
            sec_bars.addWidget(QLabel("No tagged sections detected (e.g. [Verse], [Chorus])."))

        e_layout.addLayout(sec_bars)
        layout.addWidget(energy_card)

        # ── 3. Actionable Strengths & Improvement Tips ──
        tips_card = QFrame()
        tips_card.setObjectName("card")
        t_layout = QVBoxLayout(tips_card)
        t_layout.setSpacing(4)

        lbl_t_title = QLabel("💡 Producer Recommendations & AI Safety Insights")
        lbl_t_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #10b981;")
        t_layout.addWidget(lbl_t_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        scroll_content = QWidget()
        sc_layout = QVBoxLayout(scroll_content)
        sc_layout.setContentsMargins(0, 4, 0, 4)
        sc_layout.setSpacing(6)

        for s in analysis.get("strengths", []):
            lbl = QLabel(s)
            lbl.setStyleSheet("color: #10b981; font-weight: 600; font-size: 11px;")
            lbl.setWordWrap(True)
            sc_layout.addWidget(lbl)

        for w in analysis.get("warnings", []):
            lbl = QLabel(w)
            lbl.setStyleSheet("color: #f59e0b; font-weight: 600; font-size: 11px;")
            lbl.setWordWrap(True)
            sc_layout.addWidget(lbl)

        overcrowded = analysis.get("overcrowded_lines", [])
        if overcrowded:
            sc_layout.addSpacing(4)
            lbl_ov = QLabel("🚨 Overcrowded Lines (>13 Syllables - Suno Slur Warning):")
            lbl_ov.setStyleSheet("color: #ef4444; font-weight: 700; font-size: 11px;")
            sc_layout.addWidget(lbl_ov)

            for item in overcrowded[:3]:
                lbl_item = QLabel(f"• \"{item['line']}\" ({item['syllables']}s) → {item['tip']}")
                lbl_item.setStyleSheet(f"color: {text_muted}; font-size: 10.5px; margin-left: 8px;")
                lbl_item.setWordWrap(True)
                sc_layout.addWidget(lbl_item)

        scroll_content.setLayout(sc_layout)
        scroll.setWidget(scroll_content)
        t_layout.addWidget(scroll)

        layout.addWidget(tips_card, stretch=1)

        # Bottom Close button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Close Inspector")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"background: {t['accent_gradient']}; color: #ffffff; font-weight: 700; padding: 6px 18px; border-radius: 6px; border: 1px solid {t['border_accent']};")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)
