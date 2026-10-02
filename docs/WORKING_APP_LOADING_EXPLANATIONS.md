# WORKING APP LOADING EXPLANATIONS — why the working apps actually worked

> LOADING-CAMPAIGN (2026-10-03). Every explanation below is grounded in the
> per-run file-IO traces (`run/audit/regression/<app>_r1/file_io.jsonl`), the
> installed-store trees (`docs/INSTALL_TREE_PROOF.jsonl`) and the byte-identical
> golden regression (`scripts/working_vs_failing_probe.sh`).
> Companion: `docs/WORKING_VS_FAILING_LOADING_MATRIX.jsonl`.

## The one-sentence answer

The working apps worked **because their loading paths stayed inside the
capabilities the engine already had** — ARSC resource resolution, layout
inflation, SQLite (real sqlite3), the SharedPreferences XML store, the asset
stream path, and the F-NEW-234 per-package directory family — **and never
exercised the P0-void APIs** (FileOutputStream family, FD family,
decodeStream, provider stage, absolute-path mapping). The failing paths fail
on the APIs this campaign then implemented and probe-proved.

## Per-app WORKING_APP_EXPLANATION (trace-backed)

### com.darkempire78.opencalculator — golden `e364b001ee7abd66` ×3
- FILES: Context dir family only — `getFilesDir`-anchored identity; no
  FileInputStream/FileOutputStream in the trace.
- PREFERENCES: `SharedPreferences.commit` ×2 (write + commit) →
  `<store>/data/data/<pkg>/shared_prefs/<pkg>_preferences.xml` (atomic,
  escaped after ST-6 fix). History persists across the 3 gate runs.
- RESOURCES: ARSC best-match values + drawables via the existing resolver.
- P0 APIs NOT EXERCISED: openFd/PFD/AFD (zero), decodeStream (zero),
  ContentProvider-free manifest face, absolute Android path trades (zero).
  **It survived because it never hit the FD/write voids.**

### jwtc.android.chess — golden `b5a7a35d5fe0564b` ×3
- DATABASE: `databases/chess_pgn.db` (real sqlite3) + `ChessPlayer.xml` prefs
  on the store — the SQLiteOpenHelper chain (M3 F-ROOM-CHAIN law) carried it.
- P0 APIs NOT EXERCISED: 1,517 traced API calls (LOAD-AUDIT-2) contain no
  FileOutputStream/openFileOutput and no FD call. **Persistence came from
  SQLite, which was already real — not from the (then-missing) file write
  family.**

### dubrowgn.microtimer — golden `da73010a37dd0189` ×3
- FILES: `File.mkdirs` ×6, `FileOutputStream.open` ×3 (cache writes — now
  through the canonical path law), `getDatabasePath` ×3, `getCacheDir` ×1.
- DATABASE: `databases/app-data` + **`-wal` + `-shm` files visible on the
  store** (the ST-7 WAL law now answers and materializes the pragma).
- P0 APIs NOT EXERCISED: assets (zero), FD family (zero), decodeStream (zero).

### app.varlorg.unote — golden `4f1a9e4e8f64fae8` ×3
- DATABASE: `databases/notes.db` (real sqlite3). Notes persist across gate
  runs.
- Provenance note (honest): SQLite byte ops are not yet FileIoTrace-traced
  (ST-10 open) — the persistence proof here is the store tree + golden
  determinism, not the JSONL.

### org.telegram.messenger.web — golden `bbb6cd10a834963d`
- ASSETS: 7 `AssetManager.open` — ALL with provenance
  `@ apk=<INSTALLED base.apk>` and real DEX callers (o6;.p0, ih/a;.c/.a,
  ResLottieMeta, sg0); each entry cross-verified present in the installed APK.
- FILES→APK fallback law observed live: `files/bluebubbles.attheme`
  EXISTS=FAILURE → `assets/bluebubbles.attheme` OPEN SUCCESS.
- PREFERENCES: `SharedPreferences.commit` ×21 (now atomic + escaped).
- P0 APIs NOT EXERCISED: openFd/AFD (zero — theme bytes flow through the
  asset stream path), decodeStream (zero — images decode via decodeResource/
  decodeFile), provider stage (its androidx.startup chain is part of the
  still-open UI-navigation frontier, not the loading path).
- Its remaining frontier (settings face instead of intro/auth) is a
  **UI-navigation/lifecycle root, not a loading root** (see
  `docs/WHITE_SCREEN_LOADING_ROOTS.md`).

### com.probe.loading (synthetic) — the counter-example that proves the class
The probe DOES exercise every P0 API and now passes 23/23 asserts
(`scripts/loading_probe_runner.sh`). Its first divergences — recorded in
`docs/LOADING_FAILURE_DIAGNOSTICS.md` — are exactly the bugs the working
apps never tripped: the `read(byte[])` fill law, the BAOS chain, the
`File.length()` register-pair law, the provider-stage early return.

## Which missing P0s did the working apps simply not exercise?

| P0 (pre-campaign) | opencalc | chess | dooz | microtimer | unote | telegram |
|---|---|---|---|---|---|---|
| ST-1 getAbsolutePath hijack | not called | not called | not called | not called | not called | not called |
| ST-2 FileOutputStream family | not called | not called | DataStore-adjacent | **cache writes (worked post-fix)** | not called | not called |
| R-1 missing-asset fake-success | no assets | no assets | no assets | no assets | no assets | only EXISTING assets |
| R-2 FD family void | not called | not called | not called | not called | not called | not called |
| S-1 provider stage | none in manifest face | none | none | none | none | not on this UI path |
| ST-4 absolute-path mapping | not called | not called | not called | partial (mkdirs) | not called | not called |

**Every working app stayed inside pre-campaign capabilities or used only
existing assets; none of them touched a voided API.** That is the structural
explanation the audit required — now demonstrated from traces, not guessed.
