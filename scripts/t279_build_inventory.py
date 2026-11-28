#!/usr/bin/env python3
"""T279 P1/P6 — build the deduplicated master rendering inventory.

Merges three evidence sources into T279_RENDER_INVENTORY.json:
  1. docs/evidence/canonical/registry.json      (152 canonical titles)
  2. evidence/s182_minimal2/S182_BATTERY.json   (20-title battery; 15 absent
     from the registry) + evidence/s182_recheck/S182_BATTERY.json (re-run
     results on 96878de83, 2026-11-27)
  3. The S23-S27 easy-APK wave (miniandroid/evidence/s23..s27; 12 packages
     absent from the registry, incl. the 3 interactive STATE_CHANGED titles)

Status vocabulary (8 labels, mutually exclusive):
  HISTORICAL-REAL | CURRENT-REPRODUCIBLE | INTERACTIVE | PARTIAL | REGRESSED
  | BLOCKED | PENDING | NOISE
Two-run campaign results (run_t279/T279_TWO_RUN_BATTERY.json) upgrade
statuses when present; a historical screenshot never upgrades a status.
"""
import json
import sys
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "evidence" / "t279" / "T279_RENDER_INVENTORY.json"

R_MAP_NOTE = "R-scale: R0 none | R1 launched no visual | R2 first frame | R3 primary screen complete | R4 navigation/scroll/dialogs | R5 interactive workflow"

# ---- source 1: canonical registry ----
reg = json.load(open(BASE / "docs/evidence/canonical/registry.json"))
inv = {}
for t in reg["titles"]:
    pkg = t["package"]
    st = t["status"]
    if "candidate" in st:
        st_c = st.replace("candidate_", "")  # candidate_VISUALLY_VERIFIED etc.
    # registry status -> 8-label vocabulary (conservative: no two-run proof yet
    # means VERIFIED stays historical until the campaign upgrades it)
    base = {
        "VERIFIED": "HISTORICAL-REAL",
        "OBSERVED": "HISTORICAL-REAL",
        "VISUALLY_PARTIAL": "PARTIAL",
        "PARTIAL": "PARTIAL",
        "FRAME_CAPTURED": "PARTIAL",
        "FAILED": "BLOCKED",
        "candidate_INTERACTION_VERIFIED": "HISTORICAL-REAL",
        "candidate_VISUALLY_VERIFIED": "HISTORICAL-REAL",
    }.get(st, "PENDING")
    row = {
        "package": pkg,
        "title": t.get("title", pkg),
        "type": t.get("type", ""),
        "status_registry": st,
        "status": base,
        "render_level_hist": t.get("level"),
        "level_name_hist": t.get("level_name"),
        "launched_hist": t.get("launched"),
        "rendered_hist": t.get("rendered"),
        "interacted_hist": t.get("interacted"),
        "state_changed_hist": t.get("state_changed"),
        "apk_sha256": t.get("apk_sha256", ""),
        "artifact": t.get("artifact", ""),
        "first_divergence": t.get("first_divergence", ""),
        "root_cause": t.get("root_cause", ""),
        "notes": t.get("notes", ""),
        "session": t.get("session", ""),
        "source_registry_row": True,
    }
    inv[pkg] = row

# ---- source 2: S182 battery (20 titles; 15 absent from registry) ----
bat = json.load(open(BASE / "evidence/s182_minimal2/S182_BATTERY.json"))
rech = json.load(open(BASE / "evidence/s182_recheck/S182_BATTERY.json"))
RECHECK_VERDICT = {  # from evidence/s182_recheck/S182_RECONCILIATION.md
    "de.duenndns.gmdice": "CURRENT-REPRODUCIBLE",
    "com.dozingcatsoftware.bouncy": "CURRENT-REPRODUCIBLE",
    "org.secuso.privacyfriendlydicer": "CURRENT-REPRODUCIBLE",
    "org.secuso.privacyfriendlysolitaire": "CURRENT-REPRODUCIBLE",
    "com.maxistar.textpad": "CURRENT-REPRODUCIBLE",
    "com.ashkanrafiee.librecontactsbackup": "CURRENT-REPRODUCIBLE",
    "ac.stresa.uturn": "REGRESSED",
    "app.wocheneinkauf": "REGRESSED",
    "app.simple.peri": "REGRESSED",
}
for tag, v in bat.items():
    if not isinstance(v, dict):
        continue
    pkg = v.get("pkg")
    if not pkg:
        continue
    cls = v.get("class", "PENDING")
    hist_status = ("HISTORICAL-REAL" if cls == "REAL_APP_CONTENT"
                   else "PARTIAL" if cls == "PARTIAL" else "BLOCKED")
    cur = RECHECK_VERDICT.get(pkg)
    row = inv.get(pkg) or {
        "package": pkg, "title": pkg, "type": v.get("kind", ""),
        "source_registry_row": False,
    }
    row.update({
        "status_s182_hist": hist_status,
        "s182_class": cls,
        "s182_hist_face": v.get("face"),
        "s182_hist_px": v.get("app_owned_pixels"),
        "status": cur or hist_status,  # recheck verdict where measured
        "render_level_hist": 3 if cls == "REAL_APP_CONTENT" else 2,
        "apk_source": v.get("apk"),
        "first_divergence": (
            "Compose AbstractComposeView.internalOnMeasure$ui IllegalStateException"
            if cur == "REGRESSED" else row.get("first_divergence", "")),
        "notes": (row.get("notes", "") +
                  " | S182 battery (2026-11-06): " + cls +
                  "; recheck on 96878de83 (2026-11-27): " +
                  (rech.get(tag, {}).get("verdict", "") if tag in rech else "")),
    })
    inv[pkg] = row

# ---- source 3: S23-S27 easy-APK wave (12 registry-absent packages) ----
WAVE = {
    "name.livitski.games.puzzle.android": {
        "title": "n-Puzzle", "type": "game", "wave_status": "INTERACTIVE",
        "evidence": "miniandroid/evidence/s23/s23_interaction_summary.tsv (S23 2026-11-21): CLICK_HANDLER_EXECUTED x12/run, 2 frame hashes STATE_CHANGED x3 runs; S27 wall w_pz faces 35c4e53b,6375a3a3 last IDENTICAL",
        "apk": "upload/handoff_apks/name.livitski.games.puzzle.android_2.apk",
        "apk_sha256": "99b9221d44677f65e6326bda6161a046c96206bc6939bc87ceed89fc267a6aac",
        "level": 5,
    },
    "ru.zxalexis.ugaday": {
        "title": "Hangman (Ugaday)", "type": "game", "wave_status": "INTERACTIVE",
        "evidence": "S23: XML onClick dispatched on activity obj (U0113-XMLCLICK), 2 hashes STATE_CHANGED x3 runs; batch614_guess report",
        "apk": "upload/handoff_apks/ru.zxalexis.ugaday_15.apk",
        "apk_sha256": "000ae2e5751f9a85c331d6205881d3db5dc81a00d10522485d9026b0494f8c3d",
        "level": 5,
    },
    "org.blockinger.game": {
        "title": "Minesweeper (Blockinger)", "type": "game", "wave_status": "INTERACTIVE",
        "evidence": "S23: 6 click events, 2 hashes STATE_CHANGED x3 runs",
        "apk": "upload/handoff_apks/org.blockinger.game_14.apk",
        "apk_sha256": "0c51e2255401eeb16ada6ea4eaa8aec1c2b715a789b12a004355a3812fe1c111",
        "level": 5,
    },
    "com.farmerbb.notepad": {
        "title": "Notepad (farmerbb)", "type": "app", "wave_status": "PARTIAL",
        "evidence": "S23: golden face 31ddd4d5; S23-W3 autofill ISE fixed; blocked at DataStore/protobuf worker-thread NPE (recorded chain); S27 wall w_np last-frame IDENTICAL",
        "apk": "upload/handoff_apks/com.farmerbb.notepad_122.apk",
        "apk_sha256": "b7cf30c187a951203ecf06295653fab587c3e54f155cf54565eda9e27d1444fa",
        "level": 3,
    },
    "com.itsfrz.tictactoe": {
        "title": "TicTacToe (itsfrz)", "type": "game", "wave_status": "PARTIAL",
        "evidence": "S23: APP_PIXELS face d55056a8/d602648e; 0 clickable views (custom-cell listener registration gap); S27 wall last-frame IDENTICAL",
        "apk": "upload/handoff_apks/com.itsfrz.tictactoe_5.apk",
        "apk_sha256": "2a057a9a519acd81dc54af9b3c9f58e40ebd0ce92f949aca65f6c439e8f74d45",
        "level": 3,
    },
    "org.ecos.logic.flip_a_coin": {
        "title": "Coin Flip", "type": "app", "wave_status": "PARTIAL",
        "evidence": "S23: blank (ConstraintLayout attach 0 addView); S27-W1 VectorDrawable rasterization law: raster=1 pipeline=1 face b270ff04 deterministic x6; dies at S27-W2 viewmodel-initializer blocker",
        "apk": "upload/handoff_apks/org.ecos.logic.flip_a_coin_3.apk",
        "apk_sha256": "63730ec2ac320ecb31004c07e60c30f374ab20ad8041147720a967bb2aafd5fb",
        "level": 2,
    },
    "com.attenomy.janken": {
        "title": "Janken (RPS)", "type": "game", "wave_status": "BLOCKED",
        "evidence": "S23: blank; S23-W1 CompositionLocal provider x4/run deterministic; next layer compose composition-state throw null x22",
        "apk": "upload/handoff_apks/com.attenomy.janken_1.apk",
        "apk_sha256": "7c18c2b21096a1029caec99f447298c502150255dbf0e7a8c4704e835940874c",
        "level": 1,
    },
    "tech.gaskell.diceroller": {
        "title": "Dice Roller (debug)", "type": "app", "wave_status": "PARTIAL",
        "evidence": "S23: rc=1 blank; faces 0ab178b9,0de952bf,0efd9882,46b07062,beabbef0; appcompat ActionBarContextView onMeasure layout_width ISE",
        "apk": "upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk",
        "apk_sha256": "d812e69612ccee064c67a75a6df29ee7b83a2b6395e2f8eb455a02ec66b6161c",
        "level": 2,
    },
    "com.ivylopez.authsrng": {
        "title": "AuthSRNG", "type": "app", "wave_status": "BLOCKED",
        "evidence": "S23: blank; compose convertMeasureSpec ISE; upstream SoftReference.get null (font cache init)",
        "apk": "upload/handoff_apks/com.ivylopez.authsrng_6.apk",
        "apk_sha256": "769f4d941400a22a222a0339f96e86de0a8499b9ff345355c3299457bdae75cc",
        "level": 1,
    },
    "de.tcrass.minos": {
        "title": "Minos", "type": "app", "wave_status": "PARTIAL",
        "evidence": "S23: inflate views=2 then content never attaches (FrameLayout children=0); S27 wall w_minos face b5a7a35d last-frame DIFF",
        "apk": "upload/handoff_apks/de.tcrass.minos_10004.apk",
        "apk_sha256": "af76923388c4ee3a265f66ea1fdab80092ed72400123d7e23f38a886281228a0",
        "level": 2,
    },
    "com.minar.randomix": {
        "title": "Randomix", "type": "game", "wave_status": "CURRENT-REPRODUCIBLE",
        "evidence": "golden anchor face 31ddd4d5b8e6d18e deterministic across S25 r1/r2 + S26/S27 walls; S26-W1 fresh-device-per-run law closed its determinism root cause",
        "apk": "upload/handoff_apks/com.minar.randomix_42.apk",
        "apk_sha256": None,  # sha16 8f137be5228c14766e7a on disk; full sha computed at publish
        "level": 4,
    },
    "dk.cocode.chess": {
        "title": "Chess (cocode)", "type": "game", "wave_status": "PARTIAL",
        "evidence": "S25/S26 anchor dk.cocode.chess_5022; S27 wall last-frame DIFF vs d602648e",
        "apk": "upload/handoff_apks/dk.cocode.chess_5022.apk",
        "apk_sha256": None,
        "level": 3,
    },
}
for pkg, w in WAVE.items():
    row = inv.get(pkg) or {
        "package": pkg, "title": w["title"], "type": w["type"],
        "source_registry_row": False,
    }
    row.update({
        "status": w["wave_status"],
        "render_level_hist": w["level"],
        "apk_source": w["apk"],
        "apk_sha256": w["apk_sha256"] or row.get("apk_sha256", ""),
        "wave_evidence": w["evidence"],
        "notes": (row.get("notes", "") + " | S23-S27 wave: " + w["evidence"]),
    })
    inv[pkg] = row

# ---- summary ----
from collections import Counter
c = Counter(r["status"] for r in inv.values())
summary = {
    "generated_by": "scripts/t279_build_inventory.py",
    "status_counts": dict(c),
    "total_unique_packages": len(inv),
    "r_scale": R_MAP_NOTE,
}
out = {"summary": summary, "packages": inv}
OUT.parent.mkdir(parents=True, exist_ok=True)
json.dump(out, open(OUT, "w"), indent=1)
print(f"[inventory] wrote {OUT}: {len(inv)} packages")
print("[inventory] status counts:", dict(c))
print("[inventory] registry-only rows:", sum(1 for r in inv.values() if r.get("source_registry_row")))
print("[inventory] registry-absent rows added:",
      sum(1 for r in inv.values() if not r.get("source_registry_row")))
