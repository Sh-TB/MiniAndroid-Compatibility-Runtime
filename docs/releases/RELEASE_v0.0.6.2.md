# RELEASE v0.0.6.2 — 2026-11-13

Parent release: **v0.0.6.1-Exchequer** (2026-11-02). Tag: `v0.0.6.2`.
Release branch tip at tag creation: `925d3e2c`-clean-clone build of the
committed tree (`git log v0.0.6.1-Exchequer..HEAD` = 213+ commits).

## Highlights (user-visible)

1. **F-GLZ-2 under-lay compositor law + F-BLANK-1 launch-theme law** —
   Vector Pinball's menu (Select Table, Start Game/High scores/Help/
   Preferences/Quit, status bar) renders above the GL surface per the
   AOSP SurfaceView z-order contract; window background resolves the app's
   real Theme.Black. bouncy face re-pinned `8a6c24ac → 98abca38`; the pixel
   proof shows all 936,460 changed pixels are exactly the
   `#303030 → #000000` background fill (menu pixels byte-identical).
2. Diagnostics trustworthiness (S225-M): synchronized trace ingestion,
   stream-joinable gfx rows, JNI dispatch-precedence (stub can no longer
   shadow a real native library), ELF `DT_STRTAB` VA mapping, pthread
   shadow locked-section + POSIX error semantics.
3. **Repository law + evidence honesty (#587)**: Constitution §172 with an
   executable policy validator and CI; 1,199 byte-identical evidence paths
   deduplicated; W18 Halma batch compacted with truthful reports;
   OSMesa vendored bundle (94.4 MiB) replaced by a pinned bit-reproducible
   bootstrap (`OSMESA REAL GL OK` proven); forensic raw dumps removed
   (canonical 390-row ledger + fetch/rebuild modes); `docs/METRICS.json`
   reconciles all public counts (152 titles / 24 VERIFIED / 797 roots);
   README rebuilt as an evidence-first landing page.

## Verified examples on the release-candidate binary `06f98d2a9c21ea92`

| demo | face (sha16) | proof |
|---|---|---|
| Vector Pinball (bouncy) | `98abca38` | fresh run ×2 sessions identical; pixel diff = single background pair; menu visible |
| uNote | `3b8dcb0a` | fresh run identical |
| dooz (Compose board) | `a0fae907` | fresh run identical (300 s) — PARTIAL frontier |
| GameMasterDice | `3891679d` | two runs byte-identical; ALSO reproduced by the packaged release binary in the smoke test |
| MicroTimer | `b39665f6` | fresh run |
| TicTacToe Deluxe | `7354c1b2` | three runs deterministic |

`make test-all` 28/28 at the release commit.

## Artifacts

| file | sha256 | size |
|---|---|---|
| `MiniAndroid-v0.0.6.2-linux-x64.tar.gz` | `e45433dda4ca897e9cd95e78f9c77bac0d48a594e18386930056b061f9c14629` | 4,761,562 B |

- Contents: stripped runtime binary, `run-miniandroid.sh`, `LICENSE`,
  `README.txt`, `miniandroid-demo.apk`. Release-content validator: PASS
  (0 development artifacts).
- **Windows asset honestly omitted** — no pinned Windows toolchain in this
  build environment; never re-ship an older binary (v0.0.3 precedent).
- Build provenance: built in a **clean clone** (`/tmp` clone of the release
  commit, `make -C miniandroid -j1`, g++ 14.2.0 Debian 13). Unstripped
  clean-clone binary `925d3e2ccf0a781b…`; main-tree unstripped binary
  `06f98d2a9c21ea92…`; the stripped binaries are byte-identical except the
  20-byte GNU build-id (linker-derived from unstripped inputs).

## Smoke test (outside the source directory)

Extracted the archive to `/tmp/ma_smoke` and ran: `--version`, `--help`,
`install miniandroid-demo.apk` → run (screenshot 19,255 B), and
`install de.duenndns.gmdice_8.apk` → run produced face
`3891679dff449331` — the byte-exact pinned face. No dependency on any
developer-private path.

## Known limitations

- ARM-only APKs are out of scope (`ABI_OUT_OF_SCOPE`).
- Compose: first-frame/board rendering proven; deeper stateful apps partial.
- Per-run stub census (F-NEW-200) and uncaught exceptions (F-016) are
  recorded and must accompany any SUCCESS claim.
- dooz gameplay state and Halma gameplay are documented frontiers, not claims.
- Windows binary not produced this release.

## Regression gates

6-pin byte-exact HOLD; `make test-all` 28/28; policy validator 0 violations
(4,990 reviewed grandfather entries, expiry recorded); forensic ledger
validate 390 rows / 0 errors; release-content validator PASS; README metric
staleness check OK.
