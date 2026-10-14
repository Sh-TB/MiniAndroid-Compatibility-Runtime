#!/usr/bin/env python3
"""cont46_issue_comment.py — post the CONT-46 line-by-line audit to Issue #375.
Reads the final numbers from the evidence ledger; requires GH_TOKEN in env.
"""
import json, os, sys, urllib.request

EVID = 'evidence/cont46/CONT46_RESULT.md'
body = open(EVID).read()

header = """## CONT-46 execution-stage audit — revalidation on current HEAD + the generic DEX↔Bridge object-flow contract

**Lineage**: continued from remote HEAD `8f2f6aab4f0f54e77f6081de03e483b89b198ccd` (CONT-45) after stale-snapshot recovery. Pre-fix binary `56c04526…`, post-fix binary `a63bf3b5…` (16-prefix forms). Every row below is STATUS — RESULT — EVIDENCE with exact artifacts; nothing is claimed DONE beyond its row.

### Executive verdict (honest)
- **F-NEW-260 / F-NEW-261: revalidated as LIVE INCREMENTS** on the rebased tree (probe 13/13 + runtime rows; neither was subsumed by the remote's newer laws).
- **F-NEW-262 re-classified per-manifestation**: m1 (BMI `mHandler`) RE-ROOTED — the true first divergence is a *resurrected* EXP-058 blanket `Preconditions.checkNotNull` name-gate (regression re-introduced by commit `d7427016` after R-NEW-365/S47/F-058 had removed it; the docs survived, the code fix was lost) — **FIXED (F-058-R)** at probe level (CK-1..3 FAIL→PASS) and runtime level (`mHandler` `<unset>`→`obj#29`; the full support-fragment machine now executes). m2 (solitaire) **SUPERSEDED** on the current lineage (the recorded IAE no longer reproduces; new first divergence = F-NEW-309). m3 (notes) **BLOCKED** behind the S83 androidx-bypass scope (experimental fall-through arm required; deliberately not shipped).
- **F-NEW-309 appended** (solitaire DrawerLayout drawer-gravity root, CLASSIFIED with static decode).
- **Regression**: full gate on the post-fix binary = 33/33 anchors ×3 byte-identical, csw ×3 REGAINED face, probe battery == records exactly, skill 13/13.
- **BMI is NOT REAL_APP_CONTENT yet** — the fix moves it past its recorded first divergence (transaction machine executes) into a precisely-located SECOND blocker: the v7 delegate's `inflate(resId, mContentParent)` leg (app layout root 78 never attached under the id-swapped ContentFrameLayout 163 — `[P0-1-ORDER] first-traversal attach wave root=78 attached=0`).

"""

tail = """

### Artifacts
- Evidence bundle: `evidence/cont46/CONT46_RESULT.md` (this wave's full ledger)
- Registries: `root_registry.json` (F-NEW-262 re-classification + F-NEW-260/261 revalidation rows + F-NEW-309 appended)
- Probes: `fixtures/fnew262_probe` (bridge↔DEX object-flow + CK identity rows), `fixtures/fnew260_probe` (getModifiers zoo, OpenJDK-21-oracle-corrected)
- Harnesses: `scripts/cont46_{refetch_apks,build_hmap,build_probes,phase0_gate,post_fix_gate,fanout,registry,disasm}.sh/.py`
- Runs: `run/cont46/` (pre/post A/B faces, traces, view trees, gates)
- Commit: d80351ed (pushed to main; binary a63bf3b53ac3c082)

### Next bounded steps (exact, not vague)
1. **BMI delegate content-parent attach law**: decode why the shadow `Activity.setContentView(res)` path's first-traversal attach wave attached 0 of root 78 after the real-DEX delegate id-swapped `android.R.id.content` → node 163 (AOSP law: `AppCompatDelegateImpl.setContentView(int)` inflates the app layout INTO the subdecor's content parent). Fix shape: the attach wave must target the CURRENT content parent (the F-NEW-220 id-swapped node), not the pre-subdecor record. Probe: extend fnew262_probe with a delegate-host row; A/B = BMI ViewTree (root 78 under 163) ×3.
2. **F-NEW-309**: inflater `generateLayoutParams` attr-resolution law for LayoutParams subclasses (`DrawerLayout$g.a` gravity); drawer probe positive/negative; solitaire re-run ×3.
3. **androidx fall-through experimental arm** (F-NEW-262 m3 + AlexCalc): one-line gate extension, notes/AlexCalc A/B, probes, revert-or-land by measurement.
4. Sibling EXP-058 stub audit (SkippingHelper19 / HelperInternal / AppCompatTextViewAutoSizeHelper): each needs its own probe + A/B before removal (minimal-fix discipline).
"""

full = header + body + tail

token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
repo = 'Sh-TB/MiniAndroid-Compatibility-Runtime'
api = f'https://api.github.com/repos/{repo}/issues/375/comments'
req = urllib.request.Request(api, data=json.dumps({'body': full}).encode(),
    headers={'Content-Type': 'application/json',
             'Authorization': f'Bearer {token}' if token else ''})
if not token:
    print('NO GH_TOKEN — writing comment body to evidence/cont46/issue_comment.md')
    open('evidence/cont46/issue_comment.md', 'w').write(full)
    sys.exit(0)
try:
    with urllib.request.urlopen(req) as r:
        resp = json.load(r)
        print('comment posted:', resp.get('html_url'))
except Exception as e:
    print('post failed:', e)
    open('evidence/cont46/issue_comment.md', 'w').write(full)
    sys.exit(1)
