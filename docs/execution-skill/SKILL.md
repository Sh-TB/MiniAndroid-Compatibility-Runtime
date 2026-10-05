# Android Execution Skill — vendor-neutral workflow for any coding agent

Version: 1.0 (S74). Vendor-neutral by law: this file names NO coding-agent
product, plugin, or model. Any agent (or human) executes the workflow as
written against the MiniAndroid repository.

## Purpose

Run one Android APK/game on MiniAndroid, understand its exact compatibility
state, identify its current blocker, use only the relevant verified knowledge,
fix the runtime, prove the result, update the dossier and issue — without
rereading thousands of MD files or rediscovering verified knowledge.

## Non-negotiable rules (binding on every agent)

1. **Runtime Core is shared; Compatibility Status is app-specific.** Never add
   app-specific hacks, special cases, or state injection to fix one app.
2. **Searchlight law:** SYMPTOM → FIRST DIVERGENCE → CALLER → CALLEE →
   SEMANTIC LAW → UPSTREAM SOURCE → IMPLEMENTATION → TEST → REAL APK →
   REPRODUCIBLE EVIDENCE. Never stop at exit 0, "APK loaded", PNG exists,
   blank/black/white frames, or an agent claim.
3. **SOURCE → ALGORITHM → SEMANTIC LAW → TEST → MINIANDROID.** Prefer
   REFERENCE → ADAPT → TEST → REPLACE STUB → VERIFY. External runtimes are
   validation references, never source of truth. Check license/provenance
   before adapting anything.
4. **Observed ≠ verified. Implemented ≠ tested. Tested ≠ real-APK proven.**
   Use the canonical status vocabulary only: DONE / IMPLEMENTED / TESTED /
   OBSERVED / PARTIAL / BLOCKED / PENDING / SUPERSEDED.
5. **Truth over polish.** If blocked, say BLOCKED. Never upgrade a claim
   without runtime evidence; never hide a newly exposed blocker — continue the
   causal chain until it is fixed+verified, blocked with evidence, or deferred
   with a precise reason and continuation point.
6. **No state injection for games.** The only legal actuator is the real input
   path (`--tap x,y[@frame]` through the canonical TouchDispatcher). Vision is
   rendered-frame pixels only. Never mutate game memory, call private methods,
   or bypass Activity→View→input.
7. **A screenshot is not proof.** Every visual claim passes the quality gate
   (entropy/luminance/colors/non-background/bounds/SHA256) AND provenance:
   which Activity, which View, which surface, which frame, which state, which
   draw calls, which input. `pixel count != semantic visual proof` (the dooz
   23,472-px black-region lesson — see `CLAIM-DOOZ-23472-VISUAL`).
8. **Local commit ≠ published state.** Push claims require remote verification.
   Credentials live in env vars only; never on disk, never in logs/docs.
9. **English-only** for all public GitHub content (issues, comments, commits,
   docs).
10. **Do not restart settled work.** Search the knowledge records first; only
    reopen a closed law when new evidence directly contradicts it.

## Read order (token-efficiency law — mandatory)

```
1. docs/compatibility/apps/<app>.json        (dossier: status/blocker/links)
2. GitHub [EXEC] issue for the app           (latest dated evidence comment)
3. dossier fields: current blocker, next executable task
4. docs/compatibility/capabilities/<cap>.json (only linked ones)
5. docs/knowledge/laws/<law>.json            (only linked ones)
6. tool profile -> upstream source           (only if the law needs it)
7. runtime code                              (only now)
```

Expand outward only when the linked records do not answer the question.

## Execution loop (the 22 steps)

| Step | Action | Proof artifact |
|---|---|---|
| 1 | Find the app dossier (`docs/compatibility/apps/`) | — |
| 2 | Find its canonical `[EXEC]` issue (one per app; never create duplicates) | issue number |
| 3 | Read ONLY: current blocker, last evidence, linked capabilities/laws/knowledge | — |
| 4 | Build/run the APK (source-first recipe when available) | build log, APK SHA256 |
| 5 | Capture first divergence | trace excerpt |
| 6 | Trace caller → callee → argument → receiver → return → state | compact trace |
| 7 | Search upstream law (AOSP/ART/libcore/OpenJDK/AndroidX/Compose) | source file + line refs |
| 8 | Compare MiniAndroid behavior vs source/reference behavior | delta note |
| 9 | Implement the smallest correct runtime change (shared core, no app hacks) | diff |
| 10 | Run focused test | test output |
| 11 | Run the real APK | run log |
| 12 | Verify render (quality gate + provenance) | screenshot metrics + SHA256 |
| 13 | Verify input (real dispatch; scheduled `--tap x,y@frame` for reproducibility) | input record |
| 14 | Verify state change (input → callback → state → render) | frame-SHA pair / state hash |
| 15 | Verify persistence if relevant (modify → close → reopen → inspect) | persistence record |
| 16 | Verify security/sandbox boundaries (record, never interpret: DECLARED ≠ used; network observed ≠ malicious) | security profile fields |
| 17 | Run regression (focused test → affected apps → fixture battery → corpus) | before/after table |
| 18 | Record evidence (compact bundle: metrics.json / trace.json / SHA256SUMS / representative PNG / GIF only if useful) | evidence dir |
| 19 | Update the app dossier (`docs/compatibility/apps/<id>.json`) | diff |
| 20 | Update the issue (dated evidence comment; link commit + records; update body if status changed; never destroy history) | comment URL |
| 21 | Promote newly verified semantic knowledge (`tools/promote_knowledge.py`) | knowledge record |
| 22 | Close the issue ONLY if its dossier completion criteria actually pass | closing comment |

## Reproducibility protocol

Where deterministic execution is possible, run 3 times and compare: state
sequence, event sequence, per-frame screenshot SHAs, final frame, relevant
trace. Record `RUN-1/RUN-2/RUN-3, MATCH = YES/NO`. Non-determinism must be
attributed (timing / thread scheduling / input scheduling / rendering / game
itself) — attribution, not automatic failure.

## Test levels

- **Level A** — unit/semantic tests (fixtures).
- **Level B** — framework/runtime integration tests (battery).
- **Level C** — real APK execution (corpus + probe recipes).
A capability is not fully proven if only Level A passes. Every meaningful
runtime change gets eventually probed against at least one real APK; prefer
diverse consumers. Regression law: never fix one app by silently breaking
another — record before/after/changed/unchanged.

## Safe stop / resume

If you must stop, record: CURRENT HEAD · CURRENT ISSUE · CURRENT BLOCKER ·
LAST VERIFIED STEP · NEXT EXACT COMMAND · NEXT EXACT FILE · NEXT EXACT
QUESTION · UNCOMPLETED TEST — in the issue (comment) and the worklog, so
another agent resumes without rediscovery.

## Autonomous gameplay ladder (games)

```
launch → identify controls → inspect ViewTree → inspect rendered geometry
→ plan action → send REAL input → observe state → verify expected transition → repeat
```

Evidence classes, in order: static render → input accepted → state changed →
gameplay progressed → win/loss → restart → persistence. Prove
`INPUT → callback → game state transition → render update` (e.g. tap START →
reStartGame → Thread.start → tick → snake position changes → Canvas redraw).

## Canonical records touched by this skill

- `docs/compatibility/README.md` — platform law + schemas
- `docs/compatibility/apps/*.json` — Layer A dossiers (update at step 19)
- `docs/compatibility/capabilities/*.json` — capability records
- `docs/compatibility/tools/*.json` — helper/source profiles
- `docs/knowledge/laws/*.json` — canonical knowledge (only VERIFIED is law)
- `docs/compatibility/CAPABILITY_MATRIX.md` — regenerated from records
- Validator gate before any commit: `python3 tools/validate_compatibility_graph.py`

---

# v2 (2026-10-04) — machine-readable product surface (issue #371 §D)

The workflow above is the LAW. This section is the OPERATIONAL SURFACE an
external agent (e.g. Hermes) drives without reading MiniAndroid source.

## Machine-readable manifest

`skill_manifest.json` (same directory) defines 10 operations — apk_intake,
prerequisites, full_inspection, install, run, observe, first_divergence,
classify_white_black, evidence_bundle, uninstall — each with its exact CLI,
return schema, and error contract. It also pins the deterministic status
vocabulary (DONE/IMPLEMENTED/TESTED/OBSERVED/PARTIAL/BLOCKED/PENDING/
SUPERSEDED), the frame-verdict vocabulary (REAL_APP_CONTENT /
DEFAULT_BACKGROUND_ONLY / NO_ROOT / PARTIAL_MARGINAL / WHITE_BLANK), and the
L0–L6 execution-level definitions.

## Self-test (adherence + portability proof)

```
python3 scripts/skill_selftest.py
```

Drives every manifest operation against the live runtime using ONLY the
documented CLIs (no MiniAndroid source imports): intake → prerequisites →
negative/malformed contract → install identity → run by installed identity →
frame-truth observe → 3-way white/black cause classification → run-pair
determinism → provenance bundle → uninstall + NOT_INSTALLED honesty →
manifest self-containment. Exit 0 = the skill is usable as documented.
Latest result: 13/13 PASS (see `docs/execution-skill/selftest_report.json`).

## Environment pre-flight (issue #373)

Before any run, `pkginspect --apk <path> --what prerequisites` returns the
APK requirement model (minSdk/targetSdk/features/permissions/ABIs + ELF
machines/webview) against the environment profile
(`docs/ENVIRONMENT_PROFILE.json`, ENV-001..010). The `nativeAbiVerdict`
field discriminates the redroid-class failure (advertised-but-not-executable
ABI) from ordinary runtime roots — an ARM-only APK INSTALLS and then stops
at first native use; that is an environment/translation boundary, never a
rendering bug. Full matrix: `docs/ENV_PREREQUISITE_MATRIX.jsonl`.

### Unknown-APK preflight gate (CONT-3 Phase 2 — operational)

`python3 scripts/unknown_apk_preflight.py <apk> [--json OUT] [--max-seconds S]`
is the WIRED gate: one driver, one machine-readable contract
(`MINIANDROID_UNKNOWN_APK_PREFLIGHT/1.1`), one verdict implementation shared
by the CLI and this skill. It determines package identity + APK SHA,
min/target SDK, permissions, features, native ABI trees, component counts,
DEX/resources structure, environment matches against ENVIRONMENT_PROFILE,
install + launch outcome, the first observed divergence (method + pc), and
classifies EXACTLY one verdict:

`ABI_OUT_OF_SCOPE | PREFLIGHT_PASS | ENVIRONMENT_BLOCKED | INSTALL_BLOCKED |
SECURITY_BLOCKED | IDENTITY_BLOCKED | SERVICE_BLOCKED | EXECUTION_BLOCKED |
RESOURCE_BLOCKED | GRAPHICS_BLOCKED | MEDIA_BLOCKED | NETWORK_BLOCKED |
INPUT_BLOCKED | CAPTURE_ONLY | RUNTIME_ROOT | UNKNOWN`

Laws: (0) **LAW-001 FIRST TEST LAW** — the ABI scope check runs FIRST,
before install/launch, from the real `lib/<abi>/` tree: an APK with native
trees and no x86/x86_64 ABI is `ABI_OUT_OF_SCOPE` (SKIP bucket, carried
with `verdict_class=SKIP` + `counts_as_failure=false`; ARM-only titles are
out of current scope, never counted as runtime failures — CONSTITUTION_V2
LAW-001); (1) a malformed/unparseable APK is UNKNOWN — never fabricated into a
richer verdict; (2) an ABI mismatch beyond LAW-001 (declared-but-unexecuted
paths) is a hard blocker only when the launch
actually failed on a native path — a Java-only app that reached its budget
is CAPTURE_ONLY/RUNTIME_ROOT with the mismatch recorded, not upgraded
(FA-01/FA-02 honesty works both directions); (3) a recorded divergence with
a caller chain is RUNTIME_ROOT (a genuine runtime root), never flattened
into an environment label; (4) `is_environment_prerequisite` distinguishes
proven environment prerequisites from runtime work. Verdict-class unit
coverage lives in `scripts/unknown_apk_preflight.py` (classify) — SERVICE/
MEDIA/NETWORK/INPUT branches are wired through launch_stage mapping and
fire when the CLI emits those markers; they have not yet been exercised by
real CLI outputs (honest gap, not a claim).

## White/black/partial classification (WS-002)

1. prerequisites clean? → if NOT: environment-prerequisite mismatch (quote
   `environmentMismatches`; recommended next probe included).
2. prerequisites clean + `frame_analysis.verdict != REAL_APP_CONTENT` →
   ordinary runtime root; follow `first_missing_stage` then the run log's
   first `EXC-PROPAGATE`/`SYNTH-EXC` chain.
3. `verdict == REAL_APP_CONTENT` → real content; proceed to input/state
   evidence for L4+.
Never relabel a verdict without new runtime evidence; the classifier is
frozen (21-P0-6).
