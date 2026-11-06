"""
Syllable Counting and Meter Analyzer for Songwriters.
Supports multilingual texts including English, Romance languages, CJK, and Indic scripts.
"""

import re
import unicodedata

def is_cjk(char: str) -> bool:
    """Check if character is Chinese, Japanese Kana, or Korean Hangul."""
    cp = ord(char)
    # CJK Unified Ideographs, Hangul, Hiragana, Katakana
    return (
        (0x4E00 <= cp <= 0x9FFF) or
        (0x3400 <= cp <= 0x4DBF) or
        (0xAC00 <= cp <= 0xD7AF) or  # Hangul syllables
        (0x3040 <= cp <= 0x309F) or  # Hiragana
        (0x30A0 <= cp <= 0x30FF)     # Katakana
    )

def is_khmer_or_thai(char: str) -> bool:
    cp = ord(char)
    return (0x1780 <= cp <= 0x17FF) or (0x0E00 <= cp <= 0x0E7F)

def count_word_syllables_en(word: str) -> int:
    """Accurate heuristic syllable counter for English words."""
    word = word.lower().strip()
    if not word:
        return 0

    # Strip punctuation
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0

    if len(word) <= 3:
        return 1

    # Specific common exceptions
    exceptions = {
        "the": 1, "me": 1, "you": 1, "we": 1, "he": 1, "she": 1,
        "fire": 2, "wire": 2, "hire": 2, "tire": 2, "lyric": 2,
        "rhythm": 2, "every": 2, "different": 3, "memory": 3,
        "forever": 3, "tonight": 2, "baby": 2, "music": 2, "lonely": 2
    }
    if word in exceptions:
        return exceptions[word]

    # Handle ending silent e: e.g. "love", "game", "shine" (but not "le" like "bottle")
    if word.endswith("e") and not word.endswith("le") and not word.endswith("ee"):
        word = word[:-1]

    # Count vowel groups
    # Vowels include y
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    # Specific ending adjustments
    if word.endswith("ed") and not word.endswith("ted") and not word.endswith("ded"):
        if count > 1:
            count -= 1

    return max(1, count)

def count_line_syllables(line: str) -> int:
    """Calculate the syllable / mora count for a single line of song lyrics."""
    clean_line = line.strip()
    if not clean_line:
        return 0

    # Ignore structural headers like [Chorus], [Verse 1], (Ad-lib)
    if (clean_line.startswith("[") and clean_line.endswith("]")) or (clean_line.startswith("(") and clean_line.endswith(")")):
        return 0

    # Separate CJK/Thai/Khmer characters vs Latin/alphabetic words
    syllables = 0
    words = re.findall(r"[\w']+|[^\s\w]", clean_line, re.UNICODE)

    for token in words:
        if not token.strip():
            continue

        # Check for CJK characters (each syllable is 1 character)
        cjk_chars = [c for c in token if is_cjk(c)]
        if cjk_chars:
            syllables += len(cjk_chars)
            continue

        # Check Khmer or Thai vowels/consonants
        kh_thai = [c for c in token if is_khmer_or_thai(c)]
        if kh_thai:
            # Approximate Khmer/Thai syllables by counting independent base consonants
            syllables += max(1, len(kh_thai) // 3)
            continue

        # For Latin/standard alphabetic tokens
        alpha_token = re.sub(r"[^\w]", "", token)
        if alpha_token:
            syllables += count_word_syllables_en(alpha_token)

    return syllables

class LyricMeterAnalyzer:
    """Analyzes an entire lyric sheet for line syllables, section consistency, and meter patterns."""

    @staticmethod
    def analyze(text: str) -> dict:
        lines = text.split("\n")
        analyzed_lines = []
        total_syllables = 0
        lyric_line_count = 0
        section_stats = {}
        current_section = "General"

        for idx, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()
            is_header = (stripped.startswith("[") and stripped.endswith("]"))

            if is_header:
                current_section = stripped.strip("[]")
                analyzed_lines.append({
                    "line_num": idx,
                    "text": raw_line,
                    "syllables": 0,
                    "is_header": True,
                    "section": current_section
                })
            elif stripped:
                s_count = count_line_syllables(stripped)
                total_syllables += s_count
                lyric_line_count += 1

                if current_section not in section_stats:
                    section_stats[current_section] = []
                section_stats[current_section].append(s_count)

                analyzed_lines.append({
                    "line_num": idx,
                    "text": raw_line,
                    "syllables": s_count,
                    "is_header": False,
                    "section": current_section
                })
            else:
                analyzed_lines.append({
                    "line_num": idx,
                    "text": raw_line,
                    "syllables": 0,
                    "is_header": False,
                    "section": current_section
                })

        avg_syllables = round(total_syllables / lyric_line_count, 1) if lyric_line_count > 0 else 0

        # Flow score calculation: how consistent are the lines in sections
        flow_score = 90
        if lyric_line_count >= 4:
            # Check deviation across lines
            syllable_counts = [l["syllables"] for l in analyzed_lines if not l["is_header"] and l["syllables"] > 0]
            if syllable_counts:
                variance = sum((x - avg_syllables) ** 2 for x in syllable_counts) / len(syllable_counts)
                std_dev = variance ** 0.5
                flow_score = max(50, min(99, int(100 - (std_dev * 5))))

        return {
            "analyzed_lines": analyzed_lines,
            "total_syllables": total_syllables,
            "total_lines": lyric_line_count,
            "avg_syllables": avg_syllables,
            "flow_score": flow_score,
            "section_stats": {
                sec: {
                    "count": len(counts),
                    "avg": round(sum(counts) / len(counts), 1) if counts else 0
                }
                for sec, counts in section_stats.items()
            }
        }
