# REJECTED AND CORRECTED — preserved so nothing is rediscovered later

| ID | Original claim | What was false | Disproof | Correction preserved |
|---|---|---|---|---|
| AUD-17 | mold/lld gives 3-8x faster builds | External folklore does not apply: this repo's link step is 1.5 s of a 350 s build | W24 link measurement | Keep BFD ld; revisit only if link exceeds ~5% of wall |
| AUD-18 | -gsplit-dwarf helps large TUs | +4 % SLOWER on the heaviest TU (33.8/33.5 vs 31.6/33.9 baseline) | fresh ABBA probe 2026-11-20 (audit/RAW_LOGS/b567_summary.txt) | keep -g1; split-dwarf adds .o bookkeeping |
| AUD-19 | ggc-min-expand/heapsize tuning helps | 3× SLOWER (102.5/101.6 s vs 32.7 s) — GC thrash | fresh ABBA probe 2026-11-20 | never adopt; recorded so it is not retried |
| AUD-20 | -fno-var-tracking-assignments is a cheaper -g0 | No measurable win (34.2/31.9 ≈ baseline) — GCC 14 fixed the VTA pathology | fresh ABBA probe + W23-F -ftime-report | -g1 (line tables kept) is the chosen cut |
| AUD-21 | PCH helps build time | Rejected 3× (36.4 s PCH build; ABBA probes: apkparse +40 %, net ≤0) | W23-F + W24 EXP-C | third definitive rejection on this repo |
| AUD-22 | Inline-budget params save 7-13 % | Placebo: full A/B byte-identical binaries; probe bias = page-cache order | W23-G BUG-5 record | alternate run order in every future param probe |
| AUD-24 | make/Ninja scheduler is the bottleneck | make == xargs == Ninja within ±2 %; idle is hypervisor steal | W24 EXP-B | scheduler exonerated ×2 |
| AUD-10 | job pools needed to avoid OOM | No OOM at -j2 in ~40 full builds; peak RSS 1221 MB / 4 GB | W22-W24 build logs | re-evaluate only at -j4+ |
