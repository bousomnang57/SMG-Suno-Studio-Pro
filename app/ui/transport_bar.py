"""
Master Studio Transport Bar for Lyric AI Writer / WorldLyric Studio.
Anchored DAW-style top console providing unified master controls across all workspaces:
- Master Tempo (BPM stepper, Tap Tempo, Visual LED Beat Pulse, Metronome click)
- Master Key & Harmonic Tonality (Key selector, Semitone transposition, Polyphonic Synth Audition)
- One-Touch Scratch Vocal Take Recorder & Player
- Song Title & Real-Time Suno / Production Health HUD
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QComboBox, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

class MasterStudioTransportBar(QFrame):
    bpm_changed = pyqtSignal(int)
    metro_toggle_requested = pyqtSignal()
    tap_tempo_requested = pyqtSignal()
    transpose_requested = pyqtSignal(int) # semitones offset: -1 or +1
    key_changed = pyqtSignal(str) # new key name, e.g. "Am"
    synth_play_requested = pyqtSignal()
    synth_stop_requested = pyqtSignal()
    record_toggle_requested = pyqtSignal()
    play_take_requested = pyqtSignal()
    title_changed = pyqtSignal(str)
    quick_suno_copy_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("masterTransportBar")
        self.setFixedHeight(54)
        self.is_dark = False

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(10)

        # ── 1. Left: Track Title & Project Status ──
        title_box = QHBoxLayout()
        title_box.setSpacing(6)
        title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_t = QLabel("🎵")
        lbl_t.setStyleSheet("font-size: 14px;")
        title_box.addWidget(lbl_t)

        self.txt_title = QLineEdit("Untitled Song")
        self.txt_title.setToolTip("Song Project Title (Click to rename)")
        self.txt_title.setFixedHeight(28)
        self.txt_title.setMinimumWidth(220)
        self.txt_title.setMaximumWidth(340)
        self.txt_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.txt_title.setStyleSheet("""
            QLineEdit {
                font-family: 'Kantumruy Pro', 'Segoe UI', sans-serif;
                font-weight: 700;
                font-size: 11.5px;
                padding: 2px 8px;
                border-radius: 5px;
            }
        """)
        self.txt_title.textChanged.connect(lambda t: self.title_changed.emit(t))
        title_box.addWidget(self.txt_title)

        self.lbl_sig_badge = QLabel("4/4")
        self.lbl_sig_badge.setToolTip("Time Signature")
        self.lbl_sig_badge.setFixedSize(38, 26)
        self.lbl_sig_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sig_badge.setStyleSheet("""
            background: #1e1b4b;
            color: #a78bfa;
            font-weight: 800;
            font-size: 11px;
            border-radius: 4px;
            border: 1px solid #4338ca;
        """)
        title_box.addWidget(self.lbl_sig_badge)

        layout.addLayout(title_box)

        # Separator
        layout.addWidget(self._create_divider())

        # ── 2. Center-Left: Master Metronome & Tempo Console ──
        tempo_box = QHBoxLayout()
        tempo_box.setSpacing(4)
        tempo_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Glowing LED beat dot
        self.metro_led = QLabel("●")
        self.metro_led.setToolTip("Visual Metronome Beat Pulse (Red=Beat 1, Cyan=Beats 2-4)")
        self.metro_led.setStyleSheet("color: #64748b; font-size: 17px; font-weight: 900;")
        tempo_box.addWidget(self.metro_led)

        # Metronome Button
        self.btn_metro = QPushButton("▶ Metronome")
        self.btn_metro.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_metro.setToolTip("Start / Stop Audio Metronome")
        self.btn_metro.setFixedHeight(26)
        self.btn_metro.setStyleSheet("""
            QPushButton {
                background: #1e2238;
                color: #38bdf8;
                border: 1px solid #0284c7;
                font-weight: 700;
                font-size: 10px;
                padding: 3px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #0369a1;
                color: #ffffff;
            }
        """)
        self.btn_metro.clicked.connect(lambda: self.metro_toggle_requested.emit())
        tempo_box.addWidget(self.btn_metro)

        # BPM Stepper Controls: [ - ] [ 124 BPM ] [ + ]
        self.btn_bpm_down = QPushButton("-")
        self.btn_bpm_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bpm_down.setToolTip("Decrease Tempo (-2 BPM)")
        self.btn_bpm_down.setFixedSize(26, 26)
        self.btn_bpm_down.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif; font-weight: 900; font-size: 14px; border-radius: 4px; background: #1e2438; color: #38bdf8; border: 1px solid #2c3b64;")
        self.btn_bpm_down.clicked.connect(self._step_bpm_down)
        tempo_box.addWidget(self.btn_bpm_down)

        self.spin_bpm = QSpinBox()
        self.spin_bpm.setRange(40, 240)
        self.spin_bpm.setValue(124)
        self.spin_bpm.setSuffix(" BPM")
        self.spin_bpm.setFixedSize(94, 26)
        self.spin_bpm.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_bpm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_bpm.setStyleSheet("font-weight: 800; font-size: 11px; border-radius: 4px; padding: 2px 2px;")
        self.spin_bpm.valueChanged.connect(self._on_bpm_spin_changed)
        tempo_box.addWidget(self.spin_bpm)

        self.btn_bpm_up = QPushButton("+")
        self.btn_bpm_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bpm_up.setToolTip("Increase Tempo (+2 BPM)")
        self.btn_bpm_up.setFixedSize(26, 26)
        self.btn_bpm_up.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif; font-weight: 900; font-size: 14px; border-radius: 4px; background: #1e2438; color: #38bdf8; border: 1px solid #2c3b64;")
        self.btn_bpm_up.clicked.connect(self._step_bpm_up)
        tempo_box.addWidget(self.btn_bpm_up)

        # Tap Tempo
        self.btn_tap = QPushButton("👆 Tap")
        self.btn_tap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tap.setToolTip("Tap repeatedly to match live musical tempo")
        self.btn_tap.setFixedHeight(26)
        self.btn_tap.setStyleSheet("""
            QPushButton {
                background: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
                font-weight: 700;
                font-size: 10px;
                padding: 3px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #dbeafe;
            }
        """)
        self.btn_tap.clicked.connect(lambda: self.tap_tempo_requested.emit())
        tempo_box.addWidget(self.btn_tap)

        layout.addLayout(tempo_box)

        # Separator
        layout.addWidget(self._create_divider())

        # ── 3. Center-Right: Master Key & Harmonic Tonality Console ──
        key_box = QHBoxLayout()
        key_box.setSpacing(4)
        key_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_k = QLabel("Key:")
        lbl_k.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8;")
        key_box.addWidget(lbl_k)

        self.combo_key = QComboBox()
        self.combo_key.addItems([
            "Am", "C", "Dm", "F", "Em", "G", "Bm", "D",
            "F#m", "A", "C#m", "E", "Gm", "Bb", "Cm", "Eb"
        ])
        self.combo_key.setCurrentText("Am")
        self.combo_key.setFixedSize(58, 26)
        self.combo_key.setStyleSheet("font-weight: 800; font-size: 11px; padding: 2px 4px; border-radius: 4px;")
        self.combo_key.currentTextChanged.connect(lambda k: self.key_changed.emit(k))
        key_box.addWidget(self.combo_key)

        # Semitone Transpose Buttons: [-1] and [+1] with full unicode compatibility
        self.btn_trans_down = QPushButton("-1")
        self.btn_trans_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_trans_down.setToolTip("Transpose entire song down 1 semitone (♭ -1)")
        self.btn_trans_down.setFixedSize(32, 26)
        self.btn_trans_down.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif; font-weight: 800; font-size: 11px; border-radius: 4px; background: #1a2036; color: #a5b4fc; border: 1px solid #283256;")
        self.btn_trans_down.clicked.connect(lambda: self.transpose_requested.emit(-1))
        key_box.addWidget(self.btn_trans_down)

        self.btn_trans_up = QPushButton("+1")
        self.btn_trans_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_trans_up.setToolTip("Transpose entire song up 1 semitone (♯ +1)")
        self.btn_trans_up.setFixedSize(32, 26)
        self.btn_trans_up.setStyleSheet("font-family: 'Segoe UI', Arial, sans-serif; font-weight: 800; font-size: 11px; border-radius: 4px; background: #1a2036; color: #a5b4fc; border: 1px solid #283256;")
        self.btn_trans_up.clicked.connect(lambda: self.transpose_requested.emit(1))
        key_box.addWidget(self.btn_trans_up)

        # Polyphonic Chord Synth Audition
        self.btn_synth = QPushButton("🔊 Synth")
        self.btn_synth.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_synth.setToolTip("Audition chord progression tones in current key")
        self.btn_synth.setFixedHeight(26)
        self.btn_synth.setStyleSheet("""
            QPushButton {
                background: #fdf4ff;
                color: #86198f;
                border: 1px solid #f0abfc;
                font-weight: 700;
                font-size: 10px;
                padding: 3px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #fae8ff;
            }
        """)
        self.btn_synth.clicked.connect(lambda: self.synth_play_requested.emit())
        key_box.addWidget(self.btn_synth)

        self.btn_synth_stop = QPushButton("■")
        self.btn_synth_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_synth_stop.setFixedSize(26, 26)
        self.btn_synth_stop.setToolTip("Halt synth preview (Stop)")
        self.btn_synth_stop.setStyleSheet("font-size: 11px; font-weight: 900; border-radius: 4px;")
        self.btn_synth_stop.clicked.connect(lambda: self.synth_stop_requested.emit())
        key_box.addWidget(self.btn_synth_stop)

        layout.addLayout(key_box)

        # Separator
        layout.addWidget(self._create_divider())

        # ── 4. Right: Scratch Mic Recorder Console ──
        rec_box = QHBoxLayout()
        rec_box.setSpacing(5)
        rec_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.btn_record = QPushButton("🔴 REC TAKE")
        self.btn_record.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_record.setToolTip("One-Touch Microphone Scratch Vocal Melody Recorder")
        self.btn_record.setFixedHeight(26)
        self.btn_record.setStyleSheet("""
            QPushButton {
                background: #fee2e2;
                color: #dc2626;
                border: 1px solid #fca5a5;
                font-weight: 800;
                font-size: 10px;
                padding: 3px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #fecaca;
            }
        """)
        self.btn_record.clicked.connect(lambda: self.record_toggle_requested.emit())
        rec_box.addWidget(self.btn_record)

        self.btn_play_take = QPushButton("▶ Play Take")
        self.btn_play_take.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_take.setToolTip("Listen back to latest voice scratch take")
        self.btn_play_take.setFixedHeight(26)
        self.btn_play_take.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #334155;
                border: 1px solid #cbd5e1;
                font-weight: 700;
                font-size: 10px;
                padding: 3px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        self.btn_play_take.clicked.connect(lambda: self.play_take_requested.emit())
        rec_box.addWidget(self.btn_play_take)

        layout.addLayout(rec_box)

        layout.addStretch()

        # ── 5. Far Right: Live Suno / Production Status HUD ──
        hud_box = QHBoxLayout()
        hud_box.setSpacing(6)
        hud_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.lbl_pro_hud = QLabel("⭐ PRO READY")
        self.lbl_pro_hud.setToolTip("Suno v3.5/v6 Token Density and Structure Health")
        self.lbl_pro_hud.setFixedHeight(26)
        self.lbl_pro_hud.setStyleSheet("""
            background: #ecfdf5;
            color: #047857;
            font-weight: 800;
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #a7f3d0;
        """)
        hud_box.addWidget(self.lbl_pro_hud)

        self.btn_quick_suno = QPushButton("⚡ Copy Suno Prompt")
        self.btn_quick_suno.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quick_suno.setFixedHeight(26)
        self.btn_quick_suno.setToolTip("Quick-copy master Suno style prompt to clipboard")
        self.btn_quick_suno.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
                color: #ffffff;
                font-weight: 700;
                font-size: 10px;
                padding: 5px 10px;
                border-radius: 5px;
                border: 1px solid #8b5cf6;
            }
            QPushButton:hover {
                background: #6d28d9;
            }
        """)
        self.btn_quick_suno.clicked.connect(lambda: self.quick_suno_copy_requested.emit())
        hud_box.addWidget(self.btn_quick_suno)

        layout.addLayout(hud_box)

    def _create_divider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFrameShadow(QFrame.Shadow.Sunken)
        div.setStyleSheet("color: #283256; margin: 4px 2px;")
        if not hasattr(self, "dividers"):
            self.dividers = []
        self.dividers.append(div)
        return div

    def _step_bpm_down(self):
        val = max(40, self.spin_bpm.value() - 2)
        self.spin_bpm.setValue(val)

    def _step_bpm_up(self):
        val = min(240, self.spin_bpm.value() + 2)
        self.spin_bpm.setValue(val)

    def _on_bpm_spin_changed(self, val: int):
        self.bpm_changed.emit(val)

    def set_bpm(self, bpm: int):
        self.spin_bpm.blockSignals(True)
        self.spin_bpm.setValue(bpm)
        self.spin_bpm.blockSignals(False)

    def set_key(self, key_name: str):
        idx = self.combo_key.findText(key_name)
        if idx >= 0:
            self.combo_key.blockSignals(True)
            self.combo_key.setCurrentIndex(idx)
            self.combo_key.blockSignals(False)

    def set_title(self, title: str):
        self.txt_title.blockSignals(True)
        self.txt_title.setText(title)
        self.txt_title.setCursorPosition(0)
        self.txt_title.blockSignals(False)

    def set_metro_active(self, is_running: bool):
        if is_running:
            self.btn_metro.setText("⏹ Stop")
            self.btn_metro.setStyleSheet("""
                QPushButton {
                    background: #dc2626;
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 10px;
                    padding: 4px 10px;
                    border-radius: 5px;
                    border: 1px solid #ef4444;
                }
            """)
        else:
            self.btn_metro.setText("▶ Metronome")
            if self.is_dark:
                self.btn_metro.setStyleSheet("""
                    QPushButton {
                        background: #161b30;
                        color: #38bdf8;
                        border: 1px solid #0284c7;
                        font-weight: 700;
                        font-size: 10px;
                        padding: 4px 10px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background: #0284c7;
                        color: #ffffff;
                    }
                """)
            else:
                self.btn_metro.setStyleSheet("""
                    QPushButton {
                        background: #eff6ff;
                        color: #2563eb;
                        border: 1px solid #bfdbfe;
                        font-weight: 700;
                        font-size: 10px;
                        padding: 4px 10px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background: #2563eb;
                        color: #ffffff;
                    }
                """)
            self.metro_led.setStyleSheet("color: #64748b; font-size: 17px; font-weight: 900;")

    def set_metro_beat(self, beat: int, total: int):
        if beat == 1:
            self.metro_led.setStyleSheet("color: #ef4444; font-size: 18px; font-weight: 900;") # Red pulse on beat 1
        elif beat > 1:
            self.metro_led.setStyleSheet("color: #06b6d4; font-size: 18px; font-weight: 900;") # Cyan on beats 2, 3, 4
        else:
            self.metro_led.setStyleSheet("color: #64748b; font-size: 17px; font-weight: 900;")

    def set_recording_active(self, is_recording: bool):
        if is_recording:
            self.btn_record.setText("⏹ STOP REC")
            self.btn_record.setStyleSheet("""
                QPushButton {
                    background: #dc2626;
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 10px;
                    padding: 5px 12px;
                    border-radius: 5px;
                    border: 1px solid #b91c1c;
                }
            """)
            self.btn_play_take.setEnabled(False)
        else:
            self.btn_record.setText("🔴 REC TAKE")
            if self.is_dark:
                self.btn_record.setStyleSheet("""
                    QPushButton {
                        background: #3b1115;
                        color: #f87171;
                        border: 1px solid #7f1d1d;
                        font-weight: 800;
                        font-size: 10px;
                        padding: 5px 12px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background: #4c141a;
                        color: #ffffff;
                    }
                """)
            else:
                self.btn_record.setStyleSheet("""
                    QPushButton {
                        background: #fee2e2;
                        color: #dc2626;
                        border: 1px solid #fca5a5;
                        font-weight: 800;
                        font-size: 10px;
                        padding: 5px 12px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background: #fecaca;
                    }
                """)
            self.btn_play_take.setEnabled(True)

    def apply_theme(self, is_dark: bool):
        self.is_dark = is_dark
        if hasattr(self, "dividers"):
            div_color = "#283354" if is_dark else "#cbd5e1"
            for d in self.dividers:
                d.setStyleSheet(f"color: {div_color}; margin: 4px 2px;")

        if is_dark:
            self.setStyleSheet("""
                QFrame#masterTransportBar {
                    background-color: #0b0e1b;
                    border-bottom: 1px solid #1a2035;
                }
            """)
            self.txt_title.setStyleSheet("""
                QLineEdit {
                    background-color: #121528;
                    color: #f1f5f9;
                    border: 1px solid #232c4b;
                    font-family: 'Kantumruy Pro', 'Segoe UI', sans-serif;
                    font-weight: 700;
                    font-size: 11.5px;
                    padding: 2px 8px;
                    border-radius: 5px;
                }
                QLineEdit:focus {
                    border: 1px solid #6366f1;
                    background-color: #161b34;
                }
            """)
            self.lbl_sig_badge.setStyleSheet("""
                background: #1e1b4b;
                color: #a78bfa;
                font-weight: 800;
                font-size: 11px;
                border-radius: 4px;
                border: 1px solid #4338ca;
            """)
            self.btn_metro.setStyleSheet("""
                QPushButton {
                    background: #161b30;
                    color: #38bdf8;
                    border: 1px solid #0284c7;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #0284c7;
                    color: #ffffff;
                }
            """)
            # Crisp Dark BPM Stepper: [ − ] [ 120 BPM ] [ + ]
            bpm_btn_qss = """
                QPushButton {
                    background: #1e2438;
                    color: #38bdf8;
                    border: 1px solid #2c3b64;
                    font-weight: 900;
                    font-size: 13px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #2b3552;
                    color: #ffffff;
                    border-color: #4f46e5;
                }
            """
            self.btn_bpm_down.setStyleSheet(bpm_btn_qss)
            self.btn_bpm_up.setStyleSheet(bpm_btn_qss)
            self.spin_bpm.setStyleSheet("""
                QSpinBox {
                    background: #0b0f1f;
                    color: #f1f5f9;
                    border: 1px solid #283256;
                    font-weight: 800;
                    font-size: 11px;
                    border-radius: 4px;
                    padding: 2px 4px;
                }
                QSpinBox:focus {
                    border-color: #6366f1;
                }
            """)
            self.btn_tap.setStyleSheet("""
                QPushButton {
                    background: #1e1b4b;
                    color: #c084fc;
                    border: 1px solid #4338ca;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #312e81;
                    color: #ffffff;
                    border-color: #6366f1;
                }
            """)
            self.combo_key.setStyleSheet("""
                QComboBox {
                    background: #0b0f1f;
                    color: #38bdf8;
                    border: 1px solid #283256;
                    font-weight: 800;
                    font-size: 11px;
                    padding: 2px 4px;
                    border-radius: 4px;
                }
            """)
            trans_btn_qss = """
                QPushButton {
                    background: #1a2036;
                    color: #a5b4fc;
                    border: 1px solid #283256;
                    font-weight: 800;
                    font-size: 11px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #253052;
                    color: #ffffff;
                    border-color: #6366f1;
                }
            """
            self.btn_trans_down.setStyleSheet(trans_btn_qss)
            self.btn_trans_up.setStyleSheet(trans_btn_qss)
            self.btn_synth.setStyleSheet("""
                QPushButton {
                    background: #2e1065;
                    color: #d8b4fe;
                    border: 1px solid #7c3aed;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #581c87;
                    color: #ffffff;
                }
            """)
            self.btn_synth_stop.setStyleSheet("""
                QPushButton {
                    background: #1f1d2e;
                    color: #f87171;
                    border: 1px solid #4c1d28;
                    font-size: 11px;
                    font-weight: 900;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #3d141d;
                    color: #ffffff;
                    border-color: #dc2626;
                }
            """)
            self.btn_record.setStyleSheet("""
                QPushButton {
                    background: #3b1115;
                    color: #f87171;
                    border: 1px solid #7f1d1d;
                    font-weight: 800;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #4c141a;
                    color: #ffffff;
                }
            """)
            self.btn_play_take.setStyleSheet("""
                QPushButton {
                    background: #161b30;
                    color: #cbd5e1;
                    border: 1px solid #283256;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #232c4d;
                    color: #ffffff;
                }
            """)
            self.lbl_pro_hud.setStyleSheet("""
                background: #022c22;
                color: #34d399;
                font-weight: 800;
                font-size: 10px;
                padding: 3px 8px;
                border-radius: 4px;
                border: 1px solid #059669;
            """)
            self.btn_quick_suno.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #4f46e5);
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                    border: 1px solid #a855f7;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #6366f1);
                    border-color: #c084fc;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#masterTransportBar {
                    background-color: #f8fafc;
                    border-bottom: 1px solid #e2e8f0;
                }
            """)
            self.txt_title.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    font-family: 'Kantumruy Pro', 'Segoe UI', sans-serif;
                    font-weight: 700;
                    font-size: 11.5px;
                    padding: 2px 8px;
                    border-radius: 5px;
                }
                QLineEdit:focus {
                    border: 1px solid #3b82f6;
                }
            """)
            self.lbl_sig_badge.setStyleSheet("""
                background: #eff6ff;
                color: #2563eb;
                font-weight: 800;
                font-size: 11px;
                border-radius: 4px;
                border: 1px solid #bfdbfe;
            """)
            self.btn_metro.setStyleSheet("""
                QPushButton {
                    background: #eff6ff;
                    color: #2563eb;
                    border: 1px solid #bfdbfe;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #2563eb;
                    color: #ffffff;
                }
            """)
            # Crisp Light BPM Stepper: High Contrast, Solid buttons (NO empty-box look!)
            bpm_btn_qss_light = """
                QPushButton {
                    background: #e2e8f0;
                    color: #0284c7;
                    border: 1px solid #cbd5e1;
                    font-weight: 900;
                    font-size: 13px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #0284c7;
                    color: #ffffff;
                    border-color: #0369a1;
                }
            """
            self.btn_bpm_down.setStyleSheet(bpm_btn_qss_light)
            self.btn_bpm_up.setStyleSheet(bpm_btn_qss_light)
            self.spin_bpm.setStyleSheet("""
                QSpinBox {
                    background: #ffffff;
                    color: #0f172a;
                    border: 1px solid #cbd5e1;
                    font-weight: 800;
                    font-size: 11px;
                    border-radius: 4px;
                    padding: 2px 4px;
                }
                QSpinBox:focus {
                    border-color: #3b82f6;
                }
            """)
            self.btn_tap.setStyleSheet("""
                QPushButton {
                    background: #eff6ff;
                    color: #1d4ed8;
                    border: 1px solid #bfdbfe;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #dbeafe;
                }
            """)
            self.combo_key.setStyleSheet("""
                QComboBox {
                    background: #ffffff;
                    color: #0284c7;
                    border: 1px solid #cbd5e1;
                    font-weight: 800;
                    font-size: 11px;
                    padding: 2px 4px;
                    border-radius: 4px;
                }
            """)
            trans_btn_qss_light = """
                QPushButton {
                    background: #f1f5f9;
                    color: #4338ca;
                    border: 1px solid #cbd5e1;
                    font-weight: 800;
                    font-size: 11px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #4338ca;
                    color: #ffffff;
                    border-color: #3730a3;
                }
            """
            self.btn_trans_down.setStyleSheet(trans_btn_qss_light)
            self.btn_trans_up.setStyleSheet(trans_btn_qss_light)
            self.btn_synth.setStyleSheet("""
                QPushButton {
                    background: #fdf4ff;
                    color: #86198f;
                    border: 1px solid #f0abfc;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #fae8ff;
                }
            """)
            self.btn_synth_stop.setStyleSheet("""
                QPushButton {
                    background: #fef2f2;
                    color: #dc2626;
                    border: 1px solid #fecaca;
                    font-size: 11px;
                    font-weight: 900;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #fee2e2;
                    color: #b91c1c;
                    border-color: #f87171;
                }
            """)
            self.btn_record.setStyleSheet("""
                QPushButton {
                    background: #fee2e2;
                    color: #dc2626;
                    border: 1px solid #fca5a5;
                    font-weight: 800;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #fecaca;
                }
            """)
            self.btn_play_take.setStyleSheet("""
                QPushButton {
                    background: #f1f5f9;
                    color: #334155;
                    border: 1px solid #cbd5e1;
                    font-weight: 700;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #e2e8f0;
                }
            """)
            self.lbl_pro_hud.setStyleSheet("""
                background: #ecfdf5;
                color: #047857;
                font-weight: 800;
                font-size: 10px;
                padding: 3px 8px;
                border-radius: 4px;
                border: 1px solid #a7f3d0;
            """)
            self.btn_quick_suno.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #4f46e5);
                    color: #ffffff;
                    font-weight: 800;
                    font-size: 10px;
                    padding: 3px 10px;
                    border-radius: 4px;
                    border: 1px solid #4338ca;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #3730a3);
                }
            """)
