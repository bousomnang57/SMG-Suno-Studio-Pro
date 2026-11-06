"""
Sensory & Poetic Imagery Thesaurus (Inspired by MasterWriter & Professional Lyricists).
Provides curated words, metaphors, contrast pairs, and rhyme families across sensory dimensions
in English and Khmer to break writer's block and enrich lyrical imagery.
"""

from typing import Dict, List

SENSORY_CATEGORIES: Dict[str, Dict] = {
    "👁️ Sight, Colors & Atmospheric Light (ការមើលឃើញ និងពន្លឺ)": {
        "description": "Colors, celestial light, shadows, reflections, and midnight city glows.",
        "words_en": [
            "Amber", "Glimmer", "Silhouette", "Twilight", "Prismatic",
            "Flicker", "Eclipse", "Luminescence", "Cast shadow", "Radiance",
            "Shimmering", "Bleached", "Midnight hue", "Gilded", "Neon glow",
            "Obsidian", "Halcyon", "Phosphorescent", "Golden hour", "Velvet dusk",
            "Starlight", "Blinding glare", "Silvery haze", "Incandescent", "Mirage",
            "Vivid crimson", "Pale horizon", "Kaleidoscope", "Smoky neon", "Gleam"
        ],
        "words_km": [
            "រស្មីភ្លឺផ្លេក", "ស្រមោលអ័ព្ទ", "រស្មីព្រះចន្ទ", "ពន្លឺផ្កាយ", "រស្មីថ្ងៃរៀបលិច",
            "ស្រមោលស្រពោន", "រស្មីពណ៌មាស", "ភ្លើងពណ៌រាត្រី", "ពន្លឺត្រចះត្រចង់", "ពន្លឺព្រះអាទិត្យរះ",
            "ផ្កាយព្រិចៗ", "រស្មីពណ៌ស្វាយ", "ពន្លឺព្រាលៗ", "មេឃពណ៌ស្ពាន់", "រស្មីចាំងភ្នែក",
            "ស្រមោលកណ្តាលអធ្រាត្រ", "ពន្លឺចែងចាំង", "អ័ព្ទរាត្រី", "ពន្លឺចន្ទពេញបូណ៌មី"
        ]
    },
    "👂 Sound, Silence & Acoustic Textures (សំឡេង និងចង្វាក់)": {
        "description": "Echoes, resonance, deep sub-bass pulses, whispering silence, and auditory textures.",
        "words_en": [
            "Whisper", "Resonance", "Reverberation", "Hum", "Cacophony",
            "Muffled", "Echoing", "Rustling", "Crescendo", "Hollow tone",
            "Chime", "Crackle", "Sub-bass pulse", "Sighing wind", "Stillness",
            "Deafening silence", "Static hiss", "Murmur", "Thunderclap", "Tremolo",
            "Staccato rhythm", "Vinyl hiss", "Shattered glass", "Rumble", "Syncopated",
            "Metallic clatter", "Distant siren", "Heartbeat thump", "Distorted echo", "Chime bell"
        ],
        "words_km": [
            "សំឡេងរណ្ដំ", "ខ្សឹបខ្សៀវ", "រលកបោកច្រាំង", "សូរសព្ទស្ងាត់ជ្រងំ", "បន្លឺសូររោទ៍",
            "ខ្យល់បក់រំភើយ", "សំឡេងតន្ត្រីរសាត់", "សូរទឹកហូររហឹម", "សូរសំឡេងទ្រ", "ស្គរទូងរន្ថើន",
            "សំឡេងបេះដូងលោត", "សូរសព្ទផ្គរលាន់", "សូរភ្លៀងស្រក់", "សំឡេងខ្យល់កួច", "សំឡេងដង្ហើមញ័រ",
            "សំឡេងរនាតបន្លឺ", "សូរខ្យល់ត្រជាក់", "សូររៃយំរាត្រី", "សំឡេងគោះមហោរី"
        ]
    },
    "🖐️ Touch, Temperature & Physical Sensation (ការប៉ះពាល់ និងសីតុណ្ហភាព)": {
        "description": "Warmth, chill, velvet, roughness, weight, fever, and physical sensations.",
        "words_en": [
            "Velvet", "Shiver", "Feverish", "Numb", "Frostbitten",
            "Coarse", "Silken", "Heavyhearted", "Featherweight", "Burning touch",
            "Electric sting", "Smooth marble", "Gentle graze", "Piercing cold",
            "Molten heat", "Brittle bone", "Razor-sharp", "Trembling fingertips", "Calloused hands",
            "Weightless drift", "Chilling breath", "Scalding tear", "Rough sandpaper", "Friction",
            "Soft satin", "Ice-cold grip", "Warm embrace", "Suffocating dust", "Aching muscle"
        ],
        "words_km": [
            "កម្ដៅកក់ក្ដៅ", "រងាចាក់ដោត", "ទន់ល្មើយដូចសូត្រ", "ត្រជាក់ស្រេង", "រលោងស្រិល",
            "រំញ័រដួងចិត្ត", "ស្រាលដូចស្លាបសត្វ", "ភាពស្ពឹកស្រពន់", "ញ័រទ្រូង", "កម្ដៅរោលរាល",
            "ដៃញ័រទទ្រើត", "ត្រជាក់ដល់បេះដូង", "ទន់ភ្លន់ដូចខ្យល់", "រលាក់រលាយ", "ការឱបកក់ក្ដៅ",
            "ស្បែកក្ដៅភាយ", "ភាពគ្រើមគ្រាត", "ម្រាមដៃត្រជាក់", "ការប៉ះស្រាលៗ"
        ]
    },
    "🌧️ Scent, Taste, Weather & Seasons (ក្លិន រសជាតិ និងអាកាសធាតុ)": {
        "description": "Petrichor (rain on dry earth), sea salt, smoke, bittersweet tears, and changing seasons.",
        "words_en": [
            "Petrichor", "Bittersweet", "Sea salt", "Cedarwood", "Rain-soaked",
            "Lingering perfume", "Ash and embers", "Honeyed", "Tangy citrus", "Autumn air",
            "Stale smoke", "Morning dew", "Sun-baked soil", "Brisk breeze", "Monsoon downpour",
            "Jasmine blossom", "Burnt vanilla", "Salty tears", "Winter frost", "Damp asphalt",
            "Copper taste", "Crisp pine", "Sweet nectar", "Sudden deluge", "Thunderhead"
        ],
        "words_km": [
            "ក្លិនដីសើមភ្លៀង", "រសជាតិល្វីងជូរចត់", "ផ្អែមល្ហែមដូចទឹកឃ្មុំ", "ក្លិនផ្កាម្លិះ", "ទឹកសន្សើមព្រលឹម",
            "ផ្សែងអ័ព្ទរាត្រី", "ក្លិនខ្យល់សមុទ្រ", "ខ្យល់ធ្លាក់ខែរងា", "ភ្លៀងផ្គររលឹម", "ក្លិនផ្កាចំប៉ី",
            "រសជាតិនៃទឹកភ្នែក", "ផ្សែងធូបរាត្រី", "ខ្យល់ជំនោររដូវផ្ការីក", "ពពកខ្មៅងងឹត", "ខ្យល់ព្យុះបោកបក់",
            "ក្លិនស្លឹកឈើស្ងួត", "រសជាតិជូរចត់", "ទឹកភ្លៀងស្រោចដី", "សន្សើមធ្លាក់រងារ"
        ]
    },
    "❤️ Emotion, Deep Vulnerability & Longing (អារម្មណ៍ និងដួងចិត្ត)": {
        "description": "Nostalgia, yearning, longing, euphoric release, heartbreak, and redemption.",
        "words_en": [
            "Yearning", "Melancholy", "Saudade", "Nostalgic ache", "Unspoken",
            "Reckless love", "Unconditional", "Hollow chest", "Quiet surrender", "Fierce defiance",
            "Euphoric rush", "Shattered pride", "Lingering regret", "Sanctuary", "Catharsis",
            "Solitude", "Bittersweet grace", "Unrequited", "Desolation", "Sacred vow",
            "Flickering hope", "Paralyzed heart", "Tender mercy", "Consumed by fire", "Aching void"
        ],
        "words_km": [
            "ក្ដីស្រណោះស្រណោក", "ការនឹករលឹកដួងចិត្ត", "ការឈឺចាប់ស្ងប់ស្ងាត់", "ក្ដីសង្ឃឹមមិនរលត់", "ភាពឯកាខ្លោចផ្សា",
            "ស្នេហាស្មោះស្ម័គ្រ", "ចិត្តរំជួលក្តុកក្តួល", "ពាក្យលាគ្នាមិនដាច់អាល័យ", "ស្នាមរបួសដួងចិត្ត", "ការរង់ចាំគ្មានទិសដៅ",
            "ទឹកភ្នែកហូរស្ងាត់ៗ", "ក្ដីស្រឡាញ់ស្មោះសរ", "ដួងចិត្តបាក់បែក", "ការលះបង់ដើម្បីស្នេហ៍", "ក្ដីរំភើបញាប់ញ័រ",
            "ភាពព្រងើយកន្តើយ", "ការចងចាំមិនភ្លេច", "ការអត់ទោស", "បេះដូងទន់ខ្សោយ"
        ]
    },
    "🌊 Motion, Gravity & Kinetic Flow (ចលនា និងកម្លាំង)": {
        "description": "Drifting, soaring, colliding, spiraling, current, freefall, and breaking orbit.",
        "words_en": [
            "Drifting", "Soaring", "Colliding", "Spiraling", "Current",
            "Floating", "Plummeting", "Suspended", "Surging", "Tidal wave",
            "Unraveling", "Swaying in rhythm", "Orbiting", "Dissolving", "Freefall",
            "Cascading", "Treading water", "Breaking orbit", "Stumbling stride", "Catapult",
            "Ricochet", "Whirlwind", "Levitating", "Melting away", "Crashing down"
        ],
        "words_km": [
            "រសាត់តាមខ្យល់", "ហោះហើរលើមេឃ", "បោកបក់រលក", "វិលវល់ក្នុងដួងចិត្ត", "រំកិលសន្សឹមៗ",
            "រលាយបាត់ទៅ", "អណ្ដែតតាមគំនិត", "រំជើបរំជួល", "ធ្លាក់ក្នុងជ្រោះ", "បែកខ្ញែកដូចផ្កាយ",
            "រសាត់រសាត់ទៅឆ្ងាយ", "ដើរត្រដាបត្រដួស", "វិលវល់ក្នុងអតីត", "លោតផ្លោះរនាំង", "រលកបោកបក់",
            "រសាត់តាមចរន្តទឹក", "ហោះឆ្លងវេហាស៍", "ទាញទម្លាក់មកដី", "រំកិលតាមចង្វាក់"
        ]
    },
    "⚡ Contrast & Poetic Oxymorons (ពាក្យផ្ទុយច្នៃប្រឌិត - Hit Hook Formulas)": {
        "description": "Tension-packed opposites that hit songwriters use to forge unforgettable chorus hooks.",
        "words_en": [
            "Sweet agony", "Deafening silence", "Beautiful disaster", "Frozen fire", "Cruel kindness",
            "Living ghost", "Bitter honey", "Dark sunshine", "Gentle storm", "Proud defeat",
            "Painful bliss", "Chaotic calm", "Poisonous cure", "Crowded isolation", "Shattered perfection",
            "Quiet riot", "Heavy feather", "Burning ice", "Tender violence", "Silent scream"
        ],
        "words_km": [
            "ភាពស្ងាត់ដ៏កងរំពង", "ការឈឺចាប់ដ៏ផ្អែមល្ហែម", "ភ្លើងត្រជាក់ចាក់ដោត", "ព្យុះដ៏ស្ងប់ស្ងាត់", "ស្នាមញញឹមបង្ហូរទឹកភ្នែក",
            "ការបរាជ័យដ៏មានមោទកភាព", "ទឹកឃ្មុំល្វីងជូរចត់", "ភាពឯកាក្នុងហ្វូងមនុស្ស", "ពន្លឺងងឹតសូន្យឈឹង", "ការលាគ្នាដែលមិនឃ្លាតឆ្ងាយ",
            "របួសដ៏ស្រស់បំព្រង", "សំឡេងស្រែកស្ងាត់ជ្រងំ", "ភាពកក់ក្តៅត្រជាក់ស្រេង", "ស្នេហាដែលឈឺចាប់", "ការរង់ចាំដែលគ្មានថ្ងៃជួប"
        ]
    },
    "🎯 Rhyme Family Roots & Vowel Sounds (ក្រុមសំឡេងជួនសម្រាប់ទំពក់)": {
        "description": "Phonetically aligned root sound families for rap cypher flows and melodic vocal hooks.",
        "words_en": [
            "[-ight]: Light, Night, Bright, Fight, Sight, Ignite, Midnight",
            "[-ain]: Rain, Pain, Chain, Remain, Insane, Drain, Explain",
            "[-art]: Heart, Part, Start, Depart, Torn apart, Chart, Smart",
            "[-ear]: Tear, Clear, Fear, Disappear, Near, Sincere, Severe",
            "[-ow]: Glow, Slow, Below, Flow, Shadow, Echo, Overflow",
            "[-ay]: Day, Stay, Away, Gray, Betray, Decay, Fade away",
            "[-ive]: Alive, Survive, Drive, Strive, Deprive, Dive, Revive",
            "[-ire]: Fire, Desire, Wire, Admire, Inspire, Empire, Higher"
        ],
        "words_km": [
            "[ជួនស្រៈ អើយ]: កន្តើយ, ព្រងើយ, កន្លងហើយ, អើយ, ឆ្លើយ, កើយ",
            "[ជួនស្រៈ អស់]: ស្នោះ, ស្រណោះ, ស្មោះ, ស្រស់, អស់, ផ្លាស់ប្តូរ",
            "[ជួនស្រៈ អួល]: រំជួល, ស្រួល, ក្តុកក្តួល, ស្រទន់, ផ្ទួន",
            "[ជួនស្រៈ អ៊ឺម]: សង្ឃឹម, ញញឹម, រហឹម, ស្រទឹម, ត្រជាក់",
            "[ជួនស្រៈ អែង]: តែង, ប្លែក, ស្តែង, ចែង, ឯង, ស្វែង",
            "[ជួនស្រៈ អោន]: ស្រពោន, លាក់ខ្លួន, ថ្នាក់ថ្នម, ស្រទន់"
        ]
    }
}
