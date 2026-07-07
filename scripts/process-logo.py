"""
Generate the two Spec-34 logo marks from the white-background source artwork.

Input:  frontend/react/brand/wallet-mantra-source.png
        (opaque, light/white background — see spec 34_login-always-dark.md Item 3)
Output: frontend/react/public/wallet-mantra-logo.png        (variant B — dark surfaces, outlined)
        frontend/react/public/wallet-mantra-logo-light.png  (variant A — light header, no outline)

Usage: uv run python3 scripts/process-logo.py
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "frontend/react/brand/wallet-mantra-source.png"
OUT_DARK = ROOT / "frontend/react/public/wallet-mantra-logo.png"
OUT_LIGHT = ROOT / "frontend/react/public/wallet-mantra-logo-light.png"

EXPORT_SIZE = 256
BG_LUMINANCE_THRESHOLD = 235  # near-white/near-neutral background pixels
FEATHER_RADIUS = 1.2
OUTLINE_DILATE_PX = 2
OUTLINE_BLUR_RADIUS = 1.0
OUTLINE_ALPHA = 150


def flood_key_background(rgb: np.ndarray) -> np.ndarray:
    """Border-seeded flood fill over near-white/neutral pixels -> alpha 0.

    Seeding from the four borders (rather than a global luminance threshold)
    keeps interior light highlights (e.g. the gold strokes) intact, since
    those don't touch the border and never get visited.
    """
    h, w, _ = rgb.shape
    luminance = rgb.mean(axis=2)
    is_bg_candidate = luminance >= BG_LUMINANCE_THRESHOLD

    visited = np.zeros((h, w), dtype=bool)
    stack = []
    for x in range(w):
        stack.append((0, x))
        stack.append((h - 1, x))
    for y in range(h):
        stack.append((y, 0))
        stack.append((y, w - 1))

    while stack:
        y, x = stack.pop()
        if y < 0 or y >= h or x < 0 or x >= w:
            continue
        if visited[y, x] or not is_bg_candidate[y, x]:
            continue
        visited[y, x] = True
        stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])

    alpha = np.where(visited, 0, 255).astype(np.uint8)
    return alpha


def feather(alpha_img: Image.Image, radius: float) -> Image.Image:
    return alpha_img.filter(ImageFilter.GaussianBlur(radius))


def crop_to_content(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    if bbox is None:
        return img
    return img.crop(bbox)


def pad_to_square(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = max(w, h)
    padded = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    padded.paste(img, ((side - w) // 2, (side - h) // 2))
    return padded


def make_outline_ring(alpha_img: Image.Image) -> Image.Image:
    """Dilate the silhouette outward and blur it into a soft light ring
    that sits *behind* the mark, so dark surfaces get a separating edge."""
    dilated = alpha_img
    for _ in range(OUTLINE_DILATE_PX):
        dilated = dilated.filter(ImageFilter.MaxFilter(3))
    ring_alpha = dilated.filter(ImageFilter.GaussianBlur(OUTLINE_BLUR_RADIUS))
    ring_alpha = ring_alpha.point(lambda a: min(a, OUTLINE_ALPHA))
    ring_rgba = Image.new("RGBA", alpha_img.size, (255, 255, 255, 0))
    ring_rgba.putalpha(ring_alpha)
    return ring_rgba


def process(keyed: Image.Image, with_outline: bool) -> Image.Image:
    cropped = crop_to_content(keyed)
    squared = pad_to_square(cropped)

    if with_outline:
        alpha_only = squared.getchannel("A")
        ring = make_outline_ring(alpha_only)
        composited = Image.alpha_composite(ring, squared)
    else:
        composited = squared

    return composited.resize((EXPORT_SIZE, EXPORT_SIZE), Image.LANCZOS)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(
            f"Source artwork not found at {SOURCE}.\n"
            "Drop the white-background source raster there first "
            "(see .claude/blocked/34-followups-for-reevaluation.md item 1)."
        )

    src = Image.open(SOURCE).convert("RGBA")
    rgb = np.array(src)[:, :, :3]

    alpha = flood_key_background(rgb)
    keyed = src.copy()
    alpha_img = Image.fromarray(alpha, mode="L")
    alpha_img = feather(alpha_img, FEATHER_RADIUS)
    keyed.putalpha(alpha_img)

    variant_a = process(keyed, with_outline=False)  # light header
    variant_b = process(keyed, with_outline=True)   # dark surfaces

    OUT_LIGHT.parent.mkdir(parents=True, exist_ok=True)
    variant_a.save(OUT_LIGHT)
    variant_b.save(OUT_DARK)
    print(f"Wrote {OUT_LIGHT}")
    print(f"Wrote {OUT_DARK}")


if __name__ == "__main__":
    main()
