# S47 SESSION RECORD — R-NEW-363 ROOT-CAUSED+FIXED (F-056) · HOST-ATTACH CHAIN RESTORED (F-057/F-058) · ARTIFACT FORENSIC CLEANUP

Date: 2026-09-16 · Base: origin/main b82b43c5 (S45) restored + S46 graft · Binary: rebuilt from source each gate

## 0. State reconciliation (mission §0)
- Ground truth: GitHub origin/main = `b82b43c5` (S45 push). The S47 briefing's S46 commit
  ids (`bbee608c`/`9703db9a`) did not exist in this repo — S46 ran on a parallel working
  tree whose commits were lost to a container-reset lineage split, but its WORKING-STATE
  survived at /tmp/my-project. Recovery:
  - verified remote tree contains all S44 gpg_* evidence (a6c3042c ancestor of b82b43c5);
  - archived the parallel lineage-B (migration-era 12cf043f + 2 UUID commits) to
    `archive/local-lineage-b-12cf043f` (nothing reset away);
  - reset main to b82b43c5 and grafted the exact S46 deltas (5 source files incl. F-055b,
    registry 347→349 in canonical wrapper format, README, s46 evidence dirs, s46 run
    dirs, s46 scripts, 8 upstream Compose oracles) → commit `S46 restore`.
- Registry verified: only R-NEW-361 updated + R-NEW-362/363 added vs origin (no silent
  rewrite). Toolchain re-bootstrapped (aapt2 Google Maven, ecj 3.36.0 Maven Central,
  r8 8.3.37 r8-releases, android-34 Sable).

## 1. S46 restore verification
- §29 TicTacToe golden: ALL PASS (8 checks), deterministic replay 613cfccc0f27… intact.
- Engine rebuilt from grafted source; `--agent-play` present; unit tests 4/4.

## 2. R-NEW-363 — ROOT-CAUSED, FIXED (F-056), VERIFIED
- **Repro** (real APK 2048, org.secuso.privacyfriendly2048_100, sha 02c799d3…):
  forwardPass HALT-LOOP via `SafeIterableMap$IteratorWithAdditions;.next` re-entry
  (28,700+ cycle stubs, 55MB stderr).
- **DEX ground truth** (new raw-DIS tool scripts/s47_next_dispatch.py, all-dex walk +
  hand-decode): forwardPass pc=23 = `invoke-interface Iterator.next()Ljava/lang/Object;`
  (the ERASED call site); javac BRIDGE `[13168] next()Ljava/lang/Object;` (5 units)
  delegates `invoke-virtual meth@13169 next()Ljava/util/Map$Entry;`; real body (27
  units) is pure field-advance (mBeforeStart/mCurrent iputs) — zero recursion.
- **ROOT**: the M3-19-CYCLE active-invoke key was `class.method#receiver#args` — the
  method DESCRIPTOR was missing. Bridge and real overload share name+receiver → the
  bridge entered (key armed) and the REAL body's legal delegation was stubbed as
  "re-entry" (lifetime_calls=2,4,6…) → mCurrent never advanced → hasNext() stuck true
  → forwardPass spin. JVM/ART law: ArtMethod identity = (class, name, proto INCLUDING
  return type); bridge→real covariant dispatch is legal and terminating (JLS §15.12.4.5).
- **FIX (F-056, generic)**: `m3_active_key += method_descriptor` (one line, in the
  documented key-construction site). Genuine same-(class,name,proto,receiver,args)
  re-entry still stubbed; MAX_RECURSION_DEPTH remains the backstop.
- **VERIFY**: 0 M3-19-CYCLE in the full 2048 run; run completes without timeout.

## 3. R-NEW-364 — host-attach chain restored (F-057) — the fix that exposed R-NEW-365
- Post-F-056 the 2048 frontier moved to `FragmentManager.ensureExecReady` ISE
  "FragmentManager has not been attached to a host."
- Upstream law pinned (fragment 1.5.4 + activity 1.8.0 sources fetched): the host
  attach is a CONTEXT-AVAILABLE LISTENER registered by FragmentActivity.<init> (line
  140) and fired by ComponentActivity.onCreate pc=7 dispatchOnContextAvailable.
- Env-gated probe chain ([S47-VIRT]/[S47-TOP]/[S47-TRI], MINIANDROID_S47_TRACE) walked
  the chain hop-by-hop and pinned the break: an EXP-044-era **package-specific stub**
  (`ContextAwareHelper.dispatchOnContextAvailable` — "collection iteration not
  supported") returned false before any class lookup. The justification was obsolete:
  shadow iterators + R342 COWSET semantics + F-056 keys have long covered iteration.
- **FIX (F-057, generic)**: stub removed; the real DEX body executes. Probe chain then
  proved the full law: dispatch → Set.iterator → hasNext/next → lambda
  FragmentActivity$$ExternalSyntheticLambda3.onContextAvailable → attachHost →
  attachController (bc=369) all dispatch.

## 4. R-NEW-365 — check* identity law (F-058)
- attachController STILL ran with receiver a0type=8 (NULL_REF). Probe bisect (function-
  top markers + full arg dump) pinned: `FragmentController.createController` = `new
  FragmentController(checkNotNull(host,"host"))`; an EXP-058-era stub for
  `Preconditions.checkNotNull` ("overload loop") returned false → bridge → NULL,
  DESTROYING the checked reference: probe evidence `[S47-TRI]
  FragmentController;.<init> a1=NULL`. The "overload loop" the stub guarded against is
  precisely what F-056 descriptor-aware keys fixed.
- **FIX (F-058, generic)**: stub removed; upstream law (androidx.core 1.13.0 source):
  checkNotNull is identity-on-non-null. Post-fix probe: `a1=o129(HostCallbacks)`,
  `attachController recv=o131`, `ensureExecReady mHost=o129` — HOST ATTACHED.
- ISE count on the SplashActivity chain: 14 → 6 → 0.

## 5. New honest frontier (R-NEW-366, registered not hidden)
With the host attached, 2048 reaches fragment transactions + AppCompat decoration and
hits an independent exception layer (run/s47_2048_fix3_stderr.log):
(a) IAE "Window callback may not be null" (WindowCallbackWrapper.<init> pc=12);
(b) ISE "Restarter must be created only during owner's initialization stage"
    (SavedStateRegistryController.performAttach pc=43 — attach-timing law);
(c) ISE "You need to use a Theme.AppCompat theme" (AppCompatDelegateImpl.createSubDecor
    pc=404 — theme attribute resolution);
(d) ISE "LifecycleOwner ... already garbage collected" (LifecycleRegistry.sync pc=94).
Next attacks documented in the registry entry.

## 6. Dooz (R-NEW-362) re-verified at the new fixes
- dooz v23 at F-056/057/058: 0 M3-19-CYCLE, 0 AIOOBE, 0 HALT-LOOP (no regression);
  frontier unchanged: `Ljb1;.f pc=21` IAE "Can't put value with type null into saved
  state" → caught catch-all at `Lfb1;.a invoke_pc=77` → APP BOUNDARY at
  MainActivity.onCreate invoke_pc=317 (run/s47_dooz_fix_stderr.log). R-NEW-362 remains
  the exact next Dooz attack.

## 7. Artifact forensic cleanup (§9-16)
- MEASURED (scripts/s47_artifact_audit.py): working tree 2.0 GB (of which
  miniandroid/run 1.2 GB, build 341 MB untracked), .git 634 MB, root gpg_* 192 MB/25
  dirs; tracked total 1.19 GB vs actual source ~4.4 MB. 930 MB of tracked .txt raw
  traces; 25 tracked gpg_* trace JSONs at 8.6 MB each.
- CLASSIFIED per §11 and executed: compact evidence KEPT in git (report.md +
  screenshots of every gpg_* dir, goldens, manifests); bulk traces ARCHIVED to
  /home/z/my-project-archive/ with full SHA256 provenance in
  docs/evidence/ARCHIVE_MANIFEST.json (recoverable also from git history — tip-only
  removal). Registry-referenced evidence paths NEVER removed.
- .gitignore strengthened for build/, *.o, run/*.log, *.ppm, apk_cache, tools.
- Cleanup committed SEPARATELY from runtime fixes (§17).

## 8. Regression gate (§20)
- §29 TicTacToe golden ALL PASS (8 checks) post-F-056/057/058.
- Full battery at this HEAD: see worklog/README tables (90/92, only pre-existing
  EXT-01/EXT-02; GATE H PASS).

## 9. Honest verdict
- R-NEW-363 closed with a one-line generic law (descriptor-aware method identity) —
  the deepest fix class: the guard itself was the semantic violator.
- Two obsolete package-specific stubs (EXP-044 dispatch, EXP-058 checkNotNull) removed
  with upstream-law justification and full probe evidence; 2048 advanced from
  HALT-LOOP spin to the AppCompat/theme layer; dooz verified non-regressed.
- STOP COUNTING ROOTS → COUNT PLAYABLE GAMES: TicTacToe Classic remains the playable
  anchor (9/9 agent-play, GIF c98214d3…), 2048 is one independent-law layer from its
  UI, Dooz keeps R-NEW-362 as its saved-state frontier.
