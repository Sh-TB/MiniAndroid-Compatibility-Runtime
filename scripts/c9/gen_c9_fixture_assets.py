#!/usr/bin/env python3
"""scripts/c9/gen_c9_fixture_assets.py — deterministic binary assets for the
CODER 9 resources harness (tests/fixtures/c9_resources).

Everything is generated from fixed constants (no randomness, no network):
  res/drawable-hdpi/c9_photo.png   60x30 GREEN hdpi pattern
  res/drawable-mdpi/c9_photo.png   40x20 RED mdpi pattern
  res/drawable-nodpi/c9_nodpi.png  40x20 GREEN nodpi pattern
  res/drawable/c9_webp.webp        24x12 blue lossless WebP
  res/raw/c9_invalid.dat           invalid image bytes (NOT decodable)
  assets/sub/deep/c9_nested.bin    29 bytes, head "C9-NESTE"
  assets/c9_compressed.txt         2000 'z' bytes (post-pinned DEFLATE)
  assets/c9_stored.bin             115 bytes (post-pinned STORED, AFD case)
  assets/fonts/c9_font.ttf         DejaVuSans.ttf copy (host system font)

Idempotent: safe to re-run; identical bytes every run.
"""
import os
import shutil
import zlib
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.normpath(os.path.join(
    HERE, "..", "..", "miniandroid", "tests", "fixtures", "c9_resources"))


def png_chunk(tag: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def write_png(path: str, w: int, h: int, pixel_fn) -> None:
    raw = b"".join(b"\x00" + bytes(v for x in range(w) for v in pixel_fn(x, y))
                   for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8-bit RGB
    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
           + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def main() -> None:
    # Density patterns — deliberately DIFFERENT colors per bucket so the §6
    # pixel law proves WHICH bucket was selected at the framebuffer level.
    green = lambda x, y: (0x2E, 0xB8, 0x4E)                     # hdpi pattern
    red = lambda x, y: (0xD8, 0x3A, 0x2E)                       # mdpi pattern

    write_png(os.path.join(FIXTURE, "res/drawable-hdpi/c9_photo.png"), 60, 30, green)
    write_png(os.path.join(FIXTURE, "res/drawable-mdpi/c9_photo.png"), 40, 20, red)
    write_png(os.path.join(FIXTURE, "res/drawable-nodpi/c9_nodpi.png"), 40, 20, green)

    from PIL import Image
    img = Image.new("RGB", (24, 12), (30, 144, 255))            # blue webp
    webp_path = os.path.join(FIXTURE, "res/drawable/c9_webp.webp")
    os.makedirs(os.path.dirname(webp_path), exist_ok=True)
    img.save(webp_path, "WEBP", lossless=True)

    # Invalid image: plausible magic then garbage — decoders must answer null.
    os.makedirs(os.path.join(FIXTURE, "res/raw"), exist_ok=True)  # S179 intake repair: dir was never created (posted harness omission)
    with open(os.path.join(FIXTURE, "res/raw/c9_invalid.dat"), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\xff" * 31)

    nested = (b"C9-NESTED-ASSET-DATA-OK!\x01\x02\x03\x04\x05")   # 29 bytes
    assert len(nested) == 29
    os.makedirs(os.path.join(FIXTURE, "assets/sub/deep"), exist_ok=True)
    with open(os.path.join(FIXTURE, "assets/sub/deep/c9_nested.bin"), "wb") as f:
        f.write(nested)

    with open(os.path.join(FIXTURE, "assets/c9_compressed.txt"), "wb") as f:
        f.write(b"z" * 2000)

    stored = (b"C9-STORED-ASSET-FD-LAW " + bytes(range(48, 48 + 89)) + b"END")
    assert len(stored) == 115
    with open(os.path.join(FIXTURE, "assets/c9_stored.bin"), "wb") as f:
        f.write(stored)

    font_src = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font_dst = os.path.join(FIXTURE, "assets/fonts/c9_font.ttf")
    os.makedirs(os.path.dirname(font_dst), exist_ok=True)
    if not os.path.exists(font_dst):
        shutil.copyfile(font_src, font_dst)

    print("C9 fixture assets generated at", FIXTURE)


if __name__ == "__main__":
    main()
