# CONT-156 Train 1+2 — F-NEW-481 lever census + F-NEW-486 WindowMetrics family (aat fix)

Binary: rebuild #10 d7d3d61a76129682 (deterministic, byte-identical to CONT-155) → fix binary 2dc7f5b4ff8731d2.

## Train 1 — F-NEW-481 lever census (dooz v23)
- Holder web (tools: cont156_holder_xref.py, cont156_loz_probe.py):
  - `Lpz0;.N : Loz0;` = the ONLY typed holder; single write site `Lpz0;.<init> pc=64` (one-time bind at construction).
  - `Loz0;.g : Lpz0;` back-ref; `Lpz0;.r1 pc=126` creates FRESH Loz0; (the replay lambda body).
  - R8 generic-collapse: no dex code path holds Loz0; via interface types — found via declared-type scan.
- Live census (METHOD-IN, 5 frames): dispatchDraw=6, el0.i=6, pz0.<init>=41 (2 early + 39 late),
  pz0.r1=2 (only via Lxk0;.k0/Lug0;.k0), pz0.k1=0, em1.g/ff.g/sc0.g=0 (layer callbacks NEVER),
  Loz0;.7834/.834=0, gl0.c=0 (REAL content draw never fires), framework RenderNode path UNUSED
  (beginRecording=0, drawRenderNode=0), rh1.a=0 (sole static caller of record trigger La00;.k0 — dead).
- RETRACTION: frame-pump starvation hypothesis REFUTED — Choreographer healthy (Lh9;.doFrame fires
  per frame, cb=1182 re-post loop). runnables_fired=0 measures the FRAME-SEQ re-pump only.
- Sharpened law: record trigger chain (rh1.a → La00;.k0 → i1 → r1) dies upstream of k0; only the
  2 initial layer nodes record; 39 late pz0 scopes never record; M0 kind-4 walk over the frozen
  early chain always fails → h1 overlay → blank. This log was too large to commit raw; distilled
  census in t1_method_census_top.txt; full log regenerable via scripts/cont156_train1_traces.sh.

## Train 2 — F-NEW-486 ROOT-CAUSED-FIXED (aat crossed)
- Root (F-NEW-485, CONT-155 T9): getCurrentWindowMetrics (API 30) had no shadow → null → Kotlin
  checkNotNull NPE in AppLayout.updateMeasurementSDK30 → onCreate death before any view.
- Fix (dalvik_engine.cpp, after getDefaultDisplay): getCurrentWindowMetrics/getMaximumWindowMetrics →
  singleton WindowMetrics seeded mBounds=Rect(0,0,1080,1920) (device-profile law) + mWindowInsets=
  Insets(0,0,0,0); getBounds/getWindowInsets dispatch on the receiver, never null (AOSP law).
- VERIFY: aat ch.bailu.aat_45 — killer signature ABSENT, face 99.3% non-white (was WINDOW_ROOT blank).
  WINDOW_ROOT cohort: 9/17 → 10/17 render.
- Gates at 2dc7f5b4ff8731d2: wall 9/9 MATCH (incl. re-based unote 7481e9b4 / opencalc 63020bc7),
  negatives 19/19 (after gate-A probe prelude — standalone run without prelude reads MISSING rows:
  harness artifact, not regression), skill selftest 13/13. Registry 799→800, id-unique, main==mirror.
