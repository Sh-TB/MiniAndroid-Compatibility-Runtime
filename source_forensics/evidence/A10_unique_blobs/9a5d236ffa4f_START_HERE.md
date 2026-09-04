# START_HERE — UNIFIED_011_CANONICAL_HANDOFF package

You need NOTHING outside this package to understand and build the project
(system packages and the external test-APK cache are the only externals, and
every script tells you how to get them).

Read in this order:

1. **README.md** — what MiniAndroid is, current state, quick start.
2. **MASTER_HANDOFF_011.md** — the 3-minute onboarding: what is proven,
   what is blocked, where evidence and code live, how to continue.
3. **MASTER_PROJECT_STATE_011.md** — the full canonical state (architecture,
   capabilities, blockers, corpus, next actions). `status.json` = same
   numbers, machine-readable.
4. **Build it:**
   ```bash
   sudo apt install g++ make zlib1g-dev libwebp-dev libjpeg-dev \
                    libpng-dev libfreetype-dev libharfbuzz-dev libfribidi-dev
   # rlottie static lib (only external build dep):
   git clone https://github.com/Samsung/rlottie ../tools/rlottie
   ( cd ../tools/rlottie && cmake -S . -B build -DBUILD_SHARED_LIBS=OFF \
     && cmake --build build -j )
   make
   ```
5. **Run the tests:**
   ```bash
   scripts/download_test_apks.sh        # fetch APKs into EXTERNAL cache, SHA256-verified
   python3 scripts/u011_test_matrix.py  # canonical matrix; expect telegram BASELINE_MATCH
   ```
6. **Inspect evidence:** `docs/evidence/u011/` (+ EVIDENCE_INDEX.md),
   `TEST_MATRIX.md`, `MASTER_CHANGELOG_KNOWLEDGE_011.md` (history, provenance-graded).
7. **Continue from the blockers:** `MASTER_PROJECT_STATE_011.md §11`
   (top pick: ARSC `@string/` resolution) — house rules in `DO_NOT_REINVENT.md`.

## Git history in this package

This ZIP contains the **full `.git` repository** (all 59 commits, tag
`v0.11-unified-011`). If it was shipped without `.git`, restore history from
the separate `miniandroid_unified_011_full.bundle`:

```bash
git clone miniandroid_unified_011_full.bundle MiniAndroid-Restored
cd MiniAndroid-Restored && git log --oneline | head   # verify
```

## Package guarantees (audited)

- ZERO `.apk` / `.aab` files · ZERO secrets (pattern-audited incl. history)
- No tracked image >100 KB · clean `.gitignore` (§28)
- Numbers consistent across README / status.json / TEST_MATRIX / master docs (§45)
