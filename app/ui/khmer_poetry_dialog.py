"""
Khmer Classical Poetic Meter & Rhyme Map Inspector Dialog.
Visual validation matrix for ពាក្យ៧, ពាក្យ៨, ព្រហ្មគីតិ, កាកគតិ, ភុជង្គលីលា.
Features glowing rhyme link badges, syllable count status, and rhyme suggestions.
"""

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QGroupBox, QScrollArea,
    QFrame, QGridLayout, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from typing import List, Dict, Optional
from app.khmer_poetry_meter import (
    KHMER_POETRY_FORMS, KHMER_RHYME_FAMILIES,
    KhmerPoetryMeterAnalyzer, extract_khmer_rhyme_sound
)


class KhmerPoetryMeterDialog(QDialog):
    text_updated = pyqtSignal(str)

    def __init__(self, parent=None, is_dark: bool = True, initial_lyrics: str = ""):
        super().__init__(parent)
        self.is_dark = is_dark
        self.lyrics = initial_lyrics
        self.setWindowTitle("📜 Khmer Classical Poetic Meter & Rhyme Map Engine")
        self.resize(880, 700)
        self.setMinimumSize(800, 620)

        self._init_ui()
        self.apply_theme(self.is_dark)
        self._analyze_current_text()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header Title
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        self.lbl_title = QLabel("📜 Khmer Classical Poetic Meter & Rhyme Map Engine")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 800;")
        self.lbl_subtitle = QLabel("ក្បួនកំណាព្យខ្មែរ: វិភាគជួនក្នុង ជួនឆ្លងវគ្គ និងចំនួនព្យាង្គ (ពាក្យ៧, ពាក្យ៨, ព្រហ្មគីតិ, កាកគតិ, ភុជង្គលីលា)")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_box)
        header_row.addStretch()
        main_layout.addLayout(header_row)

        # Top Bar: Poetic Form Selector & Quick Presets
        top_bar = QHBoxLayout()
        lbl_form = QLabel("Classical Meter Form (ក្បួនកាព្យ):")
        lbl_form.setStyleSheet("font-weight: 700; font-size: 12px;")
        self.combo_form = QComboBox()
        for k, v in KHMER_POETRY_FORMS.items():
            self.combo_form.addItem(v["name"], k)
        self.combo_form.currentIndexChanged.connect(self._analyze_current_text)

        self.btn_load_sample = QPushButton("📋 Load Sample Stanza")
        self.btn_load_sample.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_sample.clicked.connect(self._load_sample_stanza)

        top_bar.addWidget(lbl_form)
        top_bar.addWidget(self.combo_form, stretch=1)
        top_bar.addWidget(self.btn_load_sample)
        main_layout.addLayout(top_bar)

        # Form Description Box
        self.lbl_form_desc = QLabel()
        self.lbl_form_desc.setStyleSheet("color: #64748b; font-size: 11px; padding: 4px;")
        self.lbl_form_desc.setWordWrap(True)
        main_layout.addWidget(self.lbl_form_desc)

        # Main Split: Left Editor, Right Meter Matrix & Rhyme Cards
        split_row = QHBoxLayout()
        split_row.setSpacing(14)

        # Left Column: Stanza Editor
        editor_group = QGroupBox("✍️ Stanza Input (អត្ថបទកំណាព្យ)")
        e_layout = QVBoxLayout(editor_group)
        e_layout.setContentsMargins(10, 10, 10, 10)
        e_layout.setSpacing(8)

        self.txt_stanza = QTextEdit()
        self.txt_stanza.setPlaceholderText("Paste or write 1 stanza of Khmer lyrics here...")
        if self.lyrics.strip():
            # Extract first 4 non-bracketed lines
            lines = [l for l in self.lyrics.split("\n") if l.strip() and not l.strip().startswith("[")]
            self.txt_stanza.setPlainText("\n".join(lines[:4]))
        else:
            self._load_sample_stanza()

        self.txt_stanza.textChanged.connect(self._analyze_current_text)
        e_layout.addWidget(self.txt_stanza)

        # Rhyme Assister & Dictionary Card
        dict_box = QGroupBox("🔍 Khmer Rhyme Dictionary Assister (ពាក្យជួន)")
        d_layout = QVBoxLayout(dict_box)
        d_layout.setContentsMargins(8, 8, 8, 8)
        d_layout.setSpacing(6)

        search_row = QHBoxLayout()
        self.txt_search_word = QLineEdit()
        self.txt_search_word.setPlaceholderText("Type a Khmer word (e.g. ស្នេហ៍, កាយ, ចិត្ត)...")
        btn_search = QPushButton("Find Rhymes")
        btn_search.clicked.connect(self._search_rhymes)
        search_row.addWidget(self.txt_search_word)
        search_row.addWidget(btn_search)
        d_layout.addLayout(search_row)

        self.lbl_rhyme_results = QLabel("Matching rhyming words will appear here.")
        self.lbl_rhyme_results.setStyleSheet("color: #3b82f6; font-size: 12px; font-weight: 600;")
        self.lbl_rhyme_results.setWordWrap(True)
        d_layout.addWidget(self.lbl_rhyme_results)

        e_layout.addWidget(dict_box)
        split_row.addWidget(editor_group, stretch=1)

        # Right Column: Visual Meter Matrix & Rhyme Links
        results_group = QGroupBox("📊 Meter Validation & Rhyme Map (ផែនទីជួន)")
        r_layout = QVBoxLayout(results_group)
        r_layout.setContentsMargins(10, 10, 10, 10)
        r_layout.setSpacing(8)

        r_scroll = QScrollArea()
        r_scroll.setWidgetResizable(True)
        r_scroll.setStyleSheet("border: none; background: transparent;")
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(4, 4, 4, 4)
        self.results_layout.setSpacing(10)
        r_scroll.setWidget(self.results_container)
        r_layout.addWidget(r_scroll)

        split_row.addWidget(results_group, stretch=2)
        main_layout.addLayout(split_row, stretch=1)

        # Bottom Bar: Actions
        bottom_row = QHBoxLayout()
        self.btn_apply = QPushButton("✍️ Update Stanza into Main Editor")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setFixedHeight(36)
        self.btn_apply.setStyleSheet("background-color: #10b981; color: white; font-weight: 700; border-radius: 6px; padding: 0 16px;")
        self.btn_apply.clicked.connect(self._apply_to_main_editor)

        self.btn_close = QPushButton("Close")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedHeight(36)
        self.btn_close.setFixedWidth(90)
        self.btn_close.clicked.connect(self.accept)

        bottom_row.addStretch()
        bottom_row.addWidget(self.btn_apply)
        bottom_row.addWidget(self.btn_close)
        main_layout.addLayout(bottom_row)

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        bg_col = "#0f172a" if is_dark else "#f8fafc"
        card_bg = "#1e293b" if is_dark else "#ffffff"
        text_col = "#f8fafc" if is_dark else "#0f172a"
        border_col = "#334155" if is_dark else "#e2e8f0"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_col};
                color: {text_col};
            }}
            QGroupBox {{
                font-weight: 700;
                font-size: 12px;
                border: 1px solid {border_col};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: {card_bg};
                color: {text_col};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {text_col};
            }}
            QTextEdit, QLineEdit {{
                background-color: {bg_col};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                font-size: 13px;
            }}
            QComboBox {{
                background-color: {bg_col};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 5px 10px;
            }}
            QPushButton {{
                background-color: {card_bg};
                color: {text_col};
                border: 1px solid {border_col};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                border-color: #10b981;
            }}
        """)

    def _load_sample_stanza(self):
        sample = (
            "សែន ស្រ ណោះ ចិត្ត គិត ដល់ ស្នេហ៍\n"
            "ធ្លាប់ រស់ ក្បែរ ថែ កាយ ប្រាណ ណា\n"
            "ពេល នេះ បែក ឆ្ងាយ ខក ខាន ទៅ\n"
            "តើ ក ល្យាណ សុខ ទុក្ខ យ៉ាង ណា"
        )
        self.txt_stanza.setPlainText(sample)

    def _analyze_current_text(self):
        # Update description
        form_id = self.combo_form.currentData()
        form_info = KHMER_POETRY_FORMS.get(form_id, KHMER_POETRY_FORMS["peak_7"])
        self.lbl_form_desc.setText(f"ℹ️ {form_info['desc']}")

        # Clear previous widgets in results container
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        raw_text = self.txt_stanza.toPlainText()
        lines = [l.strip() for l in raw_text.split("\n") if l.strip() and not (l.strip().startswith("[") and l.strip().endswith("]"))]

        analysis = KhmerPoetryMeterAnalyzer.analyze_stanza(lines, form_id)

        # 1. Stanza Syllable Grid
        matrix_box = QGroupBox("1. Syllable Cadence Grid (ចំនួនព្យាង្គក្នុងឃ្លានីមួយៗ)")
        m_layout = QVBoxLayout(matrix_box)
        m_layout.setSpacing(8)

        for l_info in analysis["lines"]:
            line_card = QFrame()
            line_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.03); border-radius: 6px; padding: 4px;")
            lc_layout = QVBoxLayout(line_card)
            lc_layout.setContentsMargins(6, 4, 6, 4)
            lc_layout.setSpacing(4)

            top_row = QHBoxLayout()
            lbl_line_num = QLabel(f"<b>ឃ្លាទី {l_info['line_index'] + 1}:</b>")
            lbl_line_num.setStyleSheet("font-size: 12px; color: #94a3b8;")

            cnt_status = l_info["status"]
            cnt_color = "#10b981" if cnt_status == "PERFECT" else ("#f59e0b" if cnt_status == "TOLERABLE" else "#ef4444")
            cnt_text = f"{l_info['actual_count']}/{l_info['expected_count']} Syllables ({cnt_status})"
            lbl_cnt = QLabel(cnt_text)
            lbl_cnt.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {cnt_color};")

            top_row.addWidget(lbl_line_num)
            top_row.addStretch()
            top_row.addWidget(lbl_cnt)
            lc_layout.addLayout(top_row)

            # Syllables row pills
            syl_row = QHBoxLayout()
            syl_row.setSpacing(4)
            for idx, syl in enumerate(l_info["syllables"]):
                pill = QLabel(syl)
                pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pill.setFixedHeight(26)
                pill.setStyleSheet("""
                    background-color: #3b82f6;
                    color: white;
                    font-weight: 700;
                    border-radius: 4px;
                    padding: 0 6px;
                    font-size: 12px;
                """)
                syl_row.addWidget(pill)
            syl_row.addStretch()
            lc_layout.addLayout(syl_row)

            m_layout.addWidget(line_card)

        self.results_layout.addWidget(matrix_box)

        # 2. Rhyme Links Inspection Cards
        rhyme_box = QGroupBox("2. Classical Rhyme Links Validation (ការផ្ទៀងផ្ទាត់ជួន)")
        rb_layout = QVBoxLayout(rhyme_box)
        rb_layout.setSpacing(6)

        for check in analysis["rhyme_checks"]:
            r_card = QFrame()
            r_card.setFrameShape(QFrame.Shape.StyledPanel)
            rc_layout = QHBoxLayout(r_card)
            rc_layout.setContentsMargins(10, 8, 10, 8)

            lbl_name = QLabel(f"<b>{check['rule_name']}</b><br><span style='font-size: 11px; color: #64748b;'>{check['from_pos']} ↔ {check['to_pos']}</span>")
            lbl_name.setTextFormat(Qt.TextFormat.RichText)

            lbl_pair = QLabel(f"<span style='font-size: 14px; font-weight: 800; color: #3b82f6;'>[{check['syl1'] or '...'}]</span> ↔ <span style='font-size: 14px; font-weight: 800; color: #3b82f6;'>[{check['syl2'] or '...'}]</span>")
            lbl_pair.setTextFormat(Qt.TextFormat.RichText)

            is_perfect = check["is_rhyme"]
            status_badge = QLabel("🟢 ជួនពេញ (Rhymes)" if is_perfect else "🔴 ខ្វះជួន (No Rhyme)")
            status_badge.setStyleSheet(f"font-weight: 700; font-size: 11px; color: {'#10b981' if is_perfect else '#ef4444'};")

            rc_layout.addWidget(lbl_name, stretch=2)
            rc_layout.addWidget(lbl_pair, stretch=2)
            rc_layout.addWidget(status_badge, stretch=1)
            rb_layout.addWidget(r_card)

        self.results_layout.addWidget(rhyme_box)

    def _search_rhymes(self):
        query = self.txt_search_word.text().strip()
        if not query:
            return
        sound = extract_khmer_rhyme_sound(query)
        matches = KHMER_RHYME_FAMILIES.get(sound, [])
        if matches:
            res_text = f"✨ Words rhyming with '{query}': " + ", ".join(matches)
        else:
            res_text = f"No exact family found for '{query}'. Try: ស្នេហ៍, កាយ, ចិត្ត, ស្រី, អូន, គង់."
        self.lbl_rhyme_results.setText(res_text)

    def _apply_to_main_editor(self):
        text = self.txt_stanza.toPlainText()
        self.text_updated.emit(text)
        QMessageBox.information(self, "Updated", "Stanza updated into your main lyrics editor.")
        self.accept()

