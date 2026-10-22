## CONT-11 WAVE 8 — batch 2 of 20: TWO generic roots closed (F-NEW-510, F-NEW-511a) — مشکل این دو ریشه حل شد — with one honest deferral

Follow-up to [the W7 ledger](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/380#issuecomment-6346768886). Per the ۲۰-تا-۲۰ directive: batch 2 = the 13 W7 `DEFAULT_BACKGROUND_ONLY` survivors + the secuso PARTIAL row + 6 new LAW-001-clean fillers (secuso_ludo, sopadeletras, secuso_dicer, survivalmanual, peri, dmfs_tasks) = **8 games + 12 apps**. Fresh-store screening at `55c5e06b`: 0 REAL / 3 PARTIAL (secuso_ludo + secuso_dicer crossed on first contact) / 17 DEFAULT, 9 crash rows.

### Root 1 — F-NEW-510 `ROOT-CAUSED-FIXED`: androidx.startup discovered ZERO initializers in every androidx-startup app

`AppInitializer.discoverAndInitialize` iterated `metadata.keySet()` (`F273-PROVINFO metaData entries=4`) and `hasNext` answered **false**. Mechanism: the EXP-093/ContentValues keySet materialization is an `ArrayList` **wrapper** whose backing array hangs off the `array` heap field (no `__array_length__` on the wrapper); Set/Collection-declared iteration fell through the F-036 engine gate into `CollectionShadow`, which reads its own empty parallel state. **Fix**: one-hop wrapper resolution in `CollectionShadow.hasNext/next` — fires ONLY on the wrapper shape; the F-036 gate stays byte-identical (an engine-gate extension was tried and honestly **reverted** as higher-churn). This is the P0 family: every Kotpref/WorkManager/emoji2/lifecycle-startup consumer dies here.

### Root 2 — F-NEW-511a `ROOT-CAUSED-FIXED`: `Class.forName` aliased the instruction counter as a heap object id

`forName` returned `make_class(desc, instruction_sequence_)` — `ref_id` is a monotonic **counter**, which the CLASS_REF→arg boundary carries as `object_id`. Live face: forName tokens aliased heap ids 24/45/66/87 (PackageManager owned #24) → the initializer `HashSet` stored "Class<KotprefInitializer>" **backed by the PackageManager object** → `getDeclaredConstructor` dispatched on PackageManager → null → `Constructor.newInstance` NPE → `StartupException`. The same defect F-NEW-249 fixed for `Object.getClass` — forName never got the update. **Fix**: `make_stable_class_token` (the F-069/F-249 per-descriptor heap token).

### Honest deferral — F-NEW-511b (the container arm)

Materializing `singletonList(Class<?>)` elements at the container boundary **completes the whole startup chain** (Kotpref ISE gone, survivalmanual 34→26 uncaught, the app advances to Material FAB layout inflation) — but it flips the **chess anchor** (`a0319686` → blank; `Toolbar.setSubtitle` → `x0/f.t` NPE chain, PARTIAL→1-color). A/B bisected cleanly: 510-only and 510+511a **both preserve** the chess face; 511b is the trigger. Per the zero-drift law the arm is **deferred with its patch preserved** (`evidence/cont11/w8/fnew511_patch.diff`); W9 owns 511b **together with** the Toolbar/x0 decode and the `Resources$NotFoundException` getColorStateList family (survivalmanual FAB + alexcalc Toolbar share the signature).

### Gates at the final binary `060fdbefd3e9f9d2` (510 + 511a)

| Gate | Result |
|---|---|
| Lineage | pre-W8 tree rebuilt → `55c5e06b1e0a3997` **byte-identical** to the recorded W7-REBASE binary |
| Anchors ×3 | **6/6 MATCH, zero drift** — opencalc `63020bc7` / chess `a0319686` / dooz `31ddd4d5` / microtimer `bbd350b6` / unote `7481e9b4` / tower3d `11a38a5a` |
| Negatives | **19/19 PASS** |
| Classifier selftest | **14/14 PASS** |
| Gate A multiapp / reinstall | **ALL PASS / 8/8** |
| Batch-20 post-fix | content faces unchanged (0/3/17) — the visible content gates sit behind the deferred 511b + RNFE families; the landed fixes are trace-proven mechanism repairs |
| Registry | 823 → **825** (F-NEW-510, F-NEW-511), ids unique |

Batch evidence: `evidence/cont11/{batch20_w8_screening_prefix.json, batch20_w8_screening.json, wave8_summary.json}`; runs under `run/w8/`. The `run_test_battery.sh` failures observed in this container are pre-existing harness staleness (test links omit `build/audio/*.o`; `tools/android-34.jar` path drift — repaired by symlink), not a wave regression; the wave diff touches no audio/link surface.

### W9 frontier (named and owned)

511b + Toolbar/x0-family decode → then the getColorStateList family → then the deskclock `yg0.i` (×36), sopadeletras (`La;`/`qh1.f`, ×32), etar alerts IAE (×19), dmfs `ContentOperation.register` (×14) pins, and the libGDX native faces (F-NEW-498 family).
