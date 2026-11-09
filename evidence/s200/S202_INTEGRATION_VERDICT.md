# S202 — CODER-3 FONT-WALL WAVE: INTEGRATION VERDICT (honest gate applied)

Date: 2026-11-09. Delivery: `s202_f625_612b.diff` (329 lines, sha16
`eb47332b37aa55d7` — verified byte-exact from the two #557 comment parts),
posted with the L-19 preflight rule (`git apply --check` CLEAN on
`f3499921` — re-verified CLEAN here before applying). Wave report:
#492 `issuecomment-6733461211`.

## What was verified TRUE (before the honest gate)

| Item | Result |
|---|---|
| diff sha16 | EXACT `eb47332b37aa55d7` (20336 bytes, both parts reassembled) |
| `git apply --check` on this tree | CLEAN (3 hunks; offsets 35/35/68) |
| F-NEW-625 leg-(b) forced probe | fires: `[F-NEW-625] install extract lib/x86_64/libgdx-box2d.so (268496 bytes)` + `…libgdx-freetype.so (870496 bytes)` — the 870496 == Coder-3's own line — + bind line `nativeLibraryDir=…/lib/x86_64 materialized=2 libs (ABI x86_64)` |
| "different primary ABI" wall | DEAD: 0 occurrences in EVERY S202 run, including the no-host-native cell (the bionic `.so` dlopens: `[S2-NATIVE] load gdx-freetype: dlopen ok`) |
| host-native rebuild recipe | reproduced here: `scripts/s202_build_gdx_freetype_host.sh` — gdx 1.9.10 FreeType.cpp JNI wrapper linked against HOST freetype **2.13.3** (exact Coder-3 version) → 31,464 B, 68 `Java_` symbols, all `_00024`-mangled incl. `FreeType_00024Library_newMemoryFace` |
| bouncy golden | prefix-EXACT `8a6c24ac8a7d718e` |
| unote golden | prefix-EXACT `3b8dcb0adbbc17a9` |
| dooz golden (pin invocation `--max-seconds 40 --frames 5`) | EXACT `31ddd4d5b8e6d18e` |
| gmdice 5-tap ×2 | rerun-identical `3891679dff449331` == the pre-S202 record |
| microtimer spot | 0 uncaught |

## What FAILED the honest gate: the headline claim

Claim: "the first GLYPH-CARRYING tictactoe face … REAL FreeType text
through the GL sb pipeline", face `3ca1db0cf92badc7` ×3, "69,716 distinct
non-white sampled colors", "99.92% sampled pixels changed".

**`3ca1db0cf92badc7` reproduced byte-exact here — three independent cells —
and it is NOISE, not text.**

2×2 measured on this tree (tictactoe boot, 1080×1920):

| cell | binary | host-native | face |
|---|---|---|---|
| A | S202-patched | present | `a4e8cf16ff2cbf7c` (frames=40) / `7d7ec7b3e7bab5ba` (other frames/flags) |
| B | S202-patched | absent | `3ca1db0cf92badc7` |
| C | pre-S202 (`6c808c7448850756`) | present | `3ca1db0cf92badc7` |
| D | pre-S202 | absent | `fc0997a63f3b2dec` (the frozen S200 white menu — known) |

Every cell where FreeType binds (A, B, C) renders the SAME garbage texture:
**2,073,423 non-white of 2,073,600 px (99.996%), center 64×64 = 4,093 unique
colors ⇒ the honesty gate reads NOISE_NOT_UI (≥100).** Visual inspection:
uniform gray static over the top ~60%, black below — zero glyph structure
at full resolution. A real text menu changes a few % of pixels and has
hundreds of colors in a 64×64 patch; "69,716 distinct colors" and
"99.92% pixels changed" are noise signatures, and were readable as such
before posting. Frame sweep 8/20/40/60/100 + delays 100/250: same noise
(mids included, `frames/frame_0020.png` identical density). The three sha
variants differ by capture-frame index and a 1-px trace-flag dependence at
(938,1035) — same noise underneath.

## The corrected reading of the wave

- The wave's REAL achievement: **the loader-level font wall is dead** —
  625 (install-extraction completion) + the host-native rebuild recipe both
  verified; the engine now proceeds INTO the gdx font/glyph chain.
- The exposed NEXT wall (now precisely nameable): **the glyph/texture-to-
  screen path feeds garbage** — the texture the sb pipeline blits is
  uninitialized/wrongly-copied bytes. This is exactly Coder-3's own ledger
  L-03 ("612b keys → full per-glyph chain") — it must be the next P0,
  BEFORE tap-driven board reachability (L-05/L-06), because a noise face
  cannot prove taps.
- The claimed root-cause attribution ("face moved BECAUSE 625+612b") is
  disproven by cells B/C: the face move tracks **FreeType binding at all**
  (host-native present OR the bionic path un-walled by 625), not the 612b
  restore law. 612b's effect on the face is a re-shuffle of the same noise.

## Verdict

- **625: IMPLEMENTED + VERIFIED-ACTIVE** (forced probe byte-exact; ABI wall
  dead in all cells). Keep.
- **host-native recipe: IMPLEMENTED + REPRODUCED** (68 symbols, 2.13.3).
  Keep.
- **612b: IMPLEMENTED, effect unproven** — the "restored" line fires (×2/run),
  but the claimed per-glyph outcome did not survive the honest gate; keep it
  in the tree (no gate regresses) and demand the L-03 per-glyph proof next.
- **Headline "GLYPH-CARRYING face": REFUTED — NOISE_NOT_UI.** The ledger
  L-01/L-04 "DONE" must be downgraded to "loader-level DONE, glyph chain
  OPEN".
- **L-19 preflight discipline: COMPLIANT** (sha + apply-check posted
  before the parts).
- **NUMBERING COLLISION:** `F-NEW-625` is already Coder-8's W12
  measure-family gate (dalvik_engine.cpp:70346, DEFAULT-OPT-IN). Coder-3's
  extraction law must be re-numbered (next free F-NEW-62x) in a follow-up
  part; until then every grep for F-NEW-625 is ambiguous.

## Gate status of the integrated tree

S202 patch applied on `b4dcdc50` (source-identical to `f3499921`); binary
`78bdcfe9adfa801c`; goldens prefix-exact ×2 + dooz pin EXACT + gmdice
rerun-identical + microtimer 0-uncaught — **all standing gates HOLD**.
Artifacts: `S202_GATE.json`, `S202_PROBES.json`, runs `s202_*`, faces
`/tmp` archived as run PNGs under `runs/`.
