#!/usr/bin/env python3
"""S213 tests for tools/evidence_image_optimizer.py (#587 comment 6853869494 item B.6).

Covers all eight required cases:
  1. JPEG input                    -> idempotent skip (no recompression)
  2. large noisy PNG               -> PHOTO_NOISY, MIGRATE_TO_JPEG, converts below 200 KiB
  3. transparent PNG               -> ALPHA_PRESERVED, conversion refused
  4. pixel-art / diagram PNG       -> PIXEL_ART / DIAGRAM_LINEART, lossless keep, no conversion
  5. GIF animation                 -> ANIMATION, never flattened
  6. corrupt input                 -> validate FAIL (unreadable), inventory-safe
  7. duplicate output              -> convert twice = identical staged output, no chain
  8. already-small image           -> OK / within budget
Plus: staging is non-destructive (source bytes unchanged), SHA mapping recorded.
"""
import hashlib
import io
import os
import random
import struct
import sys
import tempfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
os.environ.setdefault("MINIANDROID_REPO_ROOT", str(Path(__file__).resolve().parents[1]))

import unittest
from PIL import Image

import evidence_image_optimizer as opt


def make_png(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def write(tmp, name, data):
    p = Path(tmp) / name
    p.write_bytes(data)
    return p


class EvidenceImageOptimizerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="eio_test_")
        self.staging = Path(self.tmp) / "staging"
        self.rng = random.Random(207)

    # 1. JPEG input: idempotent skip ------------------------------------------------
    def test_jpeg_input_is_skipped(self):
        img = Image.new("RGB", (64, 64), (10, 20, 30))
        p = write(self.tmp, "plain.jpg", _jpeg_bytes(img, 85))
        rep = opt.convert_to_jpeg(p, self.staging)
        self.assertFalse(rep["converted"])
        self.assertIn("idempotent", rep["reason"])

    # 2. large noisy PNG: photographic, migrates below 200 KiB ----------------------
    def test_large_noisy_png_converts(self):
        noise = Image.frombytes("RGB", (900, 700),
                                bytes(self.rng.randrange(256) for _ in range(900 * 700 * 3)))
        p = write(self.tmp, "noisy.png", make_png(noise))
        self.assertGreater(p.stat().st_size, 100 * 1024)
        info = opt.inspect_image(p)
        self.assertEqual(info["image_class"], "PHOTO_NOISY")
        # >200 KiB photographic PNG tracked state: promotion rejected without exception
        self.assertEqual(info["policy_verdict"], "REJECT_PROMOTION")
        # the converter rescues it: ladder lands a compliant staged JPEG
        rep = opt.convert_to_jpeg(p, self.staging)
        self.assertTrue(rep["converted"])
        self.assertLess(rep["output_bytes"], 200 * 1024)
        self.assertLess(rep["output_bytes"], rep["source_bytes"])
        self.assertIn("RMS-DELTA", rep["visual_metric"])
        self.assertTrue(rep["output"].startswith(str(self.staging)))
        # provenance mapping present
        self.assertEqual(rep["source_sha256"], hashlib.sha256(p.read_bytes()).hexdigest())

    # 3. transparent PNG: alpha preserved, conversion refused -----------------------
    def test_transparent_png_refused(self):
        img = Image.new("RGBA", (640, 480), (200, 30, 30, 128))
        p = write(self.tmp, "alpha.png", make_png(img))
        info = opt.inspect_image(p)
        self.assertTrue(info["has_alpha"])
        self.assertEqual(info["image_class"], "ALPHA_PRESERVED")
        rep = opt.convert_to_jpeg(p, self.staging)
        self.assertFalse(rep["converted"])
        self.assertIn("alpha", rep["reason"].lower())

    # 4. pixel-art / diagram PNG: lossless keep -------------------------------------
    def test_pixel_art_and_diagram_kept(self):
        art = Image.new("P", (64, 64))
        pal = []
        for i in range(16):
            pal.extend([i * 16, 255 - i * 16, i * 8])
        art.putpalette(pal)
        art.putdata([self.rng.randrange(16) for _ in range(64 * 64)])
        p_art = write(self.tmp, "pixel.png", make_png(art))
        info = opt.inspect_image(p_art)
        self.assertEqual(info["image_class"], "PIXEL_ART")
        verdict, _ = opt.policy_verdict(info)
        self.assertEqual(verdict, "OK")
        rep = opt.convert_to_jpeg(p_art, self.staging)
        self.assertFalse(rep["converted"])
        self.assertIn("lossless-required", rep["reason"])

        diagram = Image.new("RGB", (1400, 900), (255, 255, 255))
        px = diagram.load()
        for x in range(0, 1400, 7):
            for y in range(0, 900, 3):
                px[x, y] = (40, 40, 40)
        p_diag = write(self.tmp, "diagram.png", make_png(diagram))
        info = opt.inspect_image(p_diag)
        self.assertEqual(info["image_class"], "DIAGRAM_LINEART")

    # 5. GIF animation: never flattened ---------------------------------------------
    def test_gif_animation_preserved(self):
        frames = [Image.new("P", (120, 90), c) for c in ((255, 0, 0), (0, 255, 0), (0, 0, 255))]
        buf = io.BytesIO()
        frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=100)
        p = write(self.tmp, "anim.gif", buf.getvalue())
        info = opt.inspect_image(p)
        self.assertTrue(info["animated"])
        self.assertEqual(info["frames"], 3)
        self.assertEqual(info["image_class"], "ANIMATION")
        rep = opt.convert_to_jpeg(p, self.staging)
        self.assertFalse(rep["converted"])
        self.assertIn("never flattened", rep["reason"])

    # 6. corrupt input: FAIL validation, no crash -----------------------------------
    def test_corrupt_input_fails_validation(self):
        p = write(self.tmp, "corrupt.png", b"\x89PNG\r\n\x1a\n" + b"garbage" * 40)
        rc = opt.cmd_validate(arg_files(str(p)))
        self.assertEqual(rc, 1)

    # 7. duplicate output: deterministic + idempotent --------------------------------
    def test_duplicate_output_deterministic(self):
        noise = Image.frombytes("RGB", (500, 400),
                                bytes(self.rng.randrange(256) for _ in range(500 * 400 * 3)))
        p = write(self.tmp, "dup.png", make_png(noise))
        r1 = opt.convert_to_jpeg(p, self.staging)
        h1 = hashlib.sha256(Path(r1["output"]).read_bytes()).hexdigest()
        r2 = opt.convert_to_jpeg(p, self.staging)  # second run overwrites same staging path
        self.assertTrue(r2["converted"])
        self.assertEqual(r2["output"], r1["output"])
        self.assertEqual(r2["output_sha256"], r1["output_sha256"])  # deterministic bytes
        self.assertEqual(r2["source_sha256"], r1["source_sha256"])
        # and converting the produced JPEG again is a no-op (no derivative chains)
        r3 = opt.convert_to_jpeg(Path(r1["output"]), Path(self.staging) / "gen2")
        self.assertFalse(r3["converted"])
        self.assertIn("idempotent", r3["reason"])

    # 8. already-small image: OK ------------------------------------------------------
    def test_already_small_image_ok(self):
        img = Image.new("RGB", (80, 60), (5, 6, 7))
        p = write(self.tmp, "small.png", make_png(img))
        info = opt.inspect_image(p)
        verdict, _ = opt.policy_verdict(info)
        self.assertEqual(verdict, "OK")

    # staging non-destructive ----------------------------------------------------------
    def test_source_never_modified(self):
        noise = Image.frombytes("RGB", (300, 300),
                                bytes(self.rng.randrange(256) for _ in range(300 * 300 * 3)))
        p = write(self.tmp, "safe.png", make_png(noise))
        before = (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
        opt.convert_to_jpeg(p, self.staging)
        after = (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
        self.assertEqual(before, after)


def _jpeg_bytes(img, q):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=q)
    return buf.getvalue()


def arg_files(*paths):
    """Build a minimal args namespace for cmd_validate."""
    return type("A", (), {"files": list(paths)})()


if __name__ == "__main__":
    unittest.main(verbosity=2)
