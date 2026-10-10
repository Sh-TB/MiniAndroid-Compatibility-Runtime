# MiniAndroid Achievements — verified screenshot gallery

Every image below was produced by a **real run at the recorded commit** —
either a project-fixture golden sequence or a real F-Droid APK campaign.
SHAs are `SHA256(head16)`; reproduce any shot via its validator or run
command (see the Application Matrix).

| Image | What it shows | SHA256-16 |
|---|---|---|
| `connectfour_y_wins.png` | ConnectFour golden, final board (Y WINS, click 24) | `3ea188450f6be750…` |
| `tictactoe_x_wins.png` | TicTacToe golden, X WINS final board | `f64f1b8c74a8de5f…` |
| `crossword_solved.png` | Crossword golden, SOLVED! (click 9/9 fills) | `a033c183e8d9caf4…` |
| `wordpredict_done.png` | WordPredict golden, SCORE 5/5 DONE (click 6) | `2d36c464fd3cee04…` |
| `balltap_win.png` | BallTap golden, GOAL 3/3 WIN (click 35) | `0a1051141aed1608…` |
| `minesweep_win.png` | Minesweep golden, MINES 10 SAFE 71/71 WIN (click 64) | `ee1066fea1c60469…` |
| `chessclock_rendered.png` | chessclock_29 real F-Droid APK, rendered dark-theme UI (S51) | `e4a2d7c90cd2fd26…` |
| `unote_rendered.png` | unote_30 real F-Droid APK, rendered notes UI (S51) | `7b30d52201bb22ac…` |

Rules (artifact policy):
- Compact representative evidence only — no duplicate screenshots, no raw
  frame dumps in Git.
- Every image maps to a validator / evidence file:
  - games → `miniandroid/tests/fixtures/<game>_golden/validate_*.sh`
  - agent evidence → `docs/evidence/solved/S51_AGENT_C4.json`,
    `docs/evidence/solved/S51_AGENT_NEW_GAMES.json`
  - chessclock/unote → `docs/compatibility/APPLICATION_MATRIX.md` rows
- Raw PPM/framebuffer exhaust is archived externally with SHA256 provenance
  (`docs/evidence/ARCHIVE_MANIFEST.json`), never committed.
