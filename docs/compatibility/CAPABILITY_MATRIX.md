# Capability Matrix — evidence-backed (S74)

> Every cell cites the app dossier (`docs/compatibility/apps/<app>.json`),
> its `[EXEC]` issue, and committed evidence. No scores, no 'probably'
> (taskbook §17, §65, §66). Status vocabulary per taskbook §7.

| App | Status | Issue | APK | Lifecycle | View | Measure/Layout | Render | Input | State | Concurrency | Storage | Persistence | Network | Security | Autonomous | Final-frame SHA-16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| helloworld | DONE | #10 | DONE | DONE | DONE | DONE | DONE | DONE | DONE | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | - |
| tictactoe | DONE | #11 | DONE | DONE | DONE | DONE | DONE | DONE | DONE | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | - |
| connectfour | DONE | #12 | DONE | DONE | DONE | DONE | DONE | DONE | DONE | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | - |
| androidgamesnake | OBSERVED | #13 | DONE | DONE | DONE | DONE | DONE | DONE | DONE | DONE | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | OBSERVED | 1a419545419deb3a |
| dooz | BLOCKED | #14 | DONE | PARTIAL | PARTIAL | BLOCKED | BLOCKED | BLOCKED | BLOCKED | PARTIAL | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | - |
| unote | PARTIAL | #15 | DONE | DONE | DONE | DONE | DONE | PENDING | PENDING | PENDING | OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | 2928a026c4a88a14 |
| telegram | PARTIAL | #16 | DONE | PARTIAL | PARTIAL | PARTIAL | OBSERVED | OBSERVED | OBSERVED | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | - |
| gmdice | PARTIAL | #17 | DONE | DONE | DONE | DONE | DONE | OBSERVED | OBSERVED | PENDING | OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | a011e9e9eee2cb42 |
| microtimer | PARTIAL | #18 | DONE | DONE | DONE | DONE | DONE | OBSERVED | OBSERVED | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | e4869001e3638d69 |
| fishrings | PARTIAL | #19 | DONE | DONE | DONE | DONE | DONE | OBSERVED | OBSERVED | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | 19af37b69965fc48 |
| tripeaks | BLOCKED | #20 | DONE | DONE | PARTIAL | PARTIAL | PARTIAL | OBSERVED | BLOCKED | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | 834928fd671a9560 |
| bouncy | PARTIAL | #21 | DONE | DONE | DONE | DONE | DONE | OBSERVED | OBSERVED | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | OBSERVED | 108618ac7c58083b |
| stopwatch | BLOCKED | #22 | DONE | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | - |
| opmt | PARTIAL | #23 | DONE | DONE | DONE | DONE | DONE | OBSERVED | OBSERVED | PENDING | NOT_OBSERVED | PENDING | NOT_OBSERVED | OBSERVED | - | 60e5611daaf01e58 |

## Completion criteria legend (taskbook §8)

C1 APK load · C2 manifest/lifecycle · C3 view/framework · C4 measure/layout · C5 render · C6 input · C7 state change · C8 re-render · C9 persistence · C10 concurrency · C11 security/sandbox · C12 determinism · C13 regression · C14 evidence.

## Reading rule

`OBSERVED` ≠ `VERIFIED`; `IMPLEMENTED` ≠ `TESTED`; `TESTED` ≠ real-APK proven
(taskbook §59, §76.11-13). Historical cells marked in dossiers are proven in
earlier sessions and not re-run at the current HEAD; they are never silently
upgraded. The dooz visual false-claim correction is preserved as
`CLAIM-DOOZ-23472-VISUAL` (SUPERSEDED) in `docs/knowledge/laws/`.
