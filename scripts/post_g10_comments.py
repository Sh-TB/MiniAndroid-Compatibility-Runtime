#!/usr/bin/env python3
"""Post the G10 evidence comments to Issue #8 and record direct URLs.

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
C = lambda p: f"{BASE}/blob/main/{p}"
REPORT = C("MiniAndroid-Compatibility-Runtime/docs/evidence/g10_evidence/G10_FINAL_REPORT.md")
VIS = "MiniAndroid-Compatibility-Runtime/docs/evidence/g10_evidence/visual"
TEST = "MiniAndroid-Compatibility-Runtime/miniandroid/tests/g10_layout_law_test.cpp"

COMMENTS = [
    {
        "key": "g10_phase0_baseline",
        "body": f"""## G10 — PHASE 0 BASELINE (48/48 at start HEAD, engine untouched) + PHASE 1 clusters

Start HEAD: **`ae98a23f`** (G09 final) with `3c9b7001` on top — verified a
**0-line engine diff** between the two (G09 publication tooling only).

**Environment restore BEFORE baseline (no engine change):** the sandbox
reset had wiped the gitignored toolchain + corpus cache. Restored with
SHA verification: aapt2 8.13.2-14304508 (Google Maven, Apache-2.0) —
`Android Asset Packaging Tool (aapt) 2.20-14304508`; HelloWorldSelfAware
APK re-fetched **byte-exact** `009b467109c4…`; 15/18 corpus APKs restored
hash-exact, 3 previously-documented G09 upstream drifts untouched
(Telegram live, OpenLauncher re-drift `b7900f56→4d20608d` recorded,
TinyMusicPlayer dead URL).

**Baseline battery: 48/48 stage gates ALL PASS at `3c9b7001`.**
Frozen goldens reproduced byte-identically: simplestopwatch `ed1dfc89…`,
gmdice `db0f4c4b…`.

**Selected corpus (Rule 1 — same set before AND after every fix), 7 real APKs:**
required F8 failures `dubrowgn.microtimer_8` (`79c6f730…`),
`org.billthefarmer.notes_139` (`82cf8bc4…`),
`org.debian.eugen.headingcalculator_1` (`274ec873…`) + structurally
different same-mechanism guards gmdice / simplestopwatch / unote / chessclock.

**Measure/layout evidence recorded BEFORE any code change** (per APK:
root → hierarchy → lp/weight/orient → measured → bounds → pixels):
- {C("MiniAndroid-Compatibility-Runtime/docs/evidence/g10_evidence/phase0_baseline_BEFORE.json")} · [traces]({C("MiniAndroid-Compatibility-Runtime/docs/evidence/g10_evidence/phase0_traces_BEFORE.json")}) · per-APK `*_layout_trace.log`

Key baseline facts (evidence, not assumption):
1. microtimer `res/v9.xml` keypad/input rows (lines 31/66/87/108/130) carry
   **NO `android:orientation`** → runtime `orient=-1` → buttons stacked
   VERTICALLY into the left column (trace: btn1/2/3 each 23×44 in one column).
2. headingcalculator DEX class_defs: `CalculatorDisplay extends
   Landroid/widget/LinearLayout;`, `CalculatorKeypad extends
   Landroid/widget/LinearLayout;` — leaf-name substring matching missed both;
   display measured `1080x0`.
3. microtimer `RoTimeControl extends Landroid/widget/FrameLayout;` (DEX).
4. billthefarmer inflate log: `root_id=11 views=7` but the measured tree
   held ONLY the FAB ViewSwitcher (degraded to `Landroid/view/View;`) —
   the `<merge>` handler returned the LAST merged child as root and
   orphaned the main editor subtree.
5. unote delete-search ImageButton `layout_gravity=0x00800015`
   (centerVertical|right|directional).

**Phase 1 clusters (evidence-derived, NOT assumed):**

| Cluster | Violated AOSP law | Independent APKs |
|---|---|---|
| F8-C-DEFAULT | LinearLayout orientation field default = HORIZONTAL (field init + `a.getInt(..., HORIZONTAL)`) | microtimer (5 containers); XML census: 9 orientation-less LLs in KISS, 22 in markor, 5 in fossify |
| F8-B-SUPER | container behavior follows the RESOLVED SUPERCLASS CHAIN (virtual onMeasure dispatch) | headingcalculator ×2 classes, microtimer RoTimeControl, billthefarmer ViewSwitcher |
| F8-A-MERGE | `<merge>` children attach to the parent; at root the parent is the window content frame | billthefarmer |
| F8-G-GRAV | Gravity axis-field equality — mask 0x7 / 0x70 BEFORE compare | billthefarmer FAB `0x00800055`, unote `0x00800015` |

Status: RESEARCHED → Phase 0 + 1 COMPLETE (baseline recorded, engine untouched).""",
    },
    {
        "key": "g10_laws_fixes",
        "body": f"""## G10 — PHASE 2: AOSP LAWS TRANSFERRED → 5 GENERIC FIXES (zero package branches)

All fixes in **`2df49003`** + classifier early-wiring in **`e6e51648`**.
Every fix is keyed on class/attribute SEMANTICS — no package names, no
class-name special cases, no fixture branches.

| Fix | AOSP law (source of truth) | Earliest divergence fixed |
|---|---|---|
| **FIX-G10-001** | LinearLayout.java: `mOrientation` field init + styled-attr default = **HORIZONTAL**; runtime treated never-set (−1) as vertical | microtimer keypad rows rendered as a left column; input row double-height |
| **FIX-G10-002** | Class-hierarchy law: container measure/layout semantics follow the resolved superclass chain (virtual dispatch) | headingcalculator CalculatorDisplay/CalculatorKeypad (both `extends LinearLayout`) measured as content-less leaves; ViewSwitcher degraded to `View` → FAB switcher 0×0 |
| **FIX-G10-002b** | ViewAnimator.`showOnly(0)`: at inflation only the FIRST child is visible, rest GONE until showNext | billthefarmer switchers overlapped both children (edit-over-accept FABs; preview over editor) |
| **FIX-G10-003** | LayoutInflater `<merge>` law: children attach to the parent; at root synthesize the window-content FrameLayout (PhoneWindow contentParent) | `return last` orphaned every earlier merge child — billthefarmer's main editor never existed in the render tree |
| **FIX-G10-004** | Gravity axis-field equality (mask `0x7`/`0x70` first — same law family as G04's LinearLayout fix) | `bottom\\|end 0x00800055` has bit0+0x10 set → raw bit tests turned RIGHT/BOTTOM into CENTER (billthefarmer FAB centered; unote button centered instead of right) |

Framework hierarchy seed extended with AOSP-factual entries
(ViewAnimator→FrameLayout; ViewSwitcher/ViewFlipper→ViewAnimator;
TableLayout/TableRow/RadioGroup→LinearLayout; GridLayout/Toolbar→ViewGroup)
+ the tag table keeps REAL descriptors for ViewSwitcher/ViewFlipper/
ViewAnimator/RadioGroup. The DEX-backed `is_subclass_of` classifier is wired
into the inflater at inflate time (`e6e51648`) so the FIRST measure pass is
already ancestry-correct (billthefarmer FAB switcher: 0×0 → 126×126
immediately).

Diff: [2df49003]({BASE}/commit/2df49003) · [e6e51648]({BASE}/commit/e6e51648)

Status: IMPLEMENTED → validated in the next comment.""",
    },
    {
        "key": "g10_crossapk_validation",
        "body": f"""## G10 — PHASE 3/4/5/6: SAME-CORPUS VALIDATION + HOSTILE LAWS + 50/50 REGRESSION

**Before/after on the SAME 7-APK set (Phase 7 table, per-APK):**

| APK | Initial (G09) | Cluster | After (G10) | Visual proof |
|---|---|---|---|---|
| microtimer | PARTIAL — keypad collapsed to left column | F8-C-DEFAULT | **improved** — rows 1/2/3·4/5/6·7/8/9·00/0 horizontal; input row = btnClear + weighted time view + btnBackspace on ONE line (row height 252→126) | [BEFORE]({C(VIS + "/microtimer_BEFORE_collapsed.png")}) → [AFTER `57503a129012`]({C(VIS + "/microtimer_AFTER_rows_57503a12.png")}) |
| billthefarmer notes | PARTIAL — 2 collapsed boxes top-left, editor subtree missing | F8-A-MERGE + F8-B-SUPER + F8-G-GRAV | **improved, structure rendered** — editor bar top, FAB 126×126 bottom-right, preview lawfully hidden; clicks dispatched 2→3 (FAB now probed) | [BEFORE]({C(VIS + "/billthefarmer_BEFORE_collapsed.png")}) → [AFTER `06ba8026b670`]({C(VIS + "/billthefarmer_AFTER_editor_fab_06ba8026.png")}) |
| headingcalculator | BLANK — custom views 1080×0 | F8-B-SUPER | **unchanged pixels** — classification now law-correct (LinearLayout containers in trace) but app constructors never ran (children=0, onDraw 0 ops) → earliest blocker is BELOW F8 (F4/F5 app-code execution); classified, not patched | — |
| gmdice | RENDERED | — | **unchanged** `db0f4c4b` (G09 golden intact) | G09 |
| simplestopwatch | RENDERED | — | **unchanged** `ed1dfc89` (G09 golden intact) | G09 |
| unote | RENDERED | F8-G-GRAV | **improved (lawful placement)** — delete-search button `0x00800015` moved from wrong CENTER to its declared RIGHT edge | [BEFORE]({C(VIS + "/unote_BEFORE.png")}) → [AFTER `8197687f`]({C(VIS + "/unote_AFTER_gravity_8197687f.png")}) |
| chessclock | PARTIAL (null data — F5 data layer) | — | **unchanged** `4f327614` (all its LinearLayouts declare orientation) | — |

**Regressions: 0.** Guard screenshots byte-identical; G09 frozen goldens intact.

**Determinism (3 runs each):** microtimer `57503a129012` ×3 ·
billthefarmer `06ba8026b670` ×3 — real-APK frames, not fixtures.

**Honesty boundaries (Phase 3 rule):** FIX-G10-001/002/004 = **CROSS-APK
VERIFIED** (001: microtimer + markor/KISS/fossify XML census; 002: microtimer +
headingcalculator + billthefarmer; 004: billthefarmer + unote).
FIX-G10-003 (merge law) has only ONE current corpus exerciser →
**IMPLEMENTED + LAW-TESTED**, explicitly NOT CROSS-APK VERIFIED.

**Hostile law tests (Phase 5):** [`g10_layout_law_test.cpp`]({C(TEST)}) —
**23 checks, 0 failures**, package-independent synthetic trees: orientation
default (row positions + weight + vertical regression guard), chain
classification (app-subclass → LinearLayout measure), TableRow columns via
chain, GONE slot law, oversized 4000px child clamp, zero-height container,
margin chain arithmetic, gravity axis fields (`0x00800055` → bottom-right,
`0x11` → center, `0x30` → origin), ViewSwitcher chain resolution.

**Phase 6 regression:** full battery extended 48 → **50 stage gates
(48 existing intact + 2 new G10 law stages) — ALL PASS at `e6e51648`**;
EXT-01/02, density oracle, G06/G07/G08 goldens + 3-run determinism,
corpus stages all green.

Status: CROSS-APK VERIFIED (3 fixes) + IMPLEMENTED/LAW-TESTED (merge law)
+ REAL-APK TESTED corpus — Phase 3–6 COMPLETE.""",
    },
    {
        "key": "g10_impact_ranking",
        "body": f"""## G10 — PHASE 7/8: IMPACT SCORE + NEXT-CAMPAIGN RANKING (recomputed from the post-G10 corpus)

**IMPACT = APKs improved × severity × architectural reuse × AOSP-law confidence**

| Rank | Fix | APKs | Severity | Reuse | Law confidence | Score rationale |
|---|---|---|---|---|---|---|
| 1 | FIX-G10-001 orientation default | 1 now + 3 shell APKs pre-unblocked | high (whole-UI collapse) | very high (every orientation-less LinearLayout) | high | dominant |
| 2 | FIX-G10-002 superclass chain | 3 | high | very high (all custom framework subclasses) | high | |
| 3 | FIX-G10-004 gravity axis mask | 2 | medium | high (every FrameLayout child gravity) | high | |
| 4 | FIX-G10-003 merge root | 1 | high | medium (merge-tag layouts) | high | LAW-TESTED only |
| 5 | FIX-G10-002b ViewAnimator | 1 | low-medium | medium | high | |

**Campaign totals:** 4 generic AOSP laws + 1 initial-child law implemented;
**3 APKs improved** (microtimer, billthefarmer, unote), **0 regressions**,
**0 newly fully-rendered** — honest accounting: microtimer/billthefarmer each
advanced one visible-law layer (billthefarmer = blank→structured transition of
its main surface), both remain below full renders for the reasons recorded
below. **15/18 corpus APKs still blocked at their next-layer causes.**

**Recomputed next-campaign ranking (evidence-driven, per G10 Phase 8 rule):**

1. **F5 app-constructor execution + addView interception** — headingcalculator's
   remaining blocker generalized: app-defined ViewGroups never run their
   constructors, so programmatic children (keypad buttons, display children)
   never exist; onDraw dispatch returns 0 ops for the same reason. Same layer
   as muellerma's `NoClassDefFoundError` ACF chain (FIND-G09-ACF-001) and the
   cap on microtimer's Start button. Highest remaining reuse; F8 as a pure
   measurement surface is exhausted at this law layer.
2. **AppCompat/AppComponentFactory shell** (11/18 corpus APKs) — unchanged from
   G09; still the widest single unblock.
3. **F10 component-less/implicit Intent** (chessclock, unote addNote) — unchanged.
4. **F8 residuals, declared:** style/background-driven minimum dimensions
   (text-less Buttons measure 0×0 — chessclock Menu/Pause), NinePatch
   intrinsic sizes. Deferred — not the earliest blocker of any currently
   visible APK.

Full report: [G10_FINAL_REPORT.md]({REPORT})
(baseline/trace JSONs + 7 layout-trace logs + 6 before/after frames under
`docs/evidence/g10_evidence/`).

Status: G10 CLOSED — RESEARCHED / IMPLEMENTED / TESTED / REAL-APK TESTED /
RUNTIME-PROVEN / VISUALLY-PROVEN per-fixture; CROSS-APK VERIFIED per-fix as
marked above.""",
    },
]


def api_request(url, method="GET", payload=None):
    with open(TOKEN_PATH) as fh:
        token = fh.read().strip()
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", "application/json")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:  # noqa: BLE001
            return e.code, {"error": str(e)}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


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
    ok = True
    for c in COMMENTS:
        st, resp = api_request(f"{issue}/comments", "POST", {"body": c["body"]})
        if st == 201:
            url = resp.get("html_url", "")
            urls[c["key"]] = url
            print(f"POSTED {c['key']} → {url}")
        else:
            ok = False
            print(f"PUSH/COMMENT BLOCKED for {c['key']}: HTTP {st}: "
                  f"{str(resp.get('error',''))[:200]}")
    json.dump(urls, open(RESULTS, "w"), indent=2)
    print(f"urls recorded → {RESULTS}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
