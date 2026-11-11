**[CONT-131 honesty correction]** the wave comment's ttt row was registered before the measurement ran — the CONT-132 fixture work preempted phase D. Now measured (binary `4d9087c60482042b`, the rebuilt POST):

| run | face | uncaught | wall |
|-----|------|----------|------|
| ttt_1 | `7354c1b231cd581d` | 0 | 10.2 s |
| ttt_2 | `7354c1b231cd581d` | 0 | 10.2 s |
| ttt_3 | `7354c1b231cd581d` | 0 | 10.4 s |

**rerun-identity HOLD ×3 — and the face is byte-exact vs the CONT-130 lane record (`ttt 7354c1b2 HOLD`)**: the four-law re-land preserves the ttt golden too. Evidence rows `evidence/cont131/ttt_{1,2,3}.json` committed with the wave.