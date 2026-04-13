#!/usr/bin/env python3
"""Generate pixel art GIFs for blog posts based on content themes.

Usage:
    python3 scripts/generate_pixel_art.py

GIFs are written to assets/images/pixel-art/<post-slug>.gif.
The Jekyll layout displays them automatically on post pages.
"""

import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow is required. Run: pip install Pillow")
    sys.exit(1)

# ── Site colour palette (mirrors simple-tech.css custom properties) ────────
BG          = (16,  20,  22)   # --bg       #101416
PANEL       = (23,  29,  32)   # --panel    #171d20
LINE        = (42,  53,  59)   # --line     #2a353b
ACCENT      = (126, 231, 135)  # --accent   #7ee787  green
SOFT        = (157, 215, 255)  # --accent-soft #9dd7ff  blue
PURPLE      = (192, 143, 255)  # --accent-purple #c08fff
MUTED       = (143, 161, 170)  # --muted    #8fa1aa
DIM         = (30,  42,  48)   # darker off-state

# ── Generation parameters ──────────────────────────────────────────────────
SIZE           = 64   # pixel canvas width/height
N_FRAMES       = 10   # animation frames per GIF
FRAME_MS       = 110  # milliseconds per frame


def new_rgb():
    return Image.new("RGB", (SIZE, SIZE), BG)


# ── Theme: CHIP ─────────────────────────────────────────────────────────────
# Used for: hardware, FPGA, VLIW/SIMD, SpinalHDL posts

def make_chip_frames():
    frames = []
    for f in range(N_FRAMES):
        img = new_rgb()
        d = ImageDraw.Draw(img)

        cx, cy = SIZE // 2, SIZE // 2
        hw, hh = 18, 18           # half-width / half-height of chip body

        # ── chip body ──
        d.rectangle([cx - hw, cy - hh, cx + hw, cy + hh], fill=PANEL, outline=LINE)

        # ── pin headers (left & right) ──
        for i in range(4):
            py = cy - 12 + i * 8
            d.rectangle([cx - hw - 5, py, cx - hw - 1, py + 3], fill=MUTED)
            d.rectangle([cx + hw + 1, py, cx + hw + 5, py + 3], fill=MUTED)

        # ── pin headers (top & bottom) ──
        for i in range(4):
            px = cx - 12 + i * 8
            d.rectangle([px, cy - hh - 5, px + 3, cy - hh - 1], fill=MUTED)
            d.rectangle([px, cy + hh + 1, px + 3, cy + hh + 5], fill=MUTED)

        # ── internal grid lines ──
        d.line([cx - hw + 5, cy, cx + hw - 5, cy], fill=LINE)
        d.line([cx, cy - hh + 5, cx, cy + hh - 5], fill=LINE)

        # ── four activity LEDs (cycle through) ──
        led_pos = [
            (cx - 9, cy - 9),
            (cx + 5, cy - 9),
            (cx + 5, cy + 5),
            (cx - 9, cy + 5),
        ]
        active = f % 4
        for i, (lx, ly) in enumerate(led_pos):
            if i == active:
                col = ACCENT
            elif i == (active - 1) % 4 or i == (active + 1) % 4:
                col = (40, 90, 50)   # dim green
            else:
                col = DIM
            d.rectangle([lx, ly, lx + 3, ly + 3], fill=col)

        # ── data pulse travelling along right-side pins ──
        pulse_idx = f % 4
        px_pulse = cx + hw + 1
        py_pulse = cy - 12 + pulse_idx * 8
        d.rectangle([px_pulse, py_pulse, px_pulse + 5, py_pulse + 3], fill=SOFT)

        frames.append(img)
    return frames


# ── Theme: TERMINAL ──────────────────────────────────────────────────────────
# Used for: DSL, compiler, GPT posts

_CODE_ROWS = [
    [(SOFT,   7), (ACCENT, 11), (MUTED,  8)],
    [(LINE,   4), (PURPLE, 12), (LINE,   4)],
    [(LINE,   8), (SOFT,    6), (ACCENT, 8)],
    [(LINE,   4), (MUTED,  10), (LINE,   6)],
    [(SOFT,   8), (ACCENT, 10), (MUTED,  8)],
    [(LINE,   4), (ACCENT,  6), (SOFT,  10)],
    [(PURPLE, 6), (LINE,    8), (SOFT,   6)],
    [(LINE,   4), (SOFT,   12), (LINE,   4)],
]

def make_terminal_frames():
    frames = []
    for f in range(N_FRAMES):
        img = new_rgb()
        d = ImageDraw.Draw(img)

        # ── terminal window chrome ──
        d.rectangle([2, 2, SIZE - 3, SIZE - 3], fill=PANEL, outline=LINE)

        # ── title bar ──
        d.rectangle([2, 2, SIZE - 3, 9], fill=(32, 42, 48))

        # ── macOS-style traffic lights ──
        d.ellipse([5, 4, 8, 7],   fill=(255, 95,  87))
        d.ellipse([11, 4, 14, 7], fill=(255, 189, 46))
        d.ellipse([17, 4, 20, 7], fill=(40,  201, 64))

        # ── title text bar label pixels ──
        for bx in range(26, 38, 3):
            d.rectangle([bx, 5, bx + 1, 6], fill=LINE)

        # ── scrolling code lines ──
        scroll = f % len(_CODE_ROWS)
        for row in range(5):
            line_data = _CODE_ROWS[(scroll + row) % len(_CODE_ROWS)]
            x = 5
            y = 13 + row * 8
            for color, width in line_data:
                if color != LINE:
                    d.rectangle([x, y, x + width, y + 3], fill=color)
                x += width + 2

        # ── blinking cursor on last visible row ──
        cursor_row = 4
        cursor_y = 13 + cursor_row * 8
        cursor_x = 5 + (f * 5) % 28
        if f % 2 == 0:
            d.rectangle([cursor_x, cursor_y, cursor_x + 2, cursor_y + 3], fill=ACCENT)

        frames.append(img)
    return frames


# ── Theme: MATRIX ────────────────────────────────────────────────────────────
# Used for: matrix-engine, fp32 posts

def make_matrix_frames():
    GRID = 7
    cell = (SIZE - 10) // GRID
    total = GRID * GRID
    frames = []
    for f in range(N_FRAMES):
        img = new_rgb()
        d = ImageDraw.Draw(img)

        progress = (f + 1) / N_FRAMES

        for row in range(GRID):
            for col in range(GRID):
                x = 5 + col * cell
                y = 5 + row * cell
                idx = row * GRID + col
                threshold = idx / total

                if threshold < progress:
                    # filled cell – colour encodes a "value"
                    v = (idx * 41 + f * 7) % 100
                    if v > 66:
                        fill = ACCENT
                    elif v > 33:
                        fill = SOFT
                    else:
                        fill = PURPLE
                else:
                    fill = DIM

                d.rectangle([x, y, x + cell - 2, y + cell - 2], fill=fill, outline=LINE)

        # ── highlight currently active cell ──
        active = min(int(progress * total), total - 1)
        ar, ac = divmod(active, GRID)
        ax = 5 + ac * cell
        ay = 5 + ar * cell
        d.rectangle([ax, ay, ax + cell - 2, ay + cell - 2], outline=ACCENT)

        frames.append(img)
    return frames


# ── Theme: WEB ───────────────────────────────────────────────────────────────
# Used for: website / GitHub Pages posts

def make_web_frames():
    frames = []
    for f in range(N_FRAMES):
        img = new_rgb()
        d = ImageDraw.Draw(img)

        progress = (f + 1) / N_FRAMES

        # ── monitor body ──
        d.rectangle([5,  6, SIZE - 6, SIZE - 12], fill=PANEL, outline=LINE)
        # ── screen area ──
        d.rectangle([7,  8, SIZE - 8, SIZE - 14], fill=(10, 14, 16))
        # ── monitor stand ──
        d.rectangle([SIZE // 2 - 4, SIZE - 12, SIZE // 2 + 4, SIZE - 8], fill=MUTED)
        d.rectangle([SIZE // 2 - 7, SIZE - 8,  SIZE // 2 + 7, SIZE - 5], fill=MUTED)

        # ── browser chrome ──
        d.rectangle([7, 8, SIZE - 8, 14], fill=(32, 42, 48))
        # address bar
        d.rectangle([14, 10, SIZE - 10, 13], fill=LINE)
        # favicon dot
        if f % 3 != 0:
            d.rectangle([15, 10, 17, 13], fill=ACCENT)

        # ── URL typing animation ──
        typed = int(progress * 12)
        for c in range(min(typed, 12)):
            d.rectangle([19 + c * 3, 11, 20 + c * 3, 12], fill=SOFT)

        # ── page content appearing ──
        if progress > 0.15:
            d.rectangle([9, 17, SIZE - 10, 20], fill=ACCENT)   # header bar

        for line in range(5):
            if progress > 0.15 + line * 0.12:
                ly = 23 + line * 6
                lw = SIZE - 22 - (line % 2) * 4
                col = MUTED if line > 0 else (213, 222, 226)
                d.rectangle([9, ly, 9 + lw, ly + 2], fill=col)

        frames.append(img)
    return frames


# ── Theme: CONSTRUCTION ───────────────────────────────────────────────────────
# Used for: "under construction" posts

def make_construction_frames():
    frames = []
    for f in range(N_FRAMES):
        img = new_rgb()
        d = ImageDraw.Draw(img)

        # ── ground strip ──
        d.rectangle([0, SIZE - 10, SIZE, SIZE], fill=(28, 20, 10))

        # ── barrier post ──
        d.rectangle([SIZE // 2 - 2, 28, SIZE // 2 + 2, SIZE - 10], fill=MUTED)

        # ── warning board with animated chevron stripes ──
        board_x1, board_y1 = 10, 32
        board_x2, board_y2 = SIZE - 11, 44
        stripe_count = 4
        stripe_w = (board_x2 - board_x1) // stripe_count
        for s in range(stripe_count):
            sx = board_x1 + s * stripe_w
            col = (255, 195, 0) if (s + (f // 2)) % 2 == 0 else (38, 38, 38)
            d.rectangle([sx, board_y1, sx + stripe_w - 1, board_y2], fill=col)
        d.rectangle([board_x1, board_y1, board_x2, board_y2], outline=MUTED)

        # ── blinking warning beacon ──
        beacon_col = (255, 120, 0) if f % 2 == 0 else (70, 35, 0)
        bx = SIZE // 2
        d.ellipse([bx - 4, 22, bx + 4, 30], fill=beacon_col, outline=MUTED)

        # ── hard hat ──
        hx, hy = SIZE // 2 - 10, 8
        d.ellipse([hx, hy, hx + 20, hy + 12], fill=(255, 200, 0))
        d.rectangle([hx - 2, hy + 8, hx + 22, hy + 12], fill=(255, 200, 0))
        d.rectangle([hx + 6, hy + 2, hx + 14, hy + 6], fill=(200, 150, 0))

        frames.append(img)
    return frames


# ── Theme registry ─────────────────────────────────────────────────────────
GENERATORS = {
    "chip":         make_chip_frames,
    "terminal":     make_terminal_frames,
    "matrix":       make_matrix_frames,
    "web":          make_web_frames,
    "construction": make_construction_frames,
}


# ── Theme detection from post front matter ─────────────────────────────────

def detect_theme(tags, title):
    flat = " ".join(str(t).lower() for t in tags)
    title_l = title.lower()

    if "matrix-engine" in flat or "fp32" in flat:
        return "matrix"
    if "fpga" in flat or "hardware" in flat or "spinalhdl" in flat:
        return "chip"
    if "dsl" in flat or "compilers" in flat or "gpt" in flat:
        return "terminal"
    if "website" in flat or "github" in flat:
        return "web"
    if "construction" in title_l or "under" in title_l:
        return "construction"
    # default for a tech / VLIW blog
    return "chip"


# ── Front-matter parser (no external YAML dep required) ────────────────────

def parse_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm = text[3:end].strip()

    data: dict = {}
    current_key = None
    current_list = None

    for raw_line in fm.splitlines():
        # list item
        stripped = raw_line.lstrip()
        if raw_line.startswith("  - ") or raw_line.startswith("- "):
            item = stripped.lstrip("- ").strip().strip('"').strip("'")
            if isinstance(current_list, list):
                current_list.append(item)
            continue

        if ":" in raw_line and not raw_line.startswith(" "):
            key, _, val = raw_line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            current_key = key
            if val == "":
                current_list = []
                data[key] = current_list
            else:
                current_list = None
                data[key] = val

    return data


def slug_from_path(path: Path) -> str:
    """Strip date prefix and extension: 2026-03-07-tileweave-… → tileweave-…"""
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)


# ── GIF writer ─────────────────────────────────────────────────────────────

def save_gif(frames, out_path: Path):
    palette_frames = [f.quantize(colors=64, method=Image.Quantize.MEDIANCUT) for f in frames]
    palette_frames[0].save(
        out_path,
        save_all=True,
        append_images=palette_frames[1:],
        loop=0,
        duration=FRAME_MS,
        optimize=False,
    )


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    repo_root = Path(__file__).resolve().parent.parent
    posts_dir = repo_root / "_posts"
    out_dir   = repo_root / "assets" / "images" / "pixel-art"
    out_dir.mkdir(parents=True, exist_ok=True)

    posts = sorted(posts_dir.glob("*.md"))
    if not posts:
        print("No posts found in", posts_dir)
        return

    for post in posts:
        fm    = parse_front_matter(post)
        title = fm.get("title", "")
        tags  = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        slug  = slug_from_path(post)
        theme = detect_theme(tags, title)
        out   = out_dir / f"{slug}.gif"

        print(f"  {post.name}")
        print(f"    theme : {theme}")
        print(f"    output: {out.relative_to(repo_root)}")

        frames = GENERATORS[theme]()
        save_gif(frames, out)
        print(f"    saved   ({out.stat().st_size} bytes, {N_FRAMES} frames)")

    print("\nDone – GIFs written to", out_dir.relative_to(repo_root))


if __name__ == "__main__":
    main()
