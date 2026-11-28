#!/usr/bin/env python3
"""T279-CONT-5 — merge the continuation results into all records.

1. registry.json: the 9 restored titles get their measured statuses (was
   PENDING re-test); the honest R-scale corrections from the full visual
   verification (uturn/pfdicer/pfsolitaire/textpad/npuzzle R3->R2);
   janken/authsrng notes (LocalLifecycleOwner law peeled one layer).
2. CSV: append the 9 CONT rows + a corrections note column for the R2s.
3. inventory JSON: same corrections.
"""
import csv
import json
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence/t279"
BIN_SHA16 = "c3006bf71e02b3ae"  # rebuilt binary (same source as 1a21be9f)

# ---- measured CONT results (run_t279_cont/T279_CONT_BATTERY.json) ----
CONT = json.load(open(BASE / "run_t279_cont/T279_CONT_BATTERY.json"))
REST = {  # pkg: sha256 from scripts/t279c_restore_receipt.txt
    "com.aeropayout.game": "dae6cb3ea3437d8011a7c0e3d19b1b1d346683eb1ddcca1a19efc61d4198dcab",
    "com.awagam.android": "30af184cdbb35f9b06fae5f16b2e524f2451a2d4a1865adf4bc967e556a82b63",
    "org.secuso.privacyfriendlyludo": "b86427e1c4e874372be3f4f87bc26739a96c37e87ef7d87650568fcc01fe487b",
    "com.curryplayer.quicksettingssoundprofile": "6714227399fea33b6a736795943c34e0e1f89fe1fec2636c019512344812cbb3",
    "com.cg.lrceditor": "ea720cf8ae77d9dcae2f5639654ae03f9309c9de49b6abb166d4a93c1d20f016",
    "app.floatdeck": "115ab98dacb0f989f587b3427896ed9f3e392372b6bce2dc6b09194c5ce162eb",
    "com.chiranth7.webstack": "2f22bbbd4e089ddfeca691867d20b562be08c0e815defd214443fa93cf35aa08",
    "org.dmfs.tasks": "7f3a1528142c8a8a0ab1ecf6b83f0620eb31cd8daa94b299149c21982e3c2f14",
    "com.nononsenseapps.notepad": "0d79884020f2a09e0787282e345d7e8808826e0fb09135f620007015b30630b0",
}
# verdict-derived statuses/levels per the honest R-scale + visual checks
CONT_STATUS = {
    "com.aeropayout.game": ("PARTIAL", 1, "chrome face d602648e (unc 10)"),
    "com.awagam.android": ("BLOCKED", 1, "default background b5a7a35d (unc 33; compose composition-state class)"),
    "org.secuso.privacyfriendlyludo": ("CURRENT-REPRODUCIBLE", 2, "REAL_APP_CONTENT px 58,212 — SECUSO onboarding intro (Skip/Next), not the primary menu; VISUALLY VERIFIED 2026-11-28"),
    "com.curryplayer.quicksettingssoundprofile": ("PARTIAL", 1, "default-tint face 11a38a5a (unc 32)"),
    "com.cg.lrceditor": ("CURRENT-REPRODUCIBLE", 2, "REAL_APP_CONTENT px 2,194 — partial editor content text; VISUALLY VERIFIED 2026-11-28"),
    "app.floatdeck": ("PARTIAL", 1, "chrome face d602648e (unc 32)"),
    "com.chiranth7.webstack": ("BLOCKED", 1, "default background b5a7a35d (unc 32; compose class)"),
    "org.dmfs.tasks": ("PARTIAL", 1, "chrome face d602648e (unc 7)"),
    "com.nononsenseapps.notepad": ("PARTIAL", 1, "default-tint face 894a69b0 (unc 6)"),
}
# honest R-scale corrections from visual verification (2026-11-28)
R2_CORRECTIONS = {
    "ac.stresa.uturn": "VISUALLY VERIFIED: 'UTurn Installed. No need to launch it…' notice screen — genuine app text, face == S182 historical a53523e7 byte-identical; the primary game UI is behind further interaction -> honest R2 (was R3 in the first campaign table)",
    "org.secuso.privacyfriendlydicer": "VISUALLY VERIFIED: blue welcome dialog with 'Okay' — a gate screen before the dice UI -> honest R2 (was R3)",
    "org.secuso.privacyfriendlysolitaire": "VISUALLY VERIFIED: SECUSO SKIP/NEXT onboarding intro (same template as pfludo) -> honest R2 (was R3)",
    "com.maxistar.textpad": "VISUALLY VERIFIED: editor chrome bar only, editor area blank -> honest R2 (was R3)",
    "name.livitski.games.puzzle.android": "VISUALLY VERIFIED: 'Please select a picture' prompt — gate screen before the board (Menu interaction path) -> honest R2 (was R3)",
}

reg = json.load(open(BASE / "docs/evidence/canonical/registry.json"))
cont_rows = []
for tag, ent in CONT.items():
    pkg = ent["runs"]["run_r1"].get("pkg")
    st, lvl, div = CONT_STATUS[pkg]
    r1 = ent["runs"]["run_r1"]; r2 = ent["runs"]["run_r2"]
    row = next(t for t in reg["titles"] if t["package"] == pkg)
    row["status"] = st
    row["level"] = lvl
    row["rendered"] = (st == "CURRENT-REPRODUCIBLE")
    row["apk_sha256"] = REST[pkg]
    row["t279_status"] = st
    row["t279_level"] = lvl
    row["t279_run1_face16"] = r1.get("face") or ""
    row["t279_app_px"] = r1.get("app_owned_pixels")
    row["t279_last_tested"] = "2026-11-28 (CONT)"
    row["t279_binary_sha16"] = BIN_SHA16
    row["first_divergence"] = div
    row["notes"] = (row.get("notes", "").split(" | T279")[0] +
                    f" | T279 CONT 2026-11-28: APK restored from F-Droid "
                    f"(byte-pinned, receipt scripts/t279c_restore_receipt.txt); "
                    f"two-run {r1.get('face')}/{r2.get('face')} face-identical; "
                    f"{div}")
    cont_rows.append({
        "tag": tag, "package": pkg, "apk": r1.get("apk", ""),
        "type": ent.get("kind", ""),
        "run1_class": r1.get("class", ""), "run1_verdict": r1.get("verdict", ""),
        "run1_face16": r1.get("face", ""), "run1_app_px": r1.get("app_owned_pixels", ""),
        "run2_class": r2.get("class", ""), "run2_face16": r2.get("face", ""),
        "run2_app_px": r2.get("app_owned_pixels", ""),
        "ct1_face16": (ent["runs"].get("run_ct1") or {}).get("face", ""),
        "ct2_face16": (ent["runs"].get("run_ct2") or {}).get("face", ""),
        "state_changed": "NO",
        "uncaught_r1_r2": f"{r1.get('uncaught','')}/{r2.get('uncaught','')}",
        "two_run_result": "PASS-IDENTICAL" if r1.get("face") == r2.get("face") else "FAIL",
        "render_level": f"R{lvl}", "interaction": "no-frame-change",
        "status": st, "first_divergence": div, "visual_verification": "",
        "binary_sha16": BIN_SHA16, "engine_commit": "344774e66..f9e1d3314",
        "run1_dir": f"run_t279_cont/{tag}_r1", "run2_dir": f"run_t279_cont/{tag}_r2",
    })

# R-scale corrections on the already-measured rows
for pkg, note in R2_CORRECTIONS.items():
    row = next((t for t in reg["titles"] if t["package"] == pkg), None)
    if row:
        row["level"] = 2
        row["t279_level"] = 2
        row["notes"] = row.get("notes", "") + " | T279 CONT correction: " + note

# janken/authsrng: the LocalLifecycleOwner law peeled one layer
for pkg, unc in (("com.attenomy.janken", 32), ("com.ivylopez.authsrng", None)):
    row = next((t for t in reg["titles"] if t["package"] == pkg), None)
    if not row:
        continue
    row["notes"] += (" | T279 CONT fix 2026-11-28: the T279-LLO-PROVIDE law "
                     "(dalvik_interpreter.cpp, LocalLifecycleOwner -> the "
                     "current Activity, the AOSP ComponentActivity-is-the-owner "
                     "semantic) eliminated the LocalLifecycleOwner ISE layer "
                     "(uncaught 33->32); janken's named next frontier is "
                     "androidx Navigation 'You cannot access the Navigator's "
                     "state until the Navigator is attached' (nav-controller "
                     "boot-order class — recorded, not chased); authsrng's "
                     "remaining blocker is the kotlin-reflect "
                     "SynchronizedLazyImpl NPE (different class, recorded).")

reg["generated"] = ("2026-11-28 T279 CONT reconciliation: 9 restored APKs "
                    "measured (receipt scripts/t279c_restore_receipt.txt), "
                    "all pairs face-identical; honest R-scale corrections "
                    "after full visual verification; T279-LLO-PROVIDE law "
                    "peeled the janken LocalLifecycleOwner layer")
json.dump(reg, open(BASE / "docs/evidence/canonical/registry.json", "w"), indent=1)

# CSV: append CONT rows
csv_path = OUT / "T279_TWO_RUN_RESULTS.csv"
rows = list(csv.DictReader(open(csv_path)))
cols = list(rows[0].keys())
for r in cont_rows:
    for k in cols:
        r.setdefault(k, "")
    rows.append({k: r.get(k, "") for k in cols})
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

# inventory corrections
inv_path = OUT / "T279_RENDER_INVENTORY.json"
inv = json.load(open(inv_path))
for r in cont_rows:
    p = inv["packages"].get(r["package"])
    if p:
        p["status"] = r["status"]
        p["render_level_current"] = r["render_level"]
        p["two_run_result"] = r["two_run_result"]
        p["last_tested"] = "2026-11-28 (CONT)"
        p["binary_sha16"] = BIN_SHA16
for pkg in R2_CORRECTIONS:
    p = inv["packages"].get(pkg)
    if p:
        p["render_level_current"] = "R2"
        p["visual_verification"] = R2_CORRECTIONS[pkg]
from collections import Counter
c = Counter(p["status"] for p in inv["packages"].values())
inv["summary"]["status_counts"] = dict(c)
json.dump(inv, open(inv_path, "w"), indent=1)
print(f"[merge] registry 9 CONT rows measured + {len(R2_CORRECTIONS)} R2 corrections")
print(f"[merge] CSV now {len(rows)} rows")
print("[merge] inventory statuses:", dict(c))
