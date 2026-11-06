"""
Hit Potential & AI Vocal Safety Analyzer for Commercial Songs.
Evaluates lyrics for Earworm Catchiness, Hook Retention, Syllable Flow Balance,
and Suno/Udio AI Vocal Safety (preventing vocal slurring and rushed cadences).
"""

import re
from typing import Dict, Any, List
from app.syllable_meter import count_line_syllables


class HitAnalyzer:

    @classmethod
    def analyze(cls, lyrics: str, bpm: int = 120) -> Dict[str, Any]:
        """Comprehensive analysis of lyrical commercial hit potential and AI vocal delivery safety."""
        lines = [line.strip() for line in lyrics.split("\n")]
        raw_lines = [l for l in lines if l]
        text_lines = [l for l in raw_lines if not (l.startswith("[") and l.endswith("]")) and not l.startswith("SEC")]

        if not text_lines:
            return {
                "hit_score": 0,
                "hook_score": 0,
                "safety_score": 100,
                "meter_score": 0,
                "safety_grade": "No Lyrics",
                "safety_color": "#64748b",
                "sections": [],
                "warnings": ["Please enter or generate lyrics to analyze hit potential."],
                "strengths": [],
                "overcrowded_lines": []
            }

        # 1. Section Structure & Dynamic Energy Arc
        sections = []
        current_sec_name = "Intro"
        current_sec_lines = []

        energy_map = {
            "intro": 35,
            "verse": 50,
            "pre-chorus": 75,
            "build": 80,
            "chorus": 100,
            "post-chorus": 85,
            "hook": 100,
            "drop": 95,
            "bridge": 60,
            "breakdown": 45,
            "solo": 80,
            "outro": 40,
            "ending": 30
        }

        ignored_tags = {"title", "style", "tempo", "bpm", "key", "genre", "mood", "instruments", "vocal", "tags"}

        for line in raw_lines:
            # Check if line is purely chords like [Am] - [F] - [C] - [G]
            chords_stripped = re.sub(r'\[[A-G][b#]?[^\]]*\]|[-/\s]', '', line, flags=re.IGNORECASE)
            if not chords_stripped:
                continue

            if (line.startswith("[") and line.endswith("]")) or line.startswith("SEC"):
                clean_tag = line.strip("[]").replace("SEC", "").strip()
                tag_prefix = clean_tag.split(":")[0].strip().lower()
                if tag_prefix in ignored_tags:
                    continue

                sec_type = tag_prefix
                matched_energy = 50
                for k, v in energy_map.items():
                    if k in sec_type:
                        matched_energy = v
                        break
                sections.append({
                    "name": clean_tag.split(":")[0].strip(),
                    "full_name": clean_tag[:28],
                    "type": sec_type,
                    "energy": matched_energy,
                    "line_count": len(current_sec_lines)
                })
                current_sec_name = clean_tag
                current_sec_lines = []
            else:
                current_sec_lines.append(line)

        # 2. Hook & Earworm Retention (Chorus repetition & repetition of key phrases)
        chorus_occurrences = 0
        repeated_lines_count = 0
        seen_lines = {}
        for l in text_lines:
            # Clean chords like [Am]
            clean_l = re.sub(r'\[[A-G][^\]]*\]', '', l).strip().lower()
            if clean_l:
                seen_lines[clean_l] = seen_lines.get(clean_l, 0) + 1

        for count in seen_lines.values():
            if count >= 2:
                repeated_lines_count += 1

        for s in sections:
            if "chorus" in s["type"] or "hook" in s["type"] or "បន្ទរ" in s["type"]:
                chorus_occurrences += 1

        hook_score = 45
        if chorus_occurrences >= 2:
            hook_score += 35
        elif chorus_occurrences == 1:
            hook_score += 15

        if repeated_lines_count >= 2:
            hook_score += 20
        hook_score = min(100, hook_score)

        # 3. AI Vocal Safety (Suno & Udio non-slur guarantee)
        overcrowded_lines = []
        syllable_counts = []
        for l in text_lines:
            clean_l = re.sub(r'\[[A-G][^\]]*\]', '', l).strip()
            syl = count_line_syllables(clean_l)
            if syl > 0:
                syllable_counts.append(syl)
                if syl >= 14:
                    overcrowded_lines.append({
                        "line": clean_l[:45] + ("..." if len(clean_l) > 45 else ""),
                        "syllables": syl,
                        "tip": "Split into 2 lines or add commas for singer breath"
                    })

        if syllable_counts:
            ideal_ratio = sum(1 for s in syllable_counts if 5 <= s <= 11) / len(syllable_counts)
            overcrowd_penalty = min(50, len(overcrowded_lines) * 12)
            safety_score = max(30, int(ideal_ratio * 100 - overcrowd_penalty))
        else:
            safety_score = 100

        # Safety badge & color
        if safety_score >= 90:
            safety_grade = "Studio Safe (Zero Slur Risk)"
            safety_color = "#10b981"
        elif safety_score >= 75:
            safety_grade = "Good Phrasing (Natural Delivery)"
            safety_color = "#06b6d4"
        elif safety_score >= 60:
            safety_grade = "Moderate (Some Fast Lines)"
            safety_color = "#f59e0b"
        else:
            safety_grade = "Overcrowded (High Slur Risk)"
            safety_color = "#ef4444"

        # 4. Syllable Meter Balance & Cadence
        if syllable_counts:
            avg_syl = sum(syllable_counts) / len(syllable_counts)
            variance = sum((s - avg_syl) ** 2 for s in syllable_counts) / len(syllable_counts)
            meter_score = max(40, min(100, int(100 - variance * 2.5)))
        else:
            meter_score = 80

        # 5. Overall Commercial Hit Score
        overall_hit = int(0.40 * hook_score + 0.35 * safety_score + 0.25 * meter_score)

        # 6. Actionable Strengths & Improvement Tips
        strengths = []
        warnings = []

        if chorus_occurrences >= 2:
            strengths.append("✅ Strong Multi-Chorus Structure: High radio and Spotify retention.")
        if repeated_lines_count >= 2:
            strengths.append("✅ Catchy Earworm Hook: Memorable repeated lyrical motifs detected.")
        if 6.5 <= (sum(syllable_counts) / max(1, len(syllable_counts))) <= 9.5:
            strengths.append("✅ Classical Ballad & Pop Cadence: Syllable count fits natural vocal breathing.")

        if chorus_occurrences == 0:
            warnings.append("⚠️ Missing Clear Chorus: Add a [Chorus] section to boost hook memorability.")
        if len(overcrowded_lines) > 0:
            warnings.append(f"⚠️ {len(overcrowded_lines)} Overcrowded Lines: Lines with >13 syllables may be rushed by Suno AI.")
        if meter_score < 65:
            warnings.append("⚠️ Syllable Variance: Some lines are very short while others are long. Try balancing meter.")

        return {
            "hit_score": overall_hit,
            "hook_score": hook_score,
            "safety_score": safety_score,
            "meter_score": meter_score,
            "safety_grade": safety_grade,
            "safety_color": safety_color,
            "sections": sections,
            "strengths": strengths,
            "warnings": warnings,
            "overcrowded_lines": overcrowded_lines,
            "total_lines": len(text_lines),
            "avg_syllables": round(sum(syllable_counts) / max(1, len(syllable_counts)), 1) if syllable_counts else 0
        }
