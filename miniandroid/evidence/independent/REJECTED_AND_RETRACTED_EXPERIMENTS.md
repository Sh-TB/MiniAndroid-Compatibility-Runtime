# REJECTED AND RETRACTED EXPERIMENTS (preserved to avoid re-research)

1. **android_shadows.h include-removal** (#612/#627): coder's own measured
   retraction — fan-out stayed 27/98, median 6.47s -> 7.24s (WORSE), peak RSS
   unchanged, object identity changed. RETRACTED by the original proposer.
   Classification: REJECTED AS A PERFORMANCE OPTIMIZATION. Do not repeat
   without a new hypothesis (e.g., a measured complete-type requirement
   analysis, not a blind include-strip).
2. **GGC sweeps** (ggc-min-expand/heapsize): historically FAILED (compiler
   errors, timeouts, missing output files, script defects). No GGC
   performance claim is admissible. A valid matrix requires a reliable
   harness on a host that can finish the sweeps.
3. **W19 125-second header-cascade figure**: INVALID (broken .d dependency
   graph measured a false graph). True measured production header cascade =
   401.8s (28 TUs). Never use the 125s number as a baseline.
4. **make -j2 clean production build** (W20): 583.8s vs 535.8s serial on 2
   real cores — REJECTED with data (serial kept).
5. **PCH (dalvik_engine.h .gch)** (W20): 1.03x on one TU + 208MB/header disk
   cost — REJECTED (codegen-bound, not parse-bound; -ftime-report: opt+gen
   79% wall vs parsing 12%).
6. **WS2.01 "wrong blit source" hypothesis**: REFUTED by the coder themselves
   (WS2.02) — the splash is by-design.
