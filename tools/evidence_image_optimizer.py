#!/usr/bin/env python3
"""Evidence image optimizer — the executable arm of the S213 JPEG-by-default policy (#587).

Dependency: Pillow (PIL). Modes:
  inventory   dry-run over tracked images: format/dims/alpha/animation/class/policy verdict
  convert     convert ONE source image to optimized JPEG in a STAGING directory
              (never destructive in-place, never converts JPEG/JPEG-like output again)
  validate    validate one image: extension vs signature, dimensions, size, alpha,
              animation, exception-record fitness
  baseline    generate docs/IMAGE_POLICY_BASELINE.json (adoption-time inventory of
              legacy over-threshold tracked images) from the current tracked tree

Policy (S213, issue #587 comment 6853869494 + GOVERNANCE ADDENDUM):
  * photographic / noisy / raster evidence screenshots -> optimized JPEG by default,
    quality ladder 85 -> 80 -> 75 -> 70, sRGB, optimized+progressive, metadata stripped
  * target <=100 KiB; 100-200 KiB -> automatic second (lower) attempt; >200 KiB must
    fail promotion unless a reviewed per-file exception exists
  * PNG >100 KiB is disallowed by default for photographic/noisy screenshots
  * PNG stays mandatory for: alpha/transparency, diagrams/text/line art, pixel art,
    masks, pixel-exact evidence — these are exceptions, not the default
  * animated GIF/WebP/APNG are NEVER flattened to a still JPEG
  * sources under fixtures/, upstream/, miniandroid/ runtime resources are never
    converted without an explicit separate decision
  * idempotent: JPEG outputs are never recompressed; no derivative chains

Visual metric: RMS-DELTA on a 256x256 grayscale downsample (documented SSIM-equivalent,
reported with max-delta). Lossy conversion NEVER supports byte/pixel-exact claims.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(os.environ.get("MINIANDROID_REPO_ROOT") or Path(__file__).resolve().parents[1])

KIIB = 1024
PNG_LIMIT = 100 * KIIB          # PNG above this needs a narrow exception (or legacy baseline)
PROMOTE_LIMIT = 200 * KIIB      # any promoted evidence image above this fails without exception
DEFAULT_LADDER = (85, 80, 75, 70)
NEVER_CONVERT_PREFIXES = ("fixtures/", "upstream/", "miniandroid/")
NEVER_CONVERT_EXTS = (".gif",)  # animations are preserved; webp/apng detected by signature
IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sniff_signature(path):
    with open(path, "rb") as f:
        head = f.read(16)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if head.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "GIF"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "WEBP"
    if head.startswith(b"BM"):
        return "BMP"
    return "UNKNOWN"


def inspect_image(path):
    """Full structural inspection + S213 class + policy verdict for one image."""
    p = Path(path)
    st = p.stat()
    info = {
        "path": str(p), "bytes": st.st_size, "sha256": sha256_file(p),
        "extension": p.suffix.lower().lstrip("."),
    }
    sig = sniff_signature(p)
    info["signature"] = sig
    info["extension_matches_signature"] = (
        sig == {"jpg": "JPEG", "jpeg": "JPEG"}.get(info["extension"], info["extension"].upper())
        or (sig == "UNKNOWN")
    )
    img = Image.open(p)
    info["dimensions"] = "%dx%d" % img.size
    info["mode"] = img.mode
    info["has_alpha"] = bool(img.mode in ("RGBA", "LA", "PA")
                             or (img.mode == "P" and "transparency" in img.info))
    n_frames = 1
    try:
        n_frames = getattr(img, "n_frames", 1)
    except Exception:
        n_frames = 1
    info["animated"] = bool(n_frames > 1)
    info["frames"] = n_frames
    info["duration_ms_total"] = None
    if info["animated"]:
        try:
            info["duration_ms_total"] = sum(f.info.get("duration", 0) for f in ImageSequence.Iterator(img))
        except Exception:
            pass
    info["image_class"], info["class_reason"] = classify_image(img)
    info["policy_verdict"], info["policy_reason"] = policy_verdict(info)
    return info


def classify_image(img):
    """Classify PHOTO_NOISY / DIAGRAM_LINEART / PIXEL_ART / ANIMATION / ALPHA_PRESERVED."""
    if getattr(img, "n_frames", 1) > 1:
        return "ANIMATION", "multi-frame; animation format must be preserved"
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        return "ALPHA_PRESERVED", "alpha channel; JPEG cannot preserve transparency"
    rgb = img.convert("RGB")
    # sample on a bounded copy for color statistics
    sample = rgb
    if max(rgb.size) > 512:
        sample = rgb.copy()
        sample.thumbnail((512, 512))
    colors = sample.getcolors(maxcolors=1 << 17)
    if colors is None:
        n_colors = None  # more than 128k distinct sampled colors
    else:
        n_colors = len(colors)
    if n_colors is None:
        return "PHOTO_NOISY", ">128k sampled distinct colors (photographic/noisy raster)"
    if max(img.size) <= 256 and n_colors <= 64:
        return "PIXEL_ART", "small canvas with very low color count (sprite/pixel art)"
    if n_colors <= 1024:
        return "DIAGRAM_LINEART", "low color count; diagram/text/line-art PNG candidate"
    return "PHOTO_NOISY", "high color count (%d sampled colors)" % n_colors


def policy_verdict(info):
    """S213 verdict for one image. NEVER-PROMOTE >200KiB without exception."""
    size = info["bytes"]
    ext = info["extension"]
    cls = info["image_class"]
    if cls == "ANIMATION":
        return (("KEEP_ANIMATION" if size <= PROMOTE_LIMIT
                 else "EXCEPTION_REQUIRED_OVER_200KIB"),
                "animated asset; preserve format, optimize frames/palette only")
    if cls in ("ALPHA_PRESERVED", "PIXEL_ART", "DIAGRAM_LINEART"):
        if size <= PNG_LIMIT:
            return "OK", "%s lossless asset within budget" % cls
        return "PNG_EXCEPTION_REQUIRED", \
               "%s asset above 100 KiB: narrow per-file exception (owner/reason/review) required" % cls
    # PHOTO_NOISY
    if ext in ("jpg", "jpeg"):
        if size <= PROMOTE_LIMIT:
            return "OK", "JPEG within promotion budget"
        return "JPEG_EXCEPTION_REQUIRED_OVER_200KIB", \
               "promoted JPEG above 200 KiB fails without a reviewed per-file exception"
    if size <= PNG_LIMIT:
        return "MIGRATE_TO_JPEG", "photographic PNG within budget but JPEG is the storage default"
    if size <= PROMOTE_LIMIT:
        return "MIGRATE_TO_JPEG", \
               "photographic PNG above 100 KiB — JPEG-by-default policy applies (ladder 85->70)"
    return "REJECT_PROMOTION", \
           "photographic PNG above 200 KiB — promotion fails; convert to JPEG or record exception"


def rms_delta(img_a, img_b, box=(256, 256)):
    """Documented SSIM-equivalent metric: RMS + max delta of grayscale downsample."""
    a = img_a.convert("L")
    b = img_b.convert("L")
    if a.size != box:
        a = a.resize(box)
    if b.size != box:
        b = b.resize(box)
    pa, pb = list(a.getdata()), list(b.getdata())
    diffs = [x - y for x, y in zip(pa, pb)]
    n = len(diffs)
    rms = (sum(d * d for d in diffs) / n) ** 0.5
    mx = max(abs(d) for d in diffs)
    return round(rms, 3), int(mx)


def convert_to_jpeg(source, staging_dir, ladder=DEFAULT_LADDER, resize_max=None):
    """Convert one photographic/noisy image to JPEG in staging. Returns a report dict.

    Non-destructive: the source is never modified; output goes to staging_dir.
    Refuses: JPEG inputs (idempotence), animations, alpha-preserving images,
    fixtures/upstream/miniandroid runtime resources.
    """
    src = Path(source)
    rep = {"source": str(src), "source_sha256": sha256_file(src),
           "source_bytes": src.stat().st_size, "converted": False}
    if src.suffix.lower() in (".jpg", ".jpeg"):
        rep["reason"] = "already JPEG — idempotent skip (no recompression, no derivative chains)"
        return rep
    if str(src).startswith(tuple(str(ROOT / p) for p in NEVER_CONVERT_PREFIXES)) or \
            any(str(src).startswith(p) for p in NEVER_CONVERT_PREFIXES):
        rep["reason"] = "protected area (fixtures/upstream/miniandroid runtime) — never converted here"
        return rep
    img = Image.open(src)
    cls, why = classify_image(img)
    rep["image_class"] = cls
    rep["dimensions"] = "%dx%d" % img.size
    if cls == "ANIMATION":
        rep["reason"] = "animated asset — never flattened to a still JPEG; " + why
        return rep
    if cls in ("ALPHA_PRESERVED", "PIXEL_ART"):
        rep["reason"] = "lossless-required class (%s) — JPEG conversion refused: %s" % (cls, why)
        return rep
    if img.mode in ("RGBA", "LA", "P") and (
            img.mode in ("RGBA", "LA") or "transparency" in img.info):
        rep["reason"] = "alpha channel present — JPEG cannot preserve transparency; refused"
        return rep
    work = img.convert("RGB")
    if resize_max and max(work.size) > resize_max:
        work = work.copy()
        work.thumbnail((resize_max, resize_max), Image.LANCZOS)
        rep["resized_to"] = "%dx%d" % work.size
    staging = Path(staging_dir)
    staging.mkdir(parents=True, exist_ok=True)
    out_path = staging / (src.stem + ".jpg")
    attempts = []
    best = None
    scale_ladder = [1.0, 0.75, 0.5] if resize_max is None else [None]
    for scale in scale_ladder:
        work_s = work
        if scale and scale < 1.0:
            w = max(1, int(work.size[0] * scale))
            h = max(1, int(work.size[1] * scale))
            work_s = work.resize((w, h), Image.LANCZOS)
            rep["resized_to"] = "%dx%d" % work_s.size
        for q in ladder:
            buf = io.BytesIO()
            work_s.save(buf, format="JPEG", quality=q, optimize=True, progressive=True)
            size = buf.tell()
            attempts.append({"quality": q, "bytes": size, "scale": scale})
            if size <= PROMOTE_LIMIT:
                best = (q, buf.getvalue(), size, work_s)
                if size <= 100 * KIIB:
                    break
            # >200 KiB at this rung: record and continue down the ladder
        if best is not None:
            break
    if best is None:
        rep["reason"] = ("no ladder rung reached <=200 KiB (ladder %s, resize ladder %s) "
                         "— promotion rejected" % (ladder, scale_ladder))
        rep["attempts"] = attempts
        return rep
    q, payload, size, out_work = best
    out_path.write_bytes(payload)
    out_img = Image.open(out_path)
    rms, mx = rms_delta(out_work, out_img)
    rep.update({
        "converted": True, "output": str(out_path), "output_bytes": size,
        "output_sha256": hashlib.sha256(payload).hexdigest(),
        "quality": q, "ladder_attempts": attempts,
        "settings": "JPEG sRGB q=%d optimize progressive, metadata stripped" % q,
        "output_dimensions": "%dx%d" % out_img.size,
        "size_delta_bytes": size - rep["source_bytes"],
        "compression_ratio": round(rep["source_bytes"] / max(size, 1), 2),
        "visual_metric": "RMS-DELTA(gray 256x256 downsample)=%.3f max_delta=%d" % (rms, mx),
        "provenance": "source SHA-256 %s; lossy conversion — never a pixel-exact claim" % rep["source_sha256"],
    })
    return rep


def tracked_images(prefixes=None):
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    files = [l for l in out.stdout.splitlines() if l.lower().endswith(IMG_EXTS)]
    if prefixes:
        files = [f for f in files if any(f.startswith(p) for p in prefixes)]
    return files


def cmd_inventory(args):
    rows = []
    for f in tracked_images(args.paths):
        try:
            info = inspect_image(ROOT / f)
            info["path"] = f
            rows.append(info)
        except Exception as e:
            rows.append({"path": f, "error": str(e), "policy_verdict": "INSPECT_ERROR"})
    by_verdict = {}
    for r in rows:
        by_verdict.setdefault(r.get("policy_verdict", "?"), []).append(r)
    print("tracked images inspected: %d" % len(rows))
    for v in sorted(by_verdict):
        n = len(by_verdict[v])
        total = sum(r.get("bytes", 0) for r in by_verdict[v])
        print("  %-32s %4d files  %12d bytes" % (v, n, total))
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=1))
        print("inventory written: %s" % args.json)
    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["path", "bytes", "extension", "signature",
                                               "dimensions", "mode", "has_alpha", "animated",
                                               "frames", "image_class", "policy_verdict",
                                               "policy_reason", "sha256"])
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in w.fieldnames})
        print("inventory written: %s" % args.csv)
    fail = [v for v in by_verdict if v in ("REJECT_PROMOTION", "JPEG_EXCEPTION_REQUIRED_OVER_200KIB")]
    return 1 if (args.strict and fail) else 0


def cmd_convert(args):
    reps = []
    for src in args.sources:
        reps.append(convert_to_jpeg(src, args.staging, tuple(args.ladder), args.resize_max))
    ok = True
    for r in reps:
        print(json.dumps(r, indent=1))
        if r.get("policy_verdict") == "REJECT_PROMOTION" or (not r.get("converted") and not r.get("reason")):
            ok = False
    if args.report:
        Path(args.report).write_text(json.dumps(reps, indent=1))
        print("conversion report written: %s" % args.report)
    return 0


def cmd_validate(args):
    bad = 0
    for f in args.files:
        try:
            info = inspect_image(f)
        except Exception as e:
            print("FAIL VALIDATE %s: unreadable/corrupt (%s)" % (f, e))
            bad += 1
            continue
        verdict, why = info["policy_verdict"], info["policy_reason"]
        line = "%s %s [%s] %s bytes %s" % (verdict, f, info["image_class"], info["bytes"], info["dimensions"])
        if verdict in ("REJECT_PROMOTION", "JPEG_EXCEPTION_REQUIRED_OVER_200KIB", "INSPECT_ERROR"):
            print("FAIL " + line + " — " + why)
            bad += 1
        elif verdict in ("MIGRATE_TO_JPEG", "PNG_EXCEPTION_REQUIRED", "EXCEPTION_REQUIRED_OVER_200KIB"):
            print("WARN " + line + " — " + why)
        else:
            print("OK   " + line)
    return 1 if bad else 0


def cmd_baseline(args):
    rows = []
    for f in tracked_images():
        try:
            st = (ROOT / f).stat()
            size = st.st_size
            try:
                info = inspect_image(ROOT / f)
            except Exception as e:
                rows.append({
                    "path": f, "bytes": size, "sha256": None, "extension": Path(f).suffix.lower().lstrip("."),
                    "image_class": "UNREADABLE_CORRUPT", "policy_verdict": "UNREADABLE_CORRUPT",
                    "owner": "S213 adoption baseline (#587)",
                    "reason": "unreadable/corrupt or empty image at S213 adoption (%s); "
                              "disposition (DELETE_CANDIDATE) required at migration wave" % type(e).__name__,
                    "review_trigger": "incremental migration wave tracked in #386",
                })
                continue
            if info["policy_verdict"] in ("OK", "KEEP_ANIMATION", "MIGRATE_TO_JPEG") \
                    and info["bytes"] <= PNG_LIMIT:
                continue
            rows.append({
                "path": f,
                "bytes": info["bytes"],
                "sha256": info["sha256"],
                "extension": info["extension"],
                "image_class": info["image_class"],
                "policy_verdict": info["policy_verdict"],
                "owner": "S213 adoption baseline (#587)",
                "reason": "legacy asset present at S213 adoption; per-path record, not a blanket exception",
                "review_trigger": "incremental migration wave tracked in #386",
            })
        except OSError:
            continue
    doc = {
        "_meta": {
            "law": "S213 image policy (#587 comment 6853869494) + tools/evidence_image_optimizer.py",
            "generated": "2026-11-13",
            "rules": [
                "per-path legacy inventory at policy adoption; NOT a blanket folder/extension exception",
                "every entry expires at the incremental migration wave (tracked in #386)",
                "new files are never covered by this baseline; they must pass the policy or hold a narrow exception",
            ],
            "count": len(rows),
            "total_bytes": sum(r["bytes"] for r in rows),
        },
        "legacy_images": rows,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(doc, indent=1))
        print("baseline written: %s (%d entries, %d bytes)" % (args.out, len(rows), doc["_meta"]["total_bytes"]))
    else:
        print(json.dumps(doc["_meta"], indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inventory", help="dry-run inventory of tracked images")
    p.add_argument("--paths", nargs="*", default=None, help="restrict to path prefixes")
    p.add_argument("--json"); p.add_argument("--csv"); p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_inventory)
    p = sub.add_parser("convert", help="convert sources to staged JPEG (non-destructive)")
    p.add_argument("sources", nargs="+")
    p.add_argument("--staging", required=True)
    p.add_argument("--ladder", nargs="*", type=int, default=list(DEFAULT_LADDER))
    p.add_argument("--resize-max", type=int, default=None)
    p.add_argument("--report")
    p.set_defaults(func=cmd_convert)
    p = sub.add_parser("validate", help="validate image files against the S213 policy")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=cmd_validate)
    p = sub.add_parser("baseline", help="generate the adoption baseline JSON")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_baseline)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
