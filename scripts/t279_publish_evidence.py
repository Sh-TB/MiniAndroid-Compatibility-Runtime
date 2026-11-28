#!/usr/bin/env python3
"""T279 P6 — publish compact evidence: 480px screenshot copies, CSV, SHA ledger.

- Copies every run's screenshot to evidence/t279/shots/<tag>_<rid>.png at
  <=480px longest side (the compact-auditable-evidence law).
- Writes evidence/t279/T279_TWO_RUN_RESULTS.csv (APK identity, two-run
  results, render level, interaction, status, evidence refs).
- Writes evidence/t279/SHA256SUMS.txt over all published artifacts.
"""
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

BASE = Path("/home/z/my-project")
RUN = BASE / "run_t279"
OUT = BASE / "evidence" / "t279"
SHOTS = OUT / "shots"
SHOTS.mkdir(parents=True, exist_ok=True)

MAXSIDE = 480

# render level + interaction + status per campaign results (evidence-derived)
LEVEL = {  # tag: (R-level, interaction, status)
    "gmdice": (3, "state-change", "INTERACTIVE"),
    "bouncy": (3, "state-change", "INTERACTIVE"),
    "librecontactsbackup": (3, "state-change", "INTERACTIVE"),
    "ugaday": (3, "state-change", "INTERACTIVE"),
    "blockinger": (3, "state-change", "INTERACTIVE"),
    "pfdicer": (3, "no-frame-change", "CURRENT-REPRODUCIBLE"),
    "pfsolitaire": (3, "no-frame-change", "CURRENT-REPRODUCIBLE"),
    "textpad": (3, "no-frame-change", "CURRENT-REPRODUCIBLE"),
    "npuzzle": (3, "listener-registered-no-ct-change", "CURRENT-REPRODUCIBLE"),
    "randomix": (2, "listener-registered-no-ct-change", "CURRENT-REPRODUCIBLE"),
    "flip": (3, "not-tested", "CURRENT-REPRODUCIBLE"),
    "diceroller": (3, "not-tested", "CURRENT-REPRODUCIBLE"),
    "uturn": (1, "n/a", "REGRESSED"),
    "wocheneinkauf": (1, "n/a", "REGRESSED"),
    "peri": (1, "n/a", "REGRESSED"),
    "stacktower3d": (1, "no-frame-change", "PARTIAL"),
    "emmanuelttt": (1, "no-frame-change", "PARTIAL"),
    "farmerbb": (1, "n/a", "PARTIAL"),
    "itsfrz": (1, "n/a", "PARTIAL"),
    "janken": (1, "n/a", "BLOCKED"),
    "authsrng": (1, "n/a", "BLOCKED"),
    "minos": (1, "n/a", "PARTIAL"),
    "cocodechess": (1, "n/a", "PARTIAL"),
}
FIRST_DIV = {
    "uturn": "Compose AbstractComposeView.internalOnMeasure$ui ISE (8 uncaught)",
    "wocheneinkauf": "Compose measure frontier ISE (33 uncaught)",
    "peri": "Compose AbstractComposeView.internalOnMeasure$ui ISE (33 uncaught)",
    "stacktower3d": "DEFAULT_BACKGROUND_ONLY px 0 unc 0",
    "emmanuelttt": "DEFAULT_BACKGROUND_ONLY px 0 unc 0",
    "farmerbb": "DataStore/protobuf worker-thread NPE after render (28 uncaught)",
    "itsfrz": "custom-cell listener registration gap (10 uncaught)",
    "janken": "compose composition-state throw null x22 (33 uncaught)",
    "authsrng": "compose convertMeasureSpec ISE + SoftReference.get null (33)",
    "minos": "inflate views=2, content never attaches (FrameLayout children=0)",
    "cocodechess": "DEFAULT_BACKGROUND_ONLY (33 uncaught)",
}
VISUAL_NOTES = {
    "gmdice": "VISUALLY VERIFIED 2026-11-28: real dice UI (Roll it! + dice-type bar)",
    "blockinger": "VISUALLY VERIFIED: Highscores dialog over main menu; DEFECT: dialog button labels render reversed/mirrored",
    "flip": "VISUALLY VERIFIED: coin face (1) + Flip button — vector rasterized, viewtree attached",
    "diceroller": "VISUALLY VERIFIED: die square (00) + Number of Die/Sides labels; DEFECT: initial die shows 00",
    "randomix": "VISUALLY VERIFIED: near-blank AppIntro first slide + bottom chrome (1,080 app px) — R2, not a complete screen",
    "wocheneinkauf": "VISUALLY VERIFIED: uniform cream default background only — face drift e75e653c is a background-tint change, still zero app content",
    "bouncy": "VISUALLY VERIFIED: 'Touch to start' + dark vector-line table; face byte-identical to 2026-11-27 recheck",
    "ugaday": "VISUALLY VERIFIED: 'Guess the number (1-100)' + Put the number button",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    bat = json.load(open(RUN / "T279_TWO_RUN_BATTERY.json"))
    rows = []
    shot_shas = []
    for tag, ent in bat.items():
        lvl, inter, status = LEVEL[tag]
        rs = ent["runs"]
        r1, r2 = rs.get("run_r1", {}), rs.get("run_r2", {})
        c1, c2 = rs.get("run_ct1", {}), rs.get("run_ct2", {})
        # compact copies
        for rid in ("run_r1", "run_r2", "run_ct1", "run_ct2"):
            src = RUN / f"{tag}_{rid.split('_')[1]}" / "screenshot.png"
            if not src.exists():
                continue
            dst = SHOTS / f"{tag}_{rid.split('_')[1]}.png"
            im = Image.open(src)
            w, h = im.size
            if max(w, h) > MAXSIDE:
                sc = MAXSIDE / max(w, h)
                im = im.resize((max(1, int(w * sc)), max(1, int(h * sc))),
                               Image.LANCZOS)
            im.save(dst)
            shot_shas.append((dst.relative_to(BASE).as_posix(), sha256(dst)))
        both_real = (r1.get("class") == "REAL_APP_CONTENT"
                     and r2.get("class") == "REAL_APP_CONTENT")
        repro = ("PASS-IDENTICAL" if r1.get("face") == r2.get("face")
                 else "PASS-CONSISTENT" if both_real else
                 "FAIL-NOT_REPRODUCIBLE")
        rows.append({
            "tag": tag,
            "package": r1.get("pkg", ""),
            "apk": r1.get("apk", ""),
            "type": ent.get("kind", ""),
            "run1_class": r1.get("class", ""),
            "run1_verdict": r1.get("verdict", ""),
            "run1_face16": r1.get("face", ""),
            "run1_app_px": r1.get("app_owned_pixels", ""),
            "run2_class": r2.get("class", ""),
            "run2_face16": r2.get("face", ""),
            "run2_app_px": r2.get("app_owned_pixels", ""),
            "ct1_face16": c1.get("face", "") if c1 else "",
            "ct2_face16": c2.get("face", "") if c2 else "",
            "state_changed": "YES" if c1 and c1.get("face") and
                             c1.get("face") != r1.get("face") else
                             ("NO" if c1 else "n/a"),
            "uncaught_r1_r2": f"{r1.get('uncaught','')}/{r2.get('uncaught','')}",
            "two_run_result": repro,
            "render_level": f"R{lvl}",
            "interaction": inter,
            "status": status,
            "first_divergence": FIRST_DIV.get(tag, "none recorded"),
            "visual_verification": VISUAL_NOTES.get(tag, ""),
            "binary_sha16": "9c5e456b4790299e",
            "engine_commit": "344774e66",
            "run1_dir": f"run_t279/{tag}_r1",
            "run2_dir": f"run_t279/{tag}_r2",
        })
    cols = list(rows[0].keys())
    with open(OUT / "T279_TWO_RUN_RESULTS.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    # inventory status refresh: campaign upgrades
    inv_path = OUT / "T279_RENDER_INVENTORY.json"
    inv = json.load(open(inv_path))
    for r in rows:
        p = inv["packages"].get(r["package"])
        if p:
            p["two_run_result"] = r["two_run_result"]
            p["render_level_current"] = r["render_level"]
            p["status"] = r["status"]
            p["interaction_current"] = r["interaction"]
            p["run1_face16"] = r["run1_face16"]
            p["run2_face16"] = r["run2_face16"]
            p["last_tested"] = "2026-11-28"
            p["binary_sha16"] = r["binary_sha16"]
            p["engine_commit"] = r["engine_commit"]
    from collections import Counter
    inv["summary"]["status_counts"] = dict(
        Counter(p["status"] for p in inv["packages"].values()))
    json.dump(inv, open(inv_path, "w"), indent=1)
    # sha ledger
    with open(OUT / "SHA256SUMS.txt", "w") as f:
        for rel, s in shot_shas:
            f.write(f"{s}  {rel}\n")
        for name in ("T279_TWO_RUN_RESULTS.csv", "T279_RENDER_INVENTORY.json"):
            f.write(f"{sha256(OUT / name)}  evidence/t279/{name}\n")
    print(f"[publish] {len(rows)} CSV rows, {len(shot_shas)} screenshots")
    from collections import Counter
    print("[publish] status:", dict(Counter(r["status"] for r in rows)))
    print("[publish] levels:", dict(Counter(r["render_level"] for r in rows)))


if __name__ == "__main__":
    main()
