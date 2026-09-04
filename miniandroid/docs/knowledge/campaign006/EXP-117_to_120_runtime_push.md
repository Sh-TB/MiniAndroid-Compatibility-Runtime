# EXP-117/118/119/120 — Runtime push evidence (Campaign 004, T31-T43)

Date: 2026-08-28. Binary: build/miniandroid @ commit b3846f3 (parent 3a656f9 = UNIFIED_003 HEAD).
APK: Telegram 12.10.1 (sha256 f5e11927…) unless stated. Strict terminology.

## EXP-117 — ARSC auto-map (T31/T32, closes the SFS-010 root-cause chain)
- Tool shipped: `tools/arsc_automap.py` (androguard 4.1.4 ARSCParser + public-resources +
  DEX R$ field extraction). Generates `resource_values.json` in the EXP-063 loader format.
- Generated map v1: string=11,314 color=165 dimen=179 integer=18.
  Key strings verified present: StartMessaging="Start Messaging",
  SentSmsCode="We've sent an SMS with an activation code…", AppName="Telegram".
- v12 run (sms mode): EXIT=0, screenshot SHA 9aff89925dc2b4a3 (vs legacy baseline 06fb40da —
  EXPECTED behavior delta = the fix is visible).
- stderr: 106 × `[RES-INTERCEPT] LocaleController.getString(...) → "<real string>"`.
  EXP091-SETTEXT with real text on real views: view#2425 (IntroActivity$4) = "Start Messaging",
  "Your phone number", "Please confirm your country code…", "Country".
- PROOF IMAGE: evidence_004/arsc_run2_plain_enter_code.png — "Enter code" title + 5 SMS code
  input boxes + real error string rendered. FIRST TIME real Telegram UI text renders through
  the full real-DEX chain. Plain mode 2/2 deterministic at e43fd18ee6da78e0.

## EXP-117b — Uri bridge (T33)
- `Landroid/net/Uri;` REAL data class: parse (heap object per instance, RFC 3986 split),
  getScheme/getHost/getPath/getQuery/getFragment/getAuthority/getLastPathSegment/toString/
  getSchemeSpecificPart/getPort, decode/encode passthrough.
- Demand basis: EXP-105 Uri = 17/18 corpus APKs, 401 references (top missing API).
- v12 plain path: 0 calls observed (used later in app); availability PROVEN by bridge dispatch.
- Deferred honestly: Uri.Builder, Uri.EMPTY, opaque-URI edge cases, percent-decoding.

## EXP-117c — SystemClock bridge (T34)
- `Landroid/os/SystemClock;` REAL: elapsedRealtime()/uptimeMillis()/currentThreadTimeMillis()
  (steady_clock ms), elapsedRealtimeNanos(), sleep(ms) (capped 50 ms — single-threaded frame
  loop protection; documented deviation).
- v12 plain run: **7 × `SystemClock.elapsedRealtime() → 93271xx` IMPLEMENTED** (was ABSENT —
  F004/W-C3 audit "SystemClock ABSENT (0 handlers)" now closed).
- Demand basis: 13/18 APKs, 303 references.

## EXP-118 — Entry-point repair + TL_auth_signIn mock (T35/T36)
### T35 entry-point repair (3 changes, commit b3846f3)
1. Framework-namespace exclusion in BOTH the legacy heuristic and the first-class-with-methods
   fallback (stopwatch executed `Landroid/app/AppComponentFactory;.<clinit>` — an R8 throwing
   stub — because `Landroidx/activity/Cancellable;` matched the substring "activity" earlier).
2. Manifest Application-class entry: when no launcher activity exists, the engine receives the
   manifest `android:name` Application class; onCreate()V handled Application-style (ins=1).
3. `<init>()V` fallback when the Application class has no onCreate (stopwatch's StopwatchApp
   only has <init>/getLastStatusUpdate/notifyObservers — ARSC/androguard verified).
- stopwatch (tile-only app — apktool manifest decode PROVES 0 activities, 1 QS Tile service):
  now enters `StopwatchApp.<init>()V` (7 insns) instead of a framework throw-stub (3 insns).
  Grade stays honest: tile app cannot render launcher UI = PARTIAL/no-UI for the RIGHT reason.
- dicer: PARTIAL (HALT-LOOP ×2 @ 51.7 s) → **EXIT 0, 800,406 instructions** (HALT guard fires
  but execution continues past multidex ZipUtil checkNotNullParameter).
- kiss: FAILED → **353,770 instructions** (PreferenceInflater/OreoShortcuts HALT guards fire;
  later stops at IllegalStateException in KeyboardManager.performRestore, handler NOT_FOUND).

### T36 controlled sign-in mock
- sendRequest interceptor: TL_auth_signIn/TL_auth_signUp → `TL_auth_authorization`
  { flags=0, user=`TL_user` {id=1, first_name="Mini", last_name="Android",
  username="miniandroid_rt", phone="+15551234567"} } — shapes match real v12.10.1 bytecode
  (baksmali EXP-111: TLRPC$TL_auth_authorization.user : TLRPC$User; TLRPC$User field set).
- Run evidence: `[T36-SIGNIN] mocked TL_auth_authorization{user=TL_user#5173 …} resp_id=5172`
  then the REAL delegate lambda chain executes:
  `LoginActivitySmsView$$ExternalSyntheticLambda12.run(TLObject,TL_error)` →
  `LoginActivitySmsView.$r8$lambda$XLOVqDD_geoQZgX3OjM7N3Hjx0w` (real R8 synthetic, real DEX).
- Controlled boundary (mocked network) — no real Telegram servers contacted. PROVEN at that
  boundary: sign-in RESPONSE path now executes real app code (was "NOT REACHED" in EXP-103).

## EXP-119 — Corpus expansion (T41/T40/T44)
- +3 NEW F-Droid APKs (unverified-SSL python download, UA header): com.best.deskclock 2035
  (6.9 MB), de.markusfisch.android.binaryeye 177 (9.4 MB), org.secuso…activitytracker 100
  (9.9 MB). All 3 run EXIT=0 (deskclock 636 insns — deepest of the three). Corpus = 22 APKs.
  wassertimer/comics candidates dropped: F-Droid fetch timeouts (honest NOT ADDED).
- T44 SQLite (8/18 APKs, 252 refs): decision = documented gap, NOT implemented this campaign
  (large surface). Reference path: research/2b (deterministic fake-SQL is the Robolectric-style
  answer; real SQLite amalgamation is the Coder-2-style answer). Priority: after ARSC/Uri/SystemClock
  regression hardening.

## EXP-120 — RLottie decode gap (T43) — PARTIAL, root causes documented
Shipped (all committed):
1. `resource_values.json["raw"]` = 423 raw name → obfuscated path (sms_incoming_info →
   res/cs3.json ARSC-verified), drawable=1,976, mipmap=33.
2. `["raw_ids"]`/`["drawable_ids"]`/`["mipmap_ids"]` from the ARSC public table (423 ids) —
   registered into field_name_by_resid_ (insert-if-absent, DEX R keeps priority).
3. 0x7F package-byte repair at the decode site: observed setAnimation resids are truncated to
   20 bits (917654 = 0xE0036 ≡ 0x7F0E0036 = raw/contacts_sync_off, ARSC-verified); repair
   ORs 0x7F000000 on exact-match miss (AOSP app-package convention).
Remaining blockers (NOT hidden):
(a) R$ ordinal collision — resid 3 resolves to the R$string name wallet_buy_button_place_holder
    (last-writer-wins in field_name_by_resid_), so the single rendered-view decode attempt misses
    the raw map. Real Android disambiguates by annotated parameter type (@RawRes int).
(b) Most PENDING views (resids 917654/917529/917634/917597) belong to offscreen ViewPager
    fragments — never rendered → decode (render-time) never attempted (EXP-092 pre-load lesson).
- Verdict: infrastructure COMPLETE and loading PROVEN (EXP092-RES line: strings=11314
  colors=165 dimens=179 drawables=1947 integers=18); end-to-end decode = NOT YET OBSERVED.
  Next concrete step: @RawRes-aware ordinal disambiguation + render-sweep for offscreen views.

## Regression (T39)
- Post-T33..T36 plain v12 runs: 2/2 screenshot SHA e43fd18ee6da78e0 — identical to pre-change
  ARSC baseline. Zero behavior drift from the four bridges/fixes on the unchanged path.
