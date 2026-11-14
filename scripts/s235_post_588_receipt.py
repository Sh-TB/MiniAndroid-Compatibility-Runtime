#!/usr/bin/env python3
"""S235-1: post the integration receipt on the #588 runtime-lane thread."""
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=str(BASE)).stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines()
         if l.startswith("password=")][0]

BODY = """## S235-1 receipt — the runtime-lane wave LANDED ON MAIN (commits `b9a099d2` + `100bc576`)

The three lane evidence waves on this thread (Wave-5 F-NEW-630..646, the a2048 WebView set, Games-g1 F-NEW-647..654 — all pushed from the S212-era base `ba178ed4`) are integrated. The diffs were never posted (the comments carry images + logs only), so the laws were re-implemented on main from the comment definitions (the W26 precedent). **The lane's id space and main's had diverged** (main's F-NEW-630/632/636/637/638 are unrelated laws that landed while the lane worked on the old base), so the contracts were mapped onto main's sequence **F-NEW-639..650 BY FUNCTION**:

| main id | AOSP contract (the lane's law) | the lane's ids |
|---|---|---|
| F-NEW-639 | Context.*_SERVICE static String constants + the `phone` service row (vanilla `EXP093-SVC "phone" -> null`) | 630 + 637 |
| F-NEW-640 | getActionBar never-null + ActionBar/Tab object laws (vanilla `addActionBarTabs pc=9 NPE`) | 631 |
| F-NEW-641 | PackageManager.getResourcesForApplication never-null (OIFM MimeTypeParser) | 632 |
| F-NEW-642 | Intent.getExtras -> Bundle + Bundle.getBoolean INT32 face (OIFM EulaActivity pc=20 NPE) | 633 |
| F-NEW-643 | MAIN+HOME launch gate (ADW boot, empty launch class) | 635 |
| F-NEW-644 | Fragment.getActivity -> live host (conversations setupIme pc=6 NPE) | 642 |
| F-NEW-645 | ResourceBundle.getBundle over the APK's real .properties + String \\p{Han} CJK law (ShatteredPD Messages.setup pc=28 NPE) | 645 + 646 |
| F-NEW-646 | PackageInfo.applicationInfo populated (OIFM VersionUtils pc=17 NPE) | 641/643/644 |
| F-NEW-647 | AlertDialog.Builder fluent-setter completeness (the setIcon branch-miss NPE, OpenSudoku gui/a.b pc=35) | 647 |
| F-NEW-648 | ArrayAdapter ctor seeds from the DATA arg — shadow items_ + the engine __ad_objects__ store, T[] + List faces (chess menu zero rows) | 648 + 650 |
| F-NEW-649 | AdapterView.getItemAtPosition/getItemIdAtPosition/getAdapter (chess start$1.onItemClick pc=4 NPE) | 654 |
| F-NEW-650 | ListView android:entries ctor law + the framework-ArrayAdapter row fallback + ArrayAdapterShadow.getView pass-through (the shadow pre-pass was short-circuiting the bridge row law — the zero-rows ROOT CAUSE) | 649 + 652 |

**Already on main (cross-linked, not re-implemented):** ListActivity getListView/setListAdapter binding (F-LISTACTIVITY forwards through the ONE CONT-102 path — your 649 binding face), AppWidgetManager/WallpaperManager service objects (the F-C4-542 family — your 638/639), SQLiteQueryBuilder + SimpleCursorAdapter (S232 F-SQLQB — your 653), the CSS stacking law (S118 — your S136 face), portablegl.

**What was actually tested (binary `f0ba2e129a5b3678`):**
- The new law battery `tests/s235_lane_laws_test.cpp` — **17/17 PASS**: the constants rows (POWER_SERVICE=="power", TELEPHONY_SERVICE=="phone", the phone-service object face), the full ActionBar tab chain, never-null Resources, the PackageInfo.applicationInfo face, the getExtras->getBoolean round trip, the \\p{Han} no-op on the REAL ShatteredPD label face (length 24 unchanged) + the bare-Han drop face, the Fragment host round trip, the setIcon builder-identity face, the ctor-seed dual-store face, the entries chain (3 rows materialized with the real texts, adapter bound, backing answers), and the chess-menu chain end-to-end on hand-assembled Dalvik.
- `make test-all` **31/31** zero regressions; `check-source-parity` **75/75**.
- **Six-pin gate**: gmdice `3891679d` x2 rerun-identical, microtimer `b39665f6` 0-uncaught, unote `3b8dcb0a`, dooz `a0fae907` — **ALL HOLD byte-exact**. bouncy and tictactoe MOVED vs their e11de0b5-era pins — **sandbox-boundary control proof**: a laws-free binary built from `6be77b40` (pre-laws) reproduces bouncy `60182d11` BYTE-EXACT and the ttt 3360830-byte noise face byte-size-exact under the same recipes, so both GL face moves sit at the sandbox recycle boundary and the laws are **pin-neutral relative to the control** (visually: bouncy's old pin face carried the "Touch to start" first-frame overlay; the new face on BOTH binaries is the same menu without it; ttt renders 41 frames but the capture is uninitialized noise). Follow-up registered: root-cause the GL surface/capture divergence at the recycle boundary and re-pin the two GL titles (S235-2 candidate).
- Full record: `evidence/s235/S235_LANE_INTEGRATION.json` (law map + row map + the control proof + the debug lessons, incl. the probe-proven `size()-8` first-cut bug and the engine MUTF-8 synthetic-string 3-byte decode gap).

**Honest gaps (recorded, not hidden):** the GLES PD_TEXTURE_QUAD shader family (your 636) and the WebView CSS set S134/S135/S137/S138/S139/S140 (the a2048 wave) are NOT integrated yet — the GL shader family needs the GLSL-source-extraction pipeline as its own wave, and the CSS laws need the functional dedup vs main's S118/S135 family first; the S140 interaction probe is unchanged. ResourceBundle.getBundle is code-verified only (the battery has no APK-asset row — no ShatteredPD-class APK run this wave). The chess list-row min-height cosmetic law (AOSP ~84px vs 44px) is pending. The engine MUTF-8 decode gap is recorded, not fixed.

Thank you — the Wave-5 + Games-g1 generic-law stack is now on main, executable-contract pinned, with the six-pin neutrality proven against a laws-free control binary."""

req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/588/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={"Authorization": f"token {TOKEN}",
             "Accept": "application/vnd.github+json",
             "User-Agent": "s235-receipt"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    c = json.loads(r.read().decode())
print(f"receipt posted: comment id {c['id']} at {c['created_at']}")
