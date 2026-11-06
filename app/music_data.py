"""
Comprehensive World Music Taxonomy, Genre Definitions, Song Structures, and Lyrical Markers.
Covers major musical traditions from North America, Latin America, Europe, East Asia,
Southeast Asia, South Asia, Africa, and the Middle East.
"""

WORLD_REGIONS = {
    "North America & Global Pop": {
        "Pop & Synthpop": {
            "bpm": "115 - 128",
            "meter": "4/4",
            "structure": "Intro - Verse 1 - Pre-Chorus - Chorus - Verse 2 - Pre-Chorus - Chorus - Bridge - Chorus - Outro",
            "rhyme": "ABAB or AABB",
            "vocal_styles": ["Belted Chorus", "Airy Verse", "Catchy Hook", "Ad-lib Callouts"],
            "description": "High-energy earworms with infectious hooks, punchy rhyming couplets, and relatable storytelling.",
            "sample_prompt": "An electrifying neon night pop anthem about breaking free from routine under city lights."
        },
        "Hip-Hop & Trap": {
            "bpm": "130 - 150 (Half-time 65 - 75)",
            "meter": "4/4",
            "structure": "Intro - 16-Bar Verse 1 - Hook - 16-Bar Verse 2 - Hook - Bridge / Breakdown - Hook - Outro",
            "rhyme": "Multi-syllabic, Internal Rhyme, Slant Rhymes",
            "vocal_styles": ["Triplet Flow", "Melodic Auto-Tune", "Aggressive Delivery", "Ad-libs [Skrrt, Yeah]"],
            "description": "Rhythmically complex, cadence-driven lyrics with wordplay, internal rhymes, and personal bravado.",
            "sample_prompt": "A hard-hitting trap anthem with fast cadences about building an empire from late nights in the studio."
        },
        "Contemporary R&B / Neo-Soul": {
            "bpm": "70 - 95",
            "meter": "4/4 or 6/8",
            "structure": "Intro - Verse 1 - Chorus - Verse 2 - Chorus - Extended Bridge - Vocal Runs - Outro",
            "rhyme": "Loose ABAB, Melodic Assonance",
            "vocal_styles": ["Falsetto Runs", "Smoky Chest Voice", "Spoken Word Intro", "Layered Harmonies"],
            "description": "Sensual, emotional, intimate grooves with lush harmonies and vulnerable storytelling.",
            "sample_prompt": "A warm, late-night neo-soul ballad about rekindling an old spark under rain-slicked windows."
        },
        "Indie / Alternative Rock": {
            "bpm": "110 - 140",
            "meter": "4/4",
            "structure": "Intro - Verse 1 - Chorus - Verse 2 - Chorus - Guitar Solo / Noise Bridge - Big Chorus - Feedback Outro",
            "rhyme": "ABCB, Metaphorical Slant Rhymes",
            "vocal_styles": ["Raw & Breathy", "Dynamic Belting", "Understated delivery"],
            "description": "Poetic, introspective lyricism with imagery of youth, estrangement, and existential wonder.",
            "sample_prompt": "An indie rock anthem about finding solace in messy coastal road trips with old friends."
        },
        "Country & Americana": {
            "bpm": "80 - 115",
            "meter": "4/4 or 3/4 (Waltz)",
            "structure": "Intro - Verse 1 - Chorus - Verse 2 - Chorus - Story Bridge - Chorus - Guitar Outro",
            "rhyme": "Strict AABB or ABCB",
            "vocal_styles": ["Southern Twang", "Storyteller Cadence", "Acoustic Harmony"],
            "description": "Narrative storytelling focused on real life, small towns, dusty roads, heartache, and redemption.",
            "sample_prompt": "A heartfelt country song about an old guitar passed down three generations in a quiet mountain town."
        },
        "EDM & Festival Dance": {
            "bpm": "126 - 132",
            "meter": "4/4",
            "structure": "Intro - Verse - Build-Up - [DROP] - Verse 2 - Build-Up - [BIG DROP] - Outro",
            "rhyme": "Simple Catchy AABB",
            "vocal_styles": ["Euphoric Vocals", "Reverb-drenched Staccato", "Chanted Anthem"],
            "description": "Concise, emotional build-ups erupting into massive melodic instrumentals and festival sing-alongs.",
            "sample_prompt": "A soaring progressive house track about living forever in the moment when the bass hits."
        }
    },

    "Latin America & Caribbean": {
        "Reggaeton & Latin Urban": {
            "bpm": "90 - 98",
            "meter": "4/4 (Dem-bow rhythm)",
            "structure": "Intro - Coro (Hook) - Verso 1 - Pre-Coro - Coro - Verso 2 (Chanteo) - Puente - Coro - Outro",
            "rhyme": "Asonante & Consonante, Cadence-locked",
            "vocal_styles": ["Chanteo (Fast rap)", "Melodic Auto-Tune", "Party Call-and-Response"],
            "description": "Sensual, rhythmic bounce propelled by the iconic dem-bow drum loop, party energy, and romantic friction.",
            "sample_prompt": "A fiery Puerto Rican reggaeton party track with bilingual flair about dancing in San Juan."
        },
        "Bachata": {
            "bpm": "120 - 135",
            "meter": "4/4 (Bongo + Güira syncopation)",
            "structure": "Intro - Verso 1 - Coro - Verso 2 - Coro - Requinto Solo - Coro - Mambo Breakdown",
            "rhyme": "ABCB, Passionate poetic rhymes",
            "vocal_styles": ["High-pitched Falsetto", "Emotional Weeping Tone", "Dual Harmonies"],
            "description": "Sensual Dominican guitar rhythm expressing intense romance, longing, heartbreak, and seduction.",
            "sample_prompt": "A modern sensual bachata song about midnight memories and unsaid confessions across the ocean."
        },
        "Salsa & Mambo": {
            "bpm": "180 - 220 (Dance tempo)",
            "meter": "4/4 (Clave rhythm 2-3 or 3-2)",
            "structure": "Intro - Paseo - Verso - Montuno (Coro-Pregón) - Mambo Horns - Moña - Final",
            "rhyme": "Octosyllabic Décima or Copla",
            "vocal_styles": ["Sonero Improvisation (Pregón)", "Brass Choir Chorus", "Rhythmic Shouts"],
            "description": "Sophisticated Afro-Cuban polyrhythms with call-and-response vocal improvisations and horn sections.",
            "sample_prompt": "A vibrant New York/Cali salsa celebration of overcoming adversity through dance and community."
        },
        "Cumbia": {
            "bpm": "85 - 105",
            "meter": "2/4 or 4/4 (Shuffling güiro)",
            "structure": "Intro - Verso 1 - Estribillo - Verso 2 - Estribillo - Acordeón Solo - Outro",
            "rhyme": "AABB Folk Rhyme",
            "vocal_styles": ["Warm Storyteller", "Playful Shouts", "Accordion Counter-melody"],
            "description": "Hypnotic, rolling accordion and percussion groove capturing street life and celebration across the Americas.",
            "sample_prompt": "A lively Colombian/Mexican cumbia groove about meeting at the town festival under paper lanterns."
        },
        "Bossa Nova & Samba": {
            "bpm": "120 - 140 (Light 2/4)",
            "meter": "2/4 Syncopated",
            "structure": "AABA Form - Instrument Solo - A - Extended Outro",
            "rhyme": "Subtle Internal Assonance",
            "vocal_styles": ["Intimate Whisper", "Conversational Portuguese/English", "Gentle Vibrato"],
            "description": "Sophisticated jazz chords, ocean breezes, saudade (bittersweet nostalgia), and effortless elegance.",
            "sample_prompt": "A sun-dappled bossa nova about the melancholy beauty of Rio de Janeiro at golden hour."
        },
        "Corrido Tumbado / Regional Mexican": {
            "bpm": "125 - 145",
            "meter": "3/4 (Waltz tempo with tololoche bass)",
            "structure": "Requinto Intro - Verso 1 - Verso 2 - Coro - Solo de Requinto y Trombón - Verso 3 - Outro",
            "rhyme": "Consonant couplets",
            "vocal_styles": ["Nasal Youthful Delivery", "Acoustic Brass Harmonization", "Gritty Swagger"],
            "description": "Modern urban Mexican acoustic ballads blending traditional 12-string guitars and brass with street tales.",
            "sample_prompt": "A modern corrido tumbado celebrating loyalty, rise from poverty, and honoring family roots."
        }
    },

    "East Asia": {
        "K-Pop (Korean Pop)": {
            "bpm": "118 - 132",
            "meter": "4/4",
            "structure": "Intro - Verse 1 - Rap Line - Pre-Chorus - Dynamic Chorus - Verse 2 - Rap Drop - Bridge (Vocal Climax) - Final Chorus - Killing Part Outro",
            "rhyme": "Bilingual Korean/English Hooks, Rhythmic Syllable Stabs",
            "vocal_styles": ["Punchy Rap Verse", "High Note Belting", "Whisper Concept Line", "Chanted Chorus"],
            "description": "Ultra-polished, genre-blending spectacle with rapid vocal role-switches, bilingual hooks, and choreography tags.",
            "sample_prompt": "A futuristic girl-crush K-Pop title track with an explosive brass drop and fearless bilingual hook."
        },
        "J-Pop & Anime Soundtrack": {
            "bpm": "135 - 175",
            "meter": "4/4 (Often fast, energetic)",
            "structure": "Intro - A-Melo (Verse) - B-Melo (Pre-Chorus) - Sabi (Main Chorus) - A-Melo - B-Melo - Sabi - C-Melo (Bridge) - Grand Sabi - Outro",
            "rhyme": "5-7-5 / 7-7 traditional Japanese cadence, End-vowel harmony",
            "vocal_styles": ["Emotional Soaring Vocals", "Fast Syllable Enunciation", "Dramatized Crescendos"],
            "description": "Melodically rich with the classic Royal Road (Oudou) chord progression, dramatic stakes, and poetic sentiment.",
            "sample_prompt": "An exhilarating high-speed anime opening theme about running towards tomorrow despite the rain."
        },
        "City Pop & Shibuya-kei": {
            "bpm": "105 - 120",
            "meter": "4/4 (Groovy slap bass)",
            "structure": "Intro - Verse 1 - Pre-Chorus - Chorus - Sax Solo - Verse 2 - Bridge - Chorus - Smooth Fade",
            "rhyme": "Soft poetic phrasing, urban imagery",
            "vocal_styles": ["Velvet Smooth", "Sophisticated Breeze", "Melodic Spoken Interlude"],
            "description": "80s Japanese urban luxury, midnight coastal drives, cassette decks, and nostalgic neon romance.",
            "sample_prompt": "A vintage city pop track about cruising through Tokyo's expressway at 2 AM with the windows down."
        },
        "Mandopop & C-Pop Ballad": {
            "bpm": "68 - 85",
            "meter": "4/4",
            "structure": "Piano Intro - Verse 1 - Verse 2 - Chorus - Verse 3 - Grand Chorus - Strings Bridge - Climax Chorus - Soft Outro",
            "rhyme": "Tonal poetic rhymes (Classical Chinese poetic meter)",
            "vocal_styles": ["Tearful Empathy", "Pure Acoustic Tone", "Graceful Falsetto"],
            "description": "Epic tearjerker ballads with classical literary metaphors, grand orchestral sweeps, and profound emotional weight.",
            "sample_prompt": "A grand Mandopop ballad about waiting for a reincarnated love across thousand autumn seasons."
        }
    },

    "Southeast Asia": {
        "Khmer Music (Romvong / Kantrum / Modern Pop)": {
            "bpm": "95 - 125",
            "meter": "4/4 or 2/4 (Skor Daey rhythm)",
            "structure": "Tro / Roneat Intro - Verse 1 - Refrain - Verse 2 - Chorus - Tro Solo - Dance Chorus - Festive Outro",
            "rhyme": "Khmer poetic Chbap meter, Internal vowel matching",
            "vocal_styles": ["Melismatic Ornaments", "Festive Call-and-Response", "Joyous Lilt"],
            "description": "Joyful Khmer rhythms featuring traditional percussion, pentatonic scales, village celebration, and modern pop fusion.",
            "sample_prompt": "A lively Khmer modern celebration song celebrating Khmer New Year with playful village courtship."
        },
        "Thai Pop & T-Pop / Luk Thung": {
            "bpm": "100 - 130",
            "meter": "4/4",
            "structure": "Khaen Intro - Verse 1 - Pre-Chorus - Chorus - Isan Rhythmic Break - Bridge - Chorus - Outro",
            "rhyme": "Melodic tonal rhymes, flowing diphthongs",
            "vocal_styles": ["Smooth Sweet Vocals", "Vocal Vibrato Twang (Luk Thung)", "Playful Rap"],
            "description": "Sweet, catchy melodies blending northeastern Isan folk instruments with sleek modern synthesizer beats.",
            "sample_prompt": "A breezy Bangkok summer T-Pop song about shy glances and sweet iced tea in a café."
        },
        "V-Pop (Vietnamese Pop)": {
            "bpm": "75 - 110",
            "meter": "4/4",
            "structure": "Dan Tranh Intro - Verse 1 - Pre-Chorus - Emotional Chorus - Verse 2 - Bridge - Chorus - Outro",
            "rhyme": "Tonal wordplay (Luc Bat inspiration)",
            "vocal_styles": ["Gentle Whispery Vocals", "Airy High Register", "Acoustic Warmth"],
            "description": "Deeply romantic, moody, and atmospheric pop music characterized by poetic lyrical elegance.",
            "sample_prompt": "A rainy evening V-Pop ballad about a walk along West Lake in Hanoi reflecting on lost love."
        },
        "Indonesian Dangdut & Indo-Pop": {
            "bpm": "120 - 140",
            "meter": "4/4 (Kendang Tabla beat)",
            "structure": "Kendang Roll Intro - Bait 1 - Reff (Chorus) - Bait 2 - Reff - Suling (Flute) Solo - Koplo Drop - Outro",
            "rhyme": "Pantun Rhyme Scheme (ABAB)",
            "vocal_styles": ["Cengkok (Arabesque Vocal Trill)", "High Vibrato", "Party Shouts (Asik!)"],
            "description": "Electrifying dance folk-pop driven by the kendang drum, bamboo suling flute, and hypnotic Koplo drops.",
            "sample_prompt": "An upbeat Koplo Dangdut track about dancing the night away and forgetting everyday troubles."
        }
    },

    "South Asia": {
        "Bollywood / Filmi Masala": {
            "bpm": "105 - 135",
            "meter": "4/4 or 6/8 (Dholak rhythm)",
            "structure": "Shehnai/Violin Intro - Mukhda (Chorus) - Antara 1 (Verse) - Mukhda - Antara 2 - Big Orchestral Interlude - Grand Mukhda",
            "rhyme": "Urdu/Hindi poetic couplets (Shayari style)",
            "vocal_styles": ["Playback Singer Clarity", "Classical Gamak & Taans", "Dynamic Duet Exchanges"],
            "description": "Cinematic grandeur featuring dholak, soaring string sections, colorful imagery, and larger-than-life romance.",
            "sample_prompt": "A lavish Bollywood romance song set during a colorful monsoon festival with grand violin sweeps."
        },
        "Punjabi Pop & Bhangra": {
            "bpm": "128 - 145",
            "meter": "4/4 (Chaap dhol swing)",
            "structure": "Tumbi Riff Intro - Boli (Couplet) - Hook - Verse 1 - Hook - Dhol Drop - Verse 2 - Hook - Outro",
            "rhyme": "Punjabi Boliyan Rhyme (AABB with rhythmic cries like 'Balle Balle', 'Hadippa')",
            "vocal_styles": ["Chest-dominant Power", "High-pitch Shouts", "Tumbi Accents"],
            "description": "Irresistible energy propelled by dhol drums, tumbi riffs, agricultural celebrations, and triumphant swagger.",
            "sample_prompt": "A thunderous modern Punjabi Bhangra track celebrating hard work, village pride, and joyful dancing."
        },
        "Sufi Rock & Ghazal": {
            "bpm": "65 - 85",
            "meter": "Keherwa or Dadra (6/8 or 8/4)",
            "structure": "Harmonium Alaap - Matla (First Sher) - Chorus - Sher 2 - Sher 3 - Qawwali Climax Handclaps - Makhta (Outro)",
            "rhyme": "Qafiya and Radif (Strict classical Ghazal rhyming rules)",
            "vocal_styles": ["Spiritual Ecstasy", "Sustained High Notes", "Call-and-Response Chorus"],
            "description": "Devotional, transcendent poetry exploring divine union, intoxication of love, and philosophical reflection.",
            "sample_prompt": "A soaring Sufi rock fusion about the soul seeking eternal light amidst the chaos of the world."
        }
    },

    "Africa & Afro-Diaspora": {
        "Afrobeats (Naija / Ghana)": {
            "bpm": "100 - 110",
            "meter": "4/4 (Syncopated log drum & shakers)",
            "structure": "Intro - Hook - Verse 1 - Pre-Chorus - Chorus - Verse 2 - Bridge - Final Chorus - Groove Outro",
            "rhyme": "Pidgin English + Yoruba/Igbo/Twi wordplay, Melodic Bounce",
            "vocal_styles": ["Laid-back Swag", "Chant Callouts", "Warm Harmonized Group Vocals"],
            "description": "Global phenomenon blending African percussion, West African Highlife chords, Pidgin street slang, and infectious joy.",
            "sample_prompt": "An irresistible Lagos Afrobeats sunshine groove celebrating blessings, resilience, and good vibes."
        },
        "Amapiano (South African Deep House)": {
            "bpm": "112 - 116",
            "meter": "4/4 (Warm Rhodes piano + iconic Log Drum punch)",
            "structure": "Rhodes Intro - Subtle Groove - Verse 1 - Log Drum Drop - Chorus - Instrumental Break - Verse 2 - Climax - Outro",
            "rhyme": "Zulu / Xhosa / Sotho chants with English hooks",
            "vocal_styles": ["Hypnotic Chants", "Whispered Spoken Word", "Deep Bass Vocal Hits"],
            "description": "Lush, jazzy piano chords floating above deep subterranean log drums, shaker grooves, and hypnotic township party chants.",
            "sample_prompt": "A late-night Johannesburg Amapiano track with jazzy Rhodes piano chords and deep rolling bass."
        },
        "Highlife & Palm Wine": {
            "bpm": "95 - 115",
            "meter": "4/4 (Interlocking acoustic guitars)",
            "structure": "Horn Call - Verse 1 - Chorus - Guitar Solo - Verse 2 - Chorus - Percussion Outro",
            "rhyme": "AABB Folk Wisdom",
            "vocal_styles": ["Gentle Conversational Storyteller", "Brass Call-and-Response"],
            "description": "Warm, sunny, brass-infused guitar melodies carrying proverbs about moral living, family, and peaceful times.",
            "sample_prompt": "A relaxing acoustic Highlife song about sipping palm wine and counting life's simple blessings."
        },
        "Soukous & Congolese Rumba": {
            "bpm": "120 - 135 (Seben breakdown tempo 145)",
            "meter": "4/4 (Cascading solo guitar melodies)",
            "structure": "Slow Rumba Intro - Story Verses - Chorus - Seben! (Accelerated Guitar Frenzy & Atalaku Chants) - Dance Outro",
            "rhyme": "Lingala / French romantic rhymes",
            "vocal_styles": ["Velvety Tenor", "Atalaku (Hype animator shouting rhythmic cues)"],
            "description": "Intricate, sparkling guitar tapestries that build from romantic balladry into frenetic, euphoric dance explosions.",
            "sample_prompt": "A classic Kinshasa Congolese rumba that shifts into an electrifying high-speed Seben guitar dance."
        }
    },

    "Middle East & North Africa": {
        "Modern Arabic Pop": {
            "bpm": "100 - 125",
            "meter": "4/4 (Maksoum / Baladi rhythm)",
            "structure": "Nay / Oud Intro - Madkhal - Bayt 1 - Lazma (Hook) - Bayt 2 - Lazma - Taqsim (Solo) - Grand Lazma - Outro",
            "rhyme": "Monorhyme or Bayt couplets (Classical Arabic Saj' & modern colloquial)",
            "vocal_styles": ["Quarter-tone Maqam inflections", "Dramatic Mawwal Intro", "Passionate Shouts (Ya Leili)"],
            "description": "Passionate melodies built on Arabic melodic modes (Maqamat), darbouka percussion, strings, and intense emotional expression.",
            "sample_prompt": "A dramatic Mediterranean Arabic pop track about longing across distances with soaring violins."
        },
        "Dabke & Levantine Beats": {
            "bpm": "125 - 135",
            "meter": "4/4 (Stomping Mijwiz & Darbouka)",
            "structure": "Mijwiz Siren Intro - Lawwah (Leader Chant) - Verse 1 - Stomp Chorus - Mijwiz Solo - Verse 2 - Peak Stomp - Outro",
            "rhyme": "AABB Folk rhyming stanzas",
            "vocal_styles": ["Piercing High Chest Voice", "Rhythmic Foot Stomp Shouts", "Zaghrouta (Celebratory Ululation)"],
            "description": "Electrifying line-dance music featuring the screeching mijwiz reed pipe, thundering table percussion, and ecstatic pride.",
            "sample_prompt": "A high-octane modern electro-dabke track celebrating a village wedding on the hills of Mount Lebanon."
        },
        "Rai & Chaabi (Algerian / North African)": {
            "bpm": "105 - 120",
            "meter": "6/8 or 4/4 (Gellal drum + synth)",
            "structure": "Intro Istikhbar - Verse 1 - Chorus - Accordion Solo - Verse 2 - Chorus - Outro",
            "rhyme": "Oran street poetry with French slang",
            "vocal_styles": ["Gritty Blues-like Lament", "Impassioned Cry ('Cheb' rebel tone)"],
            "description": "The rebel blues of North Africa, speaking openly of social struggles, romantic passion, exile, and hope.",
            "sample_prompt": "A modern Rai track blending electric guitar, accordion, and darbuka about longing for the homeland."
        },
        "Turkish Pop & Arabesque": {
            "bpm": "95 - 120",
            "meter": "4/4 or 9/8 (Aksak Turkish rhythm)",
            "structure": "Baglama Intro - Verse 1 - Nakarat (Chorus) - Verse 2 - Nakarat - Klarnet Solo - Bridge - Grand Nakarat",
            "rhyme": "Turkish vowel harmony rhyming",
            "vocal_styles": ["Melodramatic Vibrato", "Deep Quarter-tone Melisma", "Clarinet Imitation"],
            "description": "Heart-wrenching Turkish melodies uniting Anatolian folk instruments, gypsy clarinets, and modern electronic beats.",
            "sample_prompt": "A cinematic Turkish pop song exploring fate, autumn melancholy, and the mystery of the Bosphorus."
        }
    },

    "Europe & Folk Traditions": {
        "Celtic Folk & Sea Shanty": {
            "bpm": "95 - 125",
            "meter": "6/8 (Jig) or 4/4 (Reel)",
            "structure": "Tin Whistle Intro - Verse 1 - Chorus - Verse 2 - Chorus - Fiddle Reel Solo - Verse 3 - Rousing Chorus - Outro",
            "rhyme": "AABB or ABCB Ballad Meter",
            "vocal_styles": ["Acoustic Group Singalong", "A Cappella Foot-Stomp", "Rebel Storyteller"],
            "description": "Rowdy pub singalongs, tales of high seas, legendary heroes, and haunting acoustic fiddle melodies.",
            "sample_prompt": "A rousing sea shanty about braving wild northern waves and returning home to harbor lights."
        },
        "Flamenco & Spanish Passion": {
            "bpm": "110 - 170 (Compás Bulerías or Rumba)",
            "meter": "12-beat Compás or 4/4 Rumba Flamenca",
            "structure": "Guitar Falseta - Temple (Quejío) - Copla 1 - Estribillo - Copla 2 - Remate - Fin",
            "rhyme": "Assonant Copla (8-syllable verses)",
            "vocal_styles": ["Cante Jondo (Deep guttural cry)", "Palmas Handclapping", "Jaleo Shouts ('¡Olé!')"],
            "description": "Intense raw human emotion, fiery nylon-string guitars, rhythmic footwork, and soul-piercing vocal lament.",
            "sample_prompt": "A dramatic Rumba Flamenca with acoustic guitars and rhythmic claps about an untamed spirit in Andalusia."
        },
        "French Chanson & Café Indie": {
            "bpm": "80 - 105",
            "meter": "3/4 (Waltz) or 4/4",
            "structure": "Accordion Intro - Couplet 1 - Refrain - Couplet 2 - Refrain - Bridge - Final Refrain - Outro",
            "rhyme": "Rich feminine and masculine French rhymes",
            "vocal_styles": ["Sultry Whisper", "Literary Enunciation", "Conversational Irony"],
            "description": "Literary, poetic storytelling painted with Parisian accordions, cigarette smoke, philosophy, and bittersweet romance.",
            "sample_prompt": "A charming Parisian indie chanson about wandering Montmartre on a Sunday morning."
        },
        "Nordic Melodic Folk / Metal": {
            "bpm": "100 - 140",
            "meter": "4/4 or 3/4",
            "structure": "Nyckelharpa Intro - Verse 1 - Pre-Chorus - Anthemic Chorus - Verse 2 - Chorus - Tagelharpa Solo - Grand Chorus - Outro",
            "rhyme": "Alliterative Norse verse, ABCB",
            "vocal_styles": ["Throat Singing Chants", "Kulning (Nordic herding call)", "Towering Melodic Belting"],
            "description": "Vast pine forests, ancient mythology, brooding strings, and thunderous epic choruses.",
            "sample_prompt": "An epic Nordic folk anthem invoking the northern lights, winter frost, and ancient wanderers."
        }
    }
}

SONG_STRUCTURES = {
    "Standard Pop / Global Radio (3-Minute Hit)": [
        "[Intro - Atmospheric / Hook Tease]",
        "[Verse 1 - Setting the Scene]",
        "[Pre-Chorus - Rising Tension]",
        "[Chorus - Main Hook / High Energy]",
        "[Verse 2 - Deepening the Story]",
        "[Pre-Chorus - Rising Tension]",
        "[Chorus - Main Hook / Full Band]",
        "[Bridge - Emotional Shift / New Perspective]",
        "[Chorus - Climax / Ad-libs]",
        "[Outro - Fade Out / Lasting Catchphrase]"
    ],
    "TikTok & Reels 30s-60s (Hook-First Viral)": [
        "[Hook Tease - Earworm First 3 Seconds!]",
        "[Verse - Short 4-Bar Punchy Rhythm]",
        "[Pre-Chorus - Quick 2-Bar Riser]",
        "[CHORUS CLIMAX - Viral High Energy Singalong]",
        "[Post-Chorus / Beat Loop - Dance Transition Outro]"
    ],
    "Khmer Romvong / Saravan (រាំវង់ ចូលឆ្នាំ)": [
        "[សេចក្ដីផ្ដើម - ស្នូរស្គរដៃ និងទ្រអូ]",
        "[វគ្គ១ (Verse 1) - រៀបរាប់បរិយាកាសបុណ្យភូមិ]",
        "[បន្ទរ (Chorus) - ទំនុកច្រៀងពិរោះកន្ត្រាក់អារម្មណ៍]",
        "[វគ្គ២ (Verse 2) - ជួបគូស្នេហ៍រាំជុំវិញផ្កាឈូក]",
        "[បន្ទរ (Chorus) - ក្រុមច្រៀងរួមគ្នា]",
        "[ឆ្លើយឆ្លង (Call-and-Response) - ប្រុសឆ្លើយ ស្រីឆ្លង]",
        "[ស្គរដៃរន្ថើន (Fast Drum Tempo Up) - រាំវង់សប្បាយរីករាយ]",
        "[បញ្ចប់ (Outro) - ស្នូរសើច និងជូនពរឆ្នាំថ្មី]"
    ],
    "Khmer Kantrum Rock Fusion (កន្ទ្រឹម ញាក់សប្បាយ)": [
        "[កន្ទ្រឹម Intro - សំឡេងកាឡឹង និងទ្រសូឡូ]",
        "[វគ្គ១ - ចង្វាក់កន្ទ្រឹមកន្ត្រាក់ទ្រូង]",
        "[បន្ទរ (Hook) - ពាក្យកំប្លុកកំប្លែងទាក់ទាញ]",
        "[វគ្គ២ - ឆ្លងឆ្លើយក្អាកក្អាយ]",
        "[ទ្រសូឡូ (Electric Tro & Guitar Solo)]",
        "[កន្ត្រាក់រាំ (Heavy Dance Beat Drop)]",
        "[Outro - កន្ទ្រឹមលាន់លឺពេញភូមិ]"
    ],
    "Romantic Duet (បទឆ្លើយឆ្លង ប្រុស-ស្រី)": [
        "[Intro - Romantic Acoustic Strings]",
        "[Verse 1 - ប្រុស (Male Vocal): ចាប់ផ្ដើមរៀបរាប់ក្តីស្រលាញ់]",
        "[Verse 2 - ស្រី (Female Vocal): ឆ្លើយតបដោយភាពអៀនប្រៀន]",
        "[Pre-Chorus - ច្រៀងឆ្លាស់គ្នា (Interlocking Lines)]",
        "[Chorus - ច្រៀងរួមគ្នា (Duet Harmony & High Emotion)]",
        "[Verse 3 - ប្រុស & ស្រី (Call & Response)]",
        "[Bridge - ច្រៀងបន្ទររំជួលចិត្ត (Emotional Peak)]",
        "[Final Chorus - Duet Harmony with Ad-libs]",
        "[Outro - សំឡេងខ្សឹបផ្អែមល្ហែម]"
    ],
    "Hip-Hop / Rap 16-Bar Cypher": [
        "[Intro - Producer Tag & Hype]",
        "[Verse 1 - 16 Bars of Complex Flow]",
        "[Hook - Catchy Melodic / Punchy]",
        "[Verse 2 - 16 Bars Wordplay & Story]",
        "[Hook - Catchy Melodic / Punchy]",
        "[Bridge - Beat Switch / Breakdown]",
        "[Hook - Maximum Energy]",
        "[Outro - Final Word / Beat Echoes]"
    ],
    "Trap & Drill Fast Flow (Sub-Bass Banger)": [
        "[Intro - Dark Reverb Synth & 808 Slide]",
        "[Hook - Short 8-Bar Explosive Melody]",
        "[Verse 1 - 12-Bar Triplet Cadence Flow]",
        "[Pre-Hook - Quick Pause / Gunshot / Ad-lib]",
        "[Hook - Heavy Sub-Bass]",
        "[Verse 2 - Fast Double-Time Flow]",
        "[Beat Switch - Half-Time Heavy Outro]"
    ],
    "K-Pop Multi-Role Spectacle (Idol Title Track)": [
        "[Intro - Visual Concept Whisper & Synth Stabs]",
        "[Verse 1 - Soft Vocals (Sub-Vocal)]",
        "[Rap Break 1 - Fast Punchy Rhymes (Main Rapper)]",
        "[Pre-Chorus - Rising Harmonies (Lead Vocal)]",
        "[Chorus - Explosive Drop & Chanted Hook]",
        "[Verse 2 - Smooth Flow (Lead Vocal)]",
        "[Rap Break 2 - Rhythmic Stabs (Lead Rapper)]",
        "[Pre-Chorus - Ascending Run]",
        "[Chorus - Full Choreography Energy]",
        "[Bridge - Dramatic Key Change & High Note Belting]",
        "[Dance Break / Killing Part - Iconic Catchphrase]",
        "[Outro - Fade to Silence with Concept Pose]"
    ],
    "Emotional Piano Ballad (Tearjerker)": [
        "[Intro - Solitary Piano Chord Progression]",
        "[Verse 1 - Whispered Intimacy / The Memory]",
        "[Pre-Chorus - Subtle Cello & Rising Heartache]",
        "[Chorus - Soaring Vocal Belt / Pure Vulnerability]",
        "[Verse 2 - The Empty Space Left Behind]",
        "[Pre-Chorus - Rising Emotional Tremble]",
        "[Chorus - Full String Orchestra Swell]",
        "[Bridge - The Unspoken Truth / Climax Tears]",
        "[Final Chorus - Maximum Vocal Cry]",
        "[Outro - Single Piano Note Dying Away]"
    ],
    "Acoustic Singer-Songwriter (Coffeehouse Indie)": [
        "[Intro - Warm Fingerpicked Acoustic Guitar]",
        "[Stanza 1 - Poetic Observation / Morning Coffee]",
        "[Refrain - Simple 2-Line Honest Truth]",
        "[Stanza 2 - Childhood Reflections / Golden Hour]",
        "[Refrain - Gentle Vocal Harmony]",
        "[Story Bridge - A Turning Point in the Journey]",
        "[Final Refrain - Sustained Acoustic Resonance]",
        "[Coda - Soft Whistle / Harmonica Outro]"
    ],
    "R&B / Neo-Soul Slow Jam (Midnight Groove)": [
        "[Intro - Warm Rhodes Chords & Smoky Vinyl Crackle]",
        "[Verse 1 - Silky Falsetto & Slow Intimacy]",
        "[Pre-Chorus - Finger Snaps & Bass Glide]",
        "[Chorus - Lush 4-Part Vocal Harmonies]",
        "[Verse 2 - Midnight Confessions]",
        "[Pre-Chorus - Ascending Melodic Runs]",
        "[Chorus - Deep Soulful Groove]",
        "[Extended Bridge - Improvised Vocal Runs]",
        "[Outro - Smooth Whispered Ad-libs & Fade]"
    ],
    "EDM Festival Anthem (Big Build & Drop)": [
        "[Intro - Atmospheric Pluck Pulse]",
        "[Verse - Emotional Female / Male Vocals]",
        "[Build-Up - Snare Roll Accelerating, High White Noise]",
        "[MASSIVE FESTIVAL DROP - Bass Explosion & Vocal Chop]",
        "[Verse 2 - Half-Time Reflection]",
        "[Build-Up - Double-Time Riser, Energy Stacking]",
        "[FINAL BIG DROP - Maximum Crowd Euphoria]",
        "[Outro - Cooling Synth Pads Fade]"
    ],
    "Latin Reggaeton / Perreo (Dem-bow Dance)": [
        "[Intro - Dem-bow Fades In & DJ Signature Shout]",
        "[Coro (Hook) - Ultra Pegajoso]",
        "[Verso 1 - Chanteo Callejero Rápido]",
        "[Pre-Coro - Subiendo la Presión]",
        "[Coro - Pista de Baile Encendida]",
        "[Verso 2 - Rimas Urbanas y Coqueteo]",
        "[Puente Melódico - Voz Suave]",
        "[Coro Final - Clímax Máximo con Ad-libs]",
        "[Outro - Bajo Retumbando y Saludo al Barrio]"
    ],
    "Heavy Rock & Metal (Epic Guitar Solo)": [
        "[Intro - Crushing Distortion Guitar Riff]",
        "[Verse 1 - Gritty Aggressive Vocals]",
        "[Pre-Chorus - Galloping Drums & Rising Rage]",
        "[Chorus - Massive Stadium Anthem Singalong]",
        "[Verse 2 - Driving Rhythm Section]",
        "[Pre-Chorus - Double Bass Drum Kick]",
        "[Chorus - Roaring Guitars]",
        "[EPIC GUITAR SOLO - Shredding Whammy & Arpeggios]",
        "[Final Chorus - Peak Vocal Screams & Energy]",
        "[Outro - Final Heavy Power Chord Ring-Out]"
    ],
    "Afrobeats Sunshine (Lagos Bounce)": [
        "[Intro - Shakers, Sweet Guitars & Log Drum Pulse]",
        "[Catchy Hook - Immediate Joyful Bounce]",
        "[Verse 1 - Pidgin Street Slang & Blessings]",
        "[Pre-Chorus - Callouts & Handclaps]",
        "[Chorus - Infectious Dance Rhythm]",
        "[Verse 2 - Celebration of Life & Good Vibe]",
        "[Bridge - Horn Section Stabs]",
        "[Chorus - Everyone Singing Together]",
        "[Outro - Groove Plays Out into the Sunset]"
    ],
    "Anime Opening (High-Energy J-Rock)": [
        "[Oudou Piano Riff - Sudden Explosive Full Band Tease]",
        "[A-Melo (Verse 1) - Fast Syllables / Longing Eyes]",
        "[B-Melo (Pre-Chorus) - Melodic Ascent to Battle]",
        "[Sabi (Main Chorus) - Soaring Emotional High Notes]",
        "[A-Melo (Verse 2) - Shadows on the Path Ahead]",
        "[B-Melo - Drums Pick Up Speed]",
        "[Sabi - Stadium Singalong]",
        "[C-Melo (Bridge) - Dramatic Key Change & Desperation]",
        "[Grand Sabi Climax - Overcoming All Odds]",
        "[Outro - Fast Drum Roll & Heroic Pose]"
    ],
    "Traditional Storyteller Ballad (AABA Folk)": [
        "[Acoustic Intro - Gentle Traditional Pluck]",
        "[Stanza 1 - Setting the Old Town Scene]",
        "[Refrain - Core Moral / Hook]",
        "[Stanza 2 - The Unexpected Departure]",
        "[Refrain - Core Moral / Hook]",
        "[Solo - Wooden Flute / Fiddle Reflection]",
        "[Stanza 3 - Years Later / The Return]",
        "[Refrain - Bittersweet Wisdom]",
        "[Coda - Lasting Acoustic Ring]"
    ]
}

# Ready-to-generate 1-Click Formats & Presets
ONE_CLICK_PRESETS = {
    "🇰🇭 រាំវង់ ចូលឆ្នាំថ្មី (Khmer Romvong Festive)": {
        "region": "Southeast Asia",
        "genre": "Khmer Music (Romvong / Kantrum / Modern Pop)",
        "language": "Khmer (ភាសាខ្មែរ)",
        "bpm": "110 BPM",
        "structure": "Khmer Romvong / Saravan (រាំវង់ ចូលឆ្នាំ)",
        "mood": "Euphoric & Uplifting",
        "theme": "Cultural Roots, Homeland & Ancestral Pride",
        "rhyme": "AABB (Classic Couplets)",
        "user_notes": "បទរាំវង់ចូលឆ្នាំខ្មែរ សប្បាយរីករាយ អបអរសាទរទេវតាឆ្នាំថ្មី មានបរិយាកាសភូមិស្រុក ផ្កាឈូករីក និងការរាំលេងកម្សាន្តរបស់យុវជនខ្មែរ។",
        "skeleton": """[សេចក្ដីផ្ដើម - ស្នូរស្គរដៃ និងទ្រអូ]
(អបអរសាទរពិធីបុណ្យចូលឆ្នាំថ្មីប្រពៃណីជាតិខ្មែរ!)

[វគ្គ១ - រៀបរាប់បរិយាកាសបុណ្យភូមិ]
មេឃស្រឡះខែចេត្រចូលឆ្នាំថ្មី
...

[បន្ទរ - ទំនុកច្រៀងពិរោះកន្ត្រាក់អារម្មណ៍]
ឱ! រាំវង់ខ្មែរសប្បាយអើយសែនសប្បាយ
...

[វគ្គ២ - ជួបគូស្នេហ៍រាំជុំវិញផ្កាឈូក]
...

[ឆ្លើយឆ្លង - ប្រុសឆ្លើយ ស្រីឆ្លង]
(ប្រុស): ស្រីស្រស់កល្យាណ...
(ស្រី): បងអើយបង...

[ស្គរដៃរន្ថើន - រាំវង់សប្បាយរីករាយ]
...

[បញ្ចប់ - ជូនពរឆ្នាំថ្មី]"""
    },

    "🇰🇭 មនោសញ្ចេតនា មាសស្រោប (Khmer Classic Ballad)": {
        "region": "Southeast Asia",
        "genre": "Khmer Music (Romvong / Kantrum / Modern Pop)",
        "language": "Khmer (ភាសាខ្មែរ)",
        "bpm": "72 BPM",
        "structure": "Traditional Storyteller Ballad (AABA Folk)",
        "mood": "Melancholic & Nostalgic",
        "theme": "Heartbreak, Betrayal & Moving On",
        "rhyme": "ABCB (Ballad / Folk Stanza)",
        "user_notes": "បទមនោសញ្ចេតនាកម្សត់ បែបមាសស្រោបជំនាន់ដើម រៀបរាប់ពីអនុស្សាវរីយ៍ចាស់ក្រោមពន្លឺព្រះច័ន្ទ និងការព្រាត់ប្រាសដោយមិនអស់ចិត្ត។",
        "skeleton": """[Intro - ស្នូរសាក់សូហ្វូន និងហ្គីតាជំនាន់ដើម]

[វគ្គ១ - អនុស្សាវរីយ៍យប់អាធ្រាត្រ]
...

[បន្ទរ - អួលដើមកព្រោះនឹក]
...

[វគ្គ២ - ទឹកភ្នែកក្រោមពន្លឺព្រះច័ន្ទ]
...

[សូឡូសាក់សូហ្វូន]
...

[បន្ទរបញ្ចប់ - ស្តាយស្នេហ៍មិនត្រឡប់]"""
    },

    "🇰🇭 កូនខ្មែរ Trap / Hip-Hop (Vannda Style)": {
        "region": "Southeast Asia",
        "genre": "Khmer Music (Romvong / Kantrum / Modern Pop)",
        "language": "Khmer (ភាសាខ្មែរ)",
        "bpm": "138 BPM",
        "structure": "Trap & Drill Fast Flow (Sub-Bass Banger)",
        "mood": "Aggressive & Rebellious",
        "theme": "Hustle, Ambition & Rising from the Bottom",
        "rhyme": "Internal & Multi-Syllabic (Hip-Hop / Technical)",
        "user_notes": "បទ Trap បែបកូនខ្មែរ រៀបរាប់ពីការតស៊ូពីបាតដៃទទេ ការលើកតម្កើងមរតកដូនតា និងមោទនភាពជាតិខ្មែរលើឆាកអន្តរជាតិ លាយសំឡេងទ្រអ៊ូជាមួយ 808 sub-bass។",
        "skeleton": """[Intro - សំឡេងទ្រខ្មែរ លាយជាមួយ 808 Bass Slide]
(Klaha on the track... កូនខ្មែរក្រោកឈរ!)

[Hook - ឃ្លាខ្លីចាក់ចំទ្រូង]
...

[Verse 1 - 16-Bar Fast Flow]
...

[Hook]
...

[Beat Switch - 808 Heavy Outro]"""
    },

    "👫 បទឆ្លើយឆ្លង ប្រុស-ស្រី (Romantic Duet)": {
        "region": "North America & Global Pop",
        "genre": "Pop & Synthpop",
        "language": "English",
        "bpm": "100 BPM",
        "structure": "Romantic Duet (បទឆ្លើយឆ្លង ប្រុស-ស្រី)",
        "mood": "Sensual & Romantic",
        "theme": "Unconditional Love & Romantic Devotion",
        "rhyme": "ABAB (Alternating Rhymes)",
        "user_notes": "A captivating, romantic duet where the male singer and female singer trade lines, culminating in an intertwined harmony chorus.",
        "skeleton": """[Intro - Soft Acoustic Piano]

[Verse 1 - Male]
Looking across the crowded room at midnight...

[Verse 2 - Female]
I saw you standing there, pretending to be fine...

[Pre-Chorus - Both]
(Male): Take my hand...
(Female): Don't let go...

[Chorus - Duet Harmony]
We're writing our own story in the stars...

[Verse 3 - Call & Response]
...

[Bridge - Interlocking Vocals]
...

[Final Chorus - Duet Full Climax]

[Outro - Whispered Goodnight]"""
    },

    "🔥 TikTok / Reels 60s Viral Hook (Fast Earworm)": {
        "region": "North America & Global Pop",
        "genre": "Pop & Synthpop",
        "language": "English",
        "bpm": "126 BPM",
        "structure": "TikTok & Reels 30s-60s (Hook-First Viral)",
        "mood": "Energetic & Party-Ready",
        "theme": "Summer Dancefloor & Spontaneous Adventure",
        "rhyme": "AABB (Classic Couplets)",
        "user_notes": "Designed for maximum retention on short-form videos: Starts immediately with an explosive 3-second hook, followed by a punchy 4-bar verse and dance climax.",
        "skeleton": """[Hook Tease - Earworm First 3 Seconds!]
(Don't blink, you might miss it!)
Watch the whole room stop and stare!

[Verse - Short 4-Bar Punchy Rhythm]
Late night, flash bright, moving on beat
Glitter on the runway, heat on the street

[Pre-Chorus - Quick 2-Bar Riser]
Are you ready for the drop?
3, 2, 1—

[CHORUS CLIMAX - Viral High Energy Singalong]
We own the night, yeah we own the glow!
Everywhere we step, everybody knows!

[Post-Chorus / Beat Loop - Dance Transition Outro]
(Repeat on loop...)"""
    },

    "💔 បទស្រក់ទឹកភ្នែក (Sad Piano Ballad)": {
        "region": "North America & Global Pop",
        "genre": "Contemporary R&B / Neo-Soul",
        "language": "English",
        "bpm": "68 BPM",
        "structure": "Emotional Piano Ballad (Tearjerker)",
        "mood": "Melancholic & Nostalgic",
        "theme": "Heartbreak, Betrayal & Moving On",
        "rhyme": "Slant Rhyme & Assonance (Modern Pop / Indie)",
        "user_notes": "A devastating, heartbreaking ballad built on an intimate piano melody that builds into a soaring string climax with raw vulnerability.",
        "skeleton": """[Intro - Solitary Piano Chord Progression]

[Verse 1 - Whispered Intimacy]
I still leave coffee on the counter for two...

[Pre-Chorus - Rising Heartache]
And every shadow in the hallway looks like you...

[Chorus - Soaring Vocal Belt]
How do I unlove someone who became my blood?
How do I wash away a memories in the flood?

[Verse 2]
...

[Bridge - The Unspoken Truth]
I was never really ready to let you go...

[Final Chorus - Maximum Vocal Cry]
...

[Outro - Single Piano Note Dying Away]"""
    },

    "🌟 K-Pop 3-Min Idol Title Track (Super-Drop)": {
        "region": "East Asia",
        "genre": "K-Pop (Korean Pop)",
        "language": "Bilingual: English + Korean (K-Pop style)",
        "bpm": "125 BPM",
        "structure": "K-Pop Multi-Role Spectacle (Idol Title Track)",
        "mood": "Euphoric & Uplifting",
        "theme": "Futuristic Cyberpunk & Dystopian Dreams",
        "rhyme": "Internal & Multi-Syllabic (Hip-Hop / Technical)",
        "user_notes": "Electrifying bilingual K-Pop title track with alternating vocal positions (Sub-Vocal, Main Rapper, High Note Lead Belt), explosive brass drops, and killing part catchphrase.",
        "skeleton": """[Intro - Concept Whisper & Synth Stabs]
(Shh... The future is calling!)

[Verse 1 - Sub-Vocal]
눈을 떠봐 (Open your eyes) beneath the neon glow...

[Rap Break 1 - Main Rapper]
Fast flow, locked in, step to the bass...

[Pre-Chorus - Rising Lead Vocal]
Can you feel the pulse begin to rise?

[Chorus - Explosive Drop & Chanted Hook]
BAM! Shatter the ceiling, we take the crown!

[Bridge - High Note F5 Vocal Belt]
...

[Dance Break / Killing Part]
(Concept Pose)"""
    },

    "🎧 90s Boom-Bap Hip Hop Storyteller": {
        "region": "North America & Global Pop",
        "genre": "Hip-Hop & Trap",
        "language": "English",
        "bpm": "92 BPM",
        "structure": "Hip-Hop / Rap 16-Bar Cypher",
        "mood": "Chill, Dreamy & Atmospheric",
        "theme": "Hustle, Ambition & Rising from the Bottom",
        "rhyme": "Internal & Multi-Syllabic (Hip-Hop / Technical)",
        "user_notes": "Classic East Coast boom-bap aesthetic: dusty vinyl crackle, MPC drum chops, lyrical complexity, vivid street storytelling, and scratched vocal hooks.",
        "skeleton": """[Intro - Dusty Vinyl Crackle & Producer Shouts]
(Yeah, check one-two from the five boroughs...)

[Verse 1 - 16 Bars Complex Flow]
Writing rhymes in the back of the A-train...

[Hook - Scratched Vocal Cuts]
Never fold, stay gold, that's the code...

[Verse 2 - 16 Bars Wordplay]
...

[Outro - Beat Echoes Out]"""
    },

    "⚡ EDM Festival Mainstage Drop": {
        "region": "North America & Global Pop",
        "genre": "EDM & Festival Dance",
        "language": "English",
        "bpm": "128 BPM",
        "structure": "EDM Festival Anthem (Big Build & Drop)",
        "mood": "Euphoric & Uplifting",
        "theme": "Midnight City Drive & Late-Night Thoughts",
        "rhyme": "AABB (Classic Couplets)",
        "user_notes": "Massive festival energy: Soaring female topline, accelerating snare roll build-ups, and explosive bass synths engineered for 100,000 festival fans jumping together.",
        "skeleton": """[Intro - Atmospheric Synth Pulse]
(Are you ready to lose yourself tonight?)

[Verse - Soaring Vocals]
We were strangers under stadium lights...

[Build-Up - Snare Roll Accelerating]
Higher, higher, don't let it fade!
3... 2... 1... MAKE SOME NOISE!

[MASSIVE FESTIVAL DROP - Bass Explosion]
(Heavy Synthesizer Chops)

[Verse 2]
...

[FINAL BIG DROP]
...

[Outro]"""
    },

    "🌴 Latin Urban Reggaeton Party (Perreo)": {
        "region": "Latin America & Caribbean",
        "genre": "Reggaeton & Latin Urban",
        "language": "Bilingual: Spanish + English (Spanglish Urban)",
        "bpm": "95 BPM",
        "structure": "Latin Reggaeton / Perreo (Dem-bow Dance)",
        "mood": "Energetic & Party-Ready",
        "theme": "Summer Dancefloor & Spontaneous Adventure",
        "rhyme": "AABB (Classic Couplets)",
        "user_notes": "Unstoppable dem-bow rhythm, playful Spanglish party chants, fiery Puerto Rican swagger, and sensual romantic friction.",
        "skeleton": """[Intro - Dem-bow Fades In]
(Dímelo DJ, que se sienta la presión en to'a la disco!)

[Coro - Hook Pegajoso]
Baila pegado, siente el calor...

[Verso 1 - Chanteo Rápido]
Llegó con las amigas rompiendo la noche...

[Pre-Coro]
...

[Coro Clímax]
...

[Outro - El bajo se va...]"""
    },

    "🌍 Lagos Afrobeats Sunshine (Naija Vibe)": {
        "region": "Africa & Afro-Diaspora",
        "genre": "Afrobeats (Naija / Ghana)",
        "language": "Bilingual: Pidgin English + Yoruba (Afrobeats)",
        "bpm": "104 BPM",
        "structure": "Afrobeats Sunshine (Lagos Bounce)",
        "mood": "Euphoric & Uplifting",
        "theme": "Cultural Roots, Homeland & Ancestral Pride",
        "rhyme": "ABAB (Alternating Rhymes)",
        "user_notes": "Infectious syncopated log drums, joyful Pidgin English expressions ('No wahala', 'Oshe'), warm horns, and celebratory gratefulness for life's blessings.",
        "skeleton": """[Intro - Log Drum & Sweet Guitar Lick]
(Vibes on vibes! Dem call me Gemini!)

[Catchy Hook]
Blessings follow me everywhere I go...

[Verse 1 - Pidgin / English]
Wake up in the morning, say a prayer to the Lord...

[Pre-Chorus - Handclaps]
...

[Chorus - Joyful Bounce]
...

[Outro - Fade with Percussion]"""
    },

    "🎸 Epic Alternative Rock Anthem": {
        "region": "North America & Global Pop",
        "genre": "Indie / Alternative Rock",
        "language": "English",
        "bpm": "130 BPM",
        "structure": "Heavy Rock & Metal (Epic Guitar Solo)",
        "mood": "Aggressive & Rebellious",
        "theme": "Rebellion Against Society & Breaking the Rules",
        "rhyme": "ABCB (Ballad / Folk Stanza)",
        "user_notes": "Driving distortion guitars, dynamic quiet-verse to explosive-chorus dynamics (Nirvana/Foo Fighters style), and roaring vocal catharsis.",
        "skeleton": """[Intro - Crushing Distortion Guitar Riff]

[Verse 1 - Understated & Gritty]
Told me how to walk, told me what to say...

[Pre-Chorus - Drums Accelerating]
Watch the cracks begin to show...

[Chorus - Explosive Stadium Distortion]
WE ARE NOT THE ONES YOU BREAK!

[Verse 2]
...

[EPIC GUITAR SOLO]
...

[Final Chorus - Roaring Cry]

[Outro - Feedback Ring-Out]"""
    },

    "🎌 Anime Opening J-Rock Theme": {
        "region": "East Asia",
        "genre": "J-Pop & Anime Soundtrack",
        "language": "Japanese (日本語)",
        "bpm": "165 BPM",
        "structure": "Anime Opening (High-Energy J-Rock)",
        "mood": "Triumphant & Victorious",
        "theme": "Futuristic Cyberpunk & Dystopian Dreams",
        "rhyme": "Slant Rhyme & Assonance (Modern Pop / Indie)",
        "user_notes": "High-octane anime opening formula: Oudou Royal Road chords, soaring emotional Japanese chorus, blazing tempo, and dramatic key change bridge.",
        "skeleton": """[Intro - Piano Riff into Sudden Rock Explosion]

[A-Melo (Verse 1)]
走り出した影を追いかけて (Chasing the running shadow...)

[B-Melo (Pre-Chorus)]
どんな暗闇でも (No matter how dark it gets...)

[Sabi (Main Chorus)]
響け僕らの未来へ! (Echo towards our future!)

[C-Melo (Bridge - Key Change)]
...

[Grand Sabi Climax]
...

[Outro]"""
    },

    "☕ Acoustic Coffeehouse Indie Ballad": {
        "region": "North America & Global Pop",
        "genre": "Indie / Alternative Rock",
        "language": "English",
        "bpm": "84 BPM",
        "structure": "Acoustic Singer-Songwriter (Coffeehouse Indie)",
        "mood": "Chill, Dreamy & Atmospheric",
        "theme": "Nature's Wonder, Seas, Stars & Open Horizons",
        "rhyme": "ABCB (Ballad / Folk Stanza)",
        "user_notes": "Intimate fingerpicked acoustic guitar, subtle room reverb, gentle honest lyrics about morning light, vinyl records, and peaceful companionship.",
        "skeleton": """[Intro - Warm Fingerpicked Acoustic Guitar]

[Stanza 1 - Morning Coffee]
Sunlight creeping through the bedroom blinds...

[Refrain - Honest Simplicity]
You and me, we've got all the time in the world...

[Stanza 2 - Old Records]
...

[Story Bridge]
...

[Final Refrain]

[Coda - Soft Whistle Fade]"""
    },

    "🎷 Midnight Neo-Soul & R&B Slow Jam": {
        "region": "North America & Global Pop",
        "genre": "Contemporary R&B / Neo-Soul",
        "language": "English",
        "bpm": "74 BPM",
        "structure": "R&B / Neo-Soul Slow Jam (Midnight Groove)",
        "mood": "Sensual & Romantic",
        "theme": "Midnight City Drive & Late-Night Thoughts",
        "rhyme": "Slant Rhyme & Assonance (Modern Pop / Indie)",
        "user_notes": "Lush Fender Rhodes electric piano chords, silky chest voice and falsetto runs, subtle snaps, and deep intimate late-night atmosphere.",
        "skeleton": """[Intro - Warm Rhodes Chords & Smoky Vinyl Crackle]
(Baby, it's 2 AM... where you at?)

[Verse 1 - Silky Falsetto]
Raindrops tracing patterns on the glass...

[Pre-Chorus - Finger Snaps]
You know what you do to me...

[Chorus - Lush 4-Part Harmonies]
Midnight love, falling like slow honey...

[Verse 2]
...

[Extended Bridge - Vocal Runs]
...

[Outro - Whispered Goodnight]"""
    },

    "🤠 Dusty Roads Country & Americana Tale": {
        "region": "North America & Global Pop",
        "genre": "Country & Americana",
        "language": "English",
        "bpm": "96 BPM",
        "structure": "Traditional Storyteller Ballad (AABA Folk)",
        "mood": "Nostalgic",
        "theme": "Cultural Roots, Homeland & Ancestral Pride",
        "rhyme": "AABB (Classic Couplets)",
        "user_notes": "Heartfelt storytelling with acoustic guitars, pedal steel, dusty boots, hometown memories, and honest working-class values.",
        "skeleton": """[Intro - Acoustic Strumming & Pedal Steel Whine]

[Verse 1 - Small Town Scene]
Grandpa's truck parked out behind the barn...

[Chorus - Heartfelt Truth]
This dirt road taught me everything I know...

[Verse 2]
...

[Bridge - The Turning Wheel]
...

[Final Chorus]

[Outro - Fiddle & Guitar Fade]"""
    },

    "🏆 Billboard Max Martin Pop Banger (Dua Lipa / Weeknd Style)": {
        "region": "North America & Global Pop",
        "genre": "Pop & Synthpop",
        "language": "English",
        "bpm": "124 BPM",
        "structure": "Standard Pop (Verse-Pre-Chorus-Chorus-Post)",
        "mood": "Euphoric & Uplifting",
        "theme": "Midnight City Drive & Late-Night Thoughts",
        "rhyme": "AABB (Classic Couplets)",
        "user_notes": "Billboard Hot 100 hit formula: 80s Disco-Funk bassline, crisp punchy drums, short 4-bar storytelling verse, skyrocketing pre-chorus riser, anthemic chorus, and an addictive post-chorus vocal chop earworm.",
        "skeleton": """[Intro - Analog Synth Bass Pulse & Hi-Hat Groove]
(Yeah, let the lights go down...)

[Verse 1 - 4 Bars Punchy Storytelling]
Two drinks waiting on the marble bar
Headlights flashing through a vintage car
You caught my eye across the velvet floor
I never felt this kind of heat before

[Pre-Chorus - Rising Snare Riser & Synth Chords]
One step closer, shadows start to blur
Heartbeat racing, every word's a lure
Can you feel the spark before we cross the line?
Say the word and leave this world behind!

[CHORUS - Soaring Vocal Belt & Four-on-the-Floor Kick]
Catching fire in the electric glow!
Baby, don't you let this feeling go!
Turn the radio up to the stratosphere
There is nobody else but you and me right here!
(Catching fire in the glow!)
There is nobody else but you and me right here!

[Post-Chorus - Dance Vocal Chops & Bass Drop]
(Take me higher, higher, higher!)
(Electric glow, don't let it go!)

[Verse 2 - Driving Rhythm]
Lipstick smudge upon the champagne flute
We're in deep, no looking for a parachute
City skyline burning neon red
Living out the dreams inside our head

[Pre-Chorus]
One step closer, shadows start to blur
Heartbeat racing, every word's a lure!

[CHORUS - Maximum Energy]
Catching fire in the electric glow!
Baby, don't you let this feeling go!
Turn the radio up to the stratosphere
There is nobody else but you and me right here!

[Bridge - Atmospheric Filtered Drums & Vocal Catharsis]
When morning comes and washes out the light
Will you remember how we owned tonight?
We don't need tomorrow, we just need right now!
(Hear the crowd shout out loud!)

[Final Chorus - Full Climax with High Ad-libs]
Catching fire in the electric glow!
Baby, don't you let this feeling go!
Turn the radio up to the stratosphere!
There is nobody else but you and me right here!

[Outro - Bass Groove Fades Out with Synthesizer Echoes]
Catching fire...
In the electric glow...
(Synth arpeggio fades...)"""
    },

    "🍂 Poetic Folklore Acoustic Storyteller (Taylor Swift Style)": {
        "region": "North America & Global Pop",
        "genre": "Indie / Alternative Rock",
        "language": "English",
        "bpm": "78 BPM",
        "structure": "Traditional Storyteller Ballad (AABA Folk)",
        "mood": "Melancholic & Nostalgic",
        "theme": "Heartbreak, Betrayal & Moving On",
        "rhyme": "Slant Rhyme & Assonance (Modern Pop / Indie)",
        "user_notes": "Masterpiece narrative songwriting inspired by 'Folklore' & 'Evermore': Hyper-specific sensory imagery (wine glasses, wool cardigans, rain on asphalt), conversational cadence, and a legendary 3-minute bridge that delivers maximum emotional catharsis.",
        "skeleton": """[Intro - Warm Fingerpicked Acoustic Guitar & Gentle Cello]

[Verse 1 - Grounded Sensory Object Writing]
Vintage wool cardigan draped on the chair
Smell of lavender rain in your tangled hair
We left our muddy boots by the wooden door
Listening to the pine branches scratch the floor
You whispered secrets like they were sacred law
The prettiest picture that I ever saw

[Pre-Chorus - Rising Melancholy]
And autumn leaves were bleeding into brown
Before the first snow settled on this town
Did you mean it when you held my trembling hand?
Or was I just a castle built in sand?

[CHORUS - Intimate & Anthemic Narrative]
And I still drive past that red barn road
Carrying the secrets that we never showed
You were a summer storm that cleared the sky
A quiet hello and a sudden goodbye
Now I'm standing in the November chill
And you're a silhouette on Whiskey Hill

[Verse 2 - Conversational Detail]
Found your copper key in my coat pocket today
The one to the cabin we promised we'd never sell away
The tea kettle whistles like an old ghost sigh
Watching the grey clouds swallow up the sky
Everybody says that time will heal the ache
How much more healing can one hollow heart take?

[Pre-Chorus]
And autumn leaves were bleeding into brown
Before the silence fell upon this town!

[CHORUS]
And I still drive past that red barn road
Carrying the secrets that we never showed
You were a summer storm that cleared the sky
A quiet hello and a sudden goodbye
Now I'm standing in the November chill
And you're a silhouette on Whiskey Hill

[BRIDGE - The Legendary 3-Minute Emotional Catharsis]
(Guitars build with pounding kick drum and rising strings)
And did you give her the same crooked smile?
Did you ask her to walk down the gravel aisle?
Did you tell her that I was crazy and cold,
Or did you admit that you shattered the gold?
I poured all my youth into your rusty jar,
Followed you blindly like an idiot star!
And the worst part isn't that you packed up and ran—
It's knowing you broke me because you knew that you can!

[Guitar & Cello Swell - Pure Heartache]

[Final Chorus - Half Acoustic / Whispered Intimacy]
Now I drive past that red barn road...
Nothing left but the heavy winter snow.
You were a summer storm that cleared the sky,
A quiet hello and a sudden goodbye.

[Outro - Fingerpicked Guitar Dying into Room Reverberation]
A silhouette on Whiskey Hill...
The air is still...
Cardigan on the chair...
(Soft acoustic strum finishes)"""
    },

    "🌌 Dark Bedroom Alt-Pop (Billie Eilish / Lorde Style)": {
        "region": "North America & Global Pop",
        "genre": "Indie / Alternative Rock",
        "language": "English",
        "bpm": "115 BPM",
        "structure": "Standard Pop (Verse-Pre-Chorus-Chorus-Post)",
        "mood": "Dark, Haunting & Mysterious",
        "theme": "Mental Health, Inner Demons & Finding Peace",
        "rhyme": "Internal & Multi-Syllabic (Hip-Hop / Technical)",
        "user_notes": "Intimate ASMR close-mic whispered vocals over deep 808 sub-bass, minimal eerie synths, biting lyrical irony, and sudden contrast drops.",
        "skeleton": """[Intro - ASMR Close-Mic Whisper & Minimal 808 Pulse]
(Shh... Don't wake up the monsters underneath the bed...)
(One, two... count them...)

[Verse 1 - Whispered Intimacy & Dark Irony]
Staring at the water stains along the plaster ceiling
Told my therapist I'm getting quite good at not feeling
You talk so loud like your opinions are currency
Spending all your drama like an absolute emergency
Chewing on the ice from a melted glass of gin
Waiting for the quiet little nightmare to begin

[Pre-Chorus - Subtle Snaps & Pitch-Shifted Harmonies]
You think you're the predator lurking in the dark?
Honey, you're a goldfish pretending you're a shark.
Watch the timer ticking down...
Tick... tock... drown.

[CHORUS - MASSIVE Sub-Bass 808 Drop & Menacing Whisper]
I wear the crown made of broken glass!
Watching your little empire collapse!
Smile so sweet while I cut the cord,
You wanted a drama, now you're looking bored?
(So bored...)
Yeah, you wanted a drama, now you're looking bored!

[Post-Chorus - Distorted Vocal Glitches]
(La-la-la, burn it down)
(Who's crying now?)

[Verse 2 - Sarcastic Flow]
Gold medals on your wall for pointing out the blame
Memorized your excuses, they're always just the same
Send another paragraph, I'll leave it on read
I'd rather talk to the phantom voices in my head

[Pre-Chorus]
You think you're the predator lurking in the dark?
Honey, you're a goldfish pretending you're a shark!

[CHORUS - Maximum Bass Weight]
I wear the crown made of broken glass!
Watching your little empire collapse!
Smile so sweet while I cut the cord,
You wanted a drama, now you're looking bored?

[Bridge - Sudden Eerie Silence with Celesta Music Box]
If I told you the truth, would you run away screaming?
Or would you convince yourself that you were only dreaming?
(Heavy breathing)
Too late. The door is locked.

[Final Chorus - Bass Wall & Double Whispers]
Crown made of broken glass!
Watch every single empire collapse!
Smile so sweet while I cut the cord,
Look at you now... look at you bored!

[Outro - Dry Vocal Whisper & Tape Stop Effect]
(Don't look behind you...)
(Tape rewind clicks off)"""
    },

    "🏟️ Stadium Arena Rock Anthem (Coldplay / Imagine Dragons Style)": {
        "region": "North America & Global Pop",
        "genre": "Indie / Alternative Rock",
        "language": "English",
        "bpm": "130 BPM",
        "structure": "EDM Festival Anthem (Big Build & Drop)",
        "mood": "Triumphant & Victorious",
        "theme": "Hustle, Ambition & Rising from the Bottom",
        "rhyme": "AABB (Classic Couplets)",
        "user_notes": "Massive global arena anthem: Driving four-on-the-floor floor tom drums, universal singalong 'Oh-oh-oh' stadium chant, soaring vocal belting, and triumphant lyrics of resilience.",
        "skeleton": """[Intro - Tribal Floor Tom Drums & Chiming U2-Style Guitar]
(Oh-oh-oh, oh-oh-oh-oh!)
(Let the thunder wake the dawn!)

[Verse 1 - Understated Grit Rising]
We walked through valleys made of iron and stone
Carrying the fire in our blood and bone
They counted us out before the battle began
Said we were dust in the palm of a giant's hand

[Pre-Chorus - Snare Roll Build & Swelling Organs]
Hear the rumble underneath the ground!
There is no cage that can hold this sound!
From the darkest pit to the highest cloud,
We stand up tall and we scream out loud!

[CHORUS - MASSIVE STADIUM EXPLOSION & Full Band Blast]
WE ARE THE GIANTS AWAKING FROM SLEEP!
RISING LIKE TIDES FROM THE BOTTOMLESS DEEP!
STRIKE DOWN THE WALLS THAT WERE MEANT TO DIVIDE,
WE BRING THE LIGHT TO THE OTHER SIDE!
(Oh-oh-oh-oh!)
WE BRING THE LIGHT TO THE OTHER SIDE!

[Post-Chorus - 100,000 Fan Stadium Singalong Chant]
OH-OH-OH! OH-OH-OH-OH!
OH-OH-OH! WE WON'T BACK DOWN!

[Verse 2 - Driving Bassline]
Look at the scars written into our palms
We found our courage in the heart of the storms
No more apologies, no looking behind
We are the gold that was buried to shine!

[Pre-Chorus]
Hear the rumble underneath the ground!
There is no cage that can hold this sound!

[CHORUS - Stadium Explosion]
WE ARE THE GIANTS AWAKING FROM SLEEP!
RISING LIKE TIDES FROM THE BOTTOMLESS DEEP!
STRIKE DOWN THE WALLS THAT WERE MEANT TO DIVIDE,
WE BRING THE LIGHT TO THE OTHER SIDE!

[Bridge - Epic Guitar Solo & Cymbal Washes]
(Soaring, melodic guitar solo ascending into the high registers)
And when the heavens roar,
And when the raindrops pour,
WE WILL NOT FALL!
WE TAKE IT ALL!

[Final Chorus - Maximum Stadium Power & Pyrotechnics]
WE ARE THE GIANTS AWAKING FROM SLEEP!
RISING LIKE TIDES FROM THE BOTTOMLESS DEEP!
STRIKE DOWN THE WALLS THAT WERE MEANT TO DIVIDE,
WE BRING THE LIGHT TO THE OTHER SIDE!

[Outro - Massive Chant & Crashing Cymbal Chords]
OH-OH-OH! OH-OH-OH-OH!
We bring the light...
We own the night!
(Final crashing chord rings out into cheering stadium reverb)"""
    },

    "🌙 Melodic Midnight Trap / R&B (Drake / Post Malone Style)": {
        "region": "North America & Global Pop",
        "genre": "Hip-Hop & Trap",
        "language": "English",
        "bpm": "140 BPM",
        "structure": "Trap & Drill Fast Flow (Sub-Bass Banger)",
        "mood": "Chill, Dreamy & Atmospheric",
        "theme": "Midnight City Drive & Late-Night Thoughts",
        "rhyme": "Internal & Multi-Syllabic (Hip-Hop / Technical)",
        "user_notes": "Nocturnal city atmospheric trap: Reverse guitar loops, 808 glides, melancholic autotuned vocal melodies, reflective introspective verses about success, isolation, and late-night regrets.",
        "skeleton": """[Intro - Reversed Guitar Melody & Sub-Bass Filter Pulse]
(Yeah... 3 AM in the penthouse...)
(You already know how it goes...)

[Hook - Melodic Autotune Emotional Singalong]
Midnight calls on an empty phone
Surrounded by a hundred people, still alone
Counting up the paper while the feelings fade
Paying every price for the beds we made
Yeah, they celebrate the wins that they see outside,
Nobody knows the shadows where the demons hide.

[Verse 1 - 16-Bar Introspective Fast Flow]
Window tinted dark when I cruise the boulevard
Living in the fast lane, playing every card
Used to dream of diamonds on a silver chain
Now the ice is cold enough to freeze the pain
Old friends calling with their hands stretched out
Funny how they love you when the fame is loud
Took a couple losses just to understand the math
Left my old heart on a broken path
Spilling expensive wine on a leather seat
Heartbeat racing to the trap snare beat
I told you I'd change, but the lifestyle won't
They ask if I'm happy and I swear I don't know.

[Pre-Hook - Filtered Low-End Riser]
Every city looks the same beneath the neon light
Chasing down the morning through another sleepless night...

[Hook - Melodic Autotune]
Midnight calls on an empty phone
Surrounded by a hundred people, still alone
Counting up the paper while the feelings fade
Paying every price for the beds we made
Yeah, they celebrate the wins that they see outside,
Nobody knows the shadows where the demons hide.

[Bridge - Beat Switch / Ambient Vocal Reverb]
(Reversed vocals echo...)
Did you ever care about the man behind the name?
Or was I just a ticket to the spotlight game?
(Yeah, answer that...)

[Final Hook - With Layered Ad-libs & 808 Slides]
Midnight calls on an empty phone!
Surrounded by a hundred people, still alone!
Counting up the paper while the feelings fade,
Paying every price for the beds we made!

[Outro - Ambient Guitar Delay & 808 Fade]
Still alone...
In the city of stone...
(Trap hi-hats stutter out...)"""
    },

    "🎹 Soaring Soul Powerhouse Ballad (Adele Style)": {
        "region": "North America & Global Pop",
        "genre": "Contemporary R&B / Neo-Soul",
        "language": "English",
        "bpm": "68 BPM",
        "structure": "Emotional Piano Ballad (Tearjerker)",
        "mood": "Melancholic & Nostalgic",
        "theme": "Heartbreak, Betrayal & Moving On",
        "rhyme": "Slant Rhyme & Assonance (Modern Pop / Indie)",
        "user_notes": "Soul-stirring, cinematic piano power ballad: Built from intimate whisper on Verse 1, rising with subtle cellos, exploding on the Chorus with full-chested vocal belting (F4-C5), and a tearjerker bridge.",
        "skeleton": """[Intro - Intimate Grand Piano Chords in D Minor]

[Verse 1 - Vulnerable Chest Voice & Slow Cadence]
I found your old coat hanging behind the pantry door
Smelling of peppermint and rain from days before
I couldn't bring myself to fold it in a box
Left it hanging there like a key with no more locks
We built a fortress out of promises and sand
And watched it crumble through the fingers of our hand

[Pre-Chorus - Rising Left-Hand Octaves & Low Strings]
They told me grief is just love with nowhere left to go
A lonely river freezing under winter snow
And every night I stand before the mirror glass
Praying for the ghost of yesterday to pass...

[CHORUS - Explosive Vocal Belting & Grand Piano Fortissimo]
HOW DO I BREATHE IN A ROOM WITHOUT YOUR AIR?
HOW DO I HEAL FROM A WOUND THAT DOESN'T CARE?
I GAVE YOU MY GOLD, YOU TURNED IT INTO RUST!
LEFT ME SIFTING THROUGH THE ASHES AND THE DUST!
Tell me, was it easy watching us divide?
Leaving all the pieces of my soul outside?

[Verse 2 - Piano Softens with Warm Cellos]
Our friends don't mention your name when they call me on the phone
They talk in gentle whispers so I don't feel so alone
They tell me that the sun will find my face again
That seasons always change beneath the summer rain
But every sunny morning feels like an insult to the grave
Of every single promise that we were meant to save.

[Pre-Chorus]
They told me grief is just love with nowhere left to go
A lonely river freezing under winter snow!

[CHORUS - Full Belting & High Note Climax]
HOW DO I BREATHE IN A ROOM WITHOUT YOUR AIR?
HOW DO I HEAL FROM A WOUND THAT DOESN'T CARE?
I GAVE YOU MY GOLD, YOU TURNED IT INTO RUST!
LEFT ME SIFTING THROUGH THE ASHES AND THE DUST!
Tell me, was it easy watching us divide?
Leaving all the pieces of my soul outside?

[BRIDGE - Modulated Harmonic Shift & Pure Vocal Agony]
(Piano rolls accelerate into high strings crescendo)
I don't hate you for leaving, no that's not the sin!
I hate that I'd still open up and let you in!
If you knocked on my window at three in the morn,
I would bleed all over again to keep you warm!
God help me, I loved you with every dying breath—
Why did loving you feel like a lifetime of death?!

[Grand Vocal Hold - Sustained F5 Note into Silence]

[Final Chorus - Half Time / Devastating Emotional Weight]
So tell me how to breathe without your air...
How do I heal from a wound that doesn't care?
I gave you my gold, you turned it into rust,
Left me alone in the ashes and the dust...

[Outro - Solitary Piano Chord Dying into Room Air]
Leaving all the pieces...
Of my soul outside.
(Single low D piano note resonates and fades into silence)"""
    }
}


MOODS = [
    "Euphoric & Uplifting",
    "Melancholic & Nostalgic",
    "Sensual & Romantic",
    "Aggressive & Rebellious",
    "Chill, Dreamy & Atmospheric",
    "Triumphant & Victorious",
    "Dark, Haunting & Mysterious",
    "Playful, Sarcastic & Fun",
    "Spiritual & Transcendent",
    "Energetic & Party-Ready"
]

THEMES = [
    "Midnight City Drive & Late-Night Thoughts",
    "Unconditional Love & Romantic Devotion",
    "Heartbreak, Betrayal & Moving On",
    "Hustle, Ambition & Rising from the Bottom",
    "Cultural Roots, Homeland & Ancestral Pride",
    "Summer Dancefloor & Spontaneous Adventure",
    "Mental Health, Inner Demons & Finding Peace",
    "Futuristic Cyberpunk & Dystopian Dreams",
    "Nature's Wonder, Seas, Stars & Open Horizons",
    "Rebellion Against Society & Breaking the Rules"
]

RHYME_SCHEMES = [
    "AABB (Classic Couplets)",
    "ABAB (Alternating Rhymes)",
    "ABCB (Ballad / Folk Stanza)",
    "AAAA (Monorhyme / Chant)",
    "Internal & Multi-Syllabic (Hip-Hop / Technical)",
    "Slant Rhyme & Assonance (Modern Pop / Indie)"
]

LANGUAGES = [
    {"name": "English", "code": "en", "native": "English", "tts_voice": "en-US-ChristopherNeural"},
    {"name": "Spanish (Español)", "code": "es", "native": "Español", "tts_voice": "es-ES-AlvaroNeural"},
    {"name": "Korean (한국어)", "code": "ko", "native": "한국어", "tts_voice": "ko-KR-InJoonNeural"},
    {"name": "Japanese (日本語)", "code": "ja", "native": "日本語", "tts_voice": "ja-JP-KeitaNeural"},
    {"name": "Chinese (Mandarin / 中文)", "code": "zh", "native": "中文", "tts_voice": "zh-CN-YunxiNeural"},
    {"name": "Khmer (ភាសាខ្មែរ)", "code": "km", "native": "ភាសាខ្មែរ", "tts_voice": "km-KH-PisethNeural"},
    {"name": "French (Français)", "code": "fr", "native": "Français", "tts_voice": "fr-FR-HenriNeural"},
    {"name": "Arabic (العربية)", "code": "ar", "native": "العربية", "tts_voice": "ar-SA-HamedNeural"},
    {"name": "Hindi (हिन्दी)", "code": "hi", "native": "हिन्दी", "tts_voice": "hi-IN-MadhurNeural"},
    {"name": "Portuguese (Português)", "code": "pt", "native": "Português", "tts_voice": "pt-BR-AntonioNeural"},
    {"name": "Vietnamese (Tiếng Việt)", "code": "vi", "native": "Tiếng Việt", "tts_voice": "vi-VN-NamMinhNeural"},
    {"name": "Thai (ภาษาไทย)", "code": "th", "native": "ภาษาไทย", "tts_voice": "th-TH-NiwatNeural"},
    {"name": "German (Deutsch)", "code": "de", "native": "Deutsch", "tts_voice": "de-DE-ConradNeural"},
    {"name": "Italian (Italiano)", "code": "it", "native": "Italiano", "tts_voice": "it-IT-DiegoNeural"},
    {"name": "Bilingual: English + Korean (K-Pop style)", "code": "en-ko", "native": "Bilingual EN+KO", "tts_voice": "en-US-ChristopherNeural"},
    {"name": "Bilingual: Spanish + English (Spanglish Urban)", "code": "es-en", "native": "Spanglish", "tts_voice": "es-ES-AlvaroNeural"},
    {"name": "Bilingual: Pidgin English + Yoruba (Afrobeats)", "code": "en-yo", "native": "Afrobeats Pidgin", "tts_voice": "en-US-ChristopherNeural"}
]

VOCAL_CUES = [
    "[Intro]",
    "[Verse 1]",
    "[Verse 2]",
    "[Pre-Chorus]",
    "[Chorus]",
    "[Bridge]",
    "[Hook]",
    "[Rap Breakdown]",
    "[Drop]",
    "[Solo]",
    "[High Note Climax]",
    "[Ad-lib]",
    "[Whisper]",
    "[Chant]",
    "[Outro]"
]

# --- Visual Pills & Interactive Tags for Studio UI ---
VISUAL_GENRE_PILLS = [
    {"name": "Khmer Pop", "bg": "#ef4444", "region": "Southeast Asia", "genre": "Khmer Music (Romvong / Kantrum / Modern Pop)", "bpm": "115 BPM", "mood": "Catchy & Upbeat", "instruments": "soft piano, acoustic guitar, modern pop drums, subtle Tro fiddle", "vocals": "clear native Khmer vocal, melodic pop delivery"},
    {"name": "Khmer Hip Hop", "bg": "#6366f1", "region": "Southeast Asia", "genre": "Khmer Music (Romvong / Kantrum / Modern Pop)", "bpm": "135 BPM", "mood": "Confident & Aggressive", "instruments": "sampled Chapei lute, heavy 808 sub-bass, sharp trap snares, Tro accents", "vocals": "rapid Khmer cadence, rhythmic flow, confident swagger"},
    {"name": "Khmer Remix", "bg": "#06b6d4", "region": "Southeast Asia", "genre": "Khmer Music (Romvong / Kantrum / Modern Pop)", "bpm": "138 BPM", "mood": "Party Club Energy", "instruments": "heavy club kick, sidechained synth leads, vocal chops, bounce bass", "vocals": "reverb-drenched Khmer vocals, hype ad-libs"},
    {"name": "Khmer Romvong", "bg": "#10b981", "region": "Southeast Asia", "genre": "Khmer Music (Romvong / Kantrum / Modern Pop)", "bpm": "110 BPM", "mood": "Festive & Joyful", "instruments": "Skor Daey drums, Tro fiddle, Roneat xylophone, acoustic guitar", "vocals": "traditional festive Khmer singalong, group harmonies"},
    {"name": "K-Pop", "bg": "#f59e0b", "region": "East Asia", "genre": "K-Pop (Korean Pop)", "bpm": "125 BPM", "mood": "Euphoric & Powerful", "instruments": "brass stabs, punchy 808 bass, futuristic arpeggiated synths", "vocals": "bilingual Korean/English vocal switch, rap breaks, soaring belted chorus"},
    {"name": "Electronic", "bg": "#ec4899", "region": "North America & Global Pop", "genre": "EDM & Festival Dance", "bpm": "128 BPM", "mood": "Hypnotic & High Energy", "instruments": "analog synthesizers, modular bass, crisp hi-hats, vocal chops", "vocals": "processed vocal chops, soaring euphoric topline"},
    {"name": "R&B", "bg": "#334155", "region": "North America & Global Pop", "genre": "Contemporary R&B / Neo-Soul", "bpm": "82 BPM", "mood": "Sensual & Smooth", "instruments": "Fender Rhodes electric piano, lush 808 sub-bass, warm finger snaps", "vocals": "silky falsetto runs, rich 4-part layered harmonies"},
    {"name": "Rock", "bg": "#78350f", "region": "North America & Global Pop", "genre": "Indie / Alternative Rock", "bpm": "132 BPM", "mood": "Rebellious & Raw", "instruments": "distorted electric guitars, punchy acoustic drum kit, driven bass guitar", "vocals": "gritty raspy rock lead, impassioned belt"},
    {"name": "Gospel", "bg": "#ea580c", "region": "North America & Global Pop", "genre": "Pop & Synthpop", "bpm": "95 BPM", "mood": "Triumphant & Uplifting", "instruments": "Hammond B3 organ, grand piano, foot-stomping drums, brass choir", "vocals": "towering soulful choir harmonies, expressive melismatic lead"},
    {"name": "Pop", "bg": "#8b5cf6", "region": "North America & Global Pop", "genre": "Pop & Synthpop", "bpm": "120 BPM", "mood": "Catchy & Vibrant", "instruments": "clean guitars, punchy four-on-the-floor beat, shimmering synth pads", "vocals": "polished modern pop vocal, memorable earworm chorus"},
    {"name": "Country", "bg": "#0284c7", "region": "North America & Global Pop", "genre": "Country & Americana", "bpm": "98 BPM", "mood": "Storyteller & Nostalgic", "instruments": "acoustic guitar strumming, pedal steel guitar, banjo, fiddle", "vocals": "warm Southern twang, sincere narrative phrasing"},
    {"name": "Latin", "bg": "#059669", "region": "Latin America & Caribbean", "genre": "Reggaeton & Latin Urban", "bpm": "96 BPM", "mood": "Sensual & Danceable", "instruments": "Dem-bow syncopated rhythm, nylon Spanish guitar, sub-bass pulse", "vocals": "fiery Spanglish delivery, rhythmic Chanteo cadences"},
    {"name": "Afrobeats", "bg": "#eab308", "region": "Africa & Afro-Diaspora", "genre": "Afrobeats (Naija / Ghana)", "bpm": "105 BPM", "mood": "Joyful & Grateful", "instruments": "syncopated log drum, warm West African brass, sweet guitar licks, shakers", "vocals": "playful Pidgin English cadences, infectious chant callouts"},
    {"name": "Shoegaze", "bg": "#e11d48", "region": "North America & Global Pop", "genre": "Indie / Alternative Rock", "bpm": "105 BPM", "mood": "Dreamy & Wall of Sound", "instruments": "drenched reverb guitars, fuzz pedals, tremolo glide, driving bass", "vocals": "whispered airy ethereal vocals buried in sonic textures"},
    {"name": "Experimental", "bg": "#475569", "region": "North America & Global Pop", "genre": "Pop & Synthpop", "bpm": "110 BPM", "mood": "Avant-Garde & Unpredictable", "instruments": "glitch percussion, distorted soundscapes, microtonal synths", "vocals": "unconventional vocal phrasing, pitched-shifted spoken lines"},
    {"name": "Alternative", "bg": "#713f12", "region": "North America & Global Pop", "genre": "Indie / Alternative Rock", "bpm": "124 BPM", "mood": "Moody & Introspective", "instruments": "jangly electric guitars, driving rhythm section, cello accents", "vocals": "understated poignant delivery, dynamic emotional bursts"},
    {"name": "Folk", "bg": "#f97316", "region": "Europe & Folk Traditions", "genre": "Celtic Folk & Sea Shanty", "bpm": "100 BPM", "mood": "Earthly & Authentic", "instruments": "acoustic fingerpicking, tin whistle, mandolin, hand percussion", "vocals": "pure organic vocals, communal singalong chorus"},
    {"name": "Jazz", "bg": "#9333ea", "region": "North America & Global Pop", "genre": "Contemporary R&B / Neo-Soul", "bpm": "115 BPM", "mood": "Sophisticated & Intimate", "instruments": "upright acoustic bass, brushed snare, smoky saxophone, jazz piano", "vocals": "warm velvet vocal tone, delicate scat improvisations"},
    {"name": "Blues", "bg": "#2563eb", "region": "North America & Global Pop", "genre": "Contemporary R&B / Neo-Soul", "bpm": "75 BPM", "mood": "Soulful & Melancholic", "instruments": "expressive 12-bar blues electric guitar, harmonica, upright piano", "vocals": "gravelly passionate blues lament, deep chest resonance"},
    {"name": "House", "bg": "#16a34a", "region": "North America & Global Pop", "genre": "EDM & Festival Dance", "bpm": "124 BPM", "mood": "Deep Club Groove", "instruments": "four-on-the-floor 909 kick, shuffling open hi-hats, warm piano chords", "vocals": "soulful diva vocal loops, uplifting spoken hook"},
    {"name": "Punk", "bg": "#ca8a04", "region": "North America & Global Pop", "genre": "Indie / Alternative Rock", "bpm": "165 BPM", "mood": "Rebellious & High Octane", "instruments": "power chord guitars, rapid-fire snare beats, fuzzy bass", "vocals": "snarling shouted vocals, anthemic gang-shout chorus"},
    {"name": "Dance", "bg": "#db2777", "region": "North America & Global Pop", "genre": "Pop & Synthpop", "bpm": "126 BPM", "mood": "Party Euphoria", "instruments": "sidechained bass, pumping synthesizers, bright piano, handclaps", "vocals": "catchy melodic topline, dancefloor chant hook"},
    {"name": "Indie Rock", "bg": "#1e293b", "region": "North America & Global Pop", "genre": "Indie / Alternative Rock", "bpm": "118 BPM", "mood": "Carefree & Youthful", "instruments": "vintage telecaster riffs, tambourine, warm bassline, acoustic drums", "vocals": "effortlessly cool vocal delivery, singable melodic hooks"},
    {"name": "Hip Hop", "bg": "#525252", "region": "North America & Global Pop", "genre": "Hip-Hop & Trap", "bpm": "90 BPM", "mood": "Street Narrative & Gritty", "instruments": "MPC boom-bap drums, vinyl chops, upright bass, scratched samples", "vocals": "authoritative lyricism, rhythmic multi-syllabic rhymes"},
    {"name": "Reggae", "bg": "#d97706", "region": "Latin America & Caribbean", "genre": "Reggaeton & Latin Urban", "bpm": "78 BPM", "mood": "Relaxed & Conscious", "instruments": "off-beat guitar skank, deep bubbling bassline, one-drop drum beat, organ", "vocals": "soulful roots reggae vocal, conscious spiritual message"},
    {"name": "Hyperpunk", "bg": "#a855f7", "region": "North America & Global Pop", "genre": "Pop & Synthpop", "bpm": "150 BPM", "mood": "Frenetic & Cybernetic", "instruments": "distorted metallic 808s, bitcrushed synths, hyper-speed drums", "vocals": "auto-tuned pitched vocal screams, rapid-fire staccato delivery"},
    {"name": "Metal", "bg": "#38bdf8", "region": "Europe & Folk Traditions", "genre": "Nordic Melodic Folk / Metal", "bpm": "140 BPM", "mood": "Heavy & Epic", "instruments": "down-tuned chugging guitars, double bass drum kicks, atmospheric pads", "vocals": "towering melodic heavy metal belt, guttural scream accents"},
    {"name": "Funk Soul", "bg": "#10b981", "region": "North America & Global Pop", "genre": "Contemporary R&B / Neo-Soul", "bpm": "110 BPM", "mood": "Groovy & Energetic", "instruments": "slap bass guitar, wah-wah guitar, punchy brass horns, clavinet", "vocals": "expressive soul shouts, synchronized falsetto ad-libs"},
    {"name": "Soundtrack", "bg": "#f59e0b", "region": "East Asia", "genre": "J-Pop & Anime Soundtrack", "bpm": "110 BPM", "mood": "Cinematic & Grand", "instruments": "full orchestral strings, French horns, dramatic taiko drums, piano", "vocals": "soaring emotional lead vocal, choral chants"},
    {"name": "Classical", "bg": "#ec4899", "region": "Europe & Folk Traditions", "genre": "French Chanson & Café Indie", "bpm": "70 BPM", "mood": "Timeless & Poetic", "instruments": "grand piano, string quartet, acoustic harp, woodwinds", "vocals": "operatic lyrical purity, precise dynamic control"},
    {"name": "Ambient", "bg": "#0f172a", "region": "North America & Global Pop", "genre": "Pop & Synthpop", "bpm": "60 BPM", "mood": "Meditative & Spacey", "instruments": "reverberant drone synths, soundscape textures, slow piano echoes", "vocals": "wordless ethereal hums, distant soothing reverberations"}
]

KHMER_STUDIO_TAGS = {
    "storylines": {
        "love_stories": [
            {"kh": "បងអ្នកក្រ ស្រីអ្នកមាន", "en": "Rich girl, poor boy", "prompt": "poor boy falling in love with a wealthy girl, family opposition and social status struggles"},
            {"kh": "បងអ្នកមាន ស្រីអ្នកក្រ", "en": "Poor boy, rich girl", "prompt": "wealthy man trying to prove his sincere heart to a humble countryside girl"},
            {"kh": "ស្នេហាឆ្លងវណ្ណៈ", "en": "Love across class", "prompt": "true romantic devotion defying societal expectations and class barriers"},
            {"kh": "ស្នេហាស្រុកស្រែ", "en": "Countryside love", "prompt": "sweet innocent love story amidst green rice fields, evening breeze, and palm trees"},
            {"kh": "ស្នេហាក្នុងភូមិ", "en": "Village love", "prompt": "childhood friends in a peaceful Cambodian village discovering romantic feelings"},
            {"kh": "ស្នេហាកម្មករ", "en": "Factory-worker love", "prompt": "hardworking factory workers sharing lunches and finding comfort in difficult times"},
            {"kh": "ស្នេហាបែបជីវិតពិត", "en": "Real-life love", "prompt": "realistic modern relationship overcoming financial hardship and daily struggles together"},
            {"kh": "បែកគ្នាដោយសារទ្រព្យសម្បត្តិ", "en": "Broken up over money", "prompt": "tragic romantic breakup forced by financial differences and demanding parents"},
            {"kh": "ស្នេហាដែលគ្រួសារហាមឃាត់", "en": "Love forbidden by family", "prompt": "heartbreaking forbidden love, secret promises, tears in the quiet night"},
            {"kh": "ខូចចិត្ត ក្បត់ស្នេហា", "en": "Heartbreak & betrayal", "prompt": "devastating pain of unfaithfulness and betrayal by someone deeply trusted"},
            {"kh": "ស្នេហាឆ្ងាយ ស្នេហ៍", "en": "Long-distance love", "prompt": "painful longing across ocean distances, counting hours until reunion"},
            {"kh": "ស្នេហាដំបូង", "en": "First love", "prompt": "sweet nostalgic memories of innocence, gentle smiles, and high school romance"},
            {"kh": "ស្នេហាតាមអនឡាញ", "en": "Online love", "prompt": "falling in love through late night chat messages and video calls across provinces"},
            {"kh": "ស្នេហាបែបយុវវ័យសម័យថ្មី", "en": "Gen-Z Phnom Penh", "prompt": "vibrant modern youth romance on motorbikes through the bustling streets of Phnom Penh"}
        ],
        "life_and_family": [
            {"kh": "គុណម្តាយ", "en": "A mother's love", "prompt": "boundless gratitude for a Cambodian mother's lifelong sacrifice, hard labor, and unconditional prayers"},
            {"kh": "គុណឪពុក", "en": "A father's sacrifice", "prompt": "honoring a father's silent sweat, calloused hands, and enduring protection for his children"},
            {"kh": "ធ្វើការក្រៅស្រុក", "en": "Working abroad", "prompt": "Khmer worker overseas sending remittances home while missing their children and homeland"},
            {"kh": "កូនអ្នកស្រែតស៊ូរៀន", "en": "Farmer child studying hard", "prompt": "countryside youth studying tirelessly under kerosene lamps to graduate and lift their family up"},
            {"kh": "មោទនភាពជាតិ", "en": "Homeland pride", "prompt": "deep pride in Angkor civilization, rich Khmer heritage, and standing proud on the world stage"},
            {"kh": "ការចាកចេញពីស្រុកកំណើត", "en": "Leaving hometown", "prompt": "leaving beloved parents and home village with a suitcase full of dreams"},
            {"kh": "មិត្តភាពយូរអង្វែង", "en": "Lifelong friendship", "prompt": "unbreakable brotherhood sharing meals and lifting each other up through every storm"}
        ],
        "festivals_and_occasions": [
            {"kh": "ចូលឆ្នាំខ្មែរ", "en": "Khmer New Year", "prompt": "joyous Khmer New Year celebration with traditional games, flower offerings, and Romvong dance"},
            {"kh": "បុណ្យកឋិន", "en": "Kathen festival", "prompt": "devout Kathen robe-offering procession to rural pagodas with drums, flowers, and blessings"},
            {"kh": "អាពាហ៍ពិពាហ៍", "en": "Wedding", "prompt": "traditional Cambodian wedding with areca nuts, hair cutting blessing, and colorful silk garments"},
            {"kh": "ភ្ជុំបិណ្ឌ", "en": "Pchum Ben", "prompt": "Pchum Ben ancestor remembrance, early morning pagoda bells, and honoring departed souls"},
            {"kh": "បុណ្យអុំទូក", "en": "Water Festival", "prompt": "grand Water Festival boat races in front of the Royal Palace with floating illuminated lanterns"},
            {"kh": "បុណ្យមាឃបូជា និងវិសាខបូជា", "en": "Buddhist festivals", "prompt": "peaceful candlelit processions reflecting on Buddhist teachings and inner peace"}
        ]
    },
    "music_styles_and_instruments": [
        {"kh": "ប្រពៃណីខ្មែរ", "en": "Khmer traditional", "instruments": "Roneat Ek xylophone, Tro Ou fiddle, Skor Daey drums, Chhing cymbals, Khloy bamboo flute", "vocal": "native Khmer classical ornaments, melismatic vibrato"},
        {"kh": "រាំវង់", "en": "Romvong", "instruments": "Tro fiddle, acoustic guitar, Skor Daey dance rhythm, festive shakers", "vocal": "joyful melodic Khmer singalong, infectious community chorus"},
        {"kh": "សារ៉ាវ៉ាន់", "en": "Saravan", "instruments": "swinging Saravan drum groove, acoustic Tro, electric bass, shaker rhythm", "vocal": "warm conversational lilt, rhythmic Khmer cadence"},
        {"kh": "ឡាំលាវ", "en": "Lam leav", "instruments": "gentle swaying Lam Leav rhythm, soft acoustic Tro, nylon guitar", "vocal": "tender nostalgic melody, romantic sweetness"},
        {"kh": "កន្ទ្រឹម", "en": "Kantrum", "instruments": "fast Kantrum Skor Daey percussion, electric Tro riff, driving bass guitar", "vocal": "energetic party call-and-response, high-energy village shouts"},
        {"kh": "ចាប៉ីដងវែង", "en": "Chapei", "instruments": "resonant 2-string Chapei Dong Veng lute, foot cymbals", "vocal": "improvisational storytelling bard delivery, wise moral proverbs"},
        {"kh": "អាយ៉ៃ", "en": "Ayai duet", "instruments": "Tro Sao, Tro Ou, Skor Daey, Chhing", "vocal": "humorous male and female rhyming repartee, witty banter"},
        {"kh": "សម័យ ៦០", "en": "60s golden era", "instruments": "vintage surf guitar, warm saxophone, Farfisa organ, acoustic drums", "vocal": "Sinn Sisamouth & Ros Sereysothea romantic vibrato, golden era phrasing"},
        {"kh": "កន្ទ្រឹម Rock ញាក់", "en": "Modern Kantrum Rock", "instruments": "distorted electric guitar, heavy dance drums, electric tro, punchy bass", "vocal": "high-octane party vocals, festival hype"},
        {"kh": "មហោរី", "en": "Mohori royal music", "instruments": "Tro Ou, Tro Sao, Roneat Thung, Krapeu zither, Khloy flute", "vocal": "delicate courtly singing, poetic poise"},
        {"kh": "ភ្លេងការបុរាណ", "en": "Khmer wedding ensemble", "instruments": "Tro Khmer, Chapei, Skor Chey, Pey Or flute", "vocal": "solemn celebratory blessing chants"},
        {"kh": "Hip-Hop ខ្មែរបុរាណ", "en": "Khmer Heritage Hip-Hop", "instruments": "sampled Chapei riff, heavy 808 sub-bass, crispy boom-bap drums, Tro accents", "vocal": "rapid poetic Khmer flow, confident cadence, ancestral pride"}
    ]
}

ENGLISH_STUDIO_TAGS = {
    "storylines": {
        "heartbreak_and_memories": [
            {"title": "Cardigan in the Cold Rain", "desc": "Sitting in a midnight diner with old keys, wool sweater, and unsaid goodbyes", "prompt": "nostalgic meeting with an ex at an empty diner on a rainy October night, unspoken regret"},
            {"title": "Strangers With Memories", "desc": "Passing each other on the subway platform like we never shared a lifetime", "prompt": "two former lovers crossing paths in a crowded city subway, mutual silence and heavy glances"},
            {"title": "Left on Read at 2 AM", "desc": "Blue screen glow in the dark, watching the typing dots disappear into silence", "prompt": "late night heartbreak staring at an unanswered text message while the city sleeps"},
            {"title": "The One That Got Away", "desc": "Summer faded fast, but your laughter still echoes through autumn leaves", "prompt": "bittersweet reminiscing about a missed romantic chance that still haunts years later"},
            {"title": "Ghost in My Apartment", "desc": "Every room has an echo, leaving a coffee cup on the counter for two", "prompt": "moving on while physical everyday objects still remind you of someone who walked out"},
            {"title": "Wasted Youth on You", "desc": "Poured all my golden years into someone who turned love into cold dust", "prompt": "devastating realization of wasted time, betrayal, and picking up the shattered pieces"}
        ],
        "romance_and_nightlife": [
            {"title": "Midnight Vintage Drive", "desc": "Windows down on coastal highway, city lights bleeding violet in the rear-view", "prompt": "euphoric midnight drive in a convertible car, synthwave radio, electric intimacy"},
            {"title": "Sparks in the Crowd", "desc": "Locking eyes across a velvet nightclub room, the whole party blurs away", "prompt": "instant magnetic attraction on a packed dancefloor, slow-motion romantic tension"},
            {"title": "Golden Hour Rooftop", "desc": "Drinking cheap wine out of paper cups as the sun sets over the skyline", "prompt": "carefree summer romance on an apartment rooftop, warm breeze, acoustic guitars"},
            {"title": "Dangerous Chemistry", "desc": "An electric fire we both know will burn us down, but we can't stop now", "prompt": "irresistible toxic attraction that defies logic and pulls both lovers into chaos"},
            {"title": "Falling Out of Orbit", "desc": "Weightless love, spinning into each other without caring where we land", "prompt": "surrendering completely to romantic euphoria, floating above everyday worries"},
            {"title": "Dancing in the Storm", "desc": "Stepping off the curb into heavy rain, laughing through the thunder", "prompt": "spontaneous joyous love, getting drenched together under streetlights"}
        ],
        "ambition_and_confidence": [
            {"title": "Crown of Broken Glass", "desc": "Started from nothing, turning every doubt into fuel for the fire", "prompt": "unstoppable resilience, rising from underdog status to wearing the crown"},
            {"title": "Basement to the Penthouse", "desc": "Late-night hustle, blood sweat and tears turning into pure gold", "prompt": "working relentlessly from zero to undisputed musical success and wealth"},
            {"title": "Unapologetic Energy", "desc": "Walking away with my head held high and the spotlight burning bright", "prompt": "self-love anthem, dropping fake friends, owning your worth and commanding respect"},
            {"title": "Born for the Stadium", "desc": "Refusing to stay small, built to shake the ground and take the world", "prompt": "epic victory march, 100,000 voices singing along in unison"}
        ],
        "dark_and_psychological": [
            {"title": "Demons in the Neon Shadows", "desc": "Wrestling with internal voices when the bedroom walls close in at 3 AM", "prompt": "psychological dark alt-pop exploring intrusive thoughts, insomnia, and inner ghosts"},
            {"title": "Quiet Panic at the Party", "desc": "Smiling for the cameras while feeling completely detached and hollow inside", "prompt": "imposter syndrome, social anxiety behind a glamorous celebrity mask"},
            {"title": "Sweet-Talking Villain", "desc": "Honey dripping from a razor blade, playing the savior while pulling strings", "prompt": "sarcastic expose of a manipulative charmer wrapped in innocent apologies"},
            {"title": "Insomnia Radio", "desc": "Tuning into white noise and vintage frequencies when sleep won't come", "prompt": "hazy late-night solitude, static between stations, lonely contemplative thoughts"}
        ],
        "stadium_resilience_and_hope": [
            {"title": "We Are the Giants", "desc": "Shaking off the dust, rising like thunder from the bottom of the deep", "prompt": "triumphant stadium anthem of awakening power, unity, and breaking all barriers"},
            {"title": "Rising From the Ash", "desc": "Scars on our palms, but we carry our own light into the darkest valley", "prompt": "rebirth after total heartbreak, finding inner strength when everything seemed lost"},
            {"title": "Unbreakable Tomorrow", "desc": "Standing shoulder to shoulder, no storm or earthquake can tear us down", "prompt": "universal anthem of hope, communal love, and an indomitable human spirit"}
        ]
    },
    "production_styles": [
        {
            "name": "🏆 Max Martin 80s Disco-Pop",
            "en": "Max Martin Pop",
            "genre": "Pop & Synthpop",
            "bpm": "124 BPM",
            "mood": "Euphoric & Uplifting",
            "instruments": "Analog Moog Bass, 80s LinnDrum, Juno-106 Synth Arps, Funk Guitar Strats, Handclaps",
            "vocals": "punchy high-energy lead vocal, soaring vocal belt, layered disco harmonies",
            "chords": ["Am", "F", "C", "G"],
            "prompt": "80s disco-pop, punchy synth bass, LinnDrum, funk guitar, soaring female vocal belt, earworm hook"
        },
        {
            "name": "🍂 Folklore Acoustic & Cello",
            "en": "Folklore Indie",
            "genre": "Indie / Alternative Rock",
            "bpm": "76 BPM",
            "mood": "Melancholic & Nostalgic",
            "instruments": "Fingerpicked Martin Acoustic Guitar, Warm Solo Cello, Foot Stomp Kick, Dulcimer",
            "vocals": "intimate breathy chest voice, whispered storytelling cadence, emotional soaring bridge",
            "chords": ["C", "G", "Am", "F"],
            "prompt": "indie folk storyteller, fingerpicked acoustic guitar, mournful solo cello, intimate female breathy vocal, 3-minute bridge"
        },
        {
            "name": "🌌 Dark Bedroom Alt-Pop (Billie Style)",
            "en": "Dark Alt-Pop",
            "genre": "Dark Alt-Pop",
            "bpm": "115 BPM",
            "mood": "Dark, Haunting & Mysterious",
            "instruments": "Sub-Bass 808, Distorted Glitch Snare, Music Box Celesta, Atmospheric Tape Hiss",
            "vocals": "ASMR close-mic whisper, pitch-shifted double vocal, cynical sarcastic delivery",
            "chords": ["Em", "C", "Am", "B7"],
            "prompt": "dark alt-pop, ASMR close-mic whispered vocal, deep sub-bass 808, glitch percussion, creepy celesta"
        },
        {
            "name": "🎷 Midnight Neo-Soul & R&B",
            "en": "Neo-Soul Slow Jam",
            "genre": "Contemporary R&B / Neo-Soul",
            "bpm": "74 BPM",
            "mood": "Sensual & Romantic",
            "instruments": "Fender Rhodes Electric Piano, Muted Stratocaster, Warm Brass Horns, Finger Snaps, Upright Bass",
            "vocals": "silky chest voice, agile falsetto runs, rich 4-part backing harmonies",
            "chords": ["Dm7", "G7", "Cmaj7", "Am7"],
            "prompt": "neo-soul slow jam, Fender Rhodes, warm muted guitar, finger snaps, silky falsetto runs, sensual late night groove"
        },
        {
            "name": "🏟️ Stadium Arena Rock Anthem",
            "en": "Arena Rock Anthem",
            "genre": "Indie / Alternative Rock",
            "bpm": "130 BPM",
            "mood": "Triumphant & Victorious",
            "instruments": "Chiming U2 Delay Guitars, Driving Floor-Tom Drums, Cathedral Organ, Crashing Cymbals",
            "vocals": "gritty passionate lead belt, soaring 100,000 fan 'Oh-oh-oh' crowd chant",
            "chords": ["F", "C", "G", "Am"],
            "prompt": "stadium rock anthem, chiming delay guitars, tribal tom drums, passionate lead vocal, 100000 fan crowd chant"
        },
        {
            "name": "🌙 Nocturnal Melodic Trap",
            "en": "Melodic Trap & 808",
            "genre": "Hip-Hop & Trap",
            "bpm": "140 BPM",
            "mood": "Chill, Dreamy & Atmospheric",
            "instruments": "Reversed Ambient Guitar Loop, Deep 808 Glides, Stuttering Trap Hi-Hats, Filtered Low-End",
            "vocals": "melodic autotune croon, relaxed syncopated cadence, nocturnal ad-libs",
            "chords": ["Am", "Em", "F", "G"],
            "prompt": "melodic trap, reversed guitar sample, deep 808 bass glides, autotuned emotional vocals, nocturnal city atmosphere"
        },
        {
            "name": "🎹 Grand Piano Soul Powerhouse",
            "en": "Adele Soul Ballad",
            "genre": "Contemporary R&B / Neo-Soul",
            "bpm": "68 BPM",
            "mood": "Melancholic & Nostalgic",
            "instruments": "Steinway Concert Grand Piano, Cinematic Orchestra Strings, Gentle French Horns",
            "vocals": "raw powerhouse chest belt, dynamic vocal projection, soaring climactic vibrato",
            "chords": ["Dm", "Bb", "F", "C"],
            "prompt": "cinematic soul piano ballad, concert grand piano, soaring orchestral strings, powerhouse female vocal belt, tearjerker"
        },
        {
            "name": "🌴 Tropical Dancehall Pop",
            "en": "Tropical Pop",
            "genre": "Reggaeton & Latin Urban",
            "bpm": "102 BPM",
            "mood": "Energetic & Party-Ready",
            "instruments": "Marimba, Syncopated Dem-bow Kick, Plucked Nylon Guitar, Shakers, Sub-Bass",
            "vocals": "melodic rhythmic vocal, breezy summery cadence, call-and-response party hooks",
            "chords": ["G", "Em", "C", "D"],
            "prompt": "tropical dancehall pop, marimba, breezy dem-bow groove, acoustic guitar plucks, infectious summer vocal hook"
        }
    ],
    "pro_modifiers": [
        {"tag": "[Female Belt]", "label": "🎤 Female Belt (Soaring Climax)"},
        {"tag": "[Male Raspy]", "label": "🎙️ Male Raspy (Gritty Emotional)"},
        {"tag": "[Whispered ASMR]", "label": "🤫 Whispered ASMR (Intimate)"},
        {"tag": "[Duet Harmonies]", "label": "👫 Duet Harmonies (Intertwined)"},
        {"tag": "[Fingerpicked Acoustic]", "label": "🎸 Fingerpicked Acoustic"},
        {"tag": "[Sub-Bass 808 Drop]", "label": "💥 Sub-Bass 808 Drop"},
        {"tag": "[Stadium Crowd Chant]", "label": "🏟️ Stadium Crowd Chant"},
        {"tag": "[Epic Key Change]", "label": "⚡ Epic Key Change (Half-Step Up)"},
        {"tag": "[High Note F5]", "label": "✨ High Note F5 (Vocal Peak)"},
        {"tag": "[Four on the Floor]", "label": "🥁 Four on the Floor (Dance Kick)"},
        {"tag": "[Gated Snare Reverb]", "label": "📻 Gated Snare Reverb (80s)"},
        {"tag": "[Soaring Guitar Solo]", "label": "🎸 Soaring Guitar Solo"}
    ]
}

