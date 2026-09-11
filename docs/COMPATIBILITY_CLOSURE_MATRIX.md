# COMPATIBILITY CLOSURE MATRIX — M8 (2026-09-10)

Status vocabulary: VERIFIED (live evidence + micro/visual proof), PROVEN
(VERIFIED + regression gate + determinism), ROOT-LOCATED (evidence chain
complete, fix queued), OPEN (no root), BLOCKED (external dependency),
REJECTED-CLAIM (summary/report claim not found at HEAD).

| Family | Closure | Evidence |
|---|---|---|
| APK loading (13 corpus APKs) | VERIFIED | fetch_corpus hash pins; EXP-073/076 sweeps |
| DEX execution (semantic battery) | PROVEN 91/91 | logs/battery_m8_full.log |
| Activity lifecycle | VERIFIED | G07 lifecycle goldens; dooz CREATE→RESUMED |
| Resources/ARSC | VERIFIED | chessclock/ARSC-first goldens |
| Measure/layout (View trees) | VERIFIED | tictactoe_golden, G06 taps |
| Canvas/Path/Renderer | VERIFIED | Cycle-E validator, font goldens |
| Deterministic replay | VERIFIED | 3-run byte-identical: dooz, tictactoe, f050 fixture |
| Java core (streams/enums/executor/collections) | VERIFIED | F-024..F-027, F-036/F-039 fixtures |
| Atomic/updater family | VERIFIED | F-028h, F-050c (f050 L1/L2) |
| Boxed statics | VERIFIED | F-050d (f050 L3/L4) |
| Throwable message law | VERIFIED | F-050b (f050 L5) |
| Choreographer frame pump | VERIFIED | F-050a (f050 L6/L7; doFrame tick t=1016666667ns) |
| Compose first frame (dooz) | ROOT-LOCATED | Job-active cancellation of the frame await; 4 blocker layers peeled this session; 0 non-white (honest blank) |
| Compose tap→recompose | OPEN | gated on first frame |
| WeakReference semantics | OPEN | summary claim not found at HEAD; no live trace yet |
| android.R.id.content/DecorView content hierarchy | OPEN | summary claim not found at HEAD; AbstractComposeView parent chain partially covered by F-023 laws |
| System-service completion | OPEN (queued F-046 candidate) | demand-gated |
| Telegram (JNI/natives) | BLOCKED | 1.2 MB stub served vs 82 MB pinned artifact |
| F-046..F-052 "verified" summary block | REJECTED-CLAIM | no commits/fixes/IDs at any HEAD; real bugs inside the block were re-derived live (F-050c) and the ledger reserved IDs preserved |
| v0.0.3-Chantecler release | VERIFIED (remote) | tag 7e18cd72; asset SHA256SUMS; Windows asset honestly omitted |

ROOT COMPLETENESS SCORE (self-assessment, family-weighted):
- Core execution (DEX/tag/frames/reflection/collections/atomics): 0.9
- Framework (services/lifecycle/scheduler/frame pump): 0.8
- Compose runtime: 0.55 (machinery executes; first frame pending)
- Rendering (View trees): 0.9 — (Compose trees): unproven
- Cross-APK (Telegram/JNI): 0.4 (external blocker)
Weighted overall ≈ 0.73 — the scoreboard is honest to the frontier.
