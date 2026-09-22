# MiniAndroid S80 Games — real Android games built for the runtime

Three standard Android apps (pure `android.jar` APIs, no support libraries,
no compile stubs) built with the canonical aapt2/ECJ/D8 toolchain and
executed + played on the MiniAndroid compatibility runtime
(`--execution-mode real-dalvik`). Gameplay proof GIFs live on the gh-pages
site and in `docs/evidence/s80/`.

| Game | Package | Sources | Build script | Autoplay driver |
|---|---|---|---|---|
| Snake Deluxe | `com.miniandroid.snakedeluxe` | `snake-deluxe/` | `scripts/s80_build_snakedeluxe.sh` | `scripts/s80_sd_autoplay.py` |
| Mini Tetris | `com.miniandroid.tetris` | `mini-tetris/` | `scripts/s80_build_tetris.sh` | `scripts/s80_tet_autoplay.py` |
| 2048 | `com.miniandroid.g2048` | `2048/` | `scripts/s80_build_2048.sh` | `scripts/s80_2048_autoplay.py` |

RUNTIME LAWS these games are written against (documented in
`docs/foundation/s80/S80_REPORT.md`):

1. **Static-state law** — instance-field mutation from a click listener is
   not visible to the onDraw render path (OBJECT-IDENTITY frontier): all
   game state lives in `static` fields.
2. **Thread law** — `new Thread(Runnable)` never executes the Runnable;
   a `Thread` subclass's overridden `run()` executes. Games use a
   main-looper `Handler.postDelayed` self-reposting ticker instead.
3. **Tick law (Tetris)** — the 420 ms postDelayed chain fires at frames
   {4,5,6} then every 2nd frame (repost anchors on drain time).

Zero APKs are committed (repo §20 policy): build with the scripts above;
the APK outputs stay in the external build dirs.
