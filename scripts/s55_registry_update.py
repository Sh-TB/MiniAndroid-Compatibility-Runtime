#!/usr/bin/env python3
# S55 registry update — R-NEW-361 verdict change (F-083), R-NEW-376 pinned
# frontier, R-NEW-377 (F-082 ViewAnimator law). Appends/updates entries in
# root_registry.json per the canonical schema (id/status/priority/title/
# discovered/fixed/evidence).
import json

PATH = '/home/z/my-project/root_registry.json'
with open(PATH) as f:
    reg = json.load(f)

roots = reg['roots']

def find(rid):
    for e in roots:
        if e.get('id') == rid:
            return e
    return None

# ── R-NEW-361: the standing Dooz blocker — FIXED at its root by F-083 ──
e361 = find('R-NEW-361')
assert e361, 'R-NEW-361 missing'
e361['status'] = 'VERIFIED-FIXED'
e361['priority'] = 'P1'
e361['fixed'] = 'S55 (F-083)'
e361['evidence'] += (
    ' | S55 ROOT-CAUSE+FIX (F-083): the probe spin was DOWNSTREAM. Env-gated '
    'dispatch trace (MINIANDROID_F040_DIAG) proved 55 of 56 Ln/a;.r '
    '(Kotlin LongArray-fill helper) invocations executed with their '
    'Arrays.fill dispatch SUCCESS, but the 56th — Lh/r;.d initializing map '
    'o5051 — entered try_recursive_invoke at depth=80 == MAX_RECURSION_DEPTH '
    'and was SILENTLY dropped onto the API bridge (log() is verbose-only). '
    'EXP-053 law: each DEX frame costs ~80KB C++ stack → 80-frame cap under '
    'the 8MB process stack. Dropped void initializer → metadata stayed '
    'heap-zero; Lh/r;.d pc=48 aput-wide then wrote 0xff007f6600000000 '
    '(ghost bytes, zero EMPTY 0x80) vs the correct 0xff80808080808080 seen '
    'on all healthy maps ([R361-STORE] traces) → findImpl probe never '
    'terminates → HALT-LOOP → synthetic aput-oob. FIX F-083 (generic, no '
    'interpreter-layout change): (1) cmd_run executes the engine on a '
    'dedicated pthread with a 1GB VIRTUAL stack (Linux commits on touch; '
    'ART contract: app recursion is bounded by the thread stack, not a '
    'frame count); (2) MAX_RECURSION_DEPTH 80 → 2048 (2048 × 80KB ≈ 164MB '
    'worst case, inside the reservation); (3) limit-drop is now ALWAYS '
    'loud ([RECURSION-LIMIT] stderr) — a dropped void initializer is a '
    'state-corrupting event and must never be silent. POST-FIX RUN: no '
    'HALT-LOOP, no aput-oob, metadata init correct, MainActivity.'
    'onStart/onResume dispatched for the first time in campaign history. '
    'HYGIENE: F-074 super-dispatch trace was ALWAYS-ON stderr incl. a heap '
    'message lookup per inherited call — throttled Compose-heavy apps to '
    '~1.6K instr/s (Dooz could not reach first frame in 10 min); now '
    'env-gated (MINIANDROID_F074_TRACE), law code unchanged. SUCCESSOR: '
    'R-NEW-376 (post-F-083 ctor-climb frontier).')

# ── R-NEW-376: the new precise Dooz frontier (pinned, not fixed) ──
e376 = {
    'id': 'R-NEW-376',
    'status': 'OBSERVED-FAIL',
    'priority': 'P1',
    'title': ('Dooz v18 post-F-083 frontier: Compose init builds constructor-'
              'invocation chains that exceed the 2048-frame depth budget '
              '(9 cap-climbs in one run: Lj/j0;.<init> ×7 [okhttp-family: '
              'extends LB/b;, ctor delegation LinkedHashMap,I→Map overload '
              'verified in DEX], Lt0/t;.<init>+LE0/c;.<init> ×2 [t0/t↔E0/c '
              'alternation: t0/t.<init> invokes LE0/c;.<init>(J)V, E0/c '
              'extends LB/b; with an if(j!=0) throw IllegalArgumentException '
              'guard on its long field]) — each climb costs 2048 × 80KB '
              'committed stack + interpreter work, so the run cannot finish '
              'in budget (rc=124 at ~900K instructions; diag tracing '
              '~1.6-5K instr/s); a cap-drop leaves the half-initialized '
              'object corrupt (same law as R-NEW-361)'),
    'discovered': 'S55',
    'fixed': '',
    'evidence': (
        'miniandroid/run/s55_dooz_hop2/diag_stderr.log (key excerpts in '
        'docs/evidence/s55_dooz/). [TRI-F040] hop chain: j/A;.c → j0.<init>'
        '(argc=8) depth=49 → j0.<init>(argc=7) depth=50 → j0.<init>(argc=7) '
        'depth=51→…∞ same receiver o5197 (cyclic this()-delegation is '
        'impossible in valid DEX → engine mis-dispatch or retry loop). '
        '[R376-DIRECT]: t0/t.<init> → LE0/c;.<init>(J)V argc=2 alternates '
        'with LE0/c.<init> → Object.<init> no-op; every resolved target is '
        'LEGAL — the loop driver is NOT a wrong-resolution invoke. '
        'LE0/c;.<init>(J)V body (DEX-verified): iput-wide a:J; sget X/r.g:J; '
        'if-nez → throw IllegalArgumentException; the runtime shows NO '
        'IllegalArgumentException — guard not firing. NEXT (ranked): '
        '(1) extend [TRI-F040] to print the wide arg VALUES per t0/t↔E0/c '
        'hop — constant long across hops ⇒ self-delegation mis-dispatch; '
        'varying ⇒ finite-but-huge chain (raise budget / shrink 80KB frame '
        'cost); (2) if mis-dispatch: instrument execute_invoke_direct '
        'ctor-target selection for the t0/t overload set (15 ctor overloads '
        'observed at one depth); (3) M3-19 active-cycle law exempts <init> '
        'from stubbing (correct — stub ctors return garbage) but gives '
        'ctor-cycles NO termination — evaluate a bounded synthetic '
        'StackOverflowError unwind (ART law) for pure-ctor cycles. REPRO: '
        'MINIANDROID_F040_DIAG=1 ./miniandroid/build/miniandroid run '
        'apk_cache/io.github.yamin8000.dooz_18.apk; v23 expected to '
        'converge (R-NEW-361 face already converged).'),
}
if not find('R-NEW-376'):
    roots.append(e376)

# ── R-NEW-377: the Notes ViewSwitcher law (F-082) ──
e377 = {
    'id': 'R-NEW-377',
    'status': 'VERIFIED-FIXED',
    'priority': 'P1',
    'title': ('billthefarmer Notes v139 renders RENDER_ONLY: FAB click '
              'swapped NOTHING — ViewSwitcher.setDisplayedChild (the '
              'read<->edit face state machine) was a REC-MISS silent no-op '
              '(no ViewAnimator family law in ViewShadow). S53-era '
              '"ListView item paint" hypothesis REFUTED by S55 tree '
              'forensics: v139 has NO ListView — main layout = FrameLayout '
              '→ ViewSwitcher[ScrollView+EditText | MarkdownView] + FAB '
              'ViewSwitcher[2× ImageButton]'),
    'discovered': 'S55',
    'fixed': 'S55 (F-082)',
    'evidence': (
        'F-082 (generic, AOSP ViewAnimator.java law): setDisplayedChild/'
        'getDisplayedChild/showNext/showPrevious on the ViewShadow node '
        'model — AOSP clamp (whichChild >= count → count-1; < 0 → 0; exact '
        'formula covers the childless case), showOnly visibility walk '
        '(child i VISIBLE iff i == whichChild, others GONE), requestLayout '
        'dirty flag. Regression: tests/view_animator_law_test.cpp — 18 '
        'checks (clamp high/low, walk, no-wraparound end pins, get law, '
        'childless hostile, dispatch closure), ALL PASS, wired into the '
        'battery as "F-082 ViewAnimator law (expect 15)" [18 actual]. '
        'RUNTIME PROOF: Notes v139 --click-test FAB → animateAccept → '
        'setDisplayedChild → frame delta 2,057,718 px (99.23% of frame), '
        'probed=3 state_changed=1 (was 0/3 at S53); click frames '
        'byte-identical across two binaries/runs (SHA256 in '
        'docs/evidence/s55_notes*/SHA256SUMS: cf521b16… / ae697935…). '
        'REMAINING (honest, NOT app-specific patchable): note CONTENT still '
        'blank-class — the read face is Lorg.billthefarmer.markdown.'
        'MarkdownView which extends Landroid/webkit/WebView (runtime dex '
        'parser verified); getSettings/setWebViewClient REC-MISS → the '
        'markdown load pipeline never starts → honest inline placeholder. '
        'Next dependency = a generic WebView content model (P1 shared '
        'framework); implementing it app-specifically is forbidden per the '
        'campaign scope laws. Editor face (ScrollView+EditText) inflates, '
        'measures and renders; fresh data dir = empty note is CORRECT.'),
}
if not find('R-NEW-377'):
    roots.append(e377)

reg['summary'] = reg.get('summary', {})
if isinstance(reg['summary'], dict):
    s = reg['summary']
    s['total_roots'] = len(roots)
    of = [r for r in s.get('open_frontiers', []) if r != 'R-NEW-361']
    if 'R-NEW-376' not in of:
        of.append('R-NEW-376')
    s['open_frontiers'] = of
    s['last_updated'] = 'S55 2026-09-17'
    s['note'] = s.get('note', '') + (
        ' | S55: F-082 (ViewAnimator laws) + F-083 (ART-sized engine stack '
        '+ loud limit-drop) fixed R-NEW-361 + R-NEW-377; R-NEW-376 pinned '
        '(post-F-083 Dooz ctor-climb frontier). R-NEW-361 removed from '
        'open frontiers.')
else:
    reg['summary'] += ' | S55: F-082 + F-083 fixed R-NEW-361 + R-NEW-377; R-NEW-376 pinned.'
with open(PATH, 'w') as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print('registry updated:', len(roots), 'roots')
for rid in ('R-NEW-361', 'R-NEW-376', 'R-NEW-377'):
    e = find(rid)
    print(f"  {rid}: {e['status']}")
