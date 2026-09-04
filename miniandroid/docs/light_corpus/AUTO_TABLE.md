# Light open-source corpus — real-execution evidence

- Binary: `build/miniandroid` sha256 `6cbfdddc4471e828...`
- Every frame is a direct MiniAndroid framebuffer PNG capture.
- runA: launch + 6 dispatched clicks. runB: identical repeat
  (determinism check).

| App | APK | Frames | State changes | Deterministic | Verdict |
|-----|-----|--------|---------------|---------------|---------|
| bgclockhansdezwart | 1,040,099 B | 1 | 0 | YES | RENDER |
| chessclock | 124,222 B | 7 | 2 | YES | RENDER |
| gmdice | 63,998 B | 7 | 3 | YES | REAL_RENDER |
| headingcalculator | 65,417 B | 1 | 0 | YES | BLANK |
| microtimer | 208,895 B | 7 | 0 | YES | REAL_RENDER |
| simplestopwatch | 172,399 B | 7 | 3 | YES | REAL_RENDER |
| tinymusicplayer | 16,552 B | 1 | 0 | YES | RENDER |
| unote | 163,498 B | 7 | 1 | YES | REAL_RENDER |
