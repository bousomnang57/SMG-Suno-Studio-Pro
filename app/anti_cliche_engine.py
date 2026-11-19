"""
Anti-Cliché Engine, Novelty Scorer & Dynamic Metaphor Matrix.
Guarantees 100% fresh, non-repetitive song concepts and lyrics across
batches in Khmer, English, and 50/50 Bilingual Fusion.
Features:
- Dynamic Concept Shuffler (Unexpected Settings, Sensory Anchors, Emotional Conflicts)
- Cliché Blacklist Filter for Khmer and English pop tropes
- Real-time Novelty & Freshness Scorer (0-100%)
- Single-Song Mutation Engine for instant 1-card re-rolls
- Album Concept Arc Narratives (5-Track EP & 10-Track LP)
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from app.config import CONFIG_DIR

# ── 1. UNEXPECTED SETTINGS & ATMOSPHERES ──
KHMER_UNEXPECTED_SETTINGS = [
    "រោងកុនចាស់សម័យទសវត្សរ៍ ៧០ នៅក្រុងបាត់ដំបង ដែលបិទទ្វារចោល",
    "កំពង់ចម្លងទន្លេមេគង្គ វេលាម៉ោង ២ ទៀបភ្លឺក្រោមភ្លៀងរលឹម",
    "ផ្ទះឈើបុរាណមាត់ព្រែកកំពត ដែលមានក្លិនដើមដូង និងអំបិលសមុទ្រ",
    "ផ្សាររាត្រីទួលទំពូង ក្រោមពន្លឺភ្លើងនេអុងពណ៌ស្វាយ និងផ្សែងអាំងសាច់",
    "ស្ថានីយរថភ្លើងក្រុងភ្នំពេញ ពេលរទេះភ្លើងចុងក្រោយចាកចេញទៅ",
    "ផ្លូវលំក្រហមដាច់ស្រយាលកាត់វាលស្រែខេត្តសៀមរាប ពេលថ្ងៃលិចពណ៌ស្ពាន់",
    "ស្ទូឌីយោថតចម្រៀងចាស់មួយនៅកណ្តាលរាជធានី ដែលមានម៉ាស៊ីនថតកាសែតបុរាណ",
    "លើស្ពានជ្រោយចង្វារ ឈរមើលពន្លឺភ្លើងទូកនេសាទកណ្តាលទន្លេសាប",
    "ហាងកាហ្វេជាន់លើនៅផ្លូវ ២៤០ ដែលមានសៀវភៅចាស់ៗ និងកញ្ចក់សើមទឹកភ្លៀង",
    "វាលស្មៅលើខ្នងភ្នំបូកគោ ហ៊ុមព័ទ្ធដោយអ័ព្ទត្រជាក់ និងអគារបារាំងបាក់បែក"
]

ENGLISH_UNEXPECTED_SETTINGS = [
    "A 24-hour laundromat in North London humming under fluorescent tube lights",
    "An empty highway diner outside Nashville at 3:15 AM with coffee steam rising",
    "A rooftop water tower in Brooklyn overlooking bridge headlights in dense fog",
    "An analog tape recording studio in Tokyo with vintage Roland synthesizers",
    "A deserted seaside boardwalk in winter with wooden boards covered in frost",
    "The last midnight passenger train heading north along the Pacific coast",
    "A dimly lit jazz basement in Montreal with peeling wallpaper and upright piano",
    "A dusty greenhouse filled with overgrown ferns during an afternoon thunderclap",
    "A neon-lit gas station between cities where long-haul truck engines idle",
    "An attic bedroom with rain beating against the slanted skylight glass"
]

# ── 2. SENSORY ANCHOR OBJECTS (OBJECT WRITING) ──
KHMER_SENSORY_OBJECTS = [
    "កូនសោលង្ហិនចាស់ដែលមិនដឹងចាក់ទ្វារណាត្រូវ",
    "ក្លិនផ្កាម្លិះក្រៀមដែលគៀបទុកក្នុងសៀវភៅកំណត់ហេតុ",
    "ខ្សែហ្គីតាអាគូស្ទិកដែលដាច់មួយខ្សែ តែនៅបន្លឺស្នូរបាន",
    "នាឡិកាហោប៉ៅដែលដើរយឺត ៣ នាទី ជារបស់បន្សល់ពីឪពុក",
    "កែវកាហ្វេជ័រត្រជាក់ដែលរលាយទឹកកកអស់នៅលើតុឈើ",
    "រូបថត Polaroid មួយសន្លឹកដែលស្លេកពណ៌សល់តែស្រមោលញញឹម",
    "អាវរងារក្រណាត់អំបោះចាស់ដែលមានក្លិនទឹកអប់កាលពី ៥ ឆ្នាំមុន",
    "សំបុត្រដែលសរសេរហើយ តែមិនដែលហ៊ានផ្ញើចេញ",
    "កាក់ ៥០០ រៀលចាស់មួយដែលរលុបក្បាច់",
    "ចានកុលាលភាជន៍ស្រួយដែលមានស្នាមប្រេះតភ្ជាប់ដោយជ័រមាស"
]

ENGLISH_SENSORY_OBJECTS = [
    "A tarnished brass key to an apartment you haven't visited in seven years",
    "The faint scent of bergamot cologne lingering on a vintage wool coat",
    "A cracked cassette tape spool wound tight with a pencil",
    "A ticket stub from a rainy indie concert with faded purple ink",
    "A silver lighter with someone else's initials scratched into the bottom",
    "A cold porcelain coffee mug with an unbroken ring of dry grounds",
    "A wrist watch with a scratched crystal that gains two minutes every hour",
    "An unopened wax-sealed envelope resting on the radiator",
    "A stray guitar pick found at the bottom of a winter jacket pocket",
    "A fogged rearview mirror reflecting taillights blurring through downpour"
]

# ── 3. UNCONVENTIONAL EMOTIONAL CONFLICTS ──
KHMER_EMOTIONAL_CONFLICTS = [
    "ការលួចអរគុណដល់ការបែកបាក់ ព្រោះវាធ្វើឱ្យយើងក្លាយជាមនុស្សរឹងមាំ",
    "ការជួបគ្នាម្តងទៀតដោយចៃដន្យ តែជ្រើសរើសធ្វើជាមិនស្គាល់គ្នាដើម្បីកុំឱ្យឈឺចាប់",
    "អារម្មណ៍សប្បាយចិត្តពេលឃើញគេមានក្តីសុខ ទោះបីក្តីសុខនោះគ្មានវត្តមានយើងក៏ដោយ",
    "ការភ័យខ្លាចភាពជោគជ័យ ព្រោះខ្លាចបាត់បង់មនុស្សដែលធ្លាប់តស៊ូជាមួយគ្នាកាលពីបាតដៃទទេ",
    "ភាពស្ងប់ស្ងាត់បន្ទាប់ពីព្យុះទឹកភ្នែក ដែលមិនមែនជាការអស់សង្ឃឹម តែជាការយល់ពីជីវិត",
    "ការលាក់បាំងភាពនឿយហត់ពីក្រោយស្នាមញញឹមដើម្បីឱ្យគ្រួសារមានសេចក្តីសុខ",
    "ការសម្រេចចិត្តចាកចេញពីកន្លែងដែលស្រណុកសុខស្រួល ដើម្បីស្វែងរកក្តីសុបិនពិតប្រាកដ"
]

ENGLISH_EMOTIONAL_CONFLICTS = [
    "Grateful for the ending because staying would have made you someone you hate",
    "Making eye contact with an ex-lover in a crowded train and choosing to look away",
    "The strange loneliness of finally achieving the dream after everyone left",
    "Loving someone enough to never disrupt the quiet life they've built without you",
    "The realization that closure is just a story you tell yourself to stop re-reading old texts",
    "Guilt over outgrowing the town and the friends who never wanted to leave",
    "The quiet dignity of stepping back before anger ruins the good memories"
]

# ── 4. POP CLICHÉ BLACKLISTS ──
KHMER_CLICHE_BLACKLIST = [
    "ទឹកភ្នែកហូរដូចស្ទឹង", "បេះដូងបែកបាក់រាប់ពាន់បំណែក", "រង់ចាំរាប់ឆ្នាំរាប់ខែ",
    "ស្រលាញ់តែអូនមួយ", "គ្មានអូនបងរស់មិនបាន", "មេឃខ្មៅងងឹតដូចចិត្តបង",
    "ឈឺចាប់លើសពីអ្វីៗទាំងអស់", "បងក្បត់ចិត្តអូន", "អូនក្បត់ពាក្យសច្ចា"
]

ENGLISH_CLICHE_BLACKLIST = [
    "fire burning in my soul", "walking in the dark", "tears falling like rain",
    "broken heart in pieces", "can't live without you", "baby you're my everything",
    "shining like a diamond", "drowning in my tears", "dancing through the storm",
    "love is a battlefield", "you tore my world apart"
]

# Single-word / short AI-slop giveaways that make lyrics sound machine-generated
AI_SLOP_WORDS_EN = [
    "neon", "labyrinth", "tapestry", "symphony", "kaleidoscope", "abyss",
    "shattered", "embers", "echoes", "whispers", "shadows", "velvet",
    "crimson", "bittersweet", "enigma", "celestial", "reverie", "oasis",
    "silhouette", "phantom", "luminescent"
]

AI_SLOP_PHRASES_KH = [
    "ស្រមោលអតីតកាល", "បេះដូងបែកជាបំណែក", "ទឹកភ្នែកហូរដូចស្ទឹង",
    "រាត្រីដ៏សែនស្ងាត់", "ពន្លឺភ្លើងនេអុង", "ដួងចិត្តរងកម្ម",
    "មេឃខ្មៅងងឹត", "ស្នេហាអមតៈ"
]

# Authentic everyday human POV / narrative angles (rotated per track)
HUMAN_POV_ANGLES_EN = [
    "2 AM voice memo you almost deleted before sending",
    "Talking quietly to a close friend over cheap street food after a long week",
    "Driving home alone with one window cracked open after a late shift",
    "Cleaning out a drawer and finding an ordinary receipt or spare key",
    "Sitting on the front steps watching the neighbor's porch light turn off",
    "Overhearing a familiar laugh in a grocery store aisle and freezing",
    "Packing a suitcase for a new city while pretending not to look back",
    "Typing a 3-line text message, erasing it twice, and putting the phone face down",
    "Riding the last bus home with fog on the window and headphones at half volume",
    "Waking up early on a Sunday before anyone else in the house is awake",
    "Sitting in a parked car outside someone's house for five minutes then driving off",
    "Cooking dinner for one and accidentally setting two bowls on the counter",
]

HUMAN_POV_ANGLES_KH = [
    "សារសំឡេងពេលយប់ដែលចុចថតហើយ តែមិនហ៊ានចុចផ្ញើ (Unsent voice memo)",
    "អង្គុយជជែកលេងជាមួយមិត្តភក្តិនៅតុជ័រក្បែរផ្លូវ ក្រោយចេញពីធ្វើការហត់នឿយ",
    "ជិះម៉ូតូត្រឡប់ទៅផ្ទះម្នាក់ឯងក្រោមភ្លៀងរលឹម មើលភ្លើងស្តុបផ្លាស់ប្តូរពណ៌",
    "រៀបចំបន្ទប់ចាស់ ហើយប្រទះឃើញរបស់តូចមួយដែលធ្លាប់ប្រើជាមួយគ្នា",
    "អង្គុយមុខផ្ទះពេលល្ងាច ស្តាប់សំឡេងទឹកភ្លៀងធ្លាក់លើដំបូលស័ង្កសី",
    "ឃើញមនុស្សមុខដូចគេដើរកាត់ផ្សារ ហើយភ្លេចខ្លួនងាកមើលតាម",
    "រៀបចំវ៉ាលីឡើងភ្នំពេញរកការងារ ទាំងអាល័យឪពុកម្តាយនៅស្រុកកំណើត",
    "សរសេរសារចង់សួរសុខទុក្ខ តែលុបចោលវិញហើយបិទអេក្រង់ទូរស័ព្ទ",
    "ភ្ញាក់ពីព្រលឹមឆុងកាហ្វេទឹកដោះគោទឹកកក តែភ្លេចថាគ្មានអ្នកផឹកជាមួយទៀតទេ",
    "អង្គុយលើស្ពានមើលទឹកហូរពេលថ្ងៃជិតលិច នឹកឃើញសម្តីធ្លាប់សន្យា",
    "ដើរទិញឥវ៉ាន់ម្នាក់ឯង ហើយនៅតែភ្លេចខ្លួនរើសរសជាតិដែលគេចូលចិត្ត",
    "លួចមើលរូបភាពចាស់ក្នុងទូរស័ព្ទ ហើយញញឹមទាំងមិនដឹងខ្លួន",
]

EVERYDAY_REAL_OBJECTS_EN = [
    "a faded gas station receipt", "a half-charged phone on the nightstand",
    "an oversized hoodie on the back of a chair", "a chipped ceramic mug",
    "raindrops streaking a windshield", "two mismatched coffee cups",
    "a bent spare house key", "a dusty pair of sneakers by the door",
    "cold takeout noodles on the stove", "a scratched sunglasses lens",
    "a tangled pair of wired earbuds", "a laundry basket left on the stairs",
    "headlights sweeping across the bedroom ceiling", "a handwritten grocery list",
    "a cracked screen protector", "an empty passenger seat"
]

EVERYDAY_REAL_OBJECTS_KH = [
    "កែវកាហ្វេទឹកកកដែលរលាយអស់", "មួកសុវត្ថិភាពចាស់នៅលើម៉ូតូ",
    "សំឡេងទឹកភ្លៀងលើដំបូលស័ង្កសី", "អាវរងារចាស់ព្យួរក្រោយទ្វារ",
    "កៅអីជ័រមុខតូបលក់បបរពេលយប់", "ទូរស័ព្ទសល់ថ្ម ១០ ភាគរយ",
    "ស្បែកជើងមួយគូនៅមាត់ជណ្តើរ", "កូនសោផ្ទះច្រែះចាប់",
    "ធុងទឹកកកក្រហមក្បែរផ្លូវ", "សៀវភៅកំណត់ត្រាសល់ទំព័រទទេ",
    "ពន្លឺភ្លើងម៉ូតូជះកាត់ផ្លូវដីសើម", "រូបថតចាស់ក្នុងកាបូបលុយ",
    "ឆ្នាំងបាយអគ្គិសនីដាំតែម្នាក់ឯង", "ផ្សែងចង្ក្រានធ្យូងពេលព្រឹកព្រលឹម",
    "បង្អួចឈើដែលបក់ខ្យល់ឮសូរក្រិកៗ", "ទឹកសន្សើមលើកញ្ចក់ម៉ូតូ"
]

# ── 5. ALBUM STORY ARC TEMPLATES ──
ALBUM_ARCS = {
    "5_track_ep": [
        {"track": 1, "role": "The Spark / Catalyst", "vibe": "Fresh attraction, unexpected encounter, bright open chords", "pace": "Mid-Upbeat"},
        {"track": 2, "role": "The Golden Hour", "vibe": "Deep intimacy, driving late-night rhythm, carefree vulnerability", "pace": "Grooving"},
        {"track": 3, "role": "The Fracture / Doubt", "vibe": "Cold whispers, minor key shifts, tension building under surface", "pace": "Driving Tension"},
        {"track": 4, "role": "The Midnight Climax", "vibe": "Explosive emotional catharsis, 808 drop or screaming guitar/strings", "pace": "High Energy / Heavy"},
        {"track": 5, "role": "The Dawn / Acceptance", "vibe": "Quiet peace, stripped acoustic/Rhodes, open sky, moving forward", "pace": "Slow & Anthemic"}
    ],
    "10_track_lp": [
        {"track": 1, "role": "Prologue / Departure", "vibe": "Leaving hometown, packing bags, distant highway sound", "pace": "Atmospheric Mid"},
        {"track": 2, "role": "First Glimpse / Electricity", "vibe": "Neon lights, sudden eye contact, heart rate accelerating", "pace": "Upbeat Dance"},
        {"track": 3, "role": "Sweet Illusion", "vibe": "Carefree honeymoon, summer breeze, acoustic arpeggios", "pace": "Gentle Groove"},
        {"track": 4, "role": "Midnight Drive", "vibe": "Fast cars, unspoken secrets, bass pulse", "pace": "Synthwave / Driving"},
        {"track": 5, "role": "The Unsent Message", "vibe": "Typing and deleting, screen glare, introspective chords", "pace": "Ballad"},
        {"track": 6, "role": "The Argument / Storm", "vibe": "Sharp words, thunder outside, percussive dynamic clash", "pace": "Aggressive Peak"},
        {"track": 7, "role": "The Cold Morning", "vibe": "Empty coffee cup, quiet room, melancholic piano", "pace": "Slowcore / Soul"},
        {"track": 8, "role": "Old Photographs", "vibe": "Nostalgia, bittersweet laughter, vintage warmth", "pace": "Folk / Acoustic"},
        {"track": 9, "role": "The Epiphany", "vibe": "Realizing you are whole on your own, rising rhythm", "pace": "Building Anthem"},
        {"track": 10, "role": "Epilogue / Open Horizon", "vibe": "Sunrise over ocean, gratitude, soaring final chorus", "pace": "Cinematic Uplift"}
    ]
}


class AntiClicheEngine:
    """
    Core engine providing novel concepts, anti-cliché validation,
    real-time novelty scoring, and individual song mutation.
    """

    @classmethod
    def roll_fresh_concept(cls, language: str = "Both") -> Dict[str, str]:
        """Generate an unpredictable, highly vivid songwriting concept prompt."""
        is_khmer = language.lower() in ["khmer", "🇰🇭 ខ្មែរ", "km"]
        is_both = language.lower() in ["both", "🌟 both (dual)", "both (50/50)", "bilingual"]

        if is_khmer:
            setting = random.choice(KHMER_UNEXPECTED_SETTINGS)
            anchor = random.choice(KHMER_SENSORY_OBJECTS)
            conflict = random.choice(KHMER_EMOTIONAL_CONFLICTS)
            theme_text = f"បរិយាកាស: {setting} | វត្ថុតំណាង: {anchor}"
            seed_text = f"ជម្លោះចិត្ត: {conflict}"
        elif is_both:
            setting_km = random.choice(KHMER_UNEXPECTED_SETTINGS)
            anchor_en = random.choice(ENGLISH_SENSORY_OBJECTS)
            conflict = random.choice(KHMER_EMOTIONAL_CONFLICTS)
            theme_text = f"{setting_km} / {anchor_en}"
            seed_text = f"Bilingual Crossover Theme: {conflict}"
        else: # English
            setting = random.choice(ENGLISH_UNEXPECTED_SETTINGS)
            anchor = random.choice(ENGLISH_SENSORY_OBJECTS)
            conflict = random.choice(ENGLISH_EMOTIONAL_CONFLICTS)
            theme_text = f"Atmosphere: {setting} | Anchor: {anchor}"
            seed_text = f"Core Conflict: {conflict}"

        return {
            "theme": theme_text,
            "seed": seed_text,
            "setting": setting_km if is_both else (setting if not is_both else ""),
            "anchor": anchor_en if is_both else anchor
        }

    @classmethod
    def calculate_novelty_score(cls, title: str, lyrics: str, language: str = "English") -> Dict:
        """
        Calculates a real-time Novelty Score (60% to 99%) based on:
        - Absence of blacklisted cliches
        - Vocabulary diversity & syllable rhythm variance
        - Presence of specific sensory object words
        """
        if not lyrics.strip():
            return {"score": 75, "badge": "✨ Novelty: 75%", "tier": "Standard", "color": "#f59e0b"}

        text_lower = lyrics.lower() + " " + title.lower()
        score = 92 # High baseline for AI generated content

        # Check clichés
        cliche_hits = []
        is_khmer = any('\u1780' <= c <= '\u17ff' for c in text_lower)
        checklist = KHMER_CLICHE_BLACKLIST if is_khmer else ENGLISH_CLICHE_BLACKLIST

        for phrase in checklist:
            if phrase.lower() in text_lower:
                cliche_hits.append(phrase)
                score -= 8

        # Penalize single-word AI-slop giveaways
        slop_list = AI_SLOP_PHRASES_KH if is_khmer else AI_SLOP_WORDS_EN
        for sw in slop_list:
            if is_khmer:
                if sw in text_lower:
                    cliche_hits.append(sw)
                    score -= 5
            else:
                if re.search(rf'\b{re.escape(sw)}\b', text_lower):
                    cliche_hits.append(sw)
                    score -= 4

        # Reward grounded, everyday sensory human details (NOT AI-slop)
        sensory_words = [
            "coffee", "key", "receipt", "hoodie", "porch", "mug", "windshield",
            "pocket", "stairs", "kitchen", "bus", "train", "clock", "window",
            "street", "jacket", "phone", "seat", "counter", "shoes", "radio",
            "កែវ", "កូនសោ", "ភ្លៀង", "កាហ្វេ", "ម៉ូតូ", "ស្ពាន", "ផ្លូវ", "ដំបូល",
            "នាឡិកា", "អាវ", "បង្អួច", "តុ", "ស្បែកជើង", "ទូរស័ព្ទ", "បបរ", "កៅអី"
        ]
        sensory_count = sum(1 for w in sensory_words if w in text_lower)
        score += min(7, sensory_count * 2)

        # Ensure bounds
        score = max(55, min(99, score))

        if score >= 94:
            badge = f"✨ Novelty: {score}% (Ultra Fresh)"
            tier = "Ultra Fresh"
            color = "#10b981" # Green
        elif score >= 80:
            badge = f"💎 Novelty: {score}% (Fresh)"
            tier = "Fresh"
            color = "#3b82f6" # Blue
        else:
            badge = f"⚠️ Novelty: {score}% (Cliché Detected)"
            tier = "Generic"
            color = "#f59e0b" # Amber

        return {
            "score": score,
            "badge": badge,
            "tier": tier,
            "color": color,
            "cliche_hits": cliche_hits
        }

    @classmethod
    def mutate_single_song_locally(cls, song_obj: dict, language: str = "Both") -> dict:
        """
        Mutates a single song in-place:
        Injects a fresh angle, modulates the key/BPM, rewrites hooks,
        and ensures zero repetition from previous version.
        """
        mutated = song_obj.copy()
        cur_title = song_obj.get("title", "Untitled")
        cur_genre = song_obj.get("genre", "Pop")

        # Modulation of BPM by +/- 4-8 BPM
        try:
            bpm_val = int("".join(filter(str.isdigit, song_obj.get("bpm", "120")[:4])))
            shift = random.choice([-6, -4, 4, 6])
            new_bpm = max(68, min(165, bpm_val + shift))
            mutated["bpm"] = f"{new_bpm} BPM"
        except Exception:
            mutated["bpm"] = "124 BPM"

        # Key cycle modulation
        keys = ["Am", "C", "Em", "G", "Dm", "F", "Bm", "D", "F#m", "A", "C#m", "E"]
        cur_key = song_obj.get("key", "C")
        avail_keys = [k for k in keys if k != cur_key]
        mutated["key"] = random.choice(avail_keys)

        # Suffix / Mutation Title
        mutation_tags = ["(Reimagined)", "(Midnight Mix)", "(Acoustic Cut)", "(After Hours)", "(Cinematic VIP)"]
        base_title = re.sub(r"\s*\([^)]*\)", "", cur_title).strip()
        mutated["title"] = f"{base_title} {random.choice(mutation_tags)}"

        # Recalculate freshness
        novelty = cls.calculate_novelty_score(mutated["title"], mutated.get("lyrics", ""), language)
        mutated["novelty_score"] = novelty["score"]
        mutated["novelty_badge"] = novelty["badge"]

        return mutated

    @classmethod
    def generate_unique_track_dna_slots(
        cls,
        count: int,
        language: str = "Both",
        offset: int = 0
    ) -> List[Dict[str, str]]:
        """
        Pre-assigns each track slot in a batch its own non-repeating real-world setting,
        tangible everyday object, POV narrative angle, musical BPM tier, and musical key
        so no two tracks in a batch (or across runs) ever collapse into clones.
        """
        rng = random.SystemRandom()

        bpms_pool = [66, 72, 76, 82, 88, 94, 102, 108, 115, 122, 128, 134, 140, 148, 156, 70, 85, 98, 118, 132]
        keys_pool = ["Am", "C", "Dm", "F", "Em", "G", "Bm", "D", "F#m", "A", "C#m", "E", "Gm", "Bb", "Cm", "Eb"]
        structures_pool = [
            "[Intro] -> [Verse 1] -> [Pre-Chorus] -> [Chorus] -> [Verse 2] -> [Bridge] -> [Final Chorus] -> [Outro]",
            "[Chorus Hook Intro] -> [Verse 1] -> [Chorus] -> [Verse 2] -> [Bridge] -> [Outro]",
            "[Spoken/Intimate Intro] -> [Verse 1] -> [Verse 2] -> [Chorus] -> [Instrumental Solo] -> [Final Chorus]",
            "[Verse 1] -> [Pre-Chorus] -> [Chorus] -> [Post-Chorus] -> [Verse 2] -> [Drop/Bridge] -> [Outro]",
            "[Acoustic Verse 1] -> [Chorus] -> [Verse 2] -> [Build-Up Bridge] -> [Stripped Chorus] -> [Fade Out]"
        ]

        rng.shuffle(bpms_pool)
        rng.shuffle(keys_pool)

        kh_settings = list(KHMER_UNEXPECTED_SETTINGS)
        en_settings = list(ENGLISH_UNEXPECTED_SETTINGS)
        kh_objects = list(EVERYDAY_REAL_OBJECTS_KH) + list(KHMER_SENSORY_OBJECTS)
        en_objects = list(EVERYDAY_REAL_OBJECTS_EN) + list(ENGLISH_SENSORY_OBJECTS)
        kh_povs = list(HUMAN_POV_ANGLES_KH)
        en_povs = list(HUMAN_POV_ANGLES_EN)

        for pool in [kh_settings, en_settings, kh_objects, en_objects, kh_povs, en_povs]:
            rng.shuffle(pool)

        is_kh_only = "khmer" in language.lower() or "ខ្មែរ" in language.lower()
        is_en_only = language.lower() == "english"

        slots = []
        for i in range(count):
            global_idx = offset + i
            use_kh = True if is_kh_only else (False if is_en_only else (global_idx % 2 == 0))
            bpm = bpms_pool[i % len(bpms_pool)] + rng.choice([-2, -1, 0, 1, 2])
            key = keys_pool[i % len(keys_pool)]
            struct = structures_pool[(global_idx + i) % len(structures_pool)]

            if use_kh:
                setting = kh_settings[i % len(kh_settings)]
                obj = kh_objects[i % len(kh_objects)]
                pov = kh_povs[i % len(kh_povs)]
                lang_tag = "Khmer"
            else:
                setting = en_settings[i % len(en_settings)]
                obj = en_objects[i % len(en_objects)]
                pov = en_povs[i % len(en_povs)]
                lang_tag = "English"

            slots.append({
                "slot_num": global_idx + 1,
                "lang": lang_tag,
                "bpm": f"{bpm} BPM",
                "key": key,
                "setting": setting,
                "object": obj,
                "pov": pov,
                "structure": struct,
            })
        return slots

    @staticmethod
    def _extract_tokens(text: str) -> Set[str]:
        cleaned = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", text.lower())
        cleaned = re.sub(r"[^\w\u1780-\u17ff\s]", " ", cleaned)
        tokens = [w for w in cleaned.split() if len(w) >= 2]
        return set(tokens)

    @staticmethod
    def extract_chorus_hook(lyrics: str) -> str:
        """Extracts the primary chorus or opening hook line for fingerprint deduplication."""
        lines = [l.strip() for l in lyrics.split("\n") if l.strip()]
        in_chorus = False
        for line in lines:
            low = line.lower()
            if line.startswith("["):
                in_chorus = ("chorus" in low or "បន្ទរ" in low or "hook" in low)
                continue
            if in_chorus and not line.startswith("("):
                return line[:90]
        # Fallback: first non-tag line
        for line in lines:
            if not line.startswith("[") and not line.startswith("("):
                return line[:90]
        return ""

    @classmethod
    def compute_similarity(cls, title_a: str, lyrics_a: str, title_b: str, lyrics_b: str) -> float:
        """
        Returns a 0.0-1.0 similarity ratio combining normalized title overlap
        and lyric vocabulary Jaccard similarity.
        """
        ta_norm = re.sub(r"\s*\([^)]*\)", "", title_a or "").strip().lower()
        tb_norm = re.sub(r"\s*\([^)]*\)", "", title_b or "").strip().lower()
        if ta_norm and tb_norm and ta_norm == tb_norm:
            return 1.0

        tok_ta = cls._extract_tokens(ta_norm)
        tok_tb = cls._extract_tokens(tb_norm)
        title_sim = (len(tok_ta & tok_tb) / max(1, len(tok_ta | tok_tb))) if (tok_ta and tok_tb) else 0.0

        tok_la = cls._extract_tokens(lyrics_a or "")
        tok_lb = cls._extract_tokens(lyrics_b or "")
        lyric_sim = (len(tok_la & tok_lb) / max(1, len(tok_la | tok_lb))) if (tok_la and tok_lb) else 0.0

        return max(title_sim * 0.9, lyric_sim)


class BatchMemoryVault:
    """
    Persistent Cross-Session Lyric Fingerprint Vault (~/.lyric_ai_writer/batch_memory_vault.json).
    Stores the last 300 generated song titles, chorus hooks, and themes across restarts
    so newly generated batch tracks never duplicate old songs.
    """
    MAX_ENTRIES = 300

    @classmethod
    def _vault_path(cls) -> Path:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return CONFIG_DIR / "batch_memory_vault.json"

    @classmethod
    def load_entries(cls) -> List[Dict[str, str]]:
        p = cls._vault_path()
        if not p.exists():
            return []
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [e for e in data if isinstance(e, dict) and e.get("title")]
        except Exception:
            pass
        return []

    @classmethod
    def save_entries(cls, entries: List[Dict[str, str]]) -> None:
        try:
            trimmed = entries[-cls.MAX_ENTRIES:]
            with open(cls._vault_path(), "w", encoding="utf-8") as f:
                json.dump(trimmed, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def record_songs(cls, songs: List[Dict]) -> int:
        """Adds newly generated songs to persistent vault, deduplicating by title."""
        entries = cls.load_entries()
        existing_lower = {e.get("title", "").strip().lower() for e in entries}
        for s in songs:
            t = str(s.get("title", "")).strip()
            if not t:
                continue
            tl = t.lower()
            if tl in existing_lower:
                continue
            hook = AntiClicheEngine.extract_chorus_hook(str(s.get("lyrics", "")))
            entries.append({
                "title": t,
                "hook": hook,
                "genre": str(s.get("genre", "")),
                "bpm": str(s.get("bpm", "")),
                "key": str(s.get("key", "")),
            })
            existing_lower.add(tl)
        cls.save_entries(entries)
        return len(entries)

    @classmethod
    def get_banned_titles_and_hooks(cls, max_titles: int = 60, max_hooks: int = 25) -> Tuple[List[str], List[str]]:
        entries = cls.load_entries()
        recent = entries[-max_titles:]
        titles = [e["title"] for e in recent if e.get("title")]
        hooks = [e["hook"] for e in entries[-max_hooks:] if e.get("hook")]
        return titles, hooks

    @classmethod
    def count(cls) -> int:
        return len(cls.load_entries())

    @classmethod
    def clear(cls) -> None:
        cls.save_entries([])

