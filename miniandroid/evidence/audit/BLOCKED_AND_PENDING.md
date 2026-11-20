# BLOCKED AND PENDING — v2 (2026-11-20 (continuation session, S12+S14))

## BLOCKED
| ID | Item | Exact blocker | Recovery outcome |
|---|---|---|---|
| AUD-35/36b | #628/#619 TicTacToe --frames 12 + interactive verification | emmanuelmess ttt APK absent; corpus has only the itsfrz substitute (rc=1, 0 setGraph) | original APK required; substitute never counts |
| AUD-37b/38b | #618 Counter / #623 RNG runtime verification | APKs absent from corpus | original APKs required |
| AUD-39 | #597 OpenCalc 7x3=21 through real UI | APK absent; root-cause law (F-NEW-639 bounded append) ALREADY merged via s237-w27 | APK required for the runtime re-check; the fix itself is INTEGRATED |
| AUD-53 | RC-12 exact commits | branch layout-geometry-001 is coder-local; every local source checked | partially superseded (c48773a0, 7e5473be) |
| AUD-56 | #630/#631 ten layout apps | coder-local artifacts; no substitutes allowed | documented with visual-evidence comment refs |
| #634/#295/#296/#297 | coder-local fixes (MG-012, stroke laws) | implementations live in coder trees, not in any reachable branch | documented per issue; not re-implemented here |

## PENDING
| ID | Item | Missing step |
|---|---|---|
| AUD-29/31/33 | per-call-site unit laws (gravity/ScrollView offsets/TypedValue chain) | #632 task list items |
| AUD-10b/42 | job-pool OOM guard at -j4+ / MG-012 recovery | dependent on the BLOCKED artifacts above |
| AUD-54 follow-ups | #632 per-finding focused tests beyond the 25 machine-checked cites | coder assignment per registry |

## Resolved by S14/S15
- AUD-47 UBSan E-05: profile + probes + 7 engine vectors + FULL battery under -fsanitize=undefined (probes rc=0, battery 49/49 rc=0).
- AUD-49 BUG-7: stale 0-byte duplicate removed, production battery re-verified (battery 49/49 PASS rc=0).
- AUD-52 peak-RSS limit: full BUILD_TESTS=ON build measured under GNU time metric (-j2): build rc=0, peak 1235 MB (1264520 KB), wall 491.91 s, ctest rc=8 (98% passed).
- #626 PR (S15/AUD-58): wave10 line classified SUPERSEDED-IN-FULL — all content in main; no rebase needed (see MASTER_AUDIT §1 item 13).
