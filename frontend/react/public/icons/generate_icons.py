#!/usr/bin/env python3
"""
Generate PWA icons for SanchaySaathi using Python + Pillow.
Run once from the project root:
    pip install Pillow
    python3 frontend/react/public/icons/generate_icons.py

Produces:
    frontend/react/public/icons/icon-192.png
    frontend/react/public/icons/icon-512.png
"""
import pathlib, sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install Pillow first:  pip install Pillow")
    sys.exit(1)

OUT_DIR = pathlib.Path(__file__).parent

def make_icon(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), "#0a0a0f")
    draw = ImageDraw.Draw(img)

    # Draw 💸 emoji as text — fallback to a simple indigo circle if no emoji font
    emoji = "💸"
    font_size = int(size * 0.55)
    try:
        # macOS system emoji font
        font = ImageFont.truetype(
            "/System/Library/Fonts/Apple Color Emoji.ttc", font_size
        )
    except OSError:
        try:
            # Linux — Noto Color Emoji
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", font_size
            )
        except OSError:
            font = ImageFont.load_default()

    # Centre the emoji
    bbox = draw.textbbox((0, 0), emoji, font=font)
    x = (size - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (size - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), emoji, font=font, embedded_color=True)

    return img

for sz in [192, 512]:
    path = OUT_DIR / f"icon-{sz}.png"
    make_icon(sz).save(path, "PNG")
    print(f"✅  {path}")

print("\nIcons generated. Copy to frontend/react/public/icons/ if not already there.")
