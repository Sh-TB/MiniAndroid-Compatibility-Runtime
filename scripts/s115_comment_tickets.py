#!/usr/bin/env python3
"""S115 — post fresh-status comments on the 77 NEAR_BLANK tickets (assembly-line sweep results).
English only (user directive: no Persian on GitHub). Honest: no closure under the render law."""
import json, os, time, urllib.request
from pathlib import Path

BASE = Path('/home/z/my-project')
REPO = 'Sh-TB/MiniAndroid-Compatibility-Runtime'
TOKEN = open('/tmp/.gh_token').read().strip()
state = json.load(open(BASE / 'run/s115_sweep/state.json'))
fams = json.load(open(BASE / 'run/s115_sweep/families_norm.json'))

HEAD = 'f191f839'

FAMILY_TEXT = {
    'rc0-silent (no throwable)': (
        'Empty-view-tree frontier (rc=0, 0 errors): lifecycle dispatches fully '
        '(onCreate -> onStart -> onResume via the DEX engine) but the content view never '
        'materializes — attach reports 0 view nodes. Shared frontier: #344 blank-render L0 family; '
        'Compose `setContent` (#230) / appcompat inflation (#348) variants. '
        'The S114 HTML5/WebView engine laws do NOT apply to this family (native View path, not WebView).'),
    'rc1-silent (no throwable)': (
        'Empty-view-tree frontier with recorded non-fatal errors: lifecycle dispatches but the '
        'content view never materializes (0 view nodes at attach). Shared frontier: #344 family. '
        'The S114 HTML5/WebView engine laws do NOT apply to this family (native View path, not WebView).'),
    ' IllegalStateException :: This app has been built with an incorrect configuration': (
        'libGDX native-library loading frontier: `GdxNativesLoader` throws before any view exists — '
        'APK-packaged .so loading + JNI registration capability.'),
    ' AssertionError :: Next event must be ON_CREATE': (
        'androidx LifecycleRegistry event-sequencing frontier: state machine receives a non-ON_CREATE '
        'event during initialization — generic lifecycle law, no app code involved.'),
    ' IllegalStateException :: FragmentManager has not been attached to a host.': (
        'androidx Fragment host-attachment frontier: FragmentManager is consulted before the host '
        'activity publishes it — generic fragment lifecycle law.'),
    ' RuntimeException :: MultiDex installation failed (Attempt to invoke interfa': (
        'MultiDex install frontier: `MultiDexApplication`/`MultiDex.install()` path requires the '
        'instrumentation + secondary-DEX directory contract.'),
    ' IllegalStateException :: ViewTreeLifecycleOwner not found from Lb00;@1362': (
        'androidx ViewTreeLifecycleOwner lookup frontier: set-content runs before the '
        'lifecycle-owner view-tree tag is published — generic androidx compat law (#348 family).'),
    ' IllegalStateException :: ViewTreeLifecycleOwner not found from Lxm0;@643': (
        'androidx ViewTreeLifecycleOwner lookup frontier: set-content runs before the '
        'lifecycle-owner view-tree tag is published — generic androidx compat law (#348 family).'),
}

SPECIAL = {
    191: 'Real pixels render (weather text, -- °C) but fragments OVERLAP at the top-left — layout collision, not a blank. NOT complete under the render law (content correct placement required).',
    216: 'Real UI text renders (menu items "Use imperial system" / "Delete this city", dialog buttons "OK"/"Cancel") but positioned at the bottom of a blank body — layout origin frontier. PARTIAL, NOT complete under the render law. Same plain-WebView family as blockbuster (#353 anchor).',
    219: 'Real pixels render (white/black text band at the bottom of a dark screen) — arrival-board strip only. PARTIAL, NOT complete.',
    212: 'A toolbar-like strip renders at the top (540 px band); the editor body never materializes. PARTIAL, NOT complete.',
    87: 'APK download was CORRUPT (PARSE_ERROR: no end-of-central-directory) — the runtime never parsed it. Needs a fresh APK fetch; not a runtime frontier.',
    107: 'APK download was CORRUPT (PARSE_ERROR: no end-of-central-directory) — the runtime never parsed it. Needs a fresh APK fetch; not a runtime frontier.',
    120: 'APK download was CORRUPT (PARSE_ERROR: no end-of-central-directory) — the runtime never parsed it. Needs a fresh APK fetch; not a runtime frontier.',
    185: 'APK download was CORRUPT (PARSE_ERROR: no end-of-central-directory) — the runtime never parsed it. Needs a fresh APK fetch; not a runtime frontier.',
    206: 'APK download was CORRUPT (PARSE_ERROR: no end-of-central-directory) — the runtime never parsed it. Needs a fresh APK fetch; not a runtime frontier.',
}

def api(path, data):
    url = f'https://api.github.com/repos/{REPO}/{path}'
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Accept', 'application/vnd.github+json')
    with urllib.request.urlopen(req) as r:
        return json.load(r)

# reverse map ticket -> normalized family key
ticket_family = {}
for k, nums in fams.items():
    for n in nums:
        ticket_family[str(n)] = k

posted = 0
for key in sorted(state, key=int):
    rec = state[key]
    n = rec['ticket']
    pkg = rec['package']
    v = rec.get('verdict', '?')
    fam = ticket_family.get(key, 'unknown')
    ftext = FAMILY_TEXT.get(fam, f'Family: `{fam.strip()}` — per-ticket frontier, batch evidence in the sweep report.')
    special = SPECIAL.get(n)
    metrics = (f"rc={rec.get('rc')} errors={rec.get('errors')} "
               f"screenshot={rec.get('res', 'none')} "
               f"unique_colors={rec.get('unique_colors', 0)} non_bg={rec.get('nonbg_ratio', 'n/a')}")
    body = f"""## S115 fresh re-run at S114 HEAD `{HEAD}` — 77-ticket assembly-line sweep (1 run/ticket, no per-ticket debugging)

**Verdict: NOT closed under the render law.** Fresh status at the current HEAD with the S114 HTML5/WebView engine laws landed.

| run metric | value |
|---|---|
| rc / errors | {metrics} |
| verdict | {v} |

{special if special else ftext}

*Batch context: all 77 NEAR_BLANK tickets were re-run at this HEAD in one assembly-line sweep — dominant shared frontier is the empty-view-tree family (lifecycle completes, 0 view nodes at attach: #344/#230/#348); libGDX-native, Godot-native, lifecycle-sequencing, Fragment-host and MultiDex families are the smaller clusters. The next shared-family fix will re-sweep this ticket automatically. Fresh evidence: `evidence/s115_sweep/t{n}_{pkg}/` (run.log + screenshot). Honest per the visual-evidence law: this is a status update, not a closure.*"""

    try:
        api(f'issues/{n}/comments', {'body': body})
        posted += 1
        print(f'#{n} posted ({v})')
    except Exception as e:
        print(f'#{n} FAILED: {e}')
    time.sleep(0.25)

print(f'DONE: {posted}/77 comments posted')
