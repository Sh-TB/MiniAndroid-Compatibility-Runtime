#!/usr/bin/env python3
"""post_g11g12_comments.py — G11/G12 evidence publication to Issue #8 (Rule 0.2).

Every comment URL is read back from the GitHub API and appended to
scripts/comment_urls.json. Token errors are redacted. Never fabricates URLs.
"""
import json
import sys
import time
import urllib.request

TOKEN_FILE = "/home/z/.gh_token"
RESULTS = "/home/z/my-project/scripts/comment_urls.json"

BASE = "https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime"
C = lambda p: f"{BASE}/blob/main/{p}"
REPORT = C("MiniAndroid-Compatibility-Runtime/docs/evidence/g11g12_evidence/G11G12_FINAL_REPORT.md")
BASELINE = C("MiniAndroid-Compatibility-Runtime/docs/evidence/g11g12_evidence/phase0/phase0_baseline.json")
AFTER = C("MiniAndroid-Compatibility-Runtime/docs/evidence/g11g12_evidence/phase1_after/phase0_baseline.json")
TEST = C("MiniAndroid-Compatibility-Runtime/miniandroid/tests/g11_ctor_law_test.cpp")
ANCESTRY = C("MiniAndroid-Compatibility-Runtime/miniandroid/src/framework/view_ancestry.h")
SHOTS = "MiniAndroid-Compatibility-Runtime/docs/evidence/g11g12_evidence/phase0/screenshots/base"
SHOTS_A = "MiniAndroid-Compatibility-Runtime/docs/evidence/g11g12_evidence/phase1_after/screenshots/after"

COMMENTS = [
    {
        "key": "g11g12_recovery_baseline",
        "body": f"""## G11/G12 — §1 CURRENT-HEAD RECOVERY + PHASE-0 BASELINE (52/52, engine continuity proven)

**Current-HEAD discipline (§1):** the session resumed from a lost checkpoint —
local HEAD `167c27fb` carried a stale `docs(g10)` message but contained the
recovered G11 phase-0 evidence + engine WIP; `origin/main` `3d063e01` was
verified a **byte-identical content subset** (every origin file present with
equal content; no work lost by the rebase). Resolution: rebase → honest reword
→ push `3d063e01..d8b66526` (no force).

**§1.7 environment restore (BEFORE baseline, no engine change):** aapt2
8.13.2-14304508 re-fetched from Google Maven; HelloWorldSelfAware external
fixture re-fetched byte-exact (`009b467109c4…` == recorded SHA-256); the
8-APK campaign corpus restored from the frozen 18-APK manifest with
SHA-256 verification.

**Baseline continuity proof:** 4 of the 8 phase-0 screenshots reproduce the
G10 frozen goldens byte-identically (microtimer `57503a12…`, simplestopwatch
`ed1dfc89…`, gmdice `db0f4c4b…`, unote `8197687f…`) — the baseline engine
state is exactly G10-final.

**Baseline battery: 50/50 ALL PASS at `d8b66526`** (before any new fix),
then extended to 52 stages.

Phase-0 registry (per-APK SHA-256 / status / pixel audit / tree / diag):
- baseline: {BASELINE}

Evidence subset (mandatory 6 per §2 + 2 guards, same set before AND after):
headingcalculator `274ec873…`, microtimer `79c6f730…`, billthefarmer
`82cf8bc4…`, muellerma `3b6a10c8…`, + guards simplestopwatch/gmdice/unote/chessclock.
""",
    },
    {
        "key": "g11g12_laws_fixes",
        "body": f"""## G11/G12 — LAW CHAIN: trace → root cause → AOSP law → generic fix (5 semantic commits)

**F5-C1 root cause (trace-proven, headingcalculator):** the ctor hook was
installed on the LAZY DEFAULT LayoutInflater; the framework-statics preload
then ran `ensure_loaded()` which `make_unique`-recreates the inflater and the
per-instance hook was **silently wiped** — inflate ran factory-less (3-view
childless tree; screenshot byte-identical to the G10 baseline).

Law fixes (each: law source + generic implementation + zero package branches):
1. **FIX-G11-001** — `run_custom_view_constructor()`: app-class XML tag =
   instantiation → execute the class's REAL DEX `<init>(Context,
   AttributeSet)`/`(Context)` via a DEX class-index authority (descriptor
   gate only filters framework prefixes; obfuscated `Lk/g;` passes),
   cycle guard, opt-in `MINIANDROID_G11_TRACE` ctor+super-chain proof.
2. **FIX-G11-002** — `LayoutInflaterShadow` (from/inflate 1/2/3-arg,
   attachToRoot semantics; 2-arg == `root != null`; returns ROOT) +
   `inflate_layout_resid(parent_view_id)`.
3. **Factory-law fix (`f42cf79c`)** — ResourceRuntime OWNS the process-wide
   ctor hook and re-applies it to EVERY LayoutInflater it creates
   (AOSP: `AppCompatDelegateImpl.installViewFactory` re-applies Factory2).
4. **FIX-G12-001/001b (`e7a00f3b`)** — framework ancestry table
   ({ANCESTRY}): TableRow/TableLayout→LinearLayout, ScrollView→FrameLayout,
   Button→TextView… (TableRow contained no "Layout" substring → was
   leaf-classified 0x0 under 44px children) + **descriptor form law**:
   DEX=slash-form vs AXML=dot-form; `normalize_class_desc()` at every
   cross-layer compare + TableLayout stacks rows VERTICALLY.
5. **FIX-G12-002/003 (`28c1bfe1`)** — classifier Factory survival (is_a was
   only wired on the renderer pass — the window path classified app
   containers as LEAVES) + **parent-delegation law**: framework-namespace
   `<clinit>` from app DEX never executes (muellerma's bundled
   `android.app.AppComponentFactory.<clinit>` disassembly = unconditional
   construct-and-throw; real Android resolves android.* from the boot
   classpath) + activity-less app boot law (FIND-G11-NOACTIVITY-001:
   muellerma declares NO activity — a QS-tile-only app).

**§28 hostility:** 37-check law battery — {TEST}
descriptor gate (obfuscated app classes pass / framework rejected / malformed
rejected), Factory-law regression test, LayoutInflaterShadow hostile dispatch,
addView single-mount + self-mount + ancestor-cycle rejection.
""",
    },
    {
        "key": "g11g12_cross_apk_validation",
        "body": f"""## G11/G12 — CROSS-APK VALIDATION + VISUAL EVIDENCE (same 8-APK corpus before/after)

**headingcalculator — first constructor-era frame:**
- ctor proof: `CalculatorDisplay`, `CalculatorKeypad`, `ExplainableTextView`,
  `ExplainableButton` real DEX `<init>(Context, AttributeSet)` EXECUTED
  (`executed=YES` per-class in trace); real super chains
  `CalculatorKeypad→LinearLayout→ViewGroup→View→Object`.
- child-count proof: 3 XML nodes → 46+ node final tree (display grid
  TC/TAS/WD/WS/TH/GS + 4 keypad rows digit1..9/DEL/CE + ExplainableButtons).
- measure proof: `CalculatorDisplay 1080x0 → 1080x158` (= 3 rows × 44px);
  rows `158x44/169x44/146x44`; keypad rows re-measured `EXACTLY(480)` by the
  AOSP weight second pass.
- visual proof: `6ab39944 → 0f933ff8`, 268,977 px diff, nonbg 0.263% → 6.72%.
  before: {C(SHOTS + "/headingcalculator.png")} · after: {C(SHOTS_A + "/headingcalculator.png")}

**microtimer — obfuscated programmatic build path verified:**
- `Lk/g;.<init>` executes setOrientation + new Button + `new RoTimeControl`
  + `addView(...)`×2 (F5-C7/F5-C8 exercised by REAL app code);
  RoTimeControl.a() creates a TextView programmatically (640x123).
- pixel delta band rows 951–1076 == exactly the new real TextView; classified
  LAWFUL ('null:null:null' = the app's own Java null-concat at construction;
  timer-tick update = G07 future layer).
  before: {C(SHOTS + "/microtimer.png")} · after: {C(SHOTS_A + "/after-microtimer" if False else SHOTS_A + "/microtimer.png")}

**Zero regression:** billthefarmer_notes, simplestopwatch, gmdice, unote,
chessclock screenshots **byte-identical**; muellerma byte-identical with the
unlawful stub now skipped (status PARTIAL preserved honestly).

**Determinism (§31):** headingcalculator 3 clean runs → unique screenshot
hash count 1; microtimer 3 runs → 1; battery 3-run gates (G06/G07/G08) pass.

**Full matrix + tables:** {REPORT}
after-run registry: {AFTER}
""",
    },
]

REDAC = "***REDACTED***"


def api(method, url, payload=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {open(TOKEN_FILE).read().strip()}")
    req.add_header("Accept", "application/vnd.github+json")
    data = json.dumps(payload).encode() if payload is not None else None
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body[:200].replace(open(TOKEN_FILE).read().strip(), REDAC)}",
              file=sys.stderr)
        raise


def main():
    issue = 8
    out = json.load(open(RESULTS))
    results = out if isinstance(out, list) else out
    for c in COMMENTS:
        created = api("POST", f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{issue}/comments",
                      {"body": c["body"]})
        url = created.get("html_url", "")
        entry = {"key": c["key"], "url": url, "id": created.get("id")}
        print("POSTED", c["key"], url)
        if isinstance(results, list):
            results.append(entry)
        else:
            results[c["key"]] = entry
        time.sleep(2)
    with open(RESULTS, "w") as f:
        json.dump(results, f, indent=1)
    print("URL registry updated.")


if __name__ == "__main__":
    main()
