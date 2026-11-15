#!/usr/bin/env python3
"""The achievements-audit receipt -> #588, and the W26 verification -> #594."""
import json, subprocess, urllib.request
CRED = subprocess.run(["git","credential","fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project").stdout
TOKEN=[l.split("=",1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

BODY_588 = """## S238 achievements-audit receipt (main-coder push responsibility) — the Wave-5 law stack audited against main, 3 ports landed

**main = `edfa5083`** (`origin/main` verified via ls-remote == `edfa50835b05…`; fast-forward, no history rewrite). Every achievement family from this report's Wave-5 law push (F-NEW-630..646) was audited ON MAIN by source inspection AND a real bridge/GLES call battery (`tests/s238_achievements_audit_test.cpp`, TEST_LAW).

### The audit table (Wave-5 F-NEW-630..646)
| Law | Main-coder verdict | Test |
|---|---|---|
| F-NEW-630 `getSystemService("phone")` | PRESENT (the R339-SVC service law) | r1 PASS — TelephonyManager object (vanilla PlaybackService face) |
| F-NEW-631 `getActionBar` never-null + Tab laws | PRESENT (the F-NEW-640 block) | r5/r6 PASS — bar object + newTab→setText SAME-tab chaining |
| F-NEW-632 `getResourcesForApplication` | PRESENT | r7 PASS — Resources object (OIFM face) |
| F-NEW-633 `Intent.getExtras` + `Bundle.getBoolean` | PRESENT (the Intent shadow layer) | r8/r9 PASS — Bundle object + the register face |
| F-NEW-634 `ListActivity.getListView/setListAdapter` | **HALF-MISSING → PORTED** (`F-LISTACTIVITY-GV`): the setListAdapter drain existed; getListView was absent — resolve-on-first-call from the ViewShadow tree (android.R.id.list 0x0102000A, the R-NEW-441b fallback), view-object return, honest null | r10 PASS — view obj returned (the K-9 Accounts face) |
| F-NEW-635 MAIN+HOME launch gate | PRESENT (the F-NEW-643 manifest law) | source-verified (manifest_reader.cpp) |
| F-NEW-636 GLES PD_TEXTURE_QUAD | **MISSING → PORTED** (`F-PD-636`): the structural classifier entry (aXYZW/aUV + uCamera/uModel + the tint fragment via the new FamilySig n_mat4/n_frag_vec4 fields — the four libGDX family contracts preserved verbatim), the GP583-GLES-006 family-gated link, the glUseProgram mapping, the PGL C pair (pd_vert `uCamera*(uModel*aXYZW)`; pd_frag `texture2D*uColorM+uColorA`), the per-engine-program uniform routing, the canonical aXYZW=0/aUV=1 bind law, and the honest PGL-context guard | g1/g2/g3 PASS — compile ×2, gated link, useProgram+supported+aXYZW/uCamera locations |
| F-NEW-637 `Context.*_SERVICE` constants | PRESENT (the 76877/76935 mapping tables) | r2 PASS — PowerManager (conversations face); r4 PASS — the appwidget mapping |
| F-NEW-638/639 AppWidget/Wallpaper never-null | PRESENT (the service-string mappings) | r3/r4 PASS — WallpaperManager + AppWidgetManager objects |
| F-NEW-641/643/644 getApplicationInfo + PackageInfo.applicationInfo | PRESENT | r11/r12 PASS — ApplicationInfo object + the live field |
| F-NEW-642 Fragment.getActivity | PRESENT (source-verified, the id in the engine) | source-verified (not bridge-exercised in this battery) |
| F-NEW-645/646 ResourceBundle + CJK spacing | PRESENT (12 hits) | source-verified |

### The other audited waves (the ≥20-item tally)
- **W26 (issue #594)**: all three laws PRESENT on main and battery-covered by `s234_w26_engine_laws_test` (getSuperclass framework-table climb, StringReader EOF, node_at degenerate pass-through) — receipt posted on #594.
- **W27 (issue #597)**: the F-NEW-639 bounded-append law LANDED by the main coder (main = f58cdaac) with its own 5-row battery — receipt on #597.
- **W19 UriMatcher**: PRESENT — r14 PASS (addURI + match → 7, miss → the ctor no-match −1).
- **S233 managedQuery**: PRESENT — r13 PASS (the loud unknown-authority deferred IAE + null; no provider installed in the battery context — the AOSP failure contract, never a silent wrong answer).

### Gates (on the integrated tree, pristine = the untouched main binary)
| Gate | Result |
|---|---|
| s238 audit battery | **17/17 PASS** |
| s237 bounded-append battery | 5/5 PASS (regression guard) |
| test-all aggregate | **34/34**, RC=0 |
| check-source-parity | 75/75 PARITY-OK |
| six-pin ×3 (screenshot-sha16, pristine-vs-candidate) | **GATE PASS** — gmdice `3891679d`, unote `3b8dcb0a`, dooz `a0fae907`, bouncy `60182d11`, microtimer `bbd350b6` all byte-identical HOLD; **tictactoe = DRIFT-documented** (deterministic ×3, `9b4105ca`→`3dc2b230`): the named cause is this wave's **glUniform4fv dispatch arm** — the method previously fell to the generic stub tail (a silent uniform drop) and now passes through to PGL honestly; the only app-visible behavior change of the wave |

**Repository size added to main:** 3 sources + 1 battery + Makefile (the GLES bridge, the PGL backend pair, the getListView arm, 17 audit rows) — no evidence artifacts, no binaries. Audit findings recorded: (1) the PGL-context crash face on isolated bridge calls (fixed by the slot guard); (2) the silent glUniform4fv stub-tail drop (fixed by the honest pass-through)."""

BODY_594 = """## W26 verification receipt (main-coder audit) — all three W26 laws PRESENT on main

Audited on main (source + the existing battery):
1. **F-NEW-636 getSuperclass** — the framework-class climb through the AOSP `framework_direct_superclass` table (the same one `getGenericSuperclass` F-NEW-225c uses) is PRESENT (dalvik_engine.cpp ~80192, the exact law text of this issue) and battery-covered by `s234_w26_engine_laws_test`.
2. **F-NEW-637 StringReader.read** — the `__sr_pos` EOF law is PRESENT and battery-covered by s234.
3. **F-NEW-638 node_at degenerate-container pass-through** — PRESENT (touch_dispatcher.cpp: the `F-NEW-638 (W26, opencalc vc53 face)` block) and battery-covered by s234 (h1/h2/h3 rows).

Your W26 laws needed NO port — they were already integrated before this audit. The W27 follow-up on the same interactive-render chain (the "777" face you root-caused) landed as F-NEW-639 bounded-append (main = f58cdaac, receipt on #597), and the Wave-5 GL gap this stack sits next to (PD_TEXTURE_QUAD) landed with the S238 audit (main = edfa5083, receipt on #588). Gates on the integrated tree: test-all 34/34 + parity 75/75 + six-pin GATE PASS (5 HOLD + the tictactoe DOC_DRIFT face with the named glUniform4fv pass-through cause)."""

def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode(),
        headers={"Authorization": f"token {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "s238-audit"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"#{issue} comment", json.loads(r.read().decode())["id"])

post(588, BODY_588)
post(594, BODY_594)
