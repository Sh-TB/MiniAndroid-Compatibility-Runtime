# WAVE-10 Experiment Matrix — every candidate tried, measured, accepted or rejected

Method: each candidate compiled the exact Makefile PIC command with the modified flags to a
scratch object (`/tmp/…`) — the Makefile was only changed AFTER a candidate won. Winners then
faced the full acceptance chain: battery → 3-APK screenshot parity → build-safety suite.

## Attribution (Phase 1) — what the candidates had to attack

`callgraph functions expansion` (inlining expansion) = 63% of interpreter / 50% of bridge time;
`callgraph ipa passes` = 25% of bridge; RTL PRE = 17% of interpreter; parse+templates only
5.5/8.1 s; preprocess 0.5 s.

## Interpreter candidates (baseline PIC compile 21.4 s; target ≤14.5 s for <15 s cycle)

| ID | Candidate (flags on top of production -O2 + wave-7 budget) | Compile | Verdict |
|---|---|---|---|
| I1 | inline-unit-growth=10, large-function-growth=80 | 21.79 s | REJECT — no win |
| I2 | growth=8/large=60/max-inline-insns-auto=20 | 21.74 s | REJECT — no win |
| I3 | growth=6/large=45/auto=12 (max caps) | 21.30 s | REJECT — no win |
| I4 | -fno-ipa-cp -fno-ipa-sra | 22.19 s | REJECT — regression |
| I5 | GGC_MIN_EXPAND=40 GGC_MIN_FREEHEAP=16384 | 22.97 s | REJECT — regression |
| I8 | -fno-inline-functions (-small, -called-once) | 21.31 s | REJECT — no win |
| **I6** | **-O1 (replacing -O2, wave-7 budget kept)** | **12.00 s** | **ACCEPT — cycle 12.26 s median ×5** |
| I7 | -O0 | 7.58 s | REJECT in favor of I6 (I6 meets target with real optimization retained) |

## Bridge candidates (baseline PIC compile 40.3 s; target ≤28.5 s for <30 s cycle)

| ID | Candidate | Compile | Verdict |
|---|---|---|---|
| B1 | GGC_MIN_EXPAND=30/FREEHEAP=16384 | 39.37 s | REJECT — no win |
| B2 | GGC 60/32768 | 39.61 s | REJECT — no win |
| B3 | **-O1** | **cc1plus OOM-KILLED** (rc=1, "Killed signal terminated program cc1plus") | **REJECT/BLOCKED — exceeds 4 GB cgroup** |
| B4 | -fno-ipa-cp -fno-ipa-sra -fno-ipa-pure-const | 39.41 s | REJECT — no win |
| B5 | inline caps (auto=12, growth=10) | 39.40 s | REJECT — no win |
| **B6** | **-O0** | **25.51 s / 26.61 s (RSS 2,185 MB)** | **ACCEPT — cycle 25.51 s median ×5** |

## Opcode (gate re-check during the wave)

Opcode keeps the generic -O2 PIC rule from wave-9; ×5 cycles measured median **10.02 s**
(9.75–10.33) — misses the <10 s gate by 0.02 s. The interpreter's accepted profile was applied
to the opcode PIC rule too:

| Candidate | Compile/cycle | Verdict |
|---|---|---|
| opcode @ -O2 (wave-9 state) | 10.02 s median ×5 | REJECT — gate miss |
| **opcode @ -O1** | **8.18 s median ×5 [7.82–8.21]** | **ACCEPT — parity re-verified** |

## Rejected-by-policy (not measured)

- Global -O0/-Og downgrade (mission rule), semantics-changing flags (-fno-exceptions, -fno-rtti),
  bridge dispatch-arm extraction (wave-6 ud2/SIGILL history; not attempted speculatively),
  linker work (wave-9 proved 0.20–0.22 s — not a bottleneck), PCH (parse share too small to matter).

## Acceptance evidence for the accepted profiles

- Battery 3/3 after every flag transition.
- 3-APK screenshot SHA-256 ×3 reps: `87fe2676…` / `46b07062…` / `d55056a8…` — identical to
  canonical AND stable across reps, including the final combined profile.
- Phase decomposition (harness): interpreter 11.9+0.2+0.04 ≈ cycle; bridge 25.2+0.2+0.04.
- Raw data: `w10_sweep_raw.json`, `w10_sweep2_raw.json`, `w10_verify_raw.json`,
  `w10_opcode_profile.json`, `w10_final_parity.json`, `w10_benchmarks.json`.
