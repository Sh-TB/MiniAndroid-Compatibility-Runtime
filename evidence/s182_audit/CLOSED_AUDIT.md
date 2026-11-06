# S182 — CLOSED-ISSUE FINE AUDIT (115 closures, 2026-11-06)

Question (user): the 115 closed cases — were they closed wrongly?
Method: every closure categorized; closures that claim app/game FULL
load are re-checked against TODAY's battery evidence (S180 reshoot
byte-exact pins + S181 + S182 20-title battery on main 5d7edcdb).

Counts: {"uncategorized": 18, "APP-EPIC/4APP (Coder-5 full-interactive program)": 7, "MG micro-goal (closed while PARTIAL)": 72, "MG micro-goal (other)": 4, "GAMES wave (full-load + autonomous play)": 7, "F-NEW fix": 3, "S102 fix wave": 3, "wave-log / census / recurring meta": 1}

## Verdict per category

1. **GAMES-1..8 (8 closures)** — KEEP: evidence stands TODAY. The six W8 games re-shot byte-exact on current main (tetris b818a6a7, snake_deluxe 5235683f, snakeneon 9c02d9d6, ttt db1d633d, minicraft e77a073f, gmdice 3891679d = all REAL/PIN_MATCH in S180 reshoot).

2. **APP-016..019 + 4APP EPIC (7 closures, 2026-11-03)** — **CLOSED PREMATURELY (the user's suspicion is CORRECT for this block)**: NewPipe/Joplin/Material Files/Element X have NO standing full-load evidence anywhere in the ledger; the same Compose generation is still blocked (tusky 31ddd4d5 NO_ROOT unchanged in today's reshoot; Family-1 Compose blockers re-confirmed in S181). These 4 apps have never appeared in any battery, so 'full-interactive' was closed on wave-internal claims, not user-visible proof.

3. **MG-xxx closed at (PARTIAL) (~N)** — closed while explicitly PARTIAL; component-level work, but by the user's own bar (app must load کامل کامل) these are NOT done; they should either be reopened or tracked under their parent APP issues until the parent reaches REAL_APP_CONTENT.

4. **S102 / F-NEW fix issues** — KEEP (law fixes; superseded by later wave issues that remain open).

5. **Wave-log/census/SHARED meta** — KEEP (bookkeeping).

## Full table

| # | closed | category | title |
|---|--------|----------|-------|
| #1 | 2026-09-12 | ? | EXP-064 — REAL LOGIN IMAGE PROVEN BY PIXELS (OCR-validated PhoneView rendered) |
| #2 | 2026-09-12 | ? | EXP-065 — Fix multi-DEX const-string bug (FIELD_PREFERRED_AUDIO_LANGUAGES leak resolved) |
| #3 | 2026-09-12 | ? | EXP-066 — Multi-DEX semantic audit + OutlineTextContainerView text capture (Phone number l |
| #4 | 2026-09-12 | ? | EXP-067 — Resource resolution + AXML parser + Drawable decoding (real WebP images in Login |
| #5 | 2026-09-12 | ? | EXP-068 — Generic View inheritance + Floating Next button (semantic superclass resolution) |
| #6 | 2026-09-12 | ? | EXP-069 — Generic text input + click dispatch: phone number injected + Next button clicked |
| #7 | 2026-09-12 | ? | EXP-071 — Telegram Login → SMS Code Page Transition (CHECKPOINT_M PROVEN) |
| #8 | 2026-09-12 | ? | MiniAndroid campaign evidence — verified achievements (REUSE-FIRST campaign, 2026-09-05) |
| #10 | 2026-09-21 | ? | [EXEC] HelloWorld — APK Execution & Visual Proof |
| #11 | 2026-09-21 | ? | [EXEC] TicTacToe — APK Execution & Gameplay Proof |
| #12 | 2026-09-21 | ? | [EXEC] ConnectFour — APK Execution & Gameplay Proof |
| #13 | 2026-09-21 | ? | [EXEC] AndroidGameSnake — Autonomous Gameplay Proof |
| #15 | 2026-09-21 | ? | [EXEC] Unote — Runtime/UI Completion |
| #17 | 2026-09-21 | ? | [EXEC] GMDice — APK Execution & Visual Proof |
| #18 | 2026-09-21 | ? | [EXEC] MicroTimer — APK Execution & Visual Proof |
| #68 | 2026-09-26 | ? | [GAME-044] com.smorgasbork.hotdeath — compatibility report |
| #81 | 2026-09-26 | ? | [GAME-057] org.bobstuff.bobball — compatibility report |
| #121 | 2026-09-26 | ? | [GAME-097] com.dozingcatsoftware.bouncy — compatibility report |
| #166 | 2026-09-26 | APP-EPIC/4APP (Coder-5 full-interactive program) | [APP-042] org.ucam.ssb22.pinyinfdroid — compatibility report |
| #234 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-051] Font fallback selection — text/font (PARTIAL) |
| #235 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-073] ellipsize — text/font (PARTIAL) |
| #236 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-080] Unicode combining marks — text/font (PARTIAL) |
| #237 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-081] RTL basic shaping — text/font (PARTIAL) |
| #238 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-082] Arabic joining — text/font (PARTIAL) |
| #239 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-083] emoji fallback — text/font (PARTIAL) |
| #240 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-084] surrogate pairs — text/font (PARTIAL) |
| #241 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-085] UTF-8/UTF-16 boundary — text/font (PARTIAL) |
| #242 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-115] requestLayout propagation — layout/geometry (PARTIAL) |
| #243 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-123] scroll offset — layout/geometry (PARTIAL) |
| #244 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-124] translationX — layout/geometry (PARTIAL) |
| #245 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-125] translationY — layout/geometry (PARTIAL) |
| #246 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-126] scaleX — layout/geometry (PARTIAL) |
| #247 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-127] scaleY — layout/geometry (PARTIAL) |
| #248 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-128] rotation — layout/geometry (PARTIAL) |
| #249 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-129] pivot — layout/geometry (PARTIAL) |
| #250 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-171] SharedPreferences default file — storage/state (PARTIAL) |
| #251 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-172] custom file — storage/state (PARTIAL) |
| #252 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-173] boolean persistence — storage/state (PARTIAL) |
| #253 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-174] int persistence — storage/state (PARTIAL) |
| #254 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-175] long persistence — storage/state (PARTIAL) |
| #255 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-176] float persistence — storage/state (PARTIAL) |
| #256 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-177] string persistence — storage/state (PARTIAL) |
| #257 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-178] editor apply — storage/state (PARTIAL) |
| #258 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-179] editor commit — storage/state (PARTIAL) |
| #259 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-180] remove — storage/state (PARTIAL) |
| #260 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-181] clear — storage/state (PARTIAL) |
| #261 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-182] contains — storage/state (PARTIAL) |
| #262 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-183] preference process persistence — storage/state (PARTIAL) |
| #263 | 2026-09-26 | MG micro-goal (other) | [MG-214] GIF disposal NONE — animation (OBSERVED) |
| #264 | 2026-09-26 | MG micro-goal (other) | [MG-215] GIF disposal BACKGROUND — animation (OBSERVED) |
| #265 | 2026-09-26 | MG micro-goal (other) | [MG-216] GIF disposal PREVIOUS — animation (OBSERVED) |
| #266 | 2026-09-26 | MG micro-goal (other) | [MG-248] HTTP GET — network (PENDING) |
| #267 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-047] adaptive icon foreground — resource/asset (PARTIAL) |
| #268 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-048] adaptive icon background — resource/asset (PARTIAL) |
| #269 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-052] Missing glyph detection — text/font (PARTIAL) |
| #270 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-053] tofu detection — text/font (PARTIAL) |
| #273 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-061] lineSpacing — text/font (PARTIAL) |
| #274 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-062] includeFontPadding — text/font (PARTIAL) |
| #275 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-067] font ascent — text/font (PARTIAL) |
| #276 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-068] font descent — text/font (PARTIAL) |
| #277 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-071] whitespace handling — text/font (PARTIAL) |
| #279 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-074] maxLines — text/font (PARTIAL) |
| #280 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-075] singleLine — text/font (PARTIAL) |
| #285 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-086] font file loading failure semantics — text/font (PARTIAL) |
| #286 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-087] Android resource font family — text/font (PARTIAL) |
| #287 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-088] downloadable-font failure fallback — text/font (PARTIAL) |
| #289 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-130] ViewGroup child ordering — layout/geometry (PARTIAL) |
| #291 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-002] Vector viewportWidth/viewportHeight — resource/asset (PARTIAL) |
| #292 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-003] Vector path fillType — resource/asset (PARTIAL) |
| #293 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-004] Vector path winding — resource/asset (PARTIAL) |
| #294 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-005] Vector path strokeWidth — resource/asset (PARTIAL) |
| #298 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-009] Vector group pivotX/pivotY — resource/asset (PARTIAL) |
| #299 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-010] Vector group rotation — resource/asset (PARTIAL) |
| #300 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-011] Vector group scale — resource/asset (PARTIAL) |
| #301 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-012] Vector group translation — resource/asset (PARTIAL) |
| #302 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-013] Vector nested group transforms — resource/asset (PARTIAL) |
| #303 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-014] Vector alpha inheritance — resource/asset (PARTIAL) |
| #305 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-016] Layer-list ordering — resource/asset (PARTIAL) |
| #306 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-017] Layer-list inset — resource/asset (PARTIAL) |
| #307 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-020] State-list selected state — resource/asset (PARTIAL) |
| #308 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-021] State-list disabled state — resource/asset (PARTIAL) |
| #309 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-022] State-list checked state — resource/asset (PARTIAL) |
| #310 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-023] State-list state fallback — resource/asset (PARTIAL) |
| #313 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-046] mipmap XML indirection — resource/asset (PARTIAL) |
| #314 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-204] scaling filter quality classes — graphics/render (PARTIAL) |
| #315 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-207] canvas translation — graphics/render (PARTIAL) |
| #316 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-208] canvas scale — graphics/render (PARTIAL) |
| #317 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-209] canvas rotation — graphics/render (PARTIAL) |
| #318 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-210] nested transforms — graphics/render (PARTIAL) |
| #319 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-146] event cancellation — input (PARTIAL) |
| #321 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-149] touch outside bounds — input (PARTIAL) |
| #323 | 2026-09-25 | MG micro-goal (closed while PARTIAL) | [MG-223] ValueAnimator basic timing — animation (PARTIAL) |
| #331 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-231] SoundPool initialization — audio (PARTIAL) |
| #332 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-232] MediaPlayer initialization — audio (PARTIAL) |
| #333 | 2026-09-26 | MG micro-goal (closed while PARTIAL) | [MG-233] resource audio loading — audio (PARTIAL) |
| #334 | 2026-09-25 | GAMES wave (full-load + autonomous play) | [GAMES-1] Full-load 5-10 games end-to-end (launch + render + interaction evidence) |
| #335 | 2026-09-25 | GAMES wave (full-load + autonomous play) | [GAMES-2] Autonomous Snake Deluxe play (self-play, no game-memory cheating) |
| #336 | 2026-09-25 | GAMES wave (full-load + autonomous play) | [GAMES-3] House-building autonomous play (Minicraft) |
| #337 | 2026-09-25 | GAMES wave (full-load + autonomous play) | [GAMES-4] NEW snake variant — build, load, autonomous play |
| #338 | 2026-09-25 | GAMES wave (full-load + autonomous play) | [GAMES-5] Autonomous 2048 play |
| #340 | 2026-09-25 | GAMES wave (full-load + autonomous play) | [GAMES-7] Autonomous TicTacToe Deluxe play |
| #341 | 2026-09-25 | GAMES wave (full-load + autonomous play) | [GAMES-8] Wave evidence package + gh-pages gameplay GIFs |
| #342 | 2026-09-25 | F-NEW fix | [F-NEW-165] androidx AppCompatDelegateImpl.createSubDecor theme-gate frontier — theme attr |
| #345 | 2026-09-25 | F-NEW fix | [F-NEW-168] crash-on-launch family — rc=1 NPE chains (raumballer/tictactoe-classic) + dooz |
| #347 | 2026-09-26 | F-NEW fix | [F-NEW-169] dooz compose-navigation NPE chain — 3 roots after rc=-11 fix |
| #349 | 2026-09-26 | S102 fix wave | [S102-A] solitaire: R8-merged SavedStateRegistryController — getSavedStateProvider invoked |
| #350 | 2026-09-26 | S102 fix wave | [S102-B] compose frontier: 'CompositionLocal LocalDensity not present' — WindowRecomposer  |
| #352 | 2026-09-26 | S102 fix wave | [S102-D] coroutines: CoroutineScheduler$Worker.tryPark interpreter spin (LockSupport.park  |
| #421 | 2026-11-03 | APP-EPIC/4APP (Coder-5 full-interactive program) | [APP-016][Coder-5] Material Files (me.zhanghai.android.files) — full-interactive ladder MF |
| #422 | 2026-11-03 | APP-EPIC/4APP (Coder-5 full-interactive program) | [APP-017][Coder-5] NewPipe (org.schabi.newpipe) — full-interactive ladder NP-M0..M8 |
| #423 | 2026-11-03 | APP-EPIC/4APP (Coder-5 full-interactive program) | [APP-018][Coder-5] Joplin (net.cozic.joplin) — full-interactive ladder JP-G0..M8 |
| #424 | 2026-11-03 | APP-EPIC/4APP (Coder-5 full-interactive program) | [APP-019][Coder-5] Element X (io.element.android.x) — full-interactive ladder EX-M0..M9 |
| #425 | 2026-11-03 | APP-EPIC/4APP (Coder-5 full-interactive program) | [4APP-SHARED][Coder-5] Shared-layer campaign S1–S7 — fix once, benefit all four titles |
| #426 | 2026-11-03 | wave-log / census / recurring meta | [CONT-4APP RECURRING][Coder-5] Wave log — census → roots → fixes → battery → evidence |
| #427 | 2026-11-03 | APP-EPIC/4APP (Coder-5 full-interactive program) | [4APP-EPIC][Coder-5] Four-title full-compatibility program: Material Files · NewPipe · Jop |