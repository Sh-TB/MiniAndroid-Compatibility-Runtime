# WAVE-10 Build Safety — independent verification (all timings fresh)

| Check | Result |
|---|---|
| Production static build (default `make all`, catch-up after benchmark touches) | rc=0, 136.52s, peak RSS 2137 MB |
| Production `test-core` | **3/3 PASS** (12.38s) |
| Monolith fallback LIVE (`DALVIK_SPLIT=0 all`) | rc=0, 193.67s, peak RSS 2886 MB |
| Monolith `test-core` | **3/3 PASS** (12.92s) |
| Clean dev-so build (`dev-so-clean` → `dev-so`, wave-10 profiles) | rc=0, **122.99s** (wave-9 baseline 148.5s) |
| dev-so battery / no-op | **3/3 PASS** / 0.04s |
| Production tree restored after suite | rc=0, 136.94s |

- Wave-9 zero-test-relink behavior preserved: every trace and ×5 run shows test_exe_relinks=0.
- No generated executables, APKs, object files or shared libraries committed (gitignore covers
  `miniandroid/build_dev_so/`, `/build/`, `/build_dev/`).
- Rollback: `make dev-so-clean` + `git revert <wave-10 commit>` restores the exact wave-9 state;
  production rules were not modified by wave-10.
- Raw data: `w10_build_safety_raw.json`.
