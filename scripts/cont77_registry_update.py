#!/usr/bin/env python3
"""cont77_registry_update.py — CONT-77 wave registry updates.

1. F-NEW-380 (NEW, ROOT-CAUSED-FIXED P0): the RenderNode.beginRecording
   accumulate-amplification. AOSP RecordingCanvas law: every beginRecording
   starts a FRESH display list ("the previous recording is discarded"). The
   engine kept appending to the node's prior op list, so every re-record
   ACCUMULATED its previous content (C77-RECORD rows: node 9348 prior_ops
   1->9 growing within one frame; the recorded op stream carried 1562
   identical 'New game' TEXT ops at (765,1829.976) + 189 'Dooz' ops, all
   from the single paint site Lj7;.e). drawRenderNode replay then copied
   the ever-growing lists per level; the compose draw burned the wall
   budget re-recording duplicate content; the F-NEW-298 honesty law
   (correctly) never presented the never-completing frame — dooz's
   DEFAULT_BACKGROUND_ONLY face. Fix = render_nodes_[recv].clear() at
   beginRecording (generic AOSP semantic; re-recording becomes idempotent).
   Post-fix op stream: 2477 ops, ZERO 'New game' flood rows.
2. F-NEW-381 (NEW, CLASSIFIED P1): the interpreter THROUGHPUT WALL —
   dooz's first content composition is ~10-12M interpreted instructions;
   the engine sustains ~310K ins/s (PROGRESS scaling: 3.1M@10s, 6.2M@20s,
   9.2M@30s, linear) so the frame never completes inside the 30s harness
   budget and F-NEW-298 (honesty) keeps the splash. Structural cause:
   DalvikValue carries TWO std::string members (string_val + class_desc)
   in EVERY tagged value (~112B), so every register read/write copies
   them (~60-90M string copies per run); the profile is FLAT (top leaf
   method 4.7%) — no hotspot, an architectural constant. Env-hoist of the
   two per-instruction getenv scans (PERF-1/2) measured NO gain — the
   wall is the value-copy traffic, not env lookups. Fix surface: a
   DalvikValue register-file representation change (tagged-union-only
   fast path / string-out-of-band) — a big, honest, generic project.
"""
import json

ROOT = "/home/z/my-project"
P1 = f"{ROOT}/root_registry.json"
P2 = f"{ROOT}/canonical/root_cause_registry.json"


def main():
    r = json.load(open(P1))
    roots = r["roots"] if isinstance(r, dict) and "roots" in r else r
    ids = [x.get("id") for x in roots]
    assert len(ids) == len(set(ids)), "duplicate root ids"
    by_id = {x["id"]: x for x in roots if "id" in x}
    assert "F-NEW-380" not in by_id and "F-NEW-381" not in by_id

    roots.append({
        "id": "F-NEW-380",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": (
            "RENDERNODE BEGIN-RECORDING ACCUMULATE-AMPLIFICATION (dooz draw "
            "frontier, CONT-77): every GraphicsLayer re-record APPENDED to the "
            "node's prior recorded-op list instead of starting a fresh display "
            "list, so repeated invalidation passes multiplied the recorded "
            "content (one frame's stream carried 1562 identical 'New game' "
            "TEXT ops + 189 'Dooz' ops, all emitted by the single paint site "
            "Lj7;.e through Lj7.f <- Lwu0.i <- Lnt1.Q <- Lgl0.c) and "
            "drawRenderNode replay copied the ever-growing lists per level — "
            "the compose draw burned the whole wall budget re-recording "
            "duplicate content, the frame never completed, and the F-NEW-298 "
            "frame-honesty law (correctly) never presented it."
        ),
        "layer": "graphics/canvas-recording (canvas_shadow RenderNode model)",
        "root_cause": (
            "AOSP law (android.graphics.RecordingCanvas / RenderNode.beginRecording): "
            "every beginRecording starts a FRESH display list — 'the previous "
            "recording is discarded'. MiniAndroid's CanvasShadow.beginRecording "
            "set recording_node_ WITHOUT clearing render_nodes_[recv], so the "
            "node's op list accumulated across re-records (runtime proof: "
            "[C77-RECORD] node=9348 prior_ops=1..9 growing within one frame; "
            "MINIANDROID_CANVAS_OP_TRACE before-fix stream = 2471 rows with "
            "1562 identical TEXT ops; after-fix stream = 2477 rows with ZERO "
            "flood rows). Fix: render_nodes_[recv].clear() at beginRecording "
            "(generic, no app/R8-specific code; re-recording is idempotent "
            "under any invalidation cadence)."
        ),
        "evidence": (
            "CONT-77 at fc12647ff1a7b13a (binary sha16; rebuilt deterministic "
            "from fa97fdd1 + this wave's edits): evidence/cont77/cont77_evidence.json "
            "(pre/post op-trace census, C77-RECORD growth rows, instruction "
            "scaling, A/B zero-drift battery); run/cont77/{ops.txt,ops_fix.txt} "
            "(pre/post MINIANDROID_CANVAS_OP_TRACE); MINIANDROID_TEXT_TRACE "
            "caller attribution (1553 S81 rows, all caller=Lj7;.e); "
            "MINIANDROID_CL_TRACE Lj7/Lgl0 caller chains (depth 157-164)."
        ),
        "fix": (
            "src/framework/canvas_shadow.cpp beginRecording: "
            "render_nodes_[recv].clear() before recording_node_ = recv — the "
            "AOSP fresh-display-list law. Zero drift proven: wall dooz "
            "31ddd4d5b8e6d18e x3 + opencalc f25b754c4565c38b x3 + unote "
            "90a67cc1ddda57b7 x3 = 9/9 MATCH; chess b270ff040b3601dc + "
            "microtimer bbd350b6c14fbd52 A/B byte-identical to the baseline "
            "binary 1ef983a6ff71dade; goldens 4/4, negatives 19/19, reinstall "
            "8/8, c72priv fence 13/13, MG-310 7/7, MG-150 3/3, s82 validator "
            "rc=0."
        ),
        "honest_remaining": (
            "dooz's presented face stays DEFAULT_BACKGROUND_ONLY at the 30s "
            "budget: the accumulation fix removed the amplification but the "
            "first content composition still needs ~10-12M instructions — "
            "see F-NEW-381 (the throughput wall)."
        ),
    })

    roots.append({
        "id": "F-NEW-381",
        "status": "CLASSIFIED",
        "priority": "P1",
        "title": (
            "INTERPRETER THROUGHPUT WALL: the dooz first content composition "
            "is ~10-12M interpreted instructions while the engine sustains "
            "~310K ins/s (linear PROGRESS scaling 3.1M@10s / 6.2M@20s / "
            "9.2M@30s at fc12647ff1a7b13a), so a full first frame cannot "
            "complete inside the canonical 30s harness budget and the "
            "F-NEW-298 honesty law keeps the last complete frame (splash) — "
            "the residual DEFAULT_BACKGROUND_ONLY face after F-NEW-380."
        ),
        "layer": "interpreter/performance-architecture (dalvik_engine dispatch + DalvikValue)",
        "root_cause": (
            "Structural, not a hotspot: DalvikValue carries TWO std::string "
            "members (string_val + class_desc) in EVERY tagged value (~112B "
            "per value), so every register read/write in DexRegisterFile "
            "copies two std::string objects (~60-90M copies per dooz run). "
            "The CONT-77 sampler profile (MINIANDROID_PROGRESS_INTERVAL=500, "
            "16.5K samples) is FLAT: top leaf method Lpv0;.c at 4.7%, the "
            "rest smeared across thousands of compose/coroutines methods — "
            "the cost is the per-instruction value-copy constant, not any "
            "single method. Falsified quick fix: hoisting the two raw "
            "per-instruction std::getenv scans (PERF-1/2, ~18M environ scans "
            "per run eliminated) measured NO throughput gain (313K vs 310K "
            "ins/s) — env lookups were not the wall."
        ),
        "evidence": (
            "CONT-77 at fc12647ff1a7b13a: PROGRESS scaling runs "
            "run/cont77/dooz_{10s,20s,perf2}.stderr (3.1M/6.2M/9.2M linear); "
            "sampler histogram run/cont77/dooz_prof2.stderr; "
            "--frames 1 consumes the same full budget (first-time "
            "composition, not per-frame amplification); opencalc (Compose, "
            "Kotlin+R8) completes its whole launch in <100K instructions — "
            "dooz's NavHost/destination materialization is the 100x volume."
        ),
        "fix_surface": (
            "A DalvikValue representation change for the register file: "
            "tagged-union-only fast path with strings stored out-of-band "
            "(heap/intern table handles), or a shadow-register overlay. "
            "Generic, benefits every app; touches the whole interpreter — "
            "requires its own wave with the full anchor battery (the "
            "byte-reproducibility contract must hold at the new binary)."
        ),
        "honest_note": (
            "No throughput claim is made beyond the measured numbers; no fix "
            "was attempted this wave beyond the zero-risk env hoists; the "
            "F-NEW-298 presentation law stays untouched (it is correct)."
        ),
    })

    json.dump(r, open(P1, "w"), indent=1, ensure_ascii=False)
    r2 = json.load(open(P2))
    r2["roots"] = roots
    json.dump(r2, open(P2, "w"), indent=1, ensure_ascii=False)
    print(f"registry: {len(roots)} roots (F-NEW-380 ROOT-CAUSED-FIXED P0, F-NEW-381 CLASSIFIED P1) id-unique mirrored")


if __name__ == "__main__":
    main()
