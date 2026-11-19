# W20 bench-harness results (RECOVERED — session record)
# NOTE: the raw bench_*.log files were lost with the recycled sandbox before
# this turn; the numbers below are transcribed verbatim from the recorded
# session output (p0_build_wrap wrapper lines) and re-verified by the W20-K
# rebuild where noted. Raw-log loss is an evidence-label downgrade:
# TESTED (recorded) — re-runnable via scripts/w20_bench.sh.
[WRAPPER] bench_p1_clean_prod: exit=0 wall=572.7s peak_child_RSS=1461728 KB
[WRAPPER] bench_p2_unchanged: exit=0 wall=1.0s peak_child_RSS=34512 KB
[WRAPPER] bench_p3_domain_r1: exit=2 wall=75.0s  (adapter_scrap_bin.h cstdint
          latent bug EXPOSED by the F1 dev-dep-graph fix — fixed same wave)
[WRAPPER] bench_p3_domain_r2: exit=0 wall=9.1s peak_child_RSS=1078780 KB
[WRAPPER] bench_p4_ordinary: exit=0 wall=25.9s peak_child_RSS=1097764 KB
[WRAPPER] bench_p5_header_r1 (dev-so, post-F1 true graph): exit=0 wall=284.3s
[WRAPPER] bench_p5_header_r2: exit=2 (same latent bug, fixed) 
[WRAPPER] bench_p5_header_prod: exit=0 wall=401.8s peak_child_RSS=1461488 KB
          (28 TU compiles — the TRUE production header cascade; the W19
          "125s" figure measured the broken dev graph)
[WRAPPER] bench_p6_link: exit=0 wall=1.0s
[WRAPPER] bench_p7_testall: exit=0 wall=234.0s peak_child_RSS=782964 KB
          43 PASS / 0 FAIL
# Build-profile experiments (recorded same session):
PCH (dalvik_engine.h .gch, dev flags): 1.03x on engine_core.cpp (22.4→21.6s)
     → REJECTED (codegen-bound; 208MB/header disk cost)
make -j2 clean production build: exit=0 wall=583.8s vs 535.8s -j1 (9% SLOWER
     on 2 real cores) → REJECTED with data
12-TU dev PIC profile matrix: -O0=106.8s total, -O1=158.9s (avg 8.9 vs 13.2
     s/TU) → dev generic rule set to -O0 (parity: battery 4/4 + 5-APK gate
     11/11 hashes identical)
Dev 12-TU rebuild at -O0 (measured): exit=0 wall=113.6s peak=1172584 KB
-ftime-report execution_engine.cpp (10,631 lines): parsing 12% wall/520MB,
     opt+generate 79% wall/679MB, TOTAL peak 1502MB → the bottleneck is
     -O2 codegen, NOT header parsing (corrects the W19 header-parse-floor
     theory; android_shadows.h-only TU parses in 0.7s)
