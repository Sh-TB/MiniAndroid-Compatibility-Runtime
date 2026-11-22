# S27-W3 — THE CONTENT-VIEW ATTACHMENT LAW (#633/#634)

**Base: S27-W2 (`e41ba912`). Mission: the blocker NAMED at the end of S27-W2 —
flip's `setContentView(activity_main)` RAN and its root (obj 406) was recorded
and linked under the activity view (`[F023-PARENTLINK] content view=406 linked
under activity view=32`), but the render census tree never received it — every
frame walked `FitWindowsLinearLayout(854) → ContentFrameLayout(858)
children=0` and the verdict stayed `DEFAULT_BACKGROUND_ONLY`. The S27-W3 law:
the content-view attachment must materialize as the ContentFrameLayout child
in the census/render tree.**

## 1. Root cause — measured, three laws fighting over one node

Baseline reproduction on the pre-fix binary (rc=1, verdict
`DEFAULT_BACKGROUND_ONLY`, first_missing_stage=APP_DRAW_OPS):

1. **U007 res inflate** produces the app root (406, ConstraintLayout, views=5)
   parentless and records it for the first-traversal attach wave
   (`[P0-1-ORDER] setContentView(res) root=406 recorded`).
2. **S25-W1a bind-time adoption** adopts the orphan root into the bind-time
   content host (`[S25-W1-BIND-ADOPT] content root 406 adopted under host
   761`) — the root now hangs under the window.
3. **F-023 PARENTLINK (setContentView(View)) RE-PARENTS it away**:
   `[GP-LAYOUT-003] addView child=406 re-parented 761 -> 32` +
   `[F023-PARENTLINK] content view=406 linked under activity view=32` — the
   app root moves under the ACTIVITY-AS-VIEW node (the F-057 duality node).
4. The appcompat **subdecor assembly** (R005/F165) then builds the REAL window
   chain: decor 815 → subdecor 854 (FitWindowsLinearLayout) → id-swapped
   ContentFrameLayout 858 (android.R.id.content, the F-NEW-220 id-swap).
5. The **render census roots at the activity CONTENT ROOT** (the subdecor
   chain): 854 → 858 → **children=0**. The app root hangs on the duality
   branch (decor → activity node → 406) which the census NEVER walks. An
   ancestor walk to the DECOR would wrongly call the root "attached" — the
   duality chain reaches the decor while bypassing the census root.
6. The two existing adoption laws cannot repair it: S24-W1's wave-time
   adoption keeps its `parent_id==0` orphan gate (the root HAS a parent — the
   activity node), and S25-W1a's bind-time host loses the root to F-023's
   re-parent before the frame ever renders.

## 2. The law (3 pieces + 1 honesty fix, one site)

All in the F165 subdecor-assembly site (`dalvik_bridge_domain_app_runtime.cpp`)
— exactly where AOSP `AppCompatDelegateImpl.setContentView` inflates INTO
`mContentParent` — plus the identity record in `android_shadows.{h,cpp}`:

- **(A) U007 app-root identity** (`android_shadows.h/cpp`): the res-inflate
  root is recorded under its OWN identity (`ActivityShadow::u007_inflate_root_`)
  — `content_view_id_` is re-pointed at the subdecor root by F165, which
  silently erased the app root's identity and made every adoption gate miss.
- **(B) The mContentParent adoption**: when the id-swapped content parent
  exists inside the assembled subdecor, adopt the U007 app root into it —
  AOSP `contentParent.addView(appLayout)`. Preconditions, all honest: root
  recorded and not the subdecor itself; NOT already inside the SUBDECOR
  subtree (idempotent — composes with the wave-time S24-W1 orphan adoption,
  which keeps its gate); the receipt re-parents loudly (GP-LAYOUT-003 names
  the old duality parent). `add_child`'s own G11 cycle guard stays authoritative.
- **(C) The S83-CONTENT-CHILD stray unlink (#676 family)**: a
  0x01020002-stamped FrameLayout CHILD of the app root — the lazy content
  materialize inverted under receiver=app-root (measured in the baseline:
  `[S83-CONTENT] node=800100 linked under view=461`) — is detached first: the
  content parent belongs to the window, never to the app root.
- **(D) Honest receipt fix**: the F165 `installed` print now fires only when
  `add_child` really landed — the baseline printed a FALSE receipt after the
  G11 cycle guard rejected the edge (`view=854 NOT installed under content
  parent=858 (add_child rejected: cycle/identity law)` is now the honest line).

## 3. Measured (production binary, canonical flags)

- **flip ×3: rc=1 → rc=0 ×3**, `[S27-W3-ADOPT] U007 app root=406 adopted under
  id-swapped content parent=858` ×1/run, census `ContentFrameLayout children=1`
  → root 406 `children=4` WITH real geometry: ImageView 569 (the coin face)
  331x331 at (374,794), Button "Flip" at (424,1752), CarouselRecyclerview.
- **Face `b270ff04` (blank) → `b492ee85799fb2cb`, deterministic ×3 AND
  binary-independent** (dev -O0 and production -O2 produce the same face).
  The face REGION (794..1125 × 374..705) is still pixel-empty and the frame
  gains only 234 corner pixels — the rasterized bitmap exists
  (`[S27-W1] vector rasterized … bmp_oid=792`) and the image draw dispatches
  (`[P1-2-IMAGE] setImageDrawable view=569 → real pipeline`) but the pixels do
  not land: the census shows the app root measured **0x0** (children measured,
  the ConstraintLayout's own onMeasure override never sized itself) — the
  renderer clips the app subtree to the root's empty frame. **NEXT named
  blocker (S27-W4 candidate): the root measure law — the DEX
  ConstraintLayout.onMeasure override must size the root (same family as the
  recorded minos GameMetrics pre-layout dims frontier).** The frame-truth
  verdict stays `DEFAULT_BACKGROUND_ONLY` — the same frontier family as the
  canonical minos/chess/ttt walls; on the dev -O0 binary the census answers
  `REAL_APP_CONTENT ×3` (timing-sensitive census law — recorded honestly).
- **Regression wall (canonical flags: scripts/p0_gate.sh procedure +
  apk-run Makefile convention)**: np `31ddd4d5b8e6d18e` / dice
  `0de952bf75f89409` / guess `87fe26766fc48d06` / ttt `d55056a8928a26ff` /
  rnd `31ddd4d5b8e6d18e` / minos `b5a7a35d5fe0564b` / hw `acdd9f05dc9c7ece` /
  chess `d602648e8e401895` — **8/8 IDENTICAL canonical hashes**. First wall
  attempt with wrong flags (--max-seconds 12, no --frames cap) produced 3
  apparent mismatches that are pure frame-capture-index differences — the
  canonical capture protocol (`--frames 30/50`) is part of the hash contract.
- **pz attribution (bisect receipt)**: pz runs `35c4e53b14561b2f` ×3
  deterministic (vs the w2 wall's `6375a3a3813af176`) with a REAL divergence:
  331 events / 9.1s and an app-visible `NoSuchElementException` at
  `Board.placeTilesRandom pc=60` (Iterator.next past end, GamePlay.onCreate
  APP BOUNDARY unwind). **A binary built from CLEAN origin/main with the
  S27-W3 changes STASHED reproduces the SAME `35c4e53b`**
  (`PZ-CLEAN-ORIGIN rc=1 hash=35c4e53b14561b2f` — evidence/s27/w3_pz_bisect.log):
  the pz delta is a pre-existing rebuild/environment property of the
  origin/main tree, NOT a regression of this law. Named residual: the
  placeTilesRandom iterator family is the same Iterator-law surface S24-W2
  guarded (randomix golden) — pz's board RNG iteration is the next candidate
  probe.
- **Gates: law battery 53/53 PASS** (evidence/s27/w3_law_battery.log),
  **test-core rc=0**, **test-hostile rc=0**, **source-parity OK (88 core
  sources manifest-parity)**.
- **Hygiene law restored**: the root `.gitignore` re-gains the W23-D/W22-F
  sweep-prevention entries (`tools/dl/`, `tools/ccache-bin/`) — the
  snapshot-push lineage had clobbered them.

## 4. Evidence

`evidence/s27/` — w3_base_r1 (pre-fix baseline), w3_fix_r1/r2 (dev-binary law
probes), w3_flip_r1..r3 (production ×3), w3_np/dice/guess/ttt/pz/rnd/minos/hw/
chess (canonical-flag wall), w3_pz_d1..3 (pz determinism ×3), w3_pz_clean
(clean-origin bisect run), w3_flip_smoke (post-restore smoke), w3_wall.log,
w3_pz_bisect.log, w3_law_battery.log, w3_test_core.log, w3_test_hostile.log,
w3_parity.log, build logs w3_build_*.log, `s27w3_matrix.tsv` (17 rows).
Harness committed: `scripts/s27_w3_wall.sh`, `scripts/s27_w3_battery.sh`,
`scripts/s27_w3_matrix.py`, `scripts/s27_w3_pz_bisect.sh`.

## 5. Files

`src/framework/android_shadows.h` (u007_inflate_root_ field + accessors),
`src/framework/android_shadows.cpp` (the U007 record at the res-inflate law),
`src/dex/dalvik_bridge_domain_app_runtime.cpp` (the 3 law pieces + the honest
F165 receipt, at the R005/F165 subdecor assembly).

Labels: ATTACHMENT_LAW CLOSED (census reaches the app tree, rc=0 ×3, face
deterministic ×3 binary-independent); REGRESSION_WALL 8/8 canonical IDENTICAL;
PZ_DELTA ATTRIBUTED-NOT-MINE (clean-origin bisect receipt); S27-W4 CANDIDATE
NAMED (root measure law — root 0x0 starves the draw clip).
