# W20 runtime performance baseline (P0 mission, Phase 1) — STATUS: HARNESS READY, FULL RUN PENDING
Harness: scripts/w20_runtime_perf.sh (15 APK x 5 reps, cold/warm, wall+CPU+RSS
via /usr/bin/time -v, determinism sha per run, TSV output).
The full 15x5 measurement did NOT complete this session (step budget exhausted
by the knowledge-transfer integration + sandbox-recycle tree recovery); the
harness is wired and the run is the FIRST item of the next session.
Existing single-run wall times (production binary, census conditions, 1 rep
each — NOT a median): see evidence/w20/corpus_census.md (15 APKs, 35-100s
workloads). These establish magnitude only.
