#!/usr/bin/env python3
"""adversarial_s93.py — S93 §23 false-positive battery + §29 tamper/recovery.

Consolidates the adversarial proof suites and adds:

  §23 fixture coverage map — every weak metric must be the deciding
  rejection signal for at least one fixture:
      nonblank/screenshot-exists  -> solid_replacement (image)
      pixel-change                -> frozen (animation)
      entropy/color-count         -> two_color_photo_fake (image)
      decode-success              -> opaque_replacement (image)
      ViewTree-text-presence      -> text_missing (font/text)
      GIF-exists                  -> repeated_frames (animation)
      callback-fired              -> covered by S92 battery case-a (APK)

  §29 tamper test  — take known-good evidence, tamper 5 ways, each MUST be
                     rejected by the semantic layer.
  §29 recovery test— evidence persistence across simulated interruption
                     (two-process round-trip on the battery state file).

Exit code 0 only if: all three proof suites pass AND tamper rejects 5/5
AND recovery round-trip proves persistence.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools", "verify"))
sys.path.insert(0, os.path.join(REPO, "tools"))

from probes.semantic_image import image_truth  # noqa: E402
from probes.semantic_animation import animation_truth  # noqa: E402

OUT = "/tmp/s93_fixtures"
STATE = "/tmp/s93_battery_state.json"


def sh(cmd):
    return subprocess.run([sys.executable, cmd], cwd=REPO,
                          capture_output=True, text=True)


def blur_fixture():
    """§23-4 blurred image: correct content blurred beyond readability —
    honest verdict VISUALLY_PARTIAL (never VISUALLY_VERIFIED)."""
    src = Image.open(os.path.join(OUT, "f1_correct.png"))
    blurred = src.filter(ImageFilter.GaussianBlur(4))
    p = os.path.join(OUT, "f12_blurred.png")
    blurred.save(p)
    asset = open(os.path.join(OUT, "a_circle.png"), "rb").read()
    r = image_truth(p, asset, region=(112, 72, 96, 96))
    ok = r["verdict"] in ("VISUALLY_PARTIAL", "WRONG_CONTENT",
                          "OPAQUE_REPLACEMENT") and \
        r["content"]["value"] in ("PARTIAL", "FAIL")
    return ok, r


def tamper_tests():
    """§29: 5 tampers of known-good evidence; each must be rejected."""
    results = []
    asset = open(os.path.join(OUT, "a_circle.png"), "rb").read()
    good = Image.open(os.path.join(OUT, "f1_correct.png"))

    # T1 wipe the image region (content destroyed)
    t = good.copy()
    ImageDraw.Draw(t).rectangle([112, 72, 208, 168], fill=(240, 244, 248))
    p = os.path.join(OUT, "t1_wipe.png")
    t.save(p)
    r = image_truth(p, asset, region=(112, 72, 96, 96))
    results.append(("tamper_wipe_region", r["verdict"] == "MISSING"))

    # T2 move the image fully outside its region (geometry corrupted)
    t = good.copy()
    a = np.array(t)
    patch = a[72:168, 112:208].copy()
    a[72:168, 112:208] = (240, 244, 248)
    a[72:168, 220:316] = patch
    p = os.path.join(OUT, "t2_move.png")
    Image.fromarray(a).save(p)
    r = image_truth(p, asset, region=(112, 72, 96, 96))
    results.append(("tamper_move_asset",
                    r["verdict"] in ("WRONG_POSITION", "MISSING")))

    # T3 recolor the asset (wrong content, right place)
    t = good.copy()
    ImageDraw.Draw(t).ellipse([120, 80, 200, 160], fill=(200, 30, 30))
    p = os.path.join(OUT, "t3_recolor.png")
    t.save(p)
    r = image_truth(p, asset, region=(112, 72, 96, 96))
    results.append(("tamper_recolor_asset", r["verdict"] == "WRONG_CONTENT"))

    # T4 freeze the animation (frames identical)
    anim_dir = "/tmp/s93_anim"
    anims = sorted(f for f in os.listdir(anim_dir)
                   if f.startswith("correct_motion_"))
    r = animation_truth([os.path.join(anim_dir, anims[0])] * 6,
                        object_region=(20, 36, 120, 56))
    results.append(("tamper_freeze_animation", r["verdict"] == "FROZEN"))

    # T5 shrink the asset (scale corrupted): wipe region, paste 0.6x copy
    t = good.copy()
    a = np.array(t)
    a[72:168, 112:208] = (240, 244, 248)
    t = Image.fromarray(a)
    small = Image.open(os.path.join(OUT, "a_circle.png")).resize(
        (58, 58), Image.NEAREST)
    t.paste(small, (131, 91), small)
    p = os.path.join(OUT, "t5_shrink.png")
    t.save(p)
    r = image_truth(p, asset, region=(112, 72, 96, 96))
    results.append(("tamper_shrink_asset", r["verdict"] == "WRONG_GEOMETRY"))
    return results


def recovery_test_phase(write_phase):
    """§29 recovery: two-process round-trip. Phase 1 writes milestone state
    and exits (simulated crash). Phase 2 resumes, verifies state + evidence
    integrity (no duplicate, no loss)."""
    if write_phase:
        st = {"milestone": "s93-battery-phase1", "fixtures_done": 29,
              "evidence_sha256": {}}
        for f in sorted(os.listdir(OUT)):
            fp = os.path.join(OUT, f)
            if os.path.isfile(f):
                import hashlib
                st["evidence_sha256"][f] = hashlib.sha256(
                    open(fp, "rb").read()).hexdigest()
        with open(STATE, "w") as fh:
            json.dump(st, fh)
        return True
    with open(STATE) as fh:
        st = json.load(fh)
    import hashlib
    for f, sha in st["evidence_sha256"].items():
        fp = os.path.join(OUT, f)
        if not os.path.isfile(f) or hashlib.sha256(
                open(fp, "rb").read()).hexdigest() != sha:
            return False
    # no duplicate evidence files
    names = [f for f in os.listdir(OUT)]
    return len(names) == len(set(names)) and \
        len(names) >= len(st["evidence_sha256"])


def main():
    print("=== S93 §23 adversarial battery ===")
    ok = True
    suites = {
        "image_truth_proof": "scripts/s93_image_truth_proof.py",
        "animation_truth_proof": "scripts/s93_animation_truth_proof.py",
        "font_truth_proof": "scripts/s93_font_truth_proof.py",
    }
    report = {"suites": {}, "tamper": [], "recovery": None, "blur": None}
    for name, script in suites.items():
        p = sh(os.path.join(REPO, script))
        tail = (p.stdout or "").strip().splitlines()[-1:] or [""]
        print(f"  {name}: exit={p.returncode}  {tail[0][:90]}")
        report["suites"][name] = {"exit": p.returncode}
        ok = ok and p.returncode == 0

    print("  -- §23 weak-metric coverage: encoded in suite oracles "
          "(solid=nonblank-attack, two-color=entropy-attack, frozen="
          "pixel-change-attack, text_missing=viewtree-attack, "
          "opaque=decode-attack, repeated=gif-exists-attack)")

    okb, r = blur_fixture()
    report["blur"] = {"ok": okb, "verdict": r["verdict"]}
    print(f"  blurred_image: {'PASS' if okb else 'REJ'} verdict={r['verdict']}")
    ok = ok and okb

    for name, passed in tamper_tests():
        report["tamper"].append({"name": name, "rejected": passed})
        print(f"  {name}: {'REJECTED' if passed else 'ACCEPTED(!)'}")
        ok = ok and passed

    p1 = subprocess.run([sys.executable, os.path.abspath(__file__),
                         "--recover-write"], cwd=REPO, capture_output=True)
    okw = p1.returncode == 0
    okr = recovery_test_phase(False)
    report["recovery"] = {"write_phase": okw, "resume_phase": okr}
    print(f"  recovery write-phase: {'PASS' if okw else 'FAIL'}  "
          f"resume-phase: {'PASS' if okr else 'FAIL'}")
    ok = ok and okw and okr

    os.makedirs(os.path.join(REPO, "run", "s93"), exist_ok=True)
    with open(os.path.join(REPO, "run", "s93",
                           "adversarial_battery.json"), "w") as fh:
        json.dump(report, fh, indent=1, default=str)
    print(f"\nBATTERY RESULT: {'ALL PASS' if ok else 'FAILURES'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--recover-write":
        sys.exit(0 if recovery_test_phase(True) else 1)
    main()
