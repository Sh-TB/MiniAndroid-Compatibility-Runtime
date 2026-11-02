# CONT-11 EXECUTION LEDGER — «ادامه» wave (regression + TG-SQLITE fix + new programs)

Date: 2026-11-02 (UTC+8 session)
Head at wave start: e99c2fbd (stray uuid) ← 6a66806a (CONT-10 WAVE 6)
Binary lineage:
- Pre-fix rebuild from committed tree: `aed46450c103f2ea` — BYTE-IDENTICAL to the
  binary pinned by scripts/cont10_anchors.sh (reproducible lineage proven across
  container reset).
- Post-fix binary (this wave's only engine change): `400a7c1c48eb27fc`.

## 1. Old-program regression battery (binary 400a7c1c48eb27fc, all ×3 unless noted)

Evidence: evidence/cont11/CONT11_REGRESSION.json (runs under run/cont11/).
Pre-fix battery snapshot (binary aed46450c103f2ea): evidence/cont11/CONT11_PREFIX_BINARY_aed46450.json.

| program | package | anchor ×3 | verdict | vs recorded |
|---|---|---|---|---|
| opencalc | com.darkempire78.opencalculator | e364b001ee7abd66 | REAL_APP_CONTENT | matches LONG-STANDING golden; W6-recorded a976d2f9 NOT reproduced at committed tree (flag, §4) |
| chess | jwtc.android.chess | b5a7a35d5fe0564b | DEFAULT_BACKGROUND_ONLY | MATCH |
| dooz | io.github.yamin8000.dooz | d602648e8e401895 | DEFAULT_BACKGROUND_ONLY | MATCH |
| microtimer | dubrowgn.microtimer | da73010a37dd0189 | REAL_APP_CONTENT | MATCH |
| unote | app.varlorg.unote | 4f1a9e4e8f64fae8 | REAL_APP_CONTENT | MATCH |
| 2048 | com.miniandroid.g2048 | 7ad9a8bdefba539b | REAL_APP_CONTENT | MATCH |
| mini-tetris | com.miniandroid.tetris | 26ccfce917c0e24c | REAL_APP_CONTENT | MATCH |
| minicraft | com.miniandroid.minicraft | ce27f331770f6979 | REAL_APP_CONTENT | MATCH |
| snake-deluxe | com.miniandroid.snakedeluxe | 34a712689ce66e58 | REAL_APP_CONTENT | MATCH |
| snake-neon | com.miniandroid.snakeneon | 477bb95e1e6398ce | REAL_APP_CONTENT | MATCH |
| tictactoe-deluxe | com.miniandroid.tictactoedeluxe | 0a1cd01bb490fdc5 | REAL_APP_CONTENT | MATCH |
| bouncy | com.dozingcatsoftware.bouncy | b6dde6074bf47264 (×1) | REAL_APP_CONTENT | MATCH (CAMPAIGN_STATE recorded) |
| freebloks | de.saschahlusiak.freebloks | b5a7a35d5fe0564b (×1) | DEFAULT_BACKGROUND_ONLY | generic background face (same face as chess) |
| tower3d | stack.tower3d | 31ddd4d5b8e6d18e (×1) | NO_ROOT | libGDX SharedLibraryLoadRuntimeException — native .so load frontier (standing) |

Score: **11/13 byte-identical MATCH** (opencalc matches its long-standing golden;
the W6 a976d2f9 record is the unreproduced outlier) **+ bouncy MATCH + 2 honest
standing-frontier faces** (tower3d native-lib, freebloks background).

## 2. F-NEW-259 fix-activity proof at the rebuilt binary

- fixtures/fnew259_probe rebuilt via scripts/cont10_build_probe.sh
  (probe apk sha16 6e57f8ddb2fe6554) → **7/7 PASS** at aed46450c103f2ea
  (A iterator n=3 alpha,beta,gamma; B lifecycle; C instanceof; D visibleEntries
  exactly 1; E empty queue 0; F addAll true/1; G append x,y,z).
- dooz live with MINIANDROID_F259_TRACE=1: 53 F259-ITER entries on the real
  APK + [F259-INS] Lel0;.c instanceof checks; screenshot anchor stable
  d602648e8e401895 (draw path unchanged — consistent with W6's "compose DRAW
  path" remaining root).

## 3. ROOT-CAUSED-FIXED (this wave): TG private SQLite opendb violated the ONE-PATH LAW

Symptom (user-visible, reproduced pre-fix): telegram 40 × SQLiteException at
`Lorg/telegram/SQLite/SQLiteCursor;.next` (forkgram 10 ×), log
`[TG-SQLITE] opendb FAILED rc=14 (SQLITE_CANTOPEN) file=/data/data/<pkg>/files/cache4.db`.

Root cause: miniandroid/src/jni/telegram_sqlite_jni.h opened the ANDROID-LOGICAL
path raw on the host. Host /data does not exist → CANTOPEN → every prepare/step
after it fails → the x40 SQLiteException face. This violated the canonical
one-path law (storage/data_root.h: "no subsystem may invent its own mapping").

Fix (generic, no package-specific code): opendb now routes the logical path
through `Storage::resolve_android_path` (SANDBOX_DATA →
`<data-root>/data/data/<pkg>/…`), creates the parent dir, then opens real
sqlite3 (real sqlite3_open_v2, READWRITE|CREATE).

Runtime proof at 400a7c1c48eb27fc (telegram_official.apk, package
org.telegram.messenger.web):
- `[TG-SQLITE] opendb OK logical=/data/data/org.telegram.messenger.web/files/cache4.db physical=<root>/data/data/org.telegram.messenger.web/files/cache4.db`
- **cache4.db created with 95 REAL tables** (animated_emoji, app_config,
  channel_admins_v3, chat_hints, …) + active WAL/SHM (2.6 MB WAL written).
- **SQLiteException 40 → 0**; screenshot anchor UNCHANGED bbb6cd10a834963d
  (render-neutral storage fix; REAL_APP_CONTENT retained).
- Remaining TG exceptions re-classified (NOT sqlite): 8 × `Ll9/j;`
  (Google ML Kit MlKitInitProvider chain), 1 × UnsatisfiedLinkError
  (tmessages.49 ABI extraction face, GATEA-NATIVE deferred).
- forkgram: opendb OK now; remaining 8 × SQLiteException are a DIFFERENT root —
  `prepare FAILED rc=0 sql=` (empty SQL) where the SQL String.format received an
  empty format string (engine R.string resource gap in the fork); real-JNI
  behavior faithfully reproduced (null stmt → throw). Standing frontier recorded.

### SQLite 70%-checklist proof (TWO programs, real read/write)
1. Telegram org.telegram.messenger.web — cache4.db, 95 tables, WAL (private JNI
   over real sqlite3; fixed this wave).
2. chess jwtc.android.chess — databases/chess_pgn.db, `games` table with
   **1 runtime-written row** (framework DatabaseShadow path).
3. (bonus) unote app.varlorg.unote — databases/notes.db schema created
   (table_notes + sqlite_sequence).

## 4. Honest divergence flag (registry hygiene, no inflation)

W6 (commit 6a66806a) recorded "opencalc anchor CHANGED a976d2f9 — richer render".
At the committed tree (both aed46450c103f2ea rebuild and 400a7c1c48eb27fc),
opencalc reproduces its LONG-STANDING golden e364b001ee7abd66 ×3. The F-NEW-259
fixes ARE active here (probe 7/7 §2). Conclusion recorded: the a976d2f9 record
is not reproducible from the committed tree; the long-standing golden stands;
flagged — NOT silently rewritten.

## 5. New programs (binary 400a7c1c48eb27fc)

Evidence: evidence/cont11/CONT11_NEWBATCH.json (runs under run/cont11/new_*).

| program | package | verdict | anchor | note |
|---|---|---|---|---|
| Secuso Privacy Friendly 2048 | org.secuso.privacyfriendly2048 | **REAL_APP_CONTENT** | eb5ebd559cad1028 | NEW WIN — launch-frame face was deferred-UI provisional (F-NEW-232 queue_size=1); `--frames 300` time-driven capture materialized it (301 frames, CLASSIC_CANVAS). Frontier: 1 uncaught (Glide cleanReferenceQueue F084 halt + GeneratedAppGlideModule ClassNotFound) |
| Balance (ashkanrafiee) | com.ashkanrafiee.balance | **REAL_APP_CONTENT** | 3b834ad8c55d8f76 | NEW WIN at frame 20 (Persian-resources app) |
| Ricochlime | com.adilhanney.ricochlime | NO_ROOT | 31ddd4d5… | Compose WINDOW_ROOT frontier (dooz draw-path family) |
| awagam | com.awagam.android | DEFAULT_BACKGROUND_ONLY | b5a7a35d… | NPE family + APP_DRAW_OPS missing |

## 6. Engine change list (this wave)

- miniandroid/src/jni/telegram_sqlite_jni.h: opendb routes through
  Storage::resolve_android_path (one-path law compliance) + logical/physical
  logging. No other source file touched.

## 7. Regression at the post-fix binary

All groups re-run from scratch at 400a7c1c48eb27fc (no resumed rows):
anchors 4/5 byte-identical MATCH + opencalc matches long-standing golden (§4);
six games 6/6 MATCH; bouncy MATCH; tower3d/freebloks unchanged faces;
telegram anchor UNCHANGED with SQLiteException 0. Zero regressions from the fix.
