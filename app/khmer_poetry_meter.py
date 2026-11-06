"""
Khmer Classical Poetic Meter & Rhyme Map Engine.
Analyzes traditional Khmer poetic forms:
- ពាក្យ ៧ (Péak 7)
- ពាក្យ ៨ (Péak 8)
- ព្រហ្មគីតិ (Brahmagiti / Péak 5)
- កាកគតិ (Kakagati)
- ភុជង្គលីលា (Bhujangalila / Péak 6)
Features accurate Khmer syllable segmentation, phonetic rhyme extraction,
rhyme link validation (ជួនក្នុង & ជួនឆ្លងវគ្គ), and classical rhyme dictionary.
"""

import re
import unicodedata
from typing import List, Dict, Tuple, Optional

# Khmer Unicode constants
KHMER_CONSONANTS = set(chr(cp) for cp in range(0x1780, 0x17A3))
KHMER_INDEP_VOWELS = set(chr(cp) for cp in range(0x17A3, 0x17B4))
KHMER_DEP_VOWELS = set(chr(cp) for cp in range(0x17B6, 0x17C6))
COENG = "\u17D2" # Subscript sign (្)
BANTOC = "\u17CB" # ់
NIKAHIT = "\u17C6" # ំ
REAHMUK = "\u17C7" # ះ
TOANDAKHIAT = "\u17CD" # ៍
SAMYOK = "\u17D0" # ័
ROBAT = "\u17CC" # ៌

# Common Khmer Rhyme Dictionary for instant songwriting assistance
KHMER_RHYME_FAMILIES = {
    "អាយ": ["កាយ", "ឆ្ងាយ", "រាយ", "សាយ", "ស្តាយ", "ម្តាយ", "ស្រាយ", "ខ្វាយ", "ងាយ", "បាចសាច"],
    "អែ": ["ស្នេហ៍", "ក្បែរ", "ថែ", "ស្រែ", "ខែ", "តែ", "បែរ", "ចែចូវ"],
    "អេ": ["ទេ", "វេ", "មេ", "គេ", "ចេក", "មេឃ"],
    "អិត": ["ចិត្ត", "ពិត", "គិត", "ជិត", "ជីវិត", "ស្និទ្ធ", "ប្រឌិត", "ងងឹត"],
    "អី": ["ស្រី", "ថ្មី", "បី", "ដី", "ល្បី", "ឆោមឆាយ", "ស្រស់ស្រី", "មេត្រី", "សួស្តី"],
    "អូន": ["អូន", "ក្បូន", "ប្អូន", "កូន", "សូន្យ", "នួន"],
    "អ៊ុង": ["គង់", "បង", "ចង់", "ផង់", "ត្រង់", "លង់", "ផ្ចង់"],
    "អៀវ": ["រៀវ", "ស្រៀវ", "ខៀវ", "ព្រលៀវ", "រៀបរាប់"],
    "អួង": ["ដួង", "ហួង", "ព្រលឹង", "រុងរឿង", "ទ្រូង"],
    "អ៊ឺ": ["ឈឺ", "ឮ", "ពន្លឺ", "រងរឺ"],
    "អា": ["វា", "មា", "ផ្កា", "សច្ចា", "ចេតនា", "មេត្តា", "គ្រួសារ", "ខ្លោចផ្សា"]
}

# Poetic forms specifications
KHMER_POETRY_FORMS = {
    "peak_7": {
        "name": "ពាក្យ ៧ (Péak 7 - Seven Syllables)",
        "lines_per_stanza": 4,
        "line_syllables": [7, 7, 7, 7],
        "rhyme_rules": [
            {"from": (0, 6), "to": (1, 3), "type": "Internal Stanza Rhyme 1 (ឃ្លា១ ជួន ឃ្លា២)"},
            {"from": (1, 6), "to": (2, 3), "type": "Internal Stanza Rhyme 2 (ឃ្លា២ ជួន ឃ្លា៣)"},
            {"from": (2, 6), "to": (3, 3), "type": "Internal Stanza Rhyme 3 (ឃ្លា៣ ជួន ឃ្លា៤)"},
        ],
        "inter_stanza_rule": {"from": (3, 6), "to": (1, 6), "type": "Inter-Stanza Rhyme (ជួនឆ្លងវគ្គ)"},
        "desc": "The most widely used classical Khmer poetic meter. Found in ancient epic poems and Sinn Sisamouth romantic ballads."
    },
    "peak_8": {
        "name": "ពាក្យ ៨ (Péak 8 - Eight Syllables)",
        "lines_per_stanza": 4,
        "line_syllables": [8, 8, 8, 8],
        "rhyme_rules": [
            {"from": (0, 7), "to": (1, 4), "alt_to": (1, 2), "type": "Internal Stanza Rhyme 1 (ឃ្លា១ ជួន ឃ្លា២)"},
            {"from": (1, 7), "to": (2, 4), "alt_to": (2, 2), "type": "Internal Stanza Rhyme 2 (ឃ្លា២ ជួន ឃ្លា៣)"},
            {"from": (2, 7), "to": (3, 4), "alt_to": (3, 2), "type": "Internal Stanza Rhyme 3 (ឃ្លា៣ ជួន ឃ្លា៤)"},
        ],
        "inter_stanza_rule": {"from": (3, 7), "to": (1, 7), "type": "Inter-Stanza Rhyme (ជួនឆ្លងវគ្គ)"},
        "desc": "Majestic narrative meter used for classical storytelling, high poetry, and dramatic lyric hooks."
    },
    "brahmagiti": {
        "name": "ព្រហ្មគីតិ (Brahmagiti / Péak 5)",
        "lines_per_stanza": 4,
        "line_syllables": [5, 5, 5, 5],
        "rhyme_rules": [
            {"from": (0, 4), "to": (1, 2), "type": "Internal Stanza Rhyme 1"},
            {"from": (1, 4), "to": (2, 2), "type": "Internal Stanza Rhyme 2"},
            {"from": (2, 4), "to": (3, 2), "type": "Internal Stanza Rhyme 3"},
        ],
        "inter_stanza_rule": {"from": (3, 4), "to": (1, 4), "type": "Inter-Stanza Rhyme (ជួនឆ្លងវគ្គ)"},
        "desc": "Traditional chanting and moral teaching poetry with a contemplative, steady rhythm."
    },
    "kakagati": {
        "name": "កាកគតិ (Kakagati - 7-Line Stanza)",
        "lines_per_stanza": 7,
        "line_syllables": [4, 4, 4, 6, 4, 4, 4],
        "rhyme_rules": [
            {"from": (0, 3), "to": (1, 3), "type": "Line 1-2 Rhyme"},
            {"from": (2, 3), "to": (3, 2), "type": "Line 3-4 Rhyme"},
            {"from": (3, 2), "to": (4, 3), "type": "Line 4-5 Rhyme"},
            {"from": (5, 3), "to": (6, 3), "type": "Line 6-7 Rhyme"},
        ],
        "desc": "Dynamic crow-walking cadence with rhythmic stops and short punchy lines."
    },
    "bhujangalila": {
        "name": "ភុជង្គលីលា (Bhujangalila / Péak 6)",
        "lines_per_stanza": 4,
        "line_syllables": [6, 6, 6, 6],
        "rhyme_rules": [
            {"from": (0, 5), "to": (1, 3), "type": "Internal Rhyme 1"},
            {"from": (1, 5), "to": (2, 3), "type": "Internal Rhyme 2"},
            {"from": (2, 5), "to": (3, 3), "type": "Internal Rhyme 3"},
        ],
        "desc": "Serpentine, dancing rhythm named after the graceful movements of the Naga snake."
    }
}


def segment_khmer_syllables(text: str) -> List[str]:
    """
    Accurately segment Khmer text into individual spoken syllables.
    Handles consonant clusters (Coeng), vowels, diacritics, and compound words.
    """
    clean = re.sub(r"\[.*?\]|\(.*?\)", "", text).strip()
    if not clean:
        return []

    # If the user already wrote words separated by spaces:
    words = clean.split()
    if len(words) >= 4:
        # Space-delimited line - treat each token as syllable, expanding only obvious multi-syllables
        tokens = []
        for w in words:
            # Check for common multi-syllable compounds without spaces
            if w == "កល្យាណ":
                tokens.extend(["ក", "ល្យាណ"])
            elif w == "ស្រណោះ":
                tokens.extend(["ស្រ", "ណោះ"])
            elif w == "សួស្តី":
                tokens.extend(["សួ", "ស្តី"])
            elif w == "សុខទុក្ខ":
                tokens.extend(["សុខ", "ទុក្ខ"])
            else:
                tokens.append(w)
        return tokens

    # Continuous Khmer text without spaces - regex syllable segmentation
    tokens = []
    khmer_syl_regex = re.compile(
        r"([\u1780-\u17A2\u17A3-\u17B3]"              # Base consonant or independent vowel
        r"(?:\u17D2[\u1780-\u17A2])*"                 # Subscript consonants (Coeng)
        r"[\u17B6-\u17C5]?"                            # Dependent vowel
        r"[\u17C6-\u17D1\u17D3]?"                      # Diacritics
        r"(?:[\u1780-\u17A2](?:\u17D2[\u1780-\u17A2])*(?:[\u17CB\u17CD\u17CC])?)?" # Final coda cluster
        r")"
    )

    for word in words:
        has_khmer = any(0x1780 <= ord(c) <= 0x17FF for c in word)
        if has_khmer:
            matches = khmer_syl_regex.findall(word)
            if matches:
                for m in matches:
                    if m.strip():
                        tokens.append(m.strip())
            else:
                tokens.append(word)
        else:
            tokens.append(word)

    return tokens


# Khmer phonetic coda equivalence classes (e.g. ណ = ន = /n/, ត = ដ = ស = /t/)
KHMER_CODA_CLASSES = {
    "n": {"ន", "ណ", "ល"},
    "t": {"ត", "ថ", "ទ", "ធ", "ដ", "ឋ", "ឌ", "ឍ", "ស"},
    "k": {"ក", "ខ", "គ", "ឃ"},
    "p": {"ប", "ផ", "ព", "ភ"},
    "m": {"ម", NIKAHIT},
    "ng": {"ង"},
    "y": {"យ"},
    "w": {"វ"},
}

def extract_khmer_rhyme_sound(syllable: str) -> str:
    """
    Extract the phonetic vowel + coda signature of a Khmer syllable for rhyme matching.
    e.g. 'ស្នេហ៍' -> 'អែ', 'ចិត្ត' -> 'អិត', 'កាយ' -> 'អាយ', 'ប្រាណ' -> 'អា_n', 'ខាន' -> 'អា_n'
    """
    if not syllable:
        return ""

    # Look for known rhyme families first
    for key, words in KHMER_RHYME_FAMILIES.items():
        if any(w in syllable for w in words):
            return key

    # Extract dependent vowels and diacritics
    vowels = []
    for char in syllable:
        if char in KHMER_DEP_VOWELS or char in (NIKAHIT, REAHMUK, BANTOC, SAMYOK):
            vowels.append(char)

    # Extract final coda consonant
    coda_char = ""
    for i in range(len(syllable) - 1, 0, -1):
        if syllable[i] in KHMER_CONSONANTS and (i == 0 or syllable[i-1] != COENG):
            coda_char = syllable[i]
            break

    # Map coda char to phonetic class
    coda_class = coda_char
    for pclass, char_set in KHMER_CODA_CLASSES.items():
        if coda_char in char_set:
            coda_class = pclass
            break

    vowel_str = "".join(vowels) if vowels else "អ"
    return f"{vowel_str}_{coda_class}"


def check_rhyme_match(syl_a: str, syl_b: str) -> Tuple[bool, str]:
    """
    Determines if two syllables rhyme.
    Returns (is_rhyme, match_quality: 'PERFECT' | 'NEAR' | 'NONE')
    """
    if not syl_a or not syl_b:
        return False, "NONE"

    # Exact syllable match
    if syl_a == syl_b:
        return True, "PERFECT"

    sound_a = extract_khmer_rhyme_sound(syl_a)
    sound_b = extract_khmer_rhyme_sound(syl_b)

    if sound_a and sound_b and sound_a == sound_b:
        return True, "PERFECT"

    # Check if they share any rhyme family
    for family, words in KHMER_RHYME_FAMILIES.items():
        has_a = any(w in syl_a for w in words)
        has_b = any(w in syl_b for w in words)
        if has_a and has_b:
            return True, "PERFECT"

    return False, "NONE"


class KhmerPoetryMeterAnalyzer:
    """
    Validates stanzas against classical Khmer poetic meters.
    Generates rhyme maps with glowing connection pills.
    """

    @classmethod
    def analyze_stanza(cls, lines: List[str], form_id: str = "peak_7") -> Dict:
        form = KHMER_POETRY_FORMS.get(form_id, KHMER_POETRY_FORMS["peak_7"])
        expected_lines = form["lines_per_stanza"]
        expected_sylls = form["line_syllables"]

        line_results = []
        for i in range(expected_lines):
            raw_line = lines[i] if i < len(lines) else ""
            syllables = segment_khmer_syllables(raw_line)
            actual_count = len(syllables)
            expected_count = expected_sylls[i] if i < len(expected_sylls) else 7

            status = "PERFECT"
            if actual_count == expected_count:
                status = "PERFECT"
            elif abs(actual_count - expected_count) == 1:
                status = "TOLERABLE" # Poetic license
            else:
                status = "BREACH"

            line_results.append({
                "line_index": i,
                "raw_line": raw_line,
                "syllables": syllables,
                "actual_count": actual_count,
                "expected_count": expected_count,
                "status": status
            })

        # Check rhyme rules
        rhyme_checks = []
        for rule in form.get("rhyme_rules", []):
            f_line, f_syl = rule["from"]
            t_line, t_syl = rule["to"]

            syl1 = ""
            syl2 = ""
            if f_line < len(line_results) and f_syl < len(line_results[f_line]["syllables"]):
                syl1 = line_results[f_line]["syllables"][f_syl]
            if t_line < len(line_results) and t_syl < len(line_results[t_line]["syllables"]):
                syl2 = line_results[t_line]["syllables"][t_syl]

            is_rhyme, quality = check_rhyme_match(syl1, syl2)
            rhyme_checks.append({
                "rule_name": rule["type"],
                "from_pos": f"Line {f_line+1}, Syl {f_syl+1}",
                "to_pos": f"Line {t_line+1}, Syl {t_syl+1}",
                "syl1": syl1,
                "syl2": syl2,
                "is_rhyme": is_rhyme,
                "quality": quality
            })

        return {
            "form": form,
            "lines": line_results,
            "rhyme_checks": rhyme_checks
        }
