# CONT-17 SUCCESS-PATH REPORT (SP-1..SP-12 compile) — 2026-10-08
Binary a8761a482a186eac, merged HEAD a6028be6. Zero engine changes this block.

## A. Success corpus (SP-1, SFC-1/2) — evidence/cont17/success_corpus.json
- 12 titles with full per-run signatures (verdict, app_draw_ops,
  app_owned_pixels, activity, renderer_family, 3-run reproducibility, APK SHA where available).
- 11 REAL_APP_CONTENT (11 x3 byte-identical at HEAD or
  recorded CONT-15 x3) + dooz as the honest DEFAULT_BACKGROUND_ONLY frontier row (F-NEW-265).
- Law enforced: a PNG existing is never success — verdict from F-NEW-233 frame truth only.

## B. Common successful chain (SP-2/3/12) — evidence/cont17/success_chain_microtimer.json
- 11-stage chain PASS on microtimer (fresh at HEAD): APK->manifest->Application->Activity->
  Window/Decor/content root->attachment->setContentView->ViewTree->measure/layout/draw->
  app-owned op->framebuffer->capture, no synthetic pixels (diag=0).
- White-family separation: REAL_APP_CONTENT vs DEFAULT_BACKGROUND_ONLY rows kept distinct;
  first_missing_stage names the family (APP_DRAW_OPS for dooz).

## C. Authority accounting (SP-4..8) — evidence/cont17/renderer_authority_audit.json
- Renderer selection = runtime semantics ONLY (S135 §14 sites :2925/:5221/:6195; no package
  names, no class-name guesses, no id heuristics; first claim wins, never downgrades).
- app_draw_ops increment sites audited (all app-owned guards); masquerade guard =
  frame_baseline_ pre-walk snapshot; app_content_proof() = auth_root_valid && draw_walk_ran
  && app_draw_ops>0. VERDICT: PASS.
- Legacy path classification: ApplicationRuntime/RenderPipeline = LEGACY/TEST-ONLY (megabatch
  target only); software_renderer primitives = AUTHORITATIVE backend; api::View = DEAD.
  Exactly ONE authoritative framebuffer owner.

## D. Window-canonical + traversal cross-checks (SP-6/7 family)
- view_tree_lifecycle_owner: LAW CONSISTENT (android_shadows.cpp:3095-3125; set on decor
  counterpart before content; key from app resources.arsc; R-NEW-379 ISE face historically
  reproduced; every Compose title passes onAttachedToWindow at HEAD).
- Traversal order: PARTIAL — one honest bounded divergence (requestLayout honored at stage
  granularity vs AOSP same-traversal second pass; no corpus face at HEAD).

## E. Source-op mapping + common minimum render contract (SP-9/10)
- evidence/cont17/source_op_mapping.json — 7 title families mapped source-op -> MiniAndroid
  law -> evidence pointer (upstream sources NOT fetched this wave; honest provenance noted).

## F. High-fan-out missing-law queue (SP-11 + SFC-9) — evidence/cont17/high_fanout_ranking.json
- Open rows: 208. Ranked queues: (1) F-NEW-264d six collection laws,
  (2) F-NEW-265 measure-death, (3) JNI family (F-NEW-219 + SharedLibraryLoader),
  (4) MessageQueue/Handler deep ordering edges.

## Visual gate hardening (SP-12/SFC closure) — evidence/cont17/visual_gate_matrix.json
- 8 rejection classes, each with source cite + live/recorded negative; live negatives at HEAD:
  dooz expected-and-observed DEFAULT_BACKGROUND_ONLY; gate A 98/0/1.
