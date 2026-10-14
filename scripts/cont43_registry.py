#!/usr/bin/env python3
# cont43_registry.py — CONT-43 registry update ("cross the page" wave):
#  (1) F-NEW-304 row refresh: the companion native class-measure law
#      RE-LANDED with the subtree-coherence fix (opencalc golden restored
#      byte-identical; tananaev fix face retained); tananaev frontier
#      advanced from PARTIAL d602648e (machinery-only) to rc=0 SUCCESS
#      0f649804d6e0486d (rows parsed+measured+attached, action bar band).
#  (2) F-NEW-305: tananaev visible-rows leg — ActionBarOverlayLayout
#      content inset law missing (rows build at y=0 under the bar band).
#  (3) F-NEW-306: csw composeStopwatch content-state regression sourced to
#      F-NEW-304 itself (ReportFragment drain interleaving) — discovered
#      by the CONT-43 target-case A/B that CONT-42's gate never ran.
#  (4) F-NEW-307: dooz case-E resolved (progressing-not-stalled; boot
#      completes ~80 s / 25 M insns; new deterministic content face
#      6841d52a20e6597e x5) + the frame-census app-op attribution gap.
import json

P = '/home/z/my-project/root_registry.json'
d = json.load(open(P))
ids = {r.get('id') for r in d['roots']}
for need in ('F-NEW-304',):
    assert need in ids, f'{need} missing — wrong base'
for fresh in ('F-NEW-305', 'F-NEW-306', 'F-NEW-307'):
    assert fresh not in ids, f'{fresh} already present — dedup check'

# ── (1) refresh F-NEW-304 in place ─────────────────────────────────────
for r in d['roots']:
    if r.get('id') == 'F-NEW-304':
        r['status'] = 'ROOT_CAUSED_FIXED'
        r['binary'] = '3dab3038c222031e'
        r['regression'] = (
            'ZERO DRIFT: anchors 24/24 x3 byte-identical (opencalc golden '
            'a976d2f9fb675cb3 RESTORED by the coherence fix); probes == '
            'records exactly (fcol 140/0, f259 49/0, f259g 84/7, f266 42/0, '
            'f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey '
            '105/0, cpipe 119/0, fnew302 48/24 documented, fnew252 56/0, '
            'fnew290..296 == records, fnew297 42/0, fnew298 19/0 KEEP=5 '
            'corner=PASS); frag_tx_probe 12/0 x3; notif_builder_probe 56/0 '
            'x3; simplecalc x3 rc=0 7960bce447ac6d8f. EXPOSED (pre-existing '
            'on main, not this delta): csw drifted 3442d9a9 -> 5c4a0172 '
            'because CONT-42 never ran the target case — F-NEW-306.')
        r['title'] += (
            ' CONT-43 UPDATE: the companion native class-measure law is '
            'RE-LANDED at the two guarded insertion points WITH the '
            'subtree-coherence fix (a node measured by the native class '
            'law carries dims its own container law computed coherently '
            'over the whole subtree; the ROOT-045b descent must not '
            're-measure that subtree at cruder per-node specs — the '
            'CONT-42 split-brain that broke the opencalc pad: cell widths '
            'overwritten while the row x-pitch survived -> overlapping '
            'digit labels). Post-fix A/B: tananaev keeps 0f649804d6e0486d '
            'rc=0 x3 AND opencalc returns to the exact golden a976d2f9 '
            'x3 — the honest dispatch is semantically neutral for '
            'opencalc by construction. tananaev frontier: PARTIAL '
            'd602648e (machinery-only) -> rc=0 SUCCESS 0f649804d6e0486d '
            '(4 REAL preference entries parsed+measured+attached; action '
            'bar band + tinted background; the visible-rows leg is '
            'F-NEW-305).')

d['roots'].append({
  "id": "F-NEW-305",
  "title": ("tananaev calculator v1.10 visible-rows leg: the preference "
            "rows build, measure (1080x44 at real y-pitch) and attach "
            "into the transaction container, but render UNDER the appcompat "
            "action-bar band — the frame (0f649804d6e0486d rc=0) shows the "
            "gray ActionBarContainer band and a tinted background with "
            "ZERO dark pixels (no row text). AOSP law: "
            "ActionBarOverlayLayout.onMeasure/action-bar inset dispatch "
            "positions the content BELOW the measured action bar "
            "(non-overlay mode applies the bar height as the content's "
            "top inset/padding at layout). The engine's tree hosts the "
            "real appcompat classes (ActionBarOverlayLayout / "
            "ActionBarContainer confirmed in C013-HIER) but the inset "
            "dispatch leaves the ContentFrameLayout content at y=0, and "
            "the bar band's z-order overdraws rows 0..~176. Decode+fix "
            "owned next (the fragment/preference family's slice 2); the "
            "preference page machinery itself is CLOSED (REC-MISS gone, "
            "rows parsed 4/4 with real titles, drains fire, tree "
            "attached)."),
  "status": "ROOT_CAUSED_PENDING_FIX",
  "priority": "P1",
  "layer": "framework/actionbar-insets",
  "evidence": "evidence/cont43/CONT43_CROSS_THE_PAGE.md",
  "probe": "tananaev A/B rows: [F-NEW-304] started drain view#456 container#379; frame dark-pixel count 0",
  "binary": "3dab3038c222031e",
})

d['roots'].append({
  "id": "F-NEW-306",
  "title": ("composeStopwatch v1009011 visible-content regression "
            "3442d9a9dc0fa0f9 -> 5c4a0172628849ba (deterministic x3), "
            "SOURCED TO F-NEW-304 ITSELF (the CONT-42 wave), not to the "
            "CONT-43 companion law: same-environment source A/B — binary "
            "built from the CONT-41 source tree (7063c7238e0de79b) runs "
            "csw at 3442d9a9dc0fa0f9 x3 while the same binary family with "
            "F-NEW-304 (5b7cb20a2c17441c, no companion law) runs "
            "5c4a0172628849ba x3; CONT-42's gate never ran the target "
            "case. First divergence decoded: the androidx "
            "LifecycleDispatcher ReportFragment (Li01; tag "
            "'androidx.lifecycle.LifecycleDispatcher.report_fragment_tag') "
            "now DRAINS through real DEX (onAttach/onCreateView/onStart/"
            "onResume, clean — zero exceptions in the drain window), the "
            "compose boot then takes a different interleaving that dies "
            "at Lh4;.onMeasure (a ViewGroup ComposeView family member) "
            "-> Laj0;.n (performMeasureAndLayout: 'unattached/unplaced "
            "root' guards) -> isEmpty() dispatched on a NULL state "
            "object (the Lgi0;.f chain; Lgi0; is NEVER ALLOCATED in the "
            "regressed run per MINIANDROID_ALLOC_TRACE — the compose "
            "content-state object graph never forms), catch-all NPE at "
            "pc=167, boot degrades to 600k instructions (healthy: 4.4M), "
            "no dialog/choreo content. Same identity-hash interleaving "
            "knife-edge family CONT-40 flagged (the parked "
            "getWindowToken-law flip) — the CONT-40 discriminating-probe "
            "prerequisite applies BEFORE any engine change. Fix owned by "
            "the next wave; the csw anchor expectation stays 3442d9a9 "
            "(content must be REGAINED, not re-baselined down)."),
  "status": "ROOT_CAUSED_PENDING_FIX",
  "priority": "P0",
  "layer": "compose/fragment-drain-interleaving",
  "evidence": "evidence/cont43/CONT43_CROSS_THE_PAGE.md",
  "probe": "csw A/B: CONT-41-src 3442d9a9 x3 vs F-NEW-304-src 5c4a0172 x3; MINIANDROID_ALLOC_TRACE=Lgi0; = 0 allocations",
  "binary": "3dab3038c222031e",
})

d['roots'].append({
  "id": "F-NEW-307",
  "title": ("dooz v23 case-E frontier RESOLVED as boot-cost (not a hidden "
            "spin) + the frame-census app-op attribution gap. The CONT-40 "
            "A-D-vs-E ambiguity is closed measurement-only: at 15 s the "
            "boot composition executed 4.7M instructions painting 155 "
            "app-owned draw ops; at 45 s it executed 13.7M instructions "
            "painting 659 app-owned draw ops (2.9x budget -> 4.25x ops) "
            "— the composition PROGRESSES (ops grow, [PROGRESS] tail "
            "methods differ, rate ~300k insns/s steady), it does not "
            "cycle; the 15 s wall deadline (static thread_local "
            "wall_start from the FIRST DEX instruction — every later "
            "window halts immediately, 266 [WALL-STOP]s) simply cuts a "
            "legitimately expensive Compose boot mid-paint and the "
            "F-NEW-298 frame-honesty law keeps the white frame "
            "31ddd4d5b8e6d18e. With a fair budget the boot COMPLETES: "
            "90 s (25.4M insns, wall 82 s) and 180 s (51.6M insns, wall "
            "76 s — the run ENDS, no halt) both produce the same "
            "deterministic frame 6841d52a20e6597e x5 (locked x3 + x2 on "
            "the final binary): the REAL Dooz scaffold renders — "
            "Material3 surface (250,248,254) 88.7%, secondary band "
            "(237,237,246), accent pill (185,203,255), 15,876 black "
            "glyph/icon pixels in the top bar and bottom app bar (FAB "
            "circle + rounded pill), all 5 frames identical (steady "
            "state). Residual roots: (a) the frame census still reports "
            "app_draw_ops=0 / VIEWTREE_NO_APP_PIXELS / "
            "first_missing_stage=APP_DRAW_OPS despite rendered app "
            "content — the census's draw-window attribution does not "
            "count the Compose paint path (the CDW-OP trace caps at 400 "
            "lines and the census window classification missed the path "
            "that painted) — fix the attribution and dooz flips to "
            "REAL_APP_CONTENT honestly; (b) the boot cost itself (25M "
            "instructions for first frame) is the perf frontier. The "
            "identity-hash interleaving sensitivity (CONT-40 parked-law "
            "flip) remains the pre-change prerequisite for any engine "
            "touch on this path."),
  "status": "ROOT_CAUSED_PENDING_FIX",
  "priority": "P1",
  "layer": "compose/frame-census",
  "evidence": "evidence/cont43/CONT43_CROSS_THE_PAGE.md",
  "probe": "dooz budget ladder 15s/45s/90s/180s (app_ops 155/659; faces 31ddd4d5 x6, 6841d52a x5)",
  "binary": "3dab3038c222031e",
})

d['count'] = len(d['roots'])
d['total_roots'] = len(d['roots'])
d['generated'] = 'CONT-43 session'
json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print("registry:", len(d['roots']), "roots; F-NEW-304 refreshed; F-NEW-305/306/307 appended")
