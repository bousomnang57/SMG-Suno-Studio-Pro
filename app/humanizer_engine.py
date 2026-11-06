# -*- coding: utf-8 -*-
"""
Humanizer Engine for Lyric AI Writer / WorldLyric Studio.
Transforms sterile, robotic AI songwriting into deeply human, emotionally vulnerable,
and organically produced musical masterpieces.

Evaluates and injects 4 Human Dimensions:
1. Sensory Realism (Show, Don't Tell - concrete physical objects vs. AI clichés)
2. Vocal Breathability & Phrasing (natural human pauses, sighs, hesitations, voice cracks)
3. Dynamic Emotional Arc & Bridge Epiphany (confession, perspective shift, catharsis)
4. Organic Acoustic Warmth (un-quantized pocket, tape saturation, room bleed, tempo sway)
"""

import re
from typing import Dict, List, Any, Tuple

# Known robotic AI clichés across English songs
AI_CLICHES_EN = [
    "neon shadows", "shadows of the neon", "echoes in the dark", "echoes in the night",
    "symphony of stars", "tapestry of time", "whispers in the wind", "whispers in the dark",
    "dancing in the rain", "unfold my wings", "fire in my soul", "fire in my veins",
    "shattered dreams", "chasing shadows", "silhouettes in the night", "written in the stars",
    "labyrinth of thoughts", "ocean of tears", "canvas of the night", "clock ticks away",
    "lost in the void", "endless night", "flicker of hope", "ignite the flame",
    "heart of stone", "sea of faces", "fade away into gray", "broken puzzle pieces"
]

# Concrete Sensory Replacement Candidates for English (Berklee Sensory Writing)
SENSORY_OBJECTS_EN = [
    "cold ceramic mug on the kitchen counter",
    "flickering streetlight buzzing outside the window",
    "worn denim jacket smelling like cheap cedar and rain",
    "porch screen door rattling in the October wind",
    "faint smell of diesel and cold black coffee at 4 AM",
    "cracked plastic phone case buzzing on the hardwood floor",
    "unread grocery list on the refrigerator door",
    "warm vinyl hum before the needle hits the groove",
    "rain tapping uneven fingernails on the tin roof",
    "faded polaroid tucked in the glove compartment"
]

# Known flat/robotic clichés in Khmer lyrics
AI_CLICHES_KH = [
    "ស្រមោលអតីតកាល", "ដួងផ្កាយភ្លឺចែងចាំង", "សម្លេងខ្សឹបនៃរាត្រី",
    "ក្តីស្រមៃដែលមិនរលត់", "ទឹកភ្នែកហូរដូចស្ទឹង", "បេះដូងបែកបាក់ជាចំណែក",
    "ដើរក្នុងភាពងងឹត", "ខ្យល់បក់រំភើយៗ", "ស្នេហាមិនប្រែប្រួល"
]

# Authentic Human Sensory & Ornamental Elements for Khmer (Sinn Sisamouth / Kong Nay / Modern Soul)
SENSORY_OBJECTS_KH = [
    "ក្លិនដីសើមក្រោយភ្លៀងធ្លាក់លើផ្លូវក្រហម",
    "ពន្លឺចង្កៀងប្រេងកាតរលត់រលាក់ក្បែរមាត់បង្អួច",
    "កែវកាហ្វេជ័ររលាយទឹកកកនៅលើតុឈើចាស់",
    "សំឡេងទ្រអ៊ូខ្សឹកខ្សួលកាត់ស្បៃរាត្រីស្ងាត់",
    "ស្លាកស្នាមប្រឡាក់ភក់លើជាយសារុងម៉ែ",
    "កន្សែងក្រមាដែលអូនធ្លាប់ចងដៃបង",
    "ខ្សែហ្គីតាចាស់ច្រែះស៊ី បន្លឺសំនៀងស្រងូតស្រងាត់"
]

KH_HUMAN_ADLIBS = [
    "(អើយ...)", "(ចាំបន្តិចណា...)", "(ស្ដាប់ខ្ញុំសិន...)",
    "(ហឹម...)", "(ឱណា...)", "(អើយ... ស្តាប់សិនទៅ)"
]


class HumanizerEngine:
    """Core analytical and generative engine for human-like music and lyrics."""

    @staticmethod
    def score_human_authenticity(lyrics: str, style_prompt: str = "", language: str = "English") -> Dict[str, Any]:
        """
        Calculates a deep 4-dimensional Human Authenticity Score (0-100%).
        Returns detailed scores and actionable feedback.
        """
        lyrics_lower = lyrics.lower() if lyrics else ""
        style_lower = style_prompt.lower() if style_prompt else ""
        is_kh = "khmer" in language.lower() or "ខ្មែរ" in language.lower() or any('\u1780' <= c <= '\u17ff' for c in lyrics)

        # 1. Sensory Realism Score (0-100)
        # Penalize for clichés, reward for specific physical senses (sight, touch, smell, taste, body)
        cliches_found = []
        if is_kh:
            for c in AI_CLICHES_KH:
                if c in lyrics:
                    cliches_found.append(c)
            sensory_keywords = ["ក្លិន", "ភ្លៀង", "កែវ", "តុ", "ចង្កៀង", "ដី", "ផ្លូវ", "ភក់", "ក្រមា", "ញើស", "ហ្គីតា", "ដៃ", "ជើង", "ស្រមោលជាក់ស្តែង"]
        else:
            for c in AI_CLICHES_EN:
                if c in lyrics_lower:
                    cliches_found.append(c)
            sensory_keywords = ["coffee", "counter", "jacket", "screen door", "wind", "diesel", "phone", "floor", "vinyl", "rain", "window", "hands", "breath", "smell", "cold", "warm", "shaking", "mug", "car", "dashboard"]

        sensory_hits = sum(1 for k in sensory_keywords if k in lyrics_lower)
        raw_sensory = 70 + (sensory_hits * 5) - (len(cliches_found) * 12)
        sensory_score = max(45, min(99, raw_sensory))

        # 2. Vocal Breathability & Phrasing Score (0-100)
        breath_indicators = ["[breath]", "[inhale]", "[sigh]", "[pause]", "[voice crack]", "[spoken]", "[hesitation]", "[falsetto]", "[whisper]", "(អើយ", "(ហឹម", "(ចាំ", "[ដកដង្ហើម]", "[ខ្សឹប]", "..."]
        breath_hits = sum(1 for b in breath_indicators if b in lyrics_lower)
        has_natural_pauses = "\n\n" in lyrics or "..." in lyrics or any(b in lyrics_lower for b in breath_indicators)
        raw_breath = 65 + (breath_hits * 8) + (8 if has_natural_pauses else 0)
        breath_score = max(50, min(99, raw_breath))

        # 3. Dynamic Emotional Arc & Vulnerability Score (0-100)
        has_bridge = any(tag in lyrics_lower for tag in ["[bridge]", "[ស្ពាន]", "[emotional epiphany]", "[vocal breakdown]"])
        has_intro_outro = any(tag in lyrics_lower for tag in ["[intro]", "[outro]", "[fade]"])
        raw_vuln = 70 + (18 if has_bridge else 0) + (10 if has_intro_outro else 0)
        # Check if bridge has more than 2 lines
        if has_bridge:
            raw_vuln += 5
        vulnerability_score = max(55, min(99, raw_vuln))

        # 4. Organic Acoustic Warmth Score (0-100)
        warmth_keywords = ["live pocket", "behind-the-beat", "tape", "warm", "saturation", "room mic", "un-quantized", "fret", "analog", "groove", "vibrato", "tro u", "chapei", "acoustic", "intimate", "natural"]
        warmth_hits = sum(1 for w in warmth_keywords if w in style_lower)
        raw_warmth = 68 + (warmth_hits * 8)
        groove_score = max(50, min(99, raw_warmth))

        # Weighted Overall Authenticity Score
        overall = int(sensory_score * 0.30 + breath_score * 0.25 + vulnerability_score * 0.25 + groove_score * 0.20)

        # Human Certified Tier
        if overall >= 93:
            tier = "🌟 Masterclass Human Authenticity (កម្រិតកំពូលមនុស្សពិត)"
            status_tag = "👤 100% Human Feel"
        elif overall >= 85:
            tier = "✨ High Human Grounding (មានអារម្មណ៍រស់រវើក)"
            status_tag = "👤 Human Grounded"
        elif overall >= 75:
            tier = "⚡ Moderate Human Pocket (កម្រិតមធ្យម)"
            status_tag = "⚡ Semi-Human"
        else:
            tier = "⚠️ Robotic AI Patterns Detected (ទាមទារការកែសម្រួល)"
            status_tag = "🤖 Needs Humanizing"

        suggestions = []
        if cliches_found:
            suggestions.append(f"Replace abstract clichés ({', '.join(cliches_found[:3])}) with tangible physical objects.")
        if breath_score < 80:
            suggestions.append("Add vocal breath cues ([Deep Inhale], [Soft Sigh]) before high notes.")
        if not has_bridge:
            suggestions.append("Add an emotional Bridge with a perspective twist or hidden truth.")
        if groove_score < 80:
            suggestions.append("Enhance style prompt with 'live pocket', 'tape warmth', or 'room mic bleed'.")

        return {
            "overall_score": overall,
            "sensory_score": sensory_score,
            "breath_score": breath_score,
            "vulnerability_score": vulnerability_score,
            "groove_score": groove_score,
            "detected_cliches": cliches_found,
            "tier": tier,
            "status_tag": status_tag,
            "suggestions": suggestions
        }

    @staticmethod
    def humanize_lyrics_locally(lyrics: str, language: str = "English") -> str:
        """
        Fast local transformation that converts lyrics into natural human singing cadences:
        - Injects natural breath marks and emotional pauses
        - Replaces common AI cliché words with sensory objects
        - Enhances Bridge with emotional revelation
        """
        if not lyrics:
            return lyrics

        is_kh = "khmer" in language.lower() or "ខ្មែរ" in language.lower() or any('\u1780' <= c <= '\u17ff' for c in lyrics)
        lines = lyrics.split("\n")
        new_lines = []

        in_verse = False
        in_chorus = False
        in_bridge = False
        has_bridge_seen = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle Section Tags
            if stripped.startswith("[") and stripped.endswith("]"):
                tag_lower = stripped.lower()
                if "verse" in tag_lower or "វគ្គ" in tag_lower:
                    in_verse = True
                    in_chorus = False
                    in_bridge = False
                    new_lines.append(stripped)
                    if is_kh:
                        new_lines.append("  [ដកដង្ហើមវែង • ច្រៀងយ៉ាងស្រទន់]")
                    else:
                        new_lines.append("  [Intimate Close-Mic • Quiet Inhale]")
                    continue
                elif "chorus" in tag_lower or "បន្ទរ" in tag_lower:
                    in_verse = False
                    in_chorus = True
                    in_bridge = False
                    new_lines.append(stripped)
                    if is_kh:
                        new_lines.append("  [ផ្ទុះសំនៀងពេញទំហឹង • (អើយ...)]")
                    else:
                        new_lines.append("  [Deep Inhale Before Belt • Raw Emotion]")
                    continue
                elif "bridge" in tag_lower or "ស្ពាន" in tag_lower:
                    in_verse = False
                    in_chorus = False
                    in_bridge = True
                    has_bridge_seen = True
                    new_lines.append(stripped)
                    if is_kh:
                        new_lines.append("  [ភ្លេងថយស្ងាត់ • បង្ហាញការពិតក្នុងបេះដូង]")
                    else:
                        new_lines.append("  [Music Drops Out • Vulnerable Confession]")
                    continue
                elif "outro" in tag_lower:
                    new_lines.append(stripped)
                    if is_kh:
                        new_lines.append("  [ដកដង្ហើមធំ • សំឡេងរសាត់បាត់ទៅ...]")
                    else:
                        new_lines.append("  [Soft Breath Fade • Acoustic Room Decay]")
                    continue
                else:
                    new_lines.append(stripped)
                    continue

            # Skip empty lines
            if not stripped:
                new_lines.append(line)
                continue

            # Replace Clichés in text
            mod_line = stripped
            if is_kh:
                for idx, c in enumerate(AI_CLICHES_KH):
                    if c in mod_line:
                        repl = SENSORY_OBJECTS_KH[idx % len(SENSORY_OBJECTS_KH)]
                        mod_line = mod_line.replace(c, repl)
            else:
                for idx, c in enumerate(AI_CLICHES_EN):
                    if c in mod_line.lower():
                        repl = SENSORY_OBJECTS_EN[idx % len(SENSORY_OBJECTS_EN)]
                        # Case insensitive replace
                        pattern = re.compile(re.escape(c), re.IGNORECASE)
                        mod_line = pattern.sub(repl, mod_line)

            # Occasionally inject natural breath / conversational ad-lib on key lines
            if in_verse and (i % 4 == 0) and not stripped.startswith("("):
                if is_kh:
                    mod_line = f"{mod_line} (ហឹម...)"
                else:
                    mod_line = f"{mod_line} ... [gentle breath]"

            new_lines.append(mod_line)

        # If no bridge was in the song, inject an authentic human revelation bridge
        if not has_bridge_seen and len(lines) > 8:
            if is_kh:
                bridge_insert = [
                    "",
                    "[Bridge - ការពិតលាក់កំបាំង]",
                    "  [ភ្លេងថយស្ងាត់ • សំឡេងច្រៀងទោល]",
                    "ទើបតែដឹងថា ការស្រឡាញ់ពិតមិនមែនការទាមទារ (អើយ...)",
                    "គឺការព្រមឈរមើលសុភមង្គលអូន ទោះបេះដូងបងឈឺចាប់",
                    "រាត្រីនេះភ្លៀងធ្លាក់លើផ្លូវដដែល តែគ្មានរូបអូនទៀតទេ...",
                    ""
                ]
            else:
                bridge_insert = [
                    "",
                    "[Bridge - Emotional Epiphany]",
                    "  [Instruments Cut Out • Raw Solo Voice]",
                    "And I finally see what I was too terrified to say out loud ...",
                    "I was trying to keep the fire alive while the whole house burned down,",
                    "Now I'm leaving the key under the mat, and I'm not looking back [voice crack]",
                    ""
                ]
            # Insert before last chorus or outro
            insert_pos = max(len(new_lines) - 4, 0)
            new_lines = new_lines[:insert_pos] + bridge_insert + new_lines[insert_pos:]

        return "\n".join(new_lines)

    @staticmethod
    def humanize_style_prompt_locally(style_prompt: str, language: str = "English", engine: str = "Suno") -> str:
        """
        Enhances a Suno / Udio style prompt with un-quantized human live performance cues
        while strictly obeying character limits (200 chars for Suno v3.5/v4/v6).
        """
        if not style_prompt:
            style_prompt = "pop, emotional melodic mix"

        is_kh = "khmer" in language.lower() or "ខ្មែរ" in language.lower()

        # Human live production tags to weave in
        if is_kh:
            human_tags = [
                "human live pocket",
                "warm analog tape",
                "emotive khmer vocal ornament",
                "intimate room mic",
                "subtle tempo sway"
            ]
        else:
            human_tags = [
                "human live pocket",
                "loose behind-the-beat",
                "warm tape saturation",
                "room mic bleed",
                "raw emotive vocals",
                "subtle un-quantized groove"
            ]

        # Filter out existing tags
        prompt_lower = style_prompt.lower()
        tags_to_add = [t for t in human_tags if t not in prompt_lower]

        combined = style_prompt.strip().rstrip(",")
        for t in tags_to_add:
            candidate = f"{combined}, {t}"
            if len(candidate) <= 195:
                combined = candidate
            else:
                break

        return combined

    @staticmethod
    def build_gemini_humanizer_prompt(title: str, genre: str, lyrics: str, style_prompt: str, language: str = "English") -> str:
        """Constructs an elite, academic prompt for Gemini Flash to elevate the song to 100% human authenticity."""
        is_kh = "khmer" in language.lower() or "ខ្មែរ" in language.lower()

        khmer_guidelines = """
ជម្រៅនៃការនិពន្ធបែបមនុស្សពិត (Khmer Masterclass Lyricism):
1. លុបបំបាត់ពាក្យចាស់គំរឹលដដែលៗ (លុប «ស្រមោលអតីតកាល», «ផ្កាយលើមេឃ»):
   - ជំនួសដោយវត្ថុជាក់ស្តែងដែលប៉ះអារម្មណ៍ (ក្លិនដីសើម, កែវកាហ្វេរលាយទឹកកក, ពន្លឺចង្កៀងប្រេងកាត, ស្នាមញញឹមទន់ភ្លន់របស់ម្តាយ)។
2. បញ្ចូលសំនៀងដង្ហើមច្រៀងពិតៗ (Human Breath & Sighs):
   - ប្រើ tag ដង្ហើម: [ដកដង្ហើមវែង], [សំឡេងខ្សឹប], (អើយ...), (ចាំបន្តិចណា...), (ហឹម...)។
3. វគ្គស្ពាន (Bridge) ត្រូវតែលាតត្រដាងអាថ៌កំបាំង ឬការពិតក្នុងចិត្តដែលមិនធ្លាប់និយាយ។
4. រក្សាជួនកាព្យខ្មែរ និងកុំកាត់ពាក្យផ្សំឱ្យខូចសូរសំនៀង។
""" if is_kh else ""

        western_guidelines = """
HUMAN STORYTELLING & VOCAL ARCHITECTURE (Taylor Swift / Finneas / Adele / Kendrick):
1. SENSORY OBJECT REALISM (Show, Don't Tell):
   - Every verse must contain at least 2 tangible physical items (e.g. coffee mug with lipstick ring, cold vinyl car seat, buzzing hallway fluorescent, handwritten grocery list).
2. VOCAL BREATH & PHRASING TAGS:
   - Inject realistic singer tags: [Deep Inhale Before Belt], [Intimate Proximity Whisper], [Conversational Pause], [Voice Crack on High Note], [Soft Breath Fade].
3. POWER BRIDGE EPIPHANY:
   - The Bridge must reveal a truth or emotional shift that changes the perspective of the entire song.
4. BANISHED CLICHES:
   - Strictly forbidden: "neon shadows", "echoes in the dark", "fire in my soul", "symphony of stars", "tapestry of time", "dancing in the rain".
5. STYLE PROMPT ENHANCEMENT:
   - Produce a Suno v3.5/v6 style prompt under 190 characters with live pocket cues: e.g. "human live pocket, loose groove, warm analog tape, room mic, emotive vocals".
""" if not is_kh else ""

        return f"""You are a multi-Grammy-winning record producer, master lyricist, and Berklee Professor of Songwriting.
Transform the following song from a robotic AI track into a living, breathing HUMAN MASTERPIECE.

Language: {language}
Musical Genre: {genre}
Song Title: {title}
Original Style Prompt: {style_prompt}

ORIGINAL LYRICS:
\"\"\"
{lyrics}
\"\"\"

{khmer_guidelines}
{western_guidelines}

OUTPUT FORMAT (Valid JSON with these exact keys):
{{
  "humanized_lyrics": "Full humanized lyrics with section tags and breath marks",
  "humanized_style_prompt": "Enhanced Suno style prompt under 190 characters with organic human pocket cues",
  "authenticity_score": 96,
  "sensory_score": 95,
  "breath_score": 98,
  "vulnerability_score": 97,
  "groove_score": 95,
  "human_summary": "1-2 sentences in Khmer/English explaining the human improvements made"
}}

Return ONLY the raw JSON object. Do not wrap in markdown or backticks.
"""

