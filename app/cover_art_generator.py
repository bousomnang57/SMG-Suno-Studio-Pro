"""
AI Album Cover & YouTube Thumbnail Generator Engine.
Provides dual-engine generation:
1. High-Resolution Studio Graphic Compositor (Pillow pure-Python)
2. AI Visual Prompt Builder (Imagen 3 / Gemini tailored prompts)
Supports 1:1 Square (Spotify/Suno) and 16:9 Landscape (YouTube MV),
typography overlays, and record label studio badges.
"""

import math
import random
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

STYLE_PRESETS: Dict[str, Dict] = {
    "cyberpunk_neon": {
        "name": "🌌 Cyberpunk Neon City",
        "bg_top": (15, 10, 35),
        "bg_bottom": (35, 10, 70),
        "accent_1": (0, 240, 255),    # Cyan neon
        "accent_2": (255, 0, 128),    # Magenta neon
        "style_desc": "Futuristic cyberpunk skyline, holographic violet and neon cyan glow, glowing grid horizon, cinematic lighting, 8k render."
    },
    "cinematic_anime": {
        "name": "🌸 Cinematic Anime Twilight",
        "bg_top": (25, 20, 60),
        "bg_bottom": (230, 110, 130),
        "accent_1": (255, 220, 180),  # Soft golden aura
        "accent_2": (255, 160, 200),  # Sakura pink
        "style_desc": "Makoto Shinkai / Studio Ghibli style anime twilight sky, cumulus clouds illuminated by golden sunset, stars twinkling, emotional nostalgia."
    },
    "vintage_vinyl_70s": {
        "name": "📻 Vintage 70s Analog Vinyl",
        "bg_top": (30, 25, 22),
        "bg_bottom": (80, 50, 30),
        "accent_1": (245, 166, 35),   # Warm amber
        "accent_2": (210, 90, 40),    # Burnt orange
        "style_desc": "Vintage 1970s vinyl album cover, analog tape warmth, circular vinyl grooves, retro warm color bands, subtle grain."
    },
    "khmer_angkor_heritage": {
        "name": "🏛️ Angkor Golden Hour Heritage",
        "bg_top": (20, 15, 30),
        "bg_bottom": (75, 45, 20),
        "accent_1": (245, 195, 65),   # Imperial Gold
        "accent_2": (200, 120, 50),   # Terracotta bronze
        "style_desc": "Majestic silhouette of ancient Khmer Angkor temple spires against a blazing golden-hour sunrise, sacred lotus pond reflections, mystical epic atmosphere."
    },
    "lofi_chill_sunset": {
        "name": "☕ Lo-Fi Chill Pastel Sunset",
        "bg_top": (35, 30, 65),
        "bg_bottom": (160, 90, 140),
        "accent_1": (255, 200, 150),  # Peach pastel
        "accent_2": (140, 220, 240),  # Soft sky blue
        "style_desc": "Lo-fi hip hop chill beats album cover, cozy bedroom window, rain droplets, dreamy pastel dusk gradient, mellow nostalgia."
    },
    "dark_melancholic_3d": {
        "name": "🖤 Dark Melancholic 3D Studio",
        "bg_top": (10, 12, 18),
        "bg_bottom": (24, 28, 42),
        "accent_1": (139, 92, 246),   # Electric violet
        "accent_2": (100, 116, 139),  # Chrome slate
        "style_desc": "Moody cinematic 3D abstract sculpture, liquid chrome metals, dark studio lighting, subtle violet rim light, album art of the year."
    }
}


class CoverArtGenerator:
    """
    Studio Graphic Compositor for high-resolution album covers & YouTube thumbnails.
    """

    @classmethod
    def get_font(cls, size: int, bold: bool = True) -> ImageFont.ImageFont:
        """Attempt to load high quality modern system fonts with graceful fallback."""
        font_names = [
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        ]
        for f_path in font_names:
            if Path(f_path).exists():
                try:
                    return ImageFont.truetype(f_path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @classmethod
    def generate_cover_art(
        cls,
        title: str,
        artist: str = "Lyric AI Writer",
        style_key: str = "cyberpunk_neon",
        aspect_ratio: str = "1:1", # "1:1" or "16:9"
        subtitle: str = "ORIGINAL SOUNDTRACK",
        badge: str = "STEREO · 96kHz / 24-bit"
    ) -> Image.Image:
        """
        Synthesizes a full studio-grade album cover or YouTube thumbnail using PIL.
        """
        style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cyberpunk_neon"])

        # Determine canvas dimensions
        if aspect_ratio == "16:9":
            width, height = 1920, 1080
        else: # 1:1 Square
            width, height = 1200, 1200

        # Layer 1: High-res background gradient
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        c_top = style["bg_top"]
        c_bot = style["bg_bottom"]

        for y in range(height):
            ratio = y / float(height)
            r = int(c_top[0] * (1.0 - ratio) + c_bot[0] * ratio)
            g = int(c_top[1] * (1.0 - ratio) + c_bot[1] * ratio)
            b = int(c_top[2] * (1.0 - ratio) + c_bot[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Layer 2: Atmospheric Art & Geometry based on style
        acc1 = style["accent_1"]
        acc2 = style["accent_2"]

        # Central glowing ambient orb / horizon
        orb_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        orb_draw = ImageDraw.Draw(orb_img)

        cx, cy = width // 2, int(height * 0.45)
        max_r = int(min(width, height) * 0.40)

        # Concentric rings / vinyl grooves or neon glow
        if style_key == "vintage_vinyl_70s":
            # Vinyl record grooves
            for r in range(max_r, 40, -18):
                alpha = int(45 + 30 * math.sin(r * 0.1))
                orb_draw.ellipse(
                    [(cx - r, cy - r), (cx + r, cy + r)],
                    outline=(acc1[0], acc1[1], acc1[2], alpha),
                    width=2
                )
            # Center spindle label
            label_r = 70
            orb_draw.ellipse([(cx - label_r, cy - label_r), (cx + label_r, cy + label_r)], fill=(acc2[0], acc2[1], acc2[2], 220))
            orb_draw.ellipse([(cx - 15, cy - 15), (cx + 15, cy + 15)], fill=(20, 15, 10, 255))
        else:
            # Celestial / Neon Glowing Sphere
            for r in range(max_r, 0, -12):
                alpha = int(120 * (1.0 - (r / max_r) ** 1.8))
                col = acc1 if (r % 24 == 0) else acc2
                orb_draw.ellipse(
                    [(cx - r, cy - r), (cx + r, cy + r)],
                    fill=(col[0], col[1], col[2], alpha)
                )

        # Perspective Grid Horizon for Cyberpunk / Neon
        if "neon" in style_key or "dark" in style_key:
            horizon_y = int(height * 0.65)
            # Radiating grid lines to vanish point (cx, horizon_y)
            for x in range(0, width + 100, 120):
                orb_draw.line([(cx, horizon_y), (x, height)], fill=(acc1[0], acc1[1], acc1[2], 65), width=2)
            # Horizontal lines
            for i in range(1, 10):
                gy = horizon_y + int((height - horizon_y) * (i / 10.0) ** 1.8)
                orb_draw.line([(0, gy), (width, gy)], fill=(acc2[0], acc2[1], acc2[2], 75), width=2)

        # Star / particle field
        random.seed(abs(hash(title)) % 10000)
        for _ in range(120):
            sx = random.randint(0, width)
            sy = random.randint(0, int(height * 0.7))
            s_rad = random.randint(1, 3)
            s_alpha = random.randint(80, 240)
            orb_draw.ellipse([(sx - s_rad, sy - s_rad), (sx + s_rad, sy + s_rad)], fill=(255, 255, 255, s_alpha))

        # Composite artwork layers
        img = Image.alpha_composite(img.convert("RGBA"), orb_img).convert("RGB")

        # Layer 3: Subtle Vignette / Edge Shading
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        margin = int(min(width, height) * 0.12)
        v_draw.rectangle([(0, 0), (width, height)], outline=(0, 0, 0, 160), width=margin)
        vignette = vignette.filter(ImageFilter.GaussianBlur(margin // 2))
        img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

        # Layer 4: Typography & Branding Overlays
        draw_text = ImageDraw.Draw(img)

        # Subtitle / Category
        f_sub = cls.get_font(26, bold=True)
        sub_text = subtitle.upper()
        draw_text.text((width // 2, int(height * 0.72)), sub_text, fill=(200, 210, 230), font=f_sub, anchor="mm")

        # Main Song Title with Drop Shadow
        title_font_size = 72 if len(title) <= 18 else (54 if len(title) <= 28 else 42)
        f_title = cls.get_font(title_font_size, bold=True)
        ty = int(height * 0.80)

        # Glow / Shadow
        for dx, dy in [(-3, -3), (3, 3), (-3, 3), (3, -3), (0, 4)]:
            draw_text.text((width // 2 + dx, ty + dy), title, fill=(10, 10, 20), font=f_title, anchor="mm")
        draw_text.text((width // 2, ty), title, fill=(255, 255, 255), font=f_title, anchor="mm")

        # Artist Name
        f_artist = cls.get_font(32, bold=False)
        ay = int(height * 0.88)
        draw_text.text((width // 2, ay), f"— {artist.upper()} —", fill=(acc1[0], acc1[1], acc1[2]), font=f_artist, anchor="mm")

        # Bottom Record Label Badges
        f_badge = cls.get_font(20, bold=True)
        # Left badge
        draw_text.text((60, height - 50), badge, fill=(160, 175, 195), font=f_badge, anchor="lm")
        # Right badge: SUNO AI MASTER
        draw_text.text((width - 60, height - 50), "SMG SUNO MASTER", fill=(acc1[0], acc1[1], acc1[2]), font=f_badge, anchor="rm")

        # Top corner: Aspect tag
        f_corner = cls.get_font(18, bold=True)
        draw_text.text((60, 45), f"OFFICIAL {aspect_ratio} RELEASE", fill=(140, 150, 170), font=f_corner, anchor="lm")

        return img

    @classmethod
    def craft_ai_prompt(cls, title: str, style_key: str, lyrics: str = "", genre: str = "Pop") -> str:
        """
        Creates an evocative, studio-grade Imagen 3 / Gemini image generation prompt.
        """
        style_desc = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cyberpunk_neon"])["style_desc"]

        # Extract mood keywords from lyrics if present
        mood_snippet = ""
        if lyrics:
            clean_lines = [l.strip() for l in lyrics.split("\n") if l.strip() and not l.startswith("[")]
            if clean_lines:
                mood_snippet = f"Themes: '{clean_lines[0]}', '{clean_lines[-1]}'. "

        prompt = (
            f"Commercial album cover artwork for the song '{title}', {genre} music genre. "
            f"{mood_snippet}"
            f"Visual Style: {style_desc} "
            f"High aesthetic composition, pristine digital art, dynamic colors, moody atmospheric lighting, "
            f"rule of thirds, award-winning cover design, ultra-detailed 8k resolution, no extraneous watermark."
        )
        return prompt

