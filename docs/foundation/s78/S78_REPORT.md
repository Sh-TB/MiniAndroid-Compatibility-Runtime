# S78 REPORT — DEEP RUNTIME CLOSURE & EVIDENCE-TO-IMPLEMENTATION WAVE

Generated: 2026-09-22 · Wave start HEAD: c6d14d2e (after publish) · Mandate:
use the S77 infrastructure to close the deepest real runtime gaps along
evidence → producer → upstream semantics → law → implementation → execution →
observation → regression. **No summary replaces checklist.**

```text
S78 STATUS

BASELINE:
HEAD:                    c6d14d2e at wave start (S77 docs commit)
BINARY:                  miniandroid/build/miniandroid (Sep 21 18:45 rebuild,
                         R393/R394/R347 markers verified) — fresh, not stale
DISK:                    1.3G free at start (recovered to 2.0G by snapshot
                         quarantine); guard added (§26), 84% at final gate

REMOTE:
REMOTE_STATUS:           user provided PAT + "publish all old pushes" →
                         pushed c67230be..c6d14d2e (11 commits) — verified
                         via ls-remote; publish debt = 0 (was PUBLISH_BLOCKED
                         since S75)
ACCIDENTAL_SNAPSHOT:     d51f1815 (UUID message, 2931 files, 593 MB unique
                         objects: backup zips, corpus caches, agent state,
                         platform-34.zip fragment) — quarantined on branch
                         backup/s78-accidental-snapshot (rollback preserved,
                         SHA recorded in worklog); NOT pushed: violates the
                         repo's commit-evidence rules (no backup dumps /
                         toolchain blobs). Nothing deleted — recoverable via
                         git show backup/s78-accidental-snapshot:<path>.

S77 ARTIFACT COUNT:      9 derived artifacts confirmed on filesystem +
                         generator (8 MD views + sandbox_errors.json;
                         ninth = BLAST_RADIUS.md). master_audit.json +
                         MASTER_CHECKLIST.md are canonical INPUTS, not
                         generated. item75_closure.json / ITEM75_CLOSURE.md
                         pre-exist (S75). Count=9 verified, not from report.

S77 COMMIT ACCOUNTING:   8 unpublished at S77 start (5 S75: affc0d57,
                         310aba44, 84ac7869, 2835e9c6, b326acfd + 3 S76:
                         2f13abe2, 3057ddb3, a8704916) + 3 S77 (81eab7a6,
                         aae14f0e, c6d14d2e) = 11 TOTAL — ALL PUBLISHED S78.

F-152 (dooz):            REPRODUCED → ROOT-CAUSED → FIXED → TESTED
  REPRODUCE:   run/s78_f152_repro (fresh binary; APK SHA 299eab21…b362b):
               [F141-DIAG] Llt0;.w pc=808 recv t8/o0 NULL
  PRODUCER:    pc=490 sget-object v2, Llt0;->o:Lsun/misc/Unsafe;
               ← <clinit> pc=5..18: o = (Unsafe)
                 AccessController.doPrivileged(new n12())
               ← engine bridge returned typed-default null WITHOUT
                 dispatching n12.run() (silent stub; check-cast null =
                 legal no-op → silent §12 propagation)
  LAW:         R-NEW-395 (libcore AccessController.doPrivileged = action.run())
               + R-NEW-396 (synthetic-class getDeclaredFields subset:
               Lsun/misc/Unsafe; → theUnsafe; n12.run() iterates the array)
  EXECUTION:   unsafeNPE 9 → 0; [R337-UNSAFE] real offsets return
               (Ltp1;._state$volatile → 16 etc.)
  REGRESSION:  scripts/s78_f152_regression.sh 6/6 PASS (real APK)
  HONEST NOTE: visual state unchanged (nonwhite 23,472 engine-default
               face) — dooz NOT_HUMAN_VISIBLE; §16 gate NOT claimed.

F-153 (snake CJK):       REPRODUCED → ROOT-CAUSED → FIXED → TESTED → OBSERVED
  PRODUCER:    DialogShadow painter → SoftwareCanvas::draw_text →
               BitmapFont (95 ASCII glyphs, byte-wise iteration) — every
               non-ASCII byte maps to the space glyph → 0 px (§12 skip)
  LAW:         R-NEW-398: (1) non-ASCII text routes through the platform
               pipeline (TextShaper: UTF-8→FriBidi→HarfBuzz→FreeType);
               (2) fonts.xml-style CJK fallback face (WenQuanYi Zen Hei)
               for remaining .notdef clusters (mirrors emoji fallback).
               ASCII keeps the byte-identical BitmapFont path.
  CONSUMER-INDEPENDENT (§6): fix at the single draw_text choke point
               (dialog title/message/buttons + toast all flow through it).
               No second CJK consumer exists in the 14-app corpus —
               recorded explicitly.
  EXECUTION:   frame_094: positive 重新开始 0→56 blue px; negative 退出
               0→28 blue px; ASCII 'Game Over!' 343 grey px (unchanged)
  REGRESSION:  scripts/s78_f153_regression.py 3/3 PASS; snake two-run
               dialog-restart probe re-run on the S78 binary: RESTART
               OBSERVED; second life: 120 moves, 25 turns, 2 food
               captures (frames 94..128)

NEW FAILURES:
  F-154 (PARENT_FAILURE=F-152, NEW_DEPTH +2 frames): Lh3;.h pc=36
  Set.iterator() on null Set — Ljs0;.entrySet (REAL dex bytecode) sgets
  Collections.EMPTY_SET → SGET-MISS typed-default null. ROOT: JVM-clinit-
  injected Collections constants had no seed. LAW R-NEW-397 (OpenJDK
  Collections EMPTY singletons + Empty-family read contract). FIXED:
  setIterNPE 8 → 0. Registry + depth chain updated.

FAILURE DEPTH CHAIN (dooz, §8):
  F-146 (S76, getAbsoluteFile) → F-152 (S78, doPrivileged/Unsafe init)
  → F-154 (S78, Collections.EMPTY_SET) → next: pre-existing kotlinx Job
  ISE ("already complete or completing", ×4 constant across all runs —
  NOT new) + F-147 secondary site (MainActivity.onCreate pc=228
  ViewGroup.getChildAt null receiver; getChildAt itself REC-MISS).
  Each link: reproduced, producer-traced, law-identified, fixed, tested.

R-NEW CREATED:  R-NEW-395, R-NEW-396, R-NEW-397, R-NEW-398 (all
                USED_BY_EXECUTION, knowledge records VERIFIED)

APPS ADVANCED:
  dooz:    execution deepened through protobuf/Unsafe init + DataStore
           first-launch parse (two registered roots closed); visual gate
           honestly unchanged
  snake:   F-153 closed; restart + second-life re-verified post-fix
  gmdice:  §14 replay: 5/5 real clicks dispatched into GameMasterDice
           listeners; first-click diff 1,506,884 px; result band renders
           (initial → "2 · 4 · 4"; singles "6","5","3"). No deterministic-
           result claim (Random.nextInt REC-MISS recorded — F-114 family).
           Multi-roll across frames BLOCKED this wave: --tap hit-test
           target=0 (decor-offset bounds law = next probe).

STATE→RENDER PROOFS (§13): gmdice click→roll()→text→pixels (above); snake
  dialog→restart→movement→food (post-fix re-run); dooz chain advanced but
  visual gate not met (honest).

KNOWLEDGE LINKS (§22): 4 new VERIFIED records LAW-R-NEW-395..398 with
  SOURCE(origin+file) / TEST / CONSUMERS / USED_BY_EXECUTION; index counts
  31→35 records, 20→24 verified laws.

BLAST RADIUS (§23): R-NEW-395/396/397 — every protobuf/atomicfu Unsafe
  consumer (dooz today); regression covers the real consumer APK.
  R-NEW-398 — every draw_text caller corpus-wide; ASCII path byte-identical
  (fidelity 90/90 proof) + 26/26 pixel verifier.

DISK GUARD (§26): scripts/s78_disk_guard.sh [threshold] — STOP_BUILD +
  SAFE_CLEANUP_CANDIDATES below threshold; canonical evidence never
  deleted. Operational (84% < 85% at final gate).

RETENTION POLICY (§27): CANONICAL(never delete): docs/, docs/audit/,
  docs/evidence/, root_registry.json, worklog.md, git history.
  REGENERABLE: docs/audit/*.md derived views (via generator), run/ outputs.
  STALE SCRATCH: old probe logs, temp verifier outputs — deletion only
  with rule + log entry.

REPOSITORY HEALTH (§28): pack 89.47 MiB / 6065 objects; .git 592M (loose
  + quarantine branch). History NOT rewritten. Large-blob policy enforced
  going forward via the git-evidence rules; the 593 MB snapshot stays on
  the quarantine branch as the recorded rollback anchor.

REGRESSION:  26/26 battery · 26/26 verifier (f54 A7B_GATE_OK) ·
             BYTE-IDENTICAL 90/90 fidelity — re-run AFTER all changes.

OPEN:        F-143 (stopwatch launch), F-144 (GL family), F-145 (capture
             surface), F-147 (dooz secondary: pc=228 getChildAt null; its
             own REC-MISS may be the null producer — S79 lead)
PARTIAL:     gmdice multi-roll across frames (tap hit-test target=0)
BLOCKED:     — (publish debt resolved; nothing new blocked)
UNVERIFIED:  dooz Job ISE root cause (observed ×4 constant, not yet traced)

CRITICAL GAPS:
  1. dooz visual gate: engine-default face 23,472 nonwhite px unchanged —
     execution depth advanced, pixels did not (Job ISE + F-147 ahead)
  2. Random.nextInt REC-MISS — dice results' distribution unverifiable
  3. tap hit-test on decor-childed buttons returns target=0 (blocks
     scheduled multi-interaction replays corpus-wide)

NEXT PROBES:
  1. F-147: trace the null producer of the pc=228 ViewGroup receiver
     (getChildAt REC-MISS chain) — the next dooz depth link
  2. kotlinx Job ISE (Lsx;@849 vs Lwl;@1103) — JobSupport state-machine
     law (concurrency §20: evidence-driven only)
  3. gmdice multi-roll: decor-offset law for tap targets, then reroll
     A→B without click-test burst
  4. View.getChildAt REC-MISS → implement over the ViewShadow tree
```

Per-root completed chains (§32 format): see the F-152 / F-153 / F-154
blocks above — each carries SYMPTOM → PRODUCER → ROOT CAUSE → SOURCE → LAW
→ IMPLEMENTATION → TEST → EXECUTION → OBSERVATION → EVIDENCE.

Acceptance §30: DOOZ (F-152 fixed+tested+executed with honest visual
frontier) ✓ · SNAKE (F-153 root cause → law → implementation → test →
observed rendering) ✓ · GMDICE (state→render recorded; multi-roll
PARTIAL) ✓ · RUNTIME (new silent failures F-154 registered with lineage;
getChildAt/nextInt RECORDED in registry/next-probes) ✓ · KNOWLEDGE
(source-linked ×4) ✓ · APP MATRIX (dossiers updated) ✓ · FAILURE REGISTRY
(new failures carry PARENT_FAILURE lineage) ✓ · DISK (guard operational)
✓ · REGRESSION (26/26, 26/26, 90/90) ✓.
