"""
Song Lyric Exporter: TXT, LRC (Karaoke Synced), JSON, and PDF Lyric Sheets.
"""

import json
from fpdf import FPDF
from app.syllable_meter import count_line_syllables

class Exporter:

    @staticmethod
    def export_txt(filepath: str, title: str, lyrics: str, metadata: dict):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"=== {title} ===\n")
            if metadata:
                f.write(f"Genre: {metadata.get('genre', 'Unknown')} ({metadata.get('region', 'Global')})\n")
                f.write(f"Language: {metadata.get('language', 'English')} | BPM: {metadata.get('bpm', '120')}\n")
                f.write(f"Mood: {metadata.get('mood', '')} | Theme: {metadata.get('theme', '')}\n")
                f.write("=" * (len(title) + 8) + "\n\n")
            f.write(lyrics)
            f.write("\n\n---\nGenerated with SMG Suno AI Lyric Writer (Gemini Engine)\n")

    @staticmethod
    def export_lrc(filepath: str, title: str, lyrics: str, bpm_str: str = "120"):
        """
        Generate timed .lrc (Karaoke format) estimating time based on BPM and bars.
        Assuming average 4 beats per bar and 1 bar per 8-syllable phrase.
        """
        try:
            # Extract number from bpm_str e.g. "120 BPM" -> 120
            clean_bpm = "".join(filter(str.isdigit, bpm_str[:4]))
            bpm = int(clean_bpm) if clean_bpm else 120
        except Exception:
            bpm = 120

        seconds_per_beat = 60.0 / max(40, bpm)
        current_time = 3.0 # start at 3s

        lrc_lines = [
            f"[ti:{title}]",
            f"[ar:AI Songwriter Studio]",
            f"[al:World Lyric Album]",
            f"[by:Gemini AI]",
            ""
        ]

        for line in lyrics.split("\n"):
            stripped = line.strip()
            if not stripped:
                current_time += seconds_per_beat * 2 # brief rest
                continue

            # Format current_time as [mm:ss.xx]
            mins = int(current_time // 60)
            secs = current_time % 60
            time_tag = f"[{mins:02d}:{secs:05.2f}]"

            lrc_lines.append(f"{time_tag}{stripped}")

            # Advance time according to syllables
            syllables = count_line_syllables(stripped)
            duration = max(2.0, (syllables / 3.0) * seconds_per_beat * 2)
            current_time += duration

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lrc_lines))

    @staticmethod
    def export_json(filepath: str, title: str, lyrics: str, metadata: dict):
        data = {
            "title": title,
            "metadata": metadata,
            "lyrics": lyrics,
            "sections": []
        }
        # Parse sections
        current_section = {"name": "Intro", "lines": []}
        for line in lyrics.split("\n"):
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                if current_section["lines"]:
                    data["sections"].append(current_section)
                current_section = {"name": stripped.strip("[]"), "lines": []}
            elif stripped:
                current_section["lines"].append({
                    "text": stripped,
                    "syllables": count_line_syllables(stripped)
                })
        if current_section["lines"]:
            data["sections"].append(current_section)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def export_pdf(filepath: str, title: str, lyrics: str, metadata: dict):
        class LyricPDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 18)
                self.cell(0, 10, title, border=False, align="C")
                self.ln(7)
                self.set_font("Helvetica", "I", 10)
                sub = f"{metadata.get('genre', 'Global')} | {metadata.get('bpm', '120 BPM')} | {metadata.get('mood', 'Vibrant')}"
                self.cell(0, 8, sub, border=False, align="C")
                self.ln(10)
                # Separator line
                self.set_draw_color(180, 180, 200)
                self.line(15, self.get_y(), 195, self.get_y())
                self.ln(6)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(140, 140, 150)
                self.cell(0, 10, f"Page {self.page_no()} | Created with WorldLyric AI Studio (Gemini Engine)", align="C")

        pdf = LyricPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        for line in lyrics.split("\n"):
            stripped = line.strip()
            if not stripped:
                pdf.ln(3)
                continue

            # Check if section header
            if stripped.startswith("[") and stripped.endswith("]"):
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(90, 50, 180) # Purple section header
                pdf.cell(0, 8, stripped, border=False, align="L")
                pdf.ln(6)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(30, 30, 40)
                # Clean characters for latin-1 safety if needed
                safe_line = stripped.encode("latin-1", "replace").decode("latin-1")
                pdf.cell(0, 6, safe_line, border=False, align="L")
                pdf.ln(5)

        pdf.output(filepath)

    @staticmethod
    def export_html_lead_sheet(filepath: str, title: str, lyrics: str, metadata: dict):
        """
        Export a high-fidelity printable Lead Sheet / Chord Chart supporting
        full Unicode (Khmer script & International) with chord badges above lyrics.
        """
        import re
        import html

        genre = metadata.get("genre", "Global Music")
        bpm = metadata.get("bpm", "120 BPM")
        mood = metadata.get("mood", "")

        rendered_body = []
        for line in lyrics.split("\n"):
            stripped = line.strip()
            if not stripped:
                rendered_body.append('<div class="spacer"></div>')
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                safe_tag = html.escape(stripped)
                rendered_body.append(f'<div class="section-badge">{safe_tag}</div>')
            else:
                def chord_repl(m):
                    c = m.group(1)
                    return f'<span class="chord-pill">{html.escape(c)}</span>'

                formatted = re.sub(r'\[([A-G][#b]?(?:m|maj7|m7|7|dim|aug|sus4|sus2|add9)?(?:\/[A-G][#b]?)?)\]', chord_repl, html.escape(stripped))
                rendered_body.append(f'<div class="lyric-line">{formatted}</div>')

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)} — Lead Sheet</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Kantumruy Pro", "Noto Sans Khmer", sans-serif;
        background: #f8fafc;
        color: #1e293b;
        margin: 0;
        padding: 40px 20px;
    }}
    .sheet-card {{
        max-width: 820px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 40px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }}
    .header {{
        text-align: center;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 20px;
        margin-bottom: 30px;
    }}
    .title {{
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
        margin: 0 0 8px 0;
    }}
    .meta-bar {{
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
    }}
    .section-badge {{
        font-size: 15px;
        font-weight: 800;
        color: #2563eb;
        margin: 24px 0 8px 0;
        padding-bottom: 4px;
        border-bottom: 1px dashed #cbd5e1;
    }}
    .lyric-line {{
        font-size: 16px;
        line-height: 2.2;
        color: #334155;
    }}
    .chord-pill {{
        background: #eff6ff;
        color: #1d4ed8;
        font-weight: 800;
        font-family: monospace;
        font-size: 13px;
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid #bfdbfe;
        margin: 0 3px;
        vertical-align: 2px;
    }}
    .spacer {{
        height: 12px;
    }}
    .footer {{
        margin-top: 40px;
        padding-top: 15px;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        font-size: 12px;
        color: #94a3b8;
    }}
    @media print {{
        body {{ background: #ffffff; padding: 0; }}
        .sheet-card {{ border: none; box-shadow: none; padding: 20px; }}
    }}
</style>
</head>
<body>
<div class="sheet-card">
    <div class="header">
        <h1 class="title">{html.escape(title)}</h1>
        <div class="meta-bar">Genre: {html.escape(genre)} &bull; Tempo: {html.escape(bpm)} &bull; Mood: {html.escape(mood)}</div>
    </div>
    <div class="content">
        {"".join(rendered_body)}
    </div>
    <div class="footer">
        Generated with SMG Suno AI Lyric Writer &bull; Studio Lead Sheet &bull; All Rights Reserved
    </div>
</div>
</body>
</html>"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

    @staticmethod
    def export_srt(filepath: str, title: str, lyrics: str, bpm_str: str = "120"):
        """
        Generate standard .srt Subtitles (YouTube, TikTok, Premiere Pro, CapCut ready).
        Calculates realistic syllable duration and outputs formatted subtitle blocks.
        """
        import re
        try:
            clean_bpm = "".join(filter(str.isdigit, bpm_str[:4]))
            bpm = int(clean_bpm) if clean_bpm else 120
        except Exception:
            bpm = 120

        seconds_per_beat = 60.0 / max(40, min(240, bpm))
        current_time = 2.0  # 2s lead-in

        def fmt_time(t: float) -> str:
            hrs = int(t // 3600)
            mins = int((t % 3600) // 60)
            secs = int(t % 60)
            millis = int(round((t - int(t)) * 1000))
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        srt_blocks = []
        sub_idx = 1

        for line in lyrics.split("\n"):
            stripped = line.strip()
            if not stripped:
                current_time += seconds_per_beat * 1.5
                continue

            # Section marker line
            if stripped.startswith("[") and stripped.endswith("]"):
                clean_sec = stripped.strip("[]")
                end_sec = current_time + (seconds_per_beat * 2)
                srt_blocks.append(f"{sub_idx}\n{fmt_time(current_time)} --> {fmt_time(end_sec)}\n[{clean_sec}]\n")
                sub_idx += 1
                current_time = end_sec + 0.2
                continue

            # Remove inline chords like [Am]
            clean_text = re.sub(r'\[[A-G][^\]]*\]', '', stripped).strip()
            if not clean_text:
                continue

            syllables = count_line_syllables(clean_text)
            duration = max(1.8, (syllables / 3.2) * seconds_per_beat * 2)
            end_time = current_time + duration

            srt_blocks.append(f"{sub_idx}\n{fmt_time(current_time)} --> {fmt_time(end_time)}\n{clean_text}\n")
            sub_idx += 1
            current_time = end_time + 0.25

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_blocks))

    @staticmethod
    def export_chordpro(filepath: str, title: str, lyrics: str, metadata: dict):
        """
        Export in standard ChordPro format (.cho / .chopro) for digital music stands (OnSong, SongBook).
        """
        lines = [
            f"{{title: {title}}}",
            f"{{artist: AI Songwriter Studio}}",
            f"{{tempo: {metadata.get('bpm', '120')}}}",
            f"{{key: {metadata.get('key', 'Am')}}}",
            ""
        ]
        for line in lyrics.split("\n"):
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                sec_name = stripped.strip("[]")
                lines.append(f"{{comment: {sec_name}}}")
            else:
                lines.append(line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    @staticmethod
    def export_clean_vocal_sheet(filepath: str, title: str, lyrics: str):
        """
        Export pure vocals text sheet (strips chords and bracketed tags) for teleprompter/singer.
        """
        import re
        clean_lines = [f"=== {title.upper()} (VOCALIST SHEET) ===\n"]
        for line in lyrics.split("\n"):
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                clean_lines.append(f"\n--- {stripped.strip('[]').upper()} ---")
            else:
                pure_text = re.sub(r'\[[A-G][^\]]*\]', '', stripped).strip()
                if pure_text:
                    clean_lines.append(pure_text)
                elif not stripped:
                    clean_lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(clean_lines))
