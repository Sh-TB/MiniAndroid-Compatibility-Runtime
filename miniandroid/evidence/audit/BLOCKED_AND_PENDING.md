# BLOCKED AND PENDING — v2 (2026-11-20 (continuation session))

## BLOCKED
| ID | Item | Exact blocker | Recovery outcome |
|---|---|---|---|
| AUD-35/36b | #628/#619 TicTacToe --frames 12 + interactive verification | emmanuelmess ttt APK absent; corpus has only the itsfrz substitute (rc=1, 0 setGraph) | original APK required; substitute never counts |
| AUD-37b/38b | #618 Counter / #623 RNG runtime verification | APKs absent from corpus | original APKs required |
| AUD-39 | #597 OpenCalc 7x3=21 through real UI | APK absent; root-cause law (F-NEW-639 bounded append) ALREADY merged via s237-w27 | APK required for the runtime re-check; the fix itself is INTEGRATED |
| AUD-53 | RC-12 exact commits | branch layout-geometry-001 is coder-local; every local source checked | partially superseded (c48773a0, 7e5473be) |
| AUD-56 | #630/#631 ten layout apps | coder-local artifacts; no substitutes allowed | documented with visual-evidence comment refs |
| #634/#295/#296/#297 | coder-local fixes (MG-012, stroke laws) | implementations live in coder trees, not in any reachable branch | documented per issue; not re-implemented here |
| AUD-52 (partial) | peak memory of full BUILD_TESTS=ON cmake build | session budget (2 vCPU, ~1.4 GB free disk) | graph facts measured; runtime measurement queued |

## PENDING
| ID | Item | Missing step |
|---|---|---|
| AUD-29/31/33 | per-call-site unit laws (gravity/ScrollView offsets/TypedValue chain) | #632 task list items |
| AUD-47 | UBSAN=1 profile + 7-test rerun (E-05) | optional sanitizer profile |
| AUD-49 | BUG-7 duplicate shadow_registry.h dedupe | repoint includes + rebuild |
| #626 PR | merge readiness | rebase onto current HEAD + dev-so gate |
| AUD-54 follow-ups | #632 per-finding focused tests beyond the 25 machine-checked cites | coder assignment per registry |
