# cont375 CONT-5 — FINAL COMPATIBILITY CLOSURE + INDEPENDENT FAN-OUT PROOF (Phase 0 ledger)

**Head identity (honest):** git HEAD is `bb2f4f49` = `1c2ccdfd` + `tmp/cont4_comment.md` ONLY (the posted-comment copy; zero runtime/code delta, `1c2ccdfd` is the direct parent). Recorded, not hidden.

**Binary identity (honest):** rebuilt from exact HEAD content after container reset → sha16 `1177e1d08e09ee72`. The recorded CONT-4 binary `e93c4a62…` is not bit-reproducible (clean-tree rebuild vs prior incremental build tree). Screenshot-level equivalence is PROVEN, not assumed: anchors below.

**Bootstrap repairs (same procedure as CONT-2/3, all SHA-verified):** toolchain restored (aapt2 8.13.2-14304508 / ecj / r8 8.13.23 / android-34 stubs / DroidSansMono sha-verified); `libprobe.so` x86_64 rebuilt BYTE-EXACT `d5ec1f57fef3d271`; `gate_a_probe.apk` + `native_probe_apk` rebuilt WITH `lib/x86_64` packaged; arm64 zig fixture pending.

## CONT-5 AUDIT CHECKLIST (verdict suffixes mandatory; evidence appended per phase)

| # | Item | Verdict |
|---|---|---|
| P0.1 | HEAD = `1c2ccdfd` content (bb2f4f49 delta = tmp comment copy only) | IMPLEMENTED |
| P0.2 | Registry counts recorded at HEAD: 548 roots in `roots[]`; summary block STALE (538) → Phase 8 | OBSERVED |
| P0.3 | Anchors 5/5 ×3 BYTE-IDENTICAL (e364b001/b5a7a35d/d602648e/da73010a/4f1a9e4e) at rebuilt binary | TESTED |
| P0.4 | Gate A probe **97 PASS / 0 FAIL / 2 INFO** at rebuilt probe APK | TESTED |
| P0.5 | Negatives **19/19 PASS** — runbook gap FOUND+FIXED: `closeout_baseline.sh` never populated `run/gatea/probe_store`; N-08/N-12/N-18/N-19 rows are harvested from the probe results file → 9/19 false-fails until the probe run was added. Script patched (tooling fix, no runtime change) | TESTED |
| P0.6 | User goldens 4/4 REAL_APP_CONTENT (2048/snakedeluxe/minicraft/helloworld) | TESTED |
| P0.7 | Loading probe restart-persistence ALL PASS | TESTED |
| P0.8 | Reinstall matrix 8/8 PASS | TESTED |
| P0.9 | Uninstall proof ALL PASS | TESTED |
| P0.10 | Skill selftest 13/13 PASS | TESTED |
| P0.11 | Multiapp 5/5 | PENDING |
| P0.12 | NATX 10/10 ×3 | PENDING |
| PH-1 | `Lr5;.g pc=150` residual classification (no preset attribution) | PENDING |
| PH-2 | Independent game proof (previously-white game, 3 runs, screenshot SHA, verdict class) | PENDING |
| PH-3 | Independent app proof — Fossify Clock + Compose Sudoku | PENDING |
| PH-4 | F-NEW-239..242 generic fan-out (independent consumers) | PENDING |
| PH-5 | Full 124 battery from HEAD + honest blocker proof | PENDING |
| PH-6 | Unknown-APK gate 15-verdict live coverage matrix | PENDING |
| PH-7 | FOUNDATION_CONTRACT_98 PARTIAL/PENDING → A-F classification | PENDING |
| PH-8 | Root registry reconciliation (538-vs-548 summary staleness first) | PENDING |
| PH-9 | Pixel-provenance white/black/partial audit | PENDING |
| PH-10 | No-new-app-specific-hack audit | PENDING |

RULES ACKNOWLEDGED: no manufactured completion; no source-only finding becomes runtime-proven; RESUMED ≠ success; no app-specific hacks. Final exit will state COMPLETE or **NOT COMPLETE** with ranked P0–P3 blockers.
