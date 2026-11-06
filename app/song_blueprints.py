"""
Professional Song Architecture Blueprints & Structure Presets.
Enables songwriters to instantly draft radio-ready pop hits, Khmer golden era ballads,
rap 16-bar verses, EDM drops, and R&B turnarounds.
"""

from typing import Dict, List

SONG_BLUEPRINTS: Dict[str, Dict] = {
    "Global Pop Radio (3-Minute Hit)": {
        "description": "Standard Max Martin / Top 40 Radio formula with maximum earworm hooks.",
        "bpm": "120 BPM",
        "structure": [
            "[Intro - Synth & Acoustic Guitar]",
            "[Verse 1 - Narrative Setup]",
            "[Pre-Chorus - Rising Energy]",
            "[Chorus - Catchy Hook & Maximum Harmony]",
            "[Verse 2 - Emotional Deepening]",
            "[Pre-Chorus - Tension & Build-up]",
            "[Chorus - Full Band & Punchy Drums]",
            "[Bridge - Melodic Shift & High Vocal Belt]",
            "[Final Chorus - Key Change & Ad-libs]",
            "[Outro - Fade Out with Vocal Whisper]"
        ],
        "template_lyrics": (
            "[Intro - Soft Piano & Ambient Synth]\n"
            "(Da-da-da, late night thoughts...)\n\n"
            "[Verse 1]\n"
            "City lights blur through the rainy glass\n"
            "Counting down the hours watch the shadows pass\n"
            "I still hear your footsteps down the empty hall\n"
            "Waiting for a sign or a midnight call\n\n"
            "[Pre-Chorus - Rising Energy]\n"
            "Feel the gravity slipping away\n"
            "Nothing left that I wanted to say\n"
            "Hold my breath till the lights ignite\n"
            "We're crossing the line tonight\n\n"
            "[Chorus - Catchy Hook & Anthemic Energy]\n"
            "Golden echoes dancing in the dark\n"
            "One small flame can reignite the spark\n"
            "Hear the heartbeat pulsing through the floor\n"
            "I'm never looking back anymore!\n\n"
            "[Verse 2]\n"
            "Neon reflections painted on the street\n"
            "Syncing up the rhythm to our tangled beat\n"
            "No more secrets buried in the ground\n"
            "This is where the quiet turns to sound\n\n"
            "[Pre-Chorus - Build-up]\n"
            "Feel the gravity slipping away\n"
            "Nothing left that I wanted to say\n\n"
            "[Chorus - Catchy Hook & Anthemic Energy]\n"
            "Golden echoes dancing in the dark\n"
            "One small flame can reignite the spark\n"
            "Hear the heartbeat pulsing through the floor\n"
            "I'm never looking back anymore!\n\n"
            "[Bridge - High Vocal Belt & Half-time Beat]\n"
            "Let the heavy skies fall down on me\n"
            "Finally standing where I'm meant to be!\n\n"
            "[Final Chorus - Explosive Drums & Harmonies]\n"
            "Golden echoes dancing in the dark\n"
            "One small flame can reignite the spark\n"
            "Hear the heartbeat pulsing through the floor\n"
            "I'm never looking back anymore!\n\n"
            "[Outro - Soft Fade Out]\n"
            "Never looking back... (echo)\n"
            "Golden echoes... fade."
        )
    },
    "Khmer Sinn Sisamouth Golden Classic (រចនាសម្ព័ន្ធមាស ៦០-៧០)": {
        "description": "Timeless 1960s Battambang / Phnom Penh sentimental romance structure.",
        "bpm": "74 BPM",
        "structure": [
            "[ផ្ដើមភ្លេង - សូឡូហ្គីតា និងវីយូឡុង]",
            "[វគ្គ ១ - រៀបរាប់បរិយាកាស និងការនឹក]",
            "[វគ្គ ២ - បង្ហាញអារម្មណ៍ឈឺចាប់ស្រណោះ]",
            "[បន្ទរ (Chorus) - ចំណុចកំពូលនៃបទចម្រៀង]",
            "[វគ្គ ៣ - ការសន្យា ឬពាក្យលា]",
            "[ភ្លេងសូឡូ (Solo Instrumental)]",
            "[បន្ទរ (Chorus) - បញ្ជាក់សេចក្ដីស្នេហា]",
            "[ចប់ (Outro) - បន្លឺសំឡេងស្រទន់សន្សឹមៗ]"
        ],
        "template_lyrics": (
            "[ផ្ដើមភ្លេង - សូឡូហ្គីតាអេឡិចត្រូនិក និងទ្រអ៊ូស្រទន់]\n\n"
            "[វគ្គ ១]\n"
            "ខ្យល់បក់រំភើយ ឆ្លងកាត់ស្ទឹងសង្កែ\n"
            "រាត្រីគ្មានខែ ឯកាខ្លោចផ្សា\n"
            "នឹកឃើញអនុស្សាវរីយ៍ គ្រាកន្លងរយាល\n"
            "ចិត្តអើយសោកា កំព្រាតែឯង។\n\n"
            "[វគ្គ ២]\n"
            "ដើមត្រសេកលាស់ ផ្កាធ្លាក់រុះរោយ\n"
            "បងចាំតែក្រោយ មិនឃើញជីវ៉ា\n"
            "តើអូនភ្លេចហើយ ឬយ៉ាងណាស្រស់ពៅ\n"
            "បន្សល់ទុកនូវ ស្នាមដំបៅស្នេហ៍។\n\n"
            "[បន្ទរ]\n"
            "ឱ! បាត់ដំបងអើយ បងនឹកមិនភ្លេច\n"
            "ចិត្តរែងស្រមៃ ឃើញតែភក្ត្រា\n"
            "បើទោះមេឃរលំ ភ្នំរលាយយ៉ាងណា\n"
            "ចិត្តស្នេហ៍ស្នេហា ស្មោះមួយគ្មានពីរ។\n\n"
            "[វគ្គ ៣]\n"
            "ថ្ងៃលិចកំបាំង ព្រះចន្ទរះចែង\n"
            "រលកបោកខ្យល់ នាំសារផ្ដាំទៅ\n"
            "សូមអូនវិលវិញ ជួបគ្នានៅត្រើយ\n"
            "កុំទុកបងឡើយ ឱ្យរងទារុណ។\n\n"
            "[ភ្លេងសូឡូ]\n\n"
            "[បន្ទរ]\n"
            "ឱ! បាត់ដំបងអើយ បងនឹកមិនភ្លេច\n"
            "ចិត្តរែងស្រមៃ ឃើញតែភក្ត្រា\n"
            "បើទោះមេឃរលំ ភ្នំរលាយយ៉ាងណា\n"
            "ចិត្តស្នេហ៍ស្នេហា ស្មោះមួយគ្មានពីរ។\n\n"
            "[ចប់ - សំឡេងតន្ត្រីរសាត់បាត់សន្សឹមៗ]\n"
            "ស្មោះមួយគ្មានពីរ... ឱ! ស្រីជីវ៉ា..."
        )
    },
    "Hip-Hop / Trap (16-Bar & Catchy Hook)": {
        "description": "Hard-hitting modern rap cadence with punchlines, 808 slides, and chant hook.",
        "bpm": "140 BPM (Half-time 70)",
        "structure": [
            "[Intro - 808 Bass Slide & Vocal Chant]",
            "[Verse 1 - 16 Bars Fast Flow & Storytelling]",
            "[Pre-Hook - Drum Roll & Filter Sweeps]",
            "[Hook - 8 Bars High Energy Chant]",
            "[Verse 2 - 16 Bars Pocket Flow & Wordplay]",
            "[Hook - 8 Bars Full Energy]",
            "[Outro - Beat Fade & Spoken Sign-off]"
        ],
        "template_lyrics": (
            "[Intro - Distorted 808 Bass & Atmospheric Synth]\n"
            "(Yeah, look into the mirror, who you see?)\n"
            "(Let's get it)\n\n"
            "[Verse 1 - 16 Bars Pocket Flow]\n"
            "Started from the basement now we climbing up the hill\n"
            "Never signed a contract, keep it independent real\n"
            "Midnight burning oil while the city stays asleep\n"
            "Promises we made are the promises we keep\n"
            "Stacking up the vision bar by bar, beat by beat\n"
            "Turned a heavy silence into anthems on the street\n"
            "Hustle in the blood, ain't no luck up in the game\n"
            "Walking through the fire never burn inside the flame\n\n"
            "[Pre-Hook - Snare Roll Build]\n"
            "Tick-tock, clock is ticking, hear the countdown start\n"
            "Can't fake the rhythm when it's living in the heart!\n\n"
            "[Hook - 8 Bars Chant & Heavy 808 Drop]\n"
            "We run the rhythm, never break the chain!\n"
            "Rising through the pressure, dancing in the rain!\n"
            "Shout it from the rooftops, tell 'em who we are!\n"
            "Coming from the shadows, shining like a star!\n\n"
            "[Verse 2 - 16 Bars Double-time Flow]\n"
            "Look at where we standing, look at how the tables turn\n"
            "Every bridge we crossed was a lesson that we learned\n"
            "No surrender, no retreat, we locked into the grind\n"
            "Leaving all the doubts and the shadows far behind\n\n"
            "[Hook - Heavy 808 Drop]\n"
            "We run the rhythm, never break the chain!\n"
            "Rising through the pressure, dancing in the rain!\n"
            "Shout it from the rooftops, tell 'em who we are!\n"
            "Coming from the shadows, shining like a star!\n\n"
            "[Outro - 808 Lowpass Filter Fade]\n"
            "Shining like a star... Yeah.\n"
            "SMG in the booth. Fade."
        )
    },
    "EDM / Festival Anthem (Build & Drop)": {
        "description": "Mainstage festival banger with emotional vocals, euphoric rising riser, and huge drop.",
        "bpm": "128 BPM",
        "structure": [
            "[Intro - Ambient Plucks & Filtered Kick]",
            "[Verse 1 - Intimate Vocal]",
            "[Build-Up - 16-Bar Snare Roll & Pitch Riser]",
            "[Drop - Euphoric Lead Synth & Sub Bass]",
            "[Breakdown - Atmospheric Chill Vocal]",
            "[Build-Up - High Pitch Riser]",
            "[Drop - Maximum Energy]",
            "[Outro - Soft Chord Fade]"
        ],
        "template_lyrics": (
            "[Intro - Ambient Plucks & Filtered Kick]\n"
            "In the silence of the night, waiting for the spark...\n\n"
            "[Verse 1 - Intimate Vocal]\n"
            "Step into the frequency, let the world erase\n"
            "Feel the waves collision in this open space\n"
            "Higher than the skyline, reaching for the sun\n"
            "This is where the future and the night become one\n\n"
            "[Build-Up - 16-Bar Snare Riser & White Noise]\n"
            "Feel it rising... (Snare accelerates)\n"
            "Can you hear the sound? (Pitch sweeps up)\n"
            "3... 2... 1... LET'S GO!\n\n"
            "[Drop - Mainstage Euphoric Saw Lead & Punchy Kick]\n"
            "[Instrumental Synth Drop with Vocal Chops: 'Feel the sound!']\n\n"
            "[Breakdown - Soft Piano & Ambient Pads]\n"
            "We were born to fly, no gravity can hold us now\n"
            "Lost inside the lights, we'll never touch the ground\n\n"
            "[Build-Up - Maximum Energy Riser]\n"
            "Here it comes again!\n"
            "Drop the world!\n\n"
            "[Drop - Explosive Festival Climax]\n"
            "[Outro - Reverb Tail & Soft Piano Chord]"
        )
    },
    "Acoustic Indie & Folk Ballad": {
        "description": "Intimate fingerpicked acoustic guitar, organic storytelling, and raw vulnerability.",
        "bpm": "85 BPM",
        "structure": [
            "[Intro - Fingerstyle Acoustic Guitar]",
            "[Verse 1 - Quiet Observation]",
            "[Verse 2 - Intimate Memory]",
            "[Chorus - Emotional Release & Harmonies]",
            "[Verse 3 - Time Passing]",
            "[Bridge - Poetic Revelation]",
            "[Chorus - Acoustic Swell & Foot Stomp]",
            "[Outro - Solitary Guitar String Ringing]"
        ],
        "template_lyrics": (
            "[Intro - Delicate Fingerstyle Acoustic Guitar]\n\n"
            "[Verse 1]\n"
            "Coffee's getting cold on the wooden windowsill\n"
            "Morning mist is hanging over Pine Tree Hill\n"
            "An old guitar that's missing just a single string\n"
            "Sometimes the quiet is the sweetest song to sing\n\n"
            "[Verse 2]\n"
            "Found your handwritten note in an old winter coat\n"
            "Words like little paper boats left to drift and float\n"
            "We were young and stubborn, chasing after ghosts\n"
            "Laughing at the things that we were frightened of the most\n\n"
            "[Chorus - Acoustic Swell & Warm Harmonies]\n"
            "Take me back to the porch swing in July\n"
            "Counting fireflies under an endless sky\n"
            "Time can bend and the rivers may run dry\n"
            "Love remains the only answer why\n\n"
            "[Bridge - Strumming Dynamic Build]\n"
            "Seasons turn the green to gold, and gold to winter white\n"
            "Still your memory warms me through the longest night\n\n"
            "[Chorus - Full Resonance with Foot Stomp]\n"
            "Take me back to the porch swing in July\n"
            "Counting fireflies under an endless sky\n"
            "Time can bend and the rivers may run dry\n"
            "Love remains the only answer why\n\n"
            "[Outro - Fingerpicking slows to a stop]\n"
            "The only answer why... (Single guitar harmonic)"
        )
    }
}
