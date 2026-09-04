#!/usr/bin/env python3
"""
EXP-092: Bitmap Font Generator for MiniAndroid Software Renderer.

Generates a C++ header file `bitmap_font_data.h` containing 8x16 pixel
bitmaps for all 95 printable ASCII characters (32..126).

This replaces the previous hand-coded glyph table that only had 13 glyphs
(space, H, e, l, o, M, i, n, d, r, A, t) AND was mis-indexed
(e.g. 'H' was written to slot 33 instead of 40, then overwritten by 'A').

The bitmaps are produced by rendering each character with PIL using a
monospace font, then converting each row of pixels into a single byte
(MSB-first). The renderer's `draw_text` already iterates 8 columns per
row, so an 8x16 glyph matches the existing bitmap format perfectly.

Output:
  /home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/src/renderer/bitmap_font_data.h

This file is included by software_renderer.cpp at the point where the
old hardcoded bitmaps (H_bitmap, e_bitmap, etc.) were declared.
"""

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/src/renderer/bitmap_font_data.h")

# All printable ASCII chars (32..126).
GLYPH_CHARS = [chr(c) for c in range(32, 127)]

# Dimensions: 8 cols x 16 rows per glyph. Matches the existing
# BitmapFont::Glyph struct's hardcoded `bitmap[16]` size and the
# draw_text loop's `for col in 0..8` iteration.
GLYPH_W = 8
GLYPH_H = 16

# Pick a monospace font available on the system. DejaVu Sans Mono is
# available on Debian/Ubuntu and provides clear, readable glyphs.
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def pick_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise RuntimeError(
        "No suitable TTF font found. Looked for: " + ", ".join(FONT_CANDIDATES)
    )


def render_glyph(ch: str, font: ImageFont.FreeTypeFont) -> list[int]:
    """
    Render `ch` to an 8x16 bitmap. Returns a list of 16 bytes, one per row.
    Each byte's bits (MSB first) indicate which columns in that row are dark.

    Algorithm:
      1. Create a large RGBA canvas (32x48) with white background.
      2. Draw the character centered in the canvas with black.
      3. Crop tightly to the dark pixels (the glyph's ink box).
      4. Resize to 8x16 (or pad to 8x16 if smaller) using nearest-neighbor.
      5. Threshold each pixel: dark if its luminance < 128.
      6. Pack each row's 8 bits into a byte (MSB first).
    """
    # Large canvas for antialiased rendering
    canvas_w, canvas_h = 32, 48
    img = Image.new("L", (canvas_w, canvas_h), 255)  # white background
    draw = ImageDraw.Draw(img)
    # Center the character
    try:
        bbox = draw.textbbox((0, 0), ch, font=font)
    except Exception:
        bbox = (0, 0, 8, 16)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    if text_w <= 0 or text_h <= 0:
        text_w, text_h = 4, 16
    x = (canvas_w - text_w) // 2 - bbox[0]
    y = (canvas_h - text_h) // 2 - bbox[1]
    draw.text((x, y), ch, font=font, fill=0)

    # Crop to ink box (find dark pixels)
    pixels = img.load()
    min_x, min_y = canvas_w, canvas_h
    max_x, max_y = 0, 0
    found_dark = False
    for py in range(canvas_h):
        for px in range(canvas_w):
            if pixels[px, py] < 128:
                found_dark = True
                if px < min_x: min_x = px
                if px > max_x: max_x = px
                if py < min_y: min_y = py
                if py > max_y: max_y = py

    if not found_dark:
        # Empty glyph (space, etc.)
        return [0] * GLYPH_H

    # Crop the image to the ink box
    cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    cw, ch_h = cropped.size

    # Resize to fit within 8x16 while preserving aspect ratio
    target_w = GLYPH_W
    target_h = GLYPH_H
    # Scale to fit
    scale = min(target_w / cw, target_h / ch_h)
    new_w = max(1, int(round(cw * scale)))
    new_h = max(1, int(round(ch_h * scale)))
    # Use nearest-neighbor for crisp edges (no antialiasing)
    resized = cropped.resize((new_w, new_h), Image.NEAREST)
    # Center in the 8x16 frame
    final = Image.new("L", (target_w, target_h), 255)
    final.paste(resized, ((target_w - new_w) // 2, (target_h - new_h) // 2))

    # Threshold and pack into bytes
    pixels = final.load()
    rows = []
    for py in range(target_h):
        byte = 0
        for px in range(target_w):
            if pixels[px, py] < 128:
                byte |= (0x80 >> px)
        rows.append(byte)
    return rows


def fmt_byte_array(name: str, rows: list[int]) -> str:
    """Format a single glyph's bitmap as a C++ static const uint8_t array."""
    # Note: namespace-scope (not class member) — this avoids having to
    # forward-declare 95 static members in software_renderer.h.
    lines = [f"static const uint8_t {name}[16] = {{"]
    for i, byte in enumerate(rows):
        comment = f"// row {i:2d}"
        lines.append(f"    0x{byte:02X}, {comment}")
    lines.append("};")
    return "\n".join(lines)


def main():
    font_path = pick_font()
    # Size 12 keeps the glyph inside the 8x16 frame nicely
    font = ImageFont.truetype(font_path, 12)

    glyphs = {}
    for ch in GLYPH_CHARS:
        rows = render_glyph(ch, font)
        # Sanitize name: char (32..126) → ASCII identifier
        if ch == " ":
            name = "space"
        elif ch.isalpha() or ch.isdigit():
            name = ch
        elif ch == "!":
            name = "excl"
        elif ch == '"':
            name = "quote"
        elif ch == "#":
            name = "hash"
        elif ch == "$":
            name = "dollar"
        elif ch == "%":
            name = "percent"
        elif ch == "&":
            name = "amp"
        elif ch == "'":
            name = "apos"
        elif ch == "(":
            name = "lparen"
        elif ch == ")":
            name = "rparen"
        elif ch == "*":
            name = "star"
        elif ch == "+":
            name = "plus"
        elif ch == ",":
            name = "comma"
        elif ch == "-":
            name = "minus"
        elif ch == ".":
            name = "dot"
        elif ch == "/":
            name = "slash"
        elif ch == ":":
            name = "colon"
        elif ch == ";":
            name = "semicolon"
        elif ch == "<":
            name = "lt"
        elif ch == "=":
            name = "eq"
        elif ch == ">":
            name = "gt"
        elif ch == "?":
            name = "question"
        elif ch == "@":
            name = "at"
        elif ch == "[":
            name = "lbracket"
        elif ch == "\\":
            name = "backslash"
        elif ch == "]":
            name = "rbracket"
        elif ch == "^":
            name = "caret"
        elif ch == "_":
            name = "underscore"
        elif ch == "`":
            name = "backtick"
        elif ch == "{":
            name = "lbrace"
        elif ch == "|":
            name = "pipe"
        elif ch == "}":
            name = "rbrace"
        elif ch == "~":
            name = "tilde"
        else:
            name = f"_{ord(ch):02x}"
        glyphs[ch] = (name, rows)

    # Header file with all bitmaps
    out_lines = [
        "// AUTO-GENERATED by /home/z/my-project/scripts/gen_bitmap_font.py",
        "// EXP-092: Bitmap Font Data for MiniAndroid Software Renderer",
        "//",
        "// This file contains 8x16 pixel bitmaps for all 95 printable ASCII",
        "// characters (32..126). Each glyph is stored as 16 bytes (one per row),",
        "// with each byte's 8 bits (MSB first) indicating which columns are dark.",
        "//",
        "// Generated from: " + font_path,
        "// Do NOT edit by hand — regenerate via:",
        "//   python3 /home/z/my-project/scripts/gen_bitmap_font.py",
        "",
        "#pragma once",
        "",
        "#include <cstdint>",
        "",
        "namespace miniandroid {",
        "namespace renderer {",
        "",
    ]
    # Emit each glyph bitmap
    for ch in GLYPH_CHARS:
        name, rows = glyphs[ch]
        out_lines.append(f"// ASCII {ord(ch)} = '{ch if ch != '*' else '*'}' (glyph name: {name})")
        out_lines.append(fmt_byte_array(f"{name}_bitmap" if False else f"glyph_{name}_bitmap", rows))
        out_lines.append("")

    # Emit the lookup table that maps char index → glyph bitmap pointer
    out_lines.append("// Lookup table: index i (0..94) corresponds to ASCII (i+32)")
    out_lines.append("// Each entry is a pointer to the bitmap data and the character.")
    out_lines.append("struct BitmapGlyphEntry {")
    out_lines.append("    char character;")
    out_lines.append("    int width;")
    out_lines.append("    int height;")
    out_lines.append("    int advance;")
    out_lines.append("    const uint8_t* bitmap;")
    out_lines.append("};")
    out_lines.append("")
    out_lines.append("static const BitmapGlyphEntry bitmap_font_table[95] = {")
    for ch in GLYPH_CHARS:
        name, _ = glyphs[ch]
        # advance: space gets 4, alphanumeric gets 7, others get 6 (default)
        if ch == " ":
            advance = 4
        elif ch.isalnum():
            advance = 7
        elif ch in ".,:;'!":
            advance = 3
        elif ch in "l|i":
            advance = 3
        elif ch in "+-*/=<>":
            advance = 6
        else:
            advance = 6
        width = 8  # bitmap is 8 pixels wide
        height = 16
        # Escape the character for a C char literal
        if ch == "\\":
            ch_lit = "'\\\\'"
        elif ch == "'":
            ch_lit = "'\\''"
        else:
            ch_lit = "'" + ch + "'"
        out_lines.append(
            f"    {{ {ch_lit}, "
            f"{width}, {height}, {advance}, glyph_{name}_bitmap }}, // ASCII {ord(ch)}"
        )
    out_lines.append("};")
    out_lines.append("")
    out_lines.append("}  // namespace renderer")
    out_lines.append("}  // namespace miniandroid")
    out_lines.append("")

    OUT.write_text("\n".join(out_lines))
    print(f"Wrote {OUT} ({len(out_lines)} lines, {len(GLYPH_CHARS)} glyphs)")


if __name__ == "__main__":
    main()
