"""
Professional Lyric & Suno ChordPro Syntax Highlighter for PyQt6.
Color-codes musical sections, chord markers, and performance metatags
with industry-standard DAW styling (Hookpad, Logic Pro, and Suno).
"""

import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class LyricSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, is_dark: bool = False):
        super().__init__(document)
        self.is_dark = is_dark
        self._init_rules()

    def set_dark_mode(self, is_dark: bool):
        self.is_dark = is_dark
        self._init_rules()
        self.rehighlight()

    def _init_rules(self):
        self.highlighting_rules = []

        # Color palette depending on light/dark mode
        if self.is_dark:
            col_chorus_fg = QColor("#fbbf24") # Warm Amber Gold
            col_chorus_bg = QColor("#2d2006")
            col_verse_fg = QColor("#38bdf8") # Sky Cyan
            col_verse_bg = QColor("#082f49")
            col_pre_fg = QColor("#818cf8") # Indigo
            col_pre_bg = QColor("#1e1b4b")
            col_bridge_fg = QColor("#c084fc") # Fuchsia Purple
            col_bridge_bg = QColor("#3b0764")
            col_drop_fg = QColor("#f87171") # Crimson Red
            col_drop_bg = QColor("#450a0a")
            col_intro_fg = QColor("#34d399") # Emerald
            col_intro_bg = QColor("#064e3b")
            col_chord_fg = QColor("#f472b6") # Electric Pink/Magenta
            col_chord_bg = QColor("#371329")
            col_vocal_cue_fg = QColor("#94a3b8") # Slate
        else:
            col_chorus_fg = QColor("#b45309")
            col_chorus_bg = QColor("#fef3c7")
            col_verse_fg = QColor("#0284c7")
            col_verse_bg = QColor("#e0f2fe")
            col_pre_fg = QColor("#4338ca")
            col_pre_bg = QColor("#e0e7ff")
            col_bridge_fg = QColor("#7e22ce")
            col_bridge_bg = QColor("#fae8ff")
            col_drop_fg = QColor("#b91c1c")
            col_drop_bg = QColor("#fee2e2")
            col_intro_fg = QColor("#047857")
            col_intro_bg = QColor("#d1fae5")
            col_chord_fg = QColor("#9333ea")
            col_chord_bg = QColor("#f5d0fe")
            col_vocal_cue_fg = QColor("#64748b")

        # ── 1. Section Formats ──
        def _make_fmt(fg: QColor, bg: QColor = None, bold: bool = True, italic: bool = False):
            fmt = QTextCharFormat()
            fmt.setForeground(fg)
            if bg:
                fmt.setBackground(bg)
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            if italic:
                fmt.setFontItalic(True)
            return fmt

        fmt_chorus = _make_fmt(col_chorus_fg, col_chorus_bg)
        fmt_verse = _make_fmt(col_verse_fg, col_verse_bg)
        fmt_pre = _make_fmt(col_pre_fg, col_pre_bg)
        fmt_bridge = _make_fmt(col_bridge_fg, col_bridge_bg)
        fmt_drop = _make_fmt(col_drop_fg, col_drop_bg)
        fmt_intro = _make_fmt(col_intro_fg, col_intro_bg)
        fmt_generic_sec = _make_fmt(col_verse_fg, col_verse_bg)

        # Regex rules for sections (English & authentic Khmer poetic tags)
        section_rules = [
            (re.compile(r'\[(Chorus|បន្ទរ|បន្ទរបន្ថែម|Hook)[^\]]*\]', re.IGNORECASE), fmt_chorus),
            (re.compile(r'\[(Pre-Chorus|ត្រៀមបន្ទរ|តភ្ជាប់)[^\]]*\]', re.IGNORECASE), fmt_pre),
            (re.compile(r'\[(Verse|វគ្គ|វគ្គ១|វគ្គ២|វគ្គ៣)[^\]]*\]', re.IGNORECASE), fmt_verse),
            (re.compile(r'\[(Bridge|ស្ពានចម្លង|តភ្ជាប់ផ្លាស់ប្តូរ)[^\]]*\]', re.IGNORECASE), fmt_bridge),
            (re.compile(r'\[(Drop|Bass Drop|Beat Drop)[^\]]*\]', re.IGNORECASE), fmt_drop),
            (re.compile(r'\[(Intro|Outro|End|ផ្តើម|អារម្ភកថា|បញ្ចប់)[^\]]*\]', re.IGNORECASE), fmt_intro),
            (re.compile(r'\[(Guitar Solo|Drum Break|Solo|ទោល|Instrumental)[^\]]*\]', re.IGNORECASE), fmt_bridge),
            (re.compile(r'\[Title:[^\]]*\]', re.IGNORECASE), fmt_intro),
            (re.compile(r'\[Style:[^\]]*\]', re.IGNORECASE), fmt_pre),
        ]
        self.highlighting_rules.extend(section_rules)

        # ── 2. Musical Chord Markers: [Am], [C#m7], [G/B], [Fadd9], etc. ──
        fmt_chord = _make_fmt(col_chord_fg, col_chord_bg, bold=True)
        chord_regex = re.compile(r'\[([A-G][#b]?(m|maj|min|dim|aug|sus[24]?|[0-9])*(/[A-G][#b]?)?)\]')
        self.highlighting_rules.append((chord_regex, fmt_chord))

        # ── 3. Vocal Direction & Performance Cues: (Whisper), (Belt), (Male Vocals) ──
        fmt_cue = _make_fmt(col_vocal_cue_fg, bold=False, italic=True)
        cue_regex = re.compile(r'\([^\)]+\)')
        self.highlighting_rules.append((cue_regex, fmt_cue))

    def highlightBlock(self, text: str):
        if not text:
            return

        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

