#!/usr/bin/env python3
"""S62 registry update: R-NEW-381 measured-bottleneck face; R-NEW-331 game
consumers + first-engine attach evidence. Honest status deltas only."""
import json

REG = '/home/z/my-project/root_registry.json'
r = json.load(open(REG))

def find(rid):
    for it in r['roots']:
        if it.get('id') == rid:
            return it
    return None

it = find('R-NEW-381')
it['last_updated'] = 'S62 2026-09-19'
it['evidence'] = (
    "S62 MEASURED DECOMPOSITION (docs/evidence/s62_r381/S62_REPORT.md; "
    "run/s62_f107_ab_before, run/s62_f107_ab_after, run/s62_buckets, "
    "run/s62_opself, run/s62_f109_measure, run/s62_lbl_trace): "
    "(1) F-107 A/B on identical budgets: instruction throughput UNCHANGED "
    "(700K vs ~690K instr @480s; segments within noise) — the 0->197px "
    "frame move at budget stop was F-108's dispatchDraw-contract, not "
    "F-107 throughput; (2) S62 bucket timers (insn.pre 0.026%/insn.post "
    "0.084% of wall): loop bookkeeping CLEAN; (3) per-<clinit> duration "
    "law: top-10 chains = 74% of class-init time (Lug0; 23-instr <clinit> "
    "= 7.1s), top-50 = 95%; (4) the 7.1s chain = Lug0;->Lqk;->Lbl;-> "
    "1,024x Lnd1;.c = androidx ColorSpace Rgb transfer-table static init "
    "(register evidence: 'Display P3','NTSC (1953)','SMPTE-C RGB','scRGB') "
    "= 90% of all executed instructions; (5) op self-time: sget-object "
    "23.3ms/call (37% wall), new-instance 9.4ms (14.5%), sget 88ms — "
    "~69% of wall = first-touch sget/new-instance carrying cold-init "
    "subtrees of REAL interpreted work; (6) F-109a/c (written-set bitmap + "
    "strcmp arith dispatch) = ~9-10% instruction-rate gain, honest: "
    "marginal, frontier unchanged; battery ALL PASS 96 + goldens 26/8."
)
it['next'] = (
    "(a) F-110 lever (measured, registered): per-invoke constants "
    "tri.resolve 15.8us + em.setup 22.7us and DalvikValue copy cost "
    "(2xstd::string per register read/write) — the composition needs "
    "~700K instructions; at current ~1,459-2,200 inst/s it completes only "
    "past ~480s; a 3-6x constant-cost reduction is the path to completion "
    "inside evidence budgets. (b) When composition completes: verify "
    "dispatchDraw -> CanvasShadow ops -> real Compose pixels. "
    "R-NEW-380 stays closed."
)

it331 = find('R-NEW-331')
it331['last_updated'] = 'S62 2026-09-19'
it331['evidence'] = (
    it331.get('evidence', '') + " || S62: THREE Runtime Spotlight games "
    "reproduce the SAME first failure (run/s62_game_mines, "
    "run/s62_probe_org.secuso.privacyfriendlymemory, "
    "run/s62_probe_org.secuso.privacyfriendly2048): ISE \"FragmentManager "
    "has not been attached to a host.\" from FragmentManager.ensureExecReady "
    "(pc=24) at Splash/Main onCreate -> APP BOUNDARY unwind. S62 first-"
    "engine precision (run/s62_mines_trace.log): the FULL real androidx "
    "chain dispatches as DEX and returns OK (FragmentActivity.<init>, "
    "FragmentActivity$HostCallbacks.<init>, FragmentController."
    "createController, FragmentHostCallback.<init>, FragmentManagerImpl."
    "<init>, FragmentActivity.onCreate 16 units -> ComponentActivity."
    "onCreate -> SavedStateRegistryController.performRestore) — yet "
    "FragmentController.attachHost never dispatches (no METHOD-IN; APK "
    "string pool contains 'attachHost'). 4th consumer: the Telegram golden "
    "(csearch hit, docs/evidence/mc4_telegram/tg_run1_distilled.log)."
)
it331['next'] = (
    "Engine-side candidate law (generic, no app names): when dispatching an "
    "activity whose superclass chain contains androidx FragmentActivity, "
    "ensure the real FragmentController.attachHost leg executes on the "
    "activity's own mFragments object before app onCreate proceeds "
    "(upstream: FragmentActivity.onCreate attachHost(null) <=1.3; this "
    "app's createController-generation drives it from the host chain). "
    "Unlocks 3 spotlight games + the Telegram init face."
)

# add bouncy L6 to the registry note (corpus fact)
it_b = find('R-NEW-000')  # not present; skip
r['summary']['last_updated'] = 'S62 2026-09-19'
r['summary']['note'] = r['summary'].get('note', '') + \
    " || S62: games corpus first L6 (bouncy, input->state->render, frame SHA pair); F-109a/c landed (marginal, measured); R-NEW-381 decomposed to the per-op/per-invoke constant-cost frontier."

json.dump(r, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registry updated:', it['id'], it['last_updated'], '|', it331['id'], it331['last_updated'])
