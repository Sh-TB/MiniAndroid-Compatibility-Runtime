# v0.0.6.1 — Exchequer (Real HTML5, Real SQLite, Byte-Exact Anchor Wall, Honesty Standard)

**Date:** 2026-11-02 · **Parent:** v0.0.6-Leghorn (2026-09-16, `22c58a55`) ·
**Range:** 814 commits, ≈100 campaign waves (S49…S149, CONT-series) ·
**Registry:** 853 roots, honest per-root status (was 348 at the parent)

Named after the **Exchequer Leghorn** — the mottled black-and-white color
variety of the Leghorn breed, continuing the release-mascot line
(Brahma → Australorp → Chantecler → Silkie → **Leghorn** → **Exchequer
Leghorn**). A point release named for a color variety of the parent breed:
the mottled pattern fits a patch release assembled from hundreds of
individually verified black-and-white pieces (engine laws + their evidence).

The complete itemized changelog lives in
[`miniandroid/CHANGELOG.md`](../../miniandroid/CHANGELOG.md)
(`[v0.0.6.1-Exchequer]`, Keep a Changelog 1.1.0 format). This document is
the release summary.

## What changed, in one page

- **Real HTML5/JavaScript execution** — QuickJS + live DOM + Canvas2D raster
  + CSS box-model layout + ES modules + fetch/cookies, plus the NET-001
  TLS network stack and Mini Browser: real websites and web games execute
  end-to-end (Breakout 71 fully playable with real canvas render; mykanji
  renders its complete GUI; z.ai loads end-to-end).
- **Real SQLite** — the Cursor/database contract reached ART parity
  (F-NEW-401), the private-DB ONE-PATH law fixed the Telegram
  `SQLITE_CANTOPEN` root (the x41 exception class eliminated; holds at this
  release), and real CRUD is proven on disk by the sqlnotes/sqltasks
  programs (all four arms) and microtimer (two persisted alarm rows).
- **Real content, byte-pinned** — anchor wall **12/13 byte-exact ×3**
  (opencalc, chess, dooz, microtimer, unote, tower3d + six in-house games;
  snakeneon deterministic with a flagged build-env face drift). dooz
  renders a real Compose Scaffold (6/6 frames byte-identical `851cc176`,
  231,873 content px / 113 colors); g2048 was **played** with 4 real clicks;
  Telegram reached a fully clean execution (0 errors / warnings / uncaught)
  and really loads its 21 MB native lib (`JNI_OnLoad` ran).
- **The false-success era is closed** — the S107 audit reopened 117/128
  false visual closures; every closure since carries fresh-run evidence,
  FRAME-TRUTH pixel-ownership verdicts, and byte pins. Honest ABI
  advertising (LAW-001) and the fail-closed secret guard are permanent.
- **Engine depth** — ~350+ root-caused/verified fixes across DEX/reflection
  identity, collections/libcore laws, text & graphics pipelines, input to
  AOSP parity, storage/IO laws, scheduler truth; +39.5% interpreter budget
  for the dooz board; DalvikValue ≈112 B/value lighter.
- **Platform growth** — package install/uninstall + pkginspect CLI +
  GATE A; graphics-verification subsystem + a 122-repo graphics source
  library; the TraceEngine observability backbone with ≈20 env-gated
  diagnostics; crash forensics with native symbolication.

## Verification at this tag

| Gate | Result |
|---|---|
| Anchor wall | 12/13 byte-exact ×3 (`scripts/s149_true_wall.sh`; pins recorded in the changelog) |
| Regression | negatives 19/19 · reinstall 8/8 · multiapp 3/3 · gate-A probe 98/0/1 · skill selftest 13/13 |
| Battery | 94 → 124 stages ALL PASS (GATE A record, 2026-10-03); the standing gate on this lineage is the byte-exact anchor wall |
| Reproducibility | recorded binaries rebuilt byte-identically from clean containers across ≥8 independent waves |
| SQLite proof | sqltasks all four CRUD arms real; Telegram opendb OK, 0 exceptions |
| Interaction proof | g2048 played (4 real clicks, f43face08 → 550470af); microtimer two real alarm rows |

## Artifacts (honest status)

- **No binary artifacts are published for v0.0.6.1-Exchequer.** The release
  environment has no MinGW toolchain, and per the release guard no artifact
  is shipped without its verification trail; the latest packaged binaries
  remain `MiniAndroid-v0.0.6-Leghorn-*`. Build from source:
  `scripts/build/bootstrap_toolchain.sh` then `make` in `miniandroid/`.
- **Changelog & docs** (this release's deliverables):
  `miniandroid/CHANGELOG.md` (standard rebuild incl. retroactive
  v0.0.4/v0.0.5/v0.0.6 entries), this document,
  `docs/releases/RELEASE_MANIFEST.json`, `docs/INDEX.md` pointer.

## Known limitations

See the changelog's "Known limitations (honest)" section — the short list:
Compose clickable dispatch not yet fixed (root pinned; TRAIN-70 queued),
Compose draw path open, microtimer alarm-list row render open, snakeneon
build-env drift flagged, Windows artifacts not built this release, Telegram
full messenger UI not claimed.

## Evidence pointers

- `evidence/s138_trains … s149_trains`, `evidence/cont101…cont128`
- `docs/PROGRAM_QUEUE.json` — the standing 12-slot program queue
- `root_registry.json` — 853 roots with per-root status
- GitHub issues #353–#388 — hashed evidence comments and completion ledgers
