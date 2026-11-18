# WAVE-9 Final Evidence — production-safe integration of the shared Dalvik .so dev path

## 1-2. Commit, branch, PR
- Wave-8 commit verified: cfb11936db1a05d962cc0076a106c58d95792ccb, parent eac17a660a759a58966c8124e29d97404c517f3e.
- **cfb11936 is NOT on remote** (origin/main = 125f5690, 25 commits behind local main) and **cannot be pushed as-is**: it accidentally committed four build binaries (109–114 MB each — GitHub's 100 MB push limit). It is local-only and SUPERSEDED.
- Fix (repo hygiene, user-rule "build outputs outside the source tree"): wave-9 branch starts at eac17a66 and re-carries wave-8's evidence/scripts (non-binary) + integration; `miniandroid/build_dev_so/` is now gitignored.

## 3. Exact files changed (wave-9 branch vs eac17a66)
- `miniandroid/Makefile` — additive opt-in block: dev-so / dev-so-test / dev-so-clean, per-TU PIC rules (interpreter keeps wave-7 inline budget, bridge keeps -Og), SONAME libminiandroid_dalvik.so, make-escaped `$ORIGIN` RPATH, DEV_SO_BATTERY with LD_LIBRARY_PATH, staleness guard (dev-so-test depends on the .so which depends on every PIC object; PIC objects carry -MMD dep files).
- `.gitignore` — `miniandroid/build_dev_so/`.
- `miniandroid/evidence/wave8/*` (9 files, restored from cfb11936 minus binaries), `scripts/w8_*.py`, `scripts/w9_bench.py`, `miniandroid/evidence/wave9/*`.

## 4-6. Tests A-E and benchmarks (fresh-process timing, median [min–max])
| Gate | Result | Status |
|---|---|---|
| A clean dev-so build | rc=0, 146.7 s one-time, peak RSS 2,129 MB, battery 3/3 | PASS |
| B opcode edit trace | compiles=1, so_relink=1, **test_links=0**, PASS=3, 9.51 s | PASS |
| C interpreter edit trace | compiles=1, so_relink=1, **test_links=0**, PASS=3, 20.55 s | PASS |
| D bridge edit trace | compiles=1, so_relink=1, **test_links=0**, PASS=3, 38.39 s | PASS |
| Opcode cycle ×5 | median **9.76 s** [9.73–10.16] | <10 s MET (median) |
| Interpreter cycle ×5 | median **21.33 s** [20.86–21.96] | <30 s MET; <15 s NOT met (compile-bound: 21.4 s of it is the PIC compile) |
| Bridge cycle ×3 | median **40.29 s** [38.95–41.00] | PARTIAL (unchanged giant-function blocker) |
| dev-so no-op ×5 | **0.04 s** [0.04–0.04] | <0.5 s MET (dev-so graph); production `all` no-op ≈1.1 s separately |
| Phase decomposition | interpreter 21.4+0.21+0.04 ≈ cycle; opcodes 9.6+0.21+0.04 | compile-bound confirmed |
| Peak RSS | 2,129 MB (bridge PIC) / ld 563 MB | <4 GB MET |

## Test E — production isolation
- Default `make all` references build_dev_so: **0** (grep of dry-run) — production static path cannot silently select the experimental path.
- Production `test-core`: 3/3 PASS (12.1 s). Monolith fallback: `make -n DALVIK_SPLIT=0 all` intact (dalvik_engine.o rule present); last live re-verification wave-7 rc=0.
- Production no-op re-verified ~1.1 s class after the legit catch-up rebuild (wave-8's benchmark touches had left the interpreter object stale — dep tracking caught it, which is the system working).

## 7. Test F — runtime proof (original APKs only, provenance hashes in apk_identity.txt)
| APK | rc | screenshot SHA-256 | canonical | class |
|---|---|---|---|---|
| Guess (ru.zxalexis.ugaday_15) | 0 | 87fe26766fc48d06c59d4c15 | 87fe2676 | SUCCESS (hash identical) |
| DiceRoller (tech.gaskell.diceroller_1_debug) | 1 | 46b07062ba6fe36ca8a6e42d | 46b07062 | PARTIAL — not upgraded (no genuine interaction evidence) |
| TicTacToe (com.itsfrz.tictactoe_5) | 1 | d55056a8928a26ffeb15f66d | d55056a8 | PARTIAL — not upgraded |

## 8-9. Regression & rollback
- Production static path independently re-run (Test E). Shared-library path disabled cleanly: `make dev-so-clean` (removes build_dev_so/) — no other rule references it. Failed/missing .so cannot be silently skipped: dev-so-test rebuilds it before running (missing .so = rebuilt; stale objects = relinked, proven by traces).
- Full rollback: `make dev-so-clean && git checkout main` (or revert the wave-9 commit); production artifacts and flags untouched throughout.

## 10. Acceptance-gate ledger
MET: opcode <10 (median), interpreter <30, no-op <0.5 (dev-so), no test-exe relinks, RSS <4 GB, production isolation, runtime parity hashes, clean disable.
NOT MET / PARTIAL: interpreter <15 (compile-bound 21.4 s — next lever is the interpreter TU compile itself), bridge <30 (55K-line function at -Og, 2,129 MB — architectural, wave-6 constraints stand), opcode max-run 10.16 s exceeds 10 s (median met; flagged honestly).

## Items the user forgot that were checked anyway
1. Repo hygiene: wave-8's committed 110 MB-class binaries (push-blocking, rule violation) — removed from the tip, gitignored, documented.
2. `.d` dependency files for PIC objects (header edits correctly trigger PIC rebuilds).
3. Staleness guard semantics (missing vs stale .so both handled — no silent outdated binary).
4. `dev-so-clean` target + exact rollback commands.
5. Production no-op after wave-8's touch-based benchmarks (legit catch-up, re-verified).
6. APK file identity hashes recorded (provenance).
