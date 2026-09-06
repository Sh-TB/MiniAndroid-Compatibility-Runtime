#!/usr/bin/env python3
"""Post the G09 evidence comments to Issue #8 and record direct URLs.

Security: token read from /home/z/.gh_token (mode 600, outside the git
worktree); never printed, never embedded here.
"""
import json
import ssl
import sys
import urllib.error
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
TOKEN_PATH = "/home/z/.gh_token"
RESULTS = "/home/z/my-project/scripts/comment_urls.json"

BASE = "https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime"

COMMENTS = [
    {
        "key": "g09_phase0_baseline",
        "body": f"""## G09 — PHASE 0 BASELINE (current-HEAD audit, engine untouched)

HEAD at baseline: **af99f763** (main, clean tree; 1 pre-existing unpushed
runtime/data residue commit — engine untouched).

**Battery: 48 stage gates ALL PASS** (`run_test_battery.sh`; now with
same-HEAD resume checkpoints — the sandbox reaps background process groups,
so the battery runs foreground-resumable).

Frozen hashes reproduced **byte-identically** (sha256sum vs constants):

| Frozen | Value | Status |
|---|---|---|
| EXT-01/EXT-02 frame_000 png | `142238fd92b69e11…` | ✅ identical |
| EXT-02 frame_001 png | `e242ac1e9c8cc224…` | ✅ identical |
| density-matrix | `351340a7a92e645c` | ✅ identical (det2/det3 too) |

Forensic note that produced one false alarm during this audit: the frames
manifest carries TWO hashes — `sha256` (internal raw-frame hash) and
`png_sha256` (PNG file bytes). The frozen constants are the **PNG file
hashes**; `sha256sum` of the produced files matches them exactly.

Corpus-cache restore findings (recorded, engine untouched):
- CORPUS-DRIFT `com.benny.openlauncher_39`: F-Droid now serves
  `b3320463…` (frozen manifest had `b7900f56…`) — G09 freezes today's bytes
  and records both.
- `com.martinmimigames.tinymusicplayer_1`: F-Droid URL **404** (dead).
- Telegram `dl/android`: not a frozen APK URL — registry-only.

Status: RUNTIME-PROVEN (baseline) — Phase 0 complete.
Commit of record for the campaign start of evidence: af99f763 → 48c2883b.""",
    },
    {
        "key": "g09_corpus_registry",
        "body": f"""## G09 — PHASE 1: FROZEN 18-APK REAL CORPUS (metadata only, no binaries in git)

Registry: `MiniAndroid-Compatibility-Runtime/docs/evidence/g09_corpus/g09_corpus_registry.json`
Per-APK metadata JSONs: `docs/evidence/g09_corpus/<apk>.meta.json`

Every entry records: source URL, frozen date, SHA-256, package,
versionCode/versionName, minSdk, targetSdk, label, launchable activity,
FULL activity list with intent-filters, DEX census (AppCompat / Compose /
support-v7 / setOnClickListener / startActivityForResult / setResult),
classification flags. APK binaries stay in the gitignored cache
(`miniandroid/download/**`, hash-restorable via `scripts/fetch_corpus.py`).

Structural diversity achieved: 12 framework-only · 6 AppCompat · 3
Compose · 8 multi-Activity (2..31 declared activities) · minSdk 4..28 ·
targetSdk 19..36 · WebView app · GL(libGDX) game · IME.

**Corpus corrections to prior records (manifest evidence over assumption):**
- `org.connectbot` 11009000 declares **exactly 1 Activity** + 3 Services
  (single-Activity Compose-era app). The G06–G08 record calling EXT-08 a
  "real multi-Activity app" is hereby corrected.
- OpenLauncher URL drift and TinyMusicPlayer 404 recorded (see baseline
  comment).

Status: REAL-APK TESTED (frozen + hash-verified).""",
    },
    {
        "key": "g09_corpus_matrix",
        "body": f"""## G09 — PHASES 2/3/4: REAL-APK RESULTS MATRIX (base + click-test runs, pixel audit)

Full report: `docs/evidence/G09_FINAL_REPORT.md` · Per-APK evidence JSONs:
`docs/evidence/g09_corpus/results/*.result.json` · Pixel audit:
`results/g09_screenshot_audit.json` · Visual frames: `g09_corpus/visual/`

| APK | Initial UI | G06 Input | G07 Lifecycle | G08 Navigation | Blocker |
|---|---|---|---|---|---|
| helloworldselfaware | RENDERED | **PASS** (long-press golden, VISUALLY-PROVEN) | PASS | N/A | — |
| gmdice | RENDERED (rich) | **PASS** 8/8 probed→8 state-changed | PASS | N/A | — |
| simplestopwatch | RENDERED | **PASS** 4 probed→2 visual | PASS | PARTIAL | — |
| unote | RENDERED | **PASS** 4 probed→2 visual | PASS | BLOCKED (F10) | F10 |
| chessclock | PARTIAL ("null" texts) | PARTIAL 8/0 | PASS | BLOCKED (F10 implicit) | F10 |
| microtimer | PARTIAL (keypad collapsed) | PARTIAL 12/0 | PASS | N/A | F8 |
| billthefarmer notes | PARTIAL (rows collapsed) | PARTIAL 2/0 | PASS | N/A | F8 |
| muellerma stopwatch | PARTIAL (bar) | N/A | FAIL pre-onCreate | N/A | F5 (AppComponentFactory) |
| headingcalculator | BLANK (custom views 1080x0) | FAIL | PASS | N/A | F8/F9 |
| tictactoe (real) | BLANK | N/A (GL) | PASS | N/A | F12 libGDX |
| KISS / markor / connectbot / openlauncher | BLANK shell | N/A | PASS | N/A | F12 AppCompat |
| dooz / fossify | BLANK | N/A | PASS | N/A | F12 Compose |
| bgclock | BLANK | N/A | PASS | N/A | F12 WebView |
| simplekeyboard | BLANK | N/A | PASS | N/A | F5 preferences |

Totals: **18 tested · 4 rendered · 4 partial · 10 blank** — every number is
an executed run with committed console log + JSON + (where applicable)
screenshot evidence. Key real-DEX dispatch examples: unote
`addNote→startActivity` (component-less → ACTIVITY_NOT_FOUND), chessclock
settings `startActivity` implicit → `G08-LAUNCH FAILED: no component`,
simplestopwatch `onButtonStart/onButtonReset` state changes rendered.

Corpus 3-run determinism: simplestopwatch `ed1dfc89…`×3, gmdice
`db0f4c4b…`×3 (screenshot bytes).

Status: REAL-APK TESTED (matrix) / VISUALLY-PROVEN (4 rendered + click-state
frames).""",
    },
    {
        "key": "g09_fix_and_regression",
        "body": f"""## G09 — PHASES 6/7: CROSS-APK CLUSTER → GENERIC LAW FIX + FULL REGRESSION

**FIND-G09-LC-001 (FIXED, commit 84f0fb55).** Corpus evidence: 10+
framework-only APKs recorded `ACTIVITY_CREATED→RESUMED` (STARTED skipped)
and 4+ apps recorded **guard-rejected** finish cascades
(unote: `ACTIVITY_CREATED→PAUSED/STOPPED/DESTROYED`, all success=false,
final_state stuck at ACTIVITY_CREATED). Root cause: the boot driver gated
the machine's STARTED/RESUMED transitions on app-visible DEX dispatch
success. AOSP law (ActivityThread.handleLaunchActivity →
handleStartActivity → handleResumeActivity): **the activity record advances
on the FRAMEWORK path regardless of app overrides** (the framework stub
answers for non-overriding apps).

Fix: record advances unconditionally at boot; the trace still documents
whether real app bytecode ran. Focused law test added
(lifecycle_law_test **22→25, ALL PASS**): CREATED→RESUMED without STARTED
stays REJECTED; the lawful stub-answered chain terminates RESUMED with the
FULL cascade legal from it.

Post-fix corpus verification (6 structurally different APKs re-run):
unote = `PROCESS_CREATED→ACTIVITY_CREATED→STARTED→RESUMED` all success=true,
final_state=**RESUMED**; 6/6 apps RESUMED.

**Regression:** BATTERY GATE **ALL PASS (48/48)** at 98c25ba2; frozen
goldens byte-identical (`142238fd92b69e11…`, `e242ac1e9c8cc224…`,
`351340a7a92e645c`).

No package-name branches, no fixture branches — the fix is one framework
law in the boot driver (`grep`-auditable).

Status: IMPLEMENTED → TESTED → REAL-APK TESTED → RUNTIME-PROVEN.""",
    },
    {
        "key": "g09_api_audit",
        "body": f"""## G09 — PHASE 5: API-LEVEL COMPATIBILITY AUDIT (no blind "Android 9/10 compatible" label)

Code-anchored audit of what version semantics MiniAndroid actually models:

| Surface | Anchor | Modeled? |
|---|---|---|
| Resource v-qualifiers (vN) | `res_config.cpp:158` (reject sdk>device), `:346` (AOSP closest-bucket tie-break), `:435` `c.sdkVersion = 34 // runtime target API level` | YES — device constant 34 |
| `Build.VERSION.SDK_INT` to DEX | `dalvik_engine.cpp:11539` seeds **34** | YES — constant 34 |
| Manifest minSdk/targetSdk | `manifest_reader.cpp:470-472` | METADATA ONLY |
| `ApplicationInfo.targetSdkVersion` | `android_context.h:320` (default 30, no readers) | DEAD FIELD |
| Version-gated framework behavior | — | NOT MODELED |

**Conclusion:** MiniAndroid models ONE device profile under AOSP-14 laws
plus the resource version-qualifier law (48/48 law-tested). An APK×API9×
API10 matrix would run the SAME engine twice — two identical columns would
be fake version evidence, so the matrix is refused and recorded
**NOT APPLICABLE as a runtime switch**. The real, testable version axis on
the corpus: declared minSdk 4..28 and per-APK v-qualifier buckets. A modeled
API-level axis (SDK_INT seeding switch + qualifier device value + per-API
dispatch deltas) is FUTURE work; this audit is its design baseline.
Phase 8 (9/10 loop): NOT APPLICABLE — no second version axis exists to
regress across.

Status: RESEARCHED (audit) — evidence-anchored, not label-driven.""",
    },
    {
        "key": "g09_phase9_ranking",
        "body": f"""## G09 — PHASE 9: NEXT-CAMPAIGN IMPACT RANKING (real corpus evidence decides)

IMPACT = #APKs × severity × architectural reuse × law confidence.

| Rank | Candidate | Evidence |
|---|---|---|
| **1** | **ListView/TableRow child-measure law (F8)** | microtimer keypad collapsed (12 buttons, 0 visual) + billthefarmer rows collapsed — 2 structurally different APKs, same symptom, high AOSP-law confidence |
| 2 | AppCompat shell campaign, ENTRY LAW = AppComponentFactory (F5) | 6/18 apps declare `android:appComponentFactory`; muellerma dies pre-onCreate with NoClassDefFoundError (FIND-G09-ACF-001) |
| 3 | Component-less/implicit Intent resolution (F10) | 2/18 real hits in probed flows (chessclock settings, unote addNote) |
| 4 | Custom-View onDraw/measure dispatch (F8/F9) | headingcalculator: CalculatorDisplay measured 1080x0, CalculatorKeypad draws nothing |

Preselection refused: implicit Intent was on the old boundary list, but the
corpus ranks it #3 — behind F8 and the AppCompat shell.

Full report: `docs/evidence/G09_FINAL_REPORT.md` (§F). Status: RESEARCHED
(ranking grounded in executed runs).""",
    },
]


def api_request(url, method="GET", payload=None):
    with open(TOKEN_PATH, "r", encoding="utf-8") as fh:
        token = fh.read().strip()
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "miniandroid-g09-evidence")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        with open(TOKEN_PATH) as fh:
            detail = detail.replace(fh.read().strip(), "<token>")
        return e.code, {"error": detail}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": f"{type(e).__name__}: {e}"}


def main() -> int:
    status, me = api_request("https://api.github.com/user")
    if status != 200:
        print(f"AUTH_VERIFY_FAILED: HTTP {status}: {me.get('error','')[:200]}")
        return 1
    print(f"auth OK: {me.get('login')}")
    issue = f"{API}/issues/8"
    st, cur = api_request(issue)
    if st != 200:
        print(f"ISSUE_FETCH_FAILED: HTTP {st}: {cur}")
        return 1
    print(f"issue #8: {cur.get('title')} (comments={cur.get('comments')})")

    urls = {}
    try:
        urls = json.load(open(RESULTS))
    except Exception:  # noqa: BLE001
        pass
    for c in COMMENTS:
        st, resp = api_request(f"{issue}/comments", "POST",
                               {"body": c["body"]})
        if st == 201:
            url = resp.get("html_url", "")
            urls[c["key"]] = url
            print(f"POSTED {c['key']} → {url}")
        else:
            print(f"PUSH/COMMENT BLOCKED for {c['key']}: HTTP {st}: "
                  f"{str(resp.get('error',''))[:200]}")
    json.dump(urls, open(RESULTS, "w"), indent=2)
    print(f"urls recorded → {RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
