# CONT-155 TRAIN 8 — F-NEW-484 ROOT-CAUSED-FIXED: runtime setTheme rebind

Binary: d7d3d61a76129682. Logs: run/c155/t8_*.

## Root cause (machine-verified end-to-end)
1. The C-type trio's manifest declares the LAUNCHER activity theme =
   `@style/SplashScreenTheme` (0x7f1201e9) — the androidx core-splashscreen
   pattern (byte-exact axml attr decode: dtype=0x01 REFERENCE,
   data=0x7f1201e9). The engine's launch binding was CORRECT.
2. On a real device, `installSplashScreen()` calls
   `setTheme(postSplashScreenTheme)` at onCreate start — the AOSP
   Activity.setTheme law: every later obtainStyledAttributes resolves
   against the NEW theme. The app's postSplashScreenTheme = AppTheme
   (todolist setTheme fired resid=0x7f120012 = AppTheme.NoActionBar).
3. The engine's ActivityShadow.dispatch only LOGGED setTheme — the S124
   ResourceRuntime kept the LAUNCH theme (SplashScreenTheme, zero compat
   attrs) → AppCompatTheme_windowActionBar slot-117 hasValue=false →
   createSubDecor pc=404 ISE → APP-BOUNDARY unwind → WINDOW_ROOT.

## The fix (two dispatch paths, both env-gated diag MINIANDROID_F484_DIAG)
- `ActivityShadow::dispatch` (android_shadows.cpp): setTheme handler —
  ResourceRuntime::set_activity_theme(resid) + handled_void.
- The dalvik_engine bridge site (same law, receiver-first arg convention).

## Verification
- todolist: [F-NEW-484] setTheme rebind resid=0x7f120012 → the ISE GONE,
  content_view_id root=628 (real root), face 0% → **100% non-white**.
- ca.leradar.app: **100% non-white**. org.eu.exodus_privacy.exodusprivacy:
  **100% non-white**. **C-type trio 3/3 render.**
- WINDOW_ROOT cohort cumulative: **9/17 now render** (6 from F-NEW-482 +
  3 from F-NEW-484).
- Zero-drift wall: 2 anchors honestly RE-BASED (unote 90a67cc1→7481e9b4 —
  app calls setTheme(0x1030128) platform theme; opencalc d5f3c7b5→63020bc7 —
  app calls setTheme(0x7f12013d) app theme). Both = AOSP Activity.setTheme
  law now honored, REAL_APP_CONTENT advance (same category as the CONT-10
  opencalc a976d2f9 re-base). Wall 9/9 MATCH at the new anchors.
- Negatives 19/19 PASS (probe-store prep intact). Skill selftest 13/13.

## Residuals (honest)
- B-type Koin pair (goodtime/readrops): upstream DI registry completeness —
  unchanged by this fix (correctly so).
- D-type NPE/ArrayStore trio: per-app decodes pending.
- aat: onCreate resolution case pending (TRAIN 9 lever from TRAIN 4).
