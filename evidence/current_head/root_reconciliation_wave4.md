# ROOT RECONCILIATION — CONT-8 WAVE 4 (evidence/current_head/root_reconciliation_wave4.md)

HEAD at reconciliation: `50b63bc74a44fa1fc506f3e0f97f2142b8960c32` (origin/main `c1407326` + W3-re-proof evidence commits)
Binary: `c0fa65ccc7f284e7` (byte-identical rebuild lineage from W3 re-proof; no engine code changed this wave)
Method: every row below was re-verified against CURRENT HEAD by live run or probe (no trust in historical DONE).
Issue-comment access note: GitHub API rate-limited + comment threads lazy-loaded; issue BODIES for
#354/#371–#378 fetched (200 OK); the authoritative per-wave record = git commits + worklog (worklog.md),
which are the same content posted as dated issue comments each wave.

## Minimum reconciliation set

| ROOT | Original claim | Current HEAD status | Current evidence | Still active? | Regression? | Duplicate? | Historical only? | Action taken | Verification APK | 3-run |
|---|---|---|---|---|---|---|---|---|---|---|
| F-NEW-158 graphics provenance | placeholder pixels overpainted real frames | **NOT_IN_REGISTRY (superseded/renumbered)** — the live law set is C013/EXP092/ARSC provenance telemetry | current runs print U007/ARSC/EXP092 provenance lines; W4 fish provenance proves APK-entry→pixel identity | no (as a distinct root) | no | superseded by C013/EXP092 family | yes | none (registry name-space audit) | fishrings + g2048 | yes |
| F-NEW-160 field identity | bare-name heap fields collide across same-named fields | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** (FieldKeyResolver law; F-NEW-251 is its W7 deepening) | registry 564; no bare/qualified split-brain rows in W4 runs | no | no | no | no | none | dooz + probes | yes |
| F-NEW-162 C013 routing | inline placeholder contaminates frames | **PARTIAL (unchanged, honest)** — placeholder never paints over surface-family/text routes; §30 SUCCESS-downgrade for surface-only frames still owed | run/w4 logs show C013-CUSTOMVIEW "unrendered RECORDED (not painted)" (honest, non-painting) | partial | no | no | no | none this wave (scope: F-NEW-256 first) | w4_ladder_probe (placeholders absent from its frames) | n/a |
| F-NEW-175 TypedArray | diagnostic placeholders out of authoritative frame | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** | no placeholder frames in any W4 run | no | no | no | no | none | all W4 runs | yes |
| ROOT-062/063/064 | historical pre-F-NEW numbering | **NOT_IN_REGISTRY (renumbered into R-NEW/F-NEW space during earlier audits)** | registry census 564 contains no such ids | no | — | superseded | yes | none | — | — |
| F-NEW-228 weighted-row heights | opencalc button-row height law | **IMPLEMENTED+TESTED (unchanged)** | opencalc anchor e364b001 ×3 byte-identical this wave | no | no | no | no | none (anchor re-run) | opencalc | yes |
| F-NEW-251 field-slot identity (Unsafe/AFU) | split-brain heap field storage | **VERIFIED_CURRENT — NOT reopened** (§5 directive) | F252 probe CAS1/2/3+UPD 7/7 PASS live this wave | no | no | no | no | none | fnew252_probe | yes |
| F-NEW-252 NULL_REF semantics | Snapshot tracking IAE | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** | PNULL row PASS live; dooz 0 tracking-IAE | no | no | no | no | none | fnew252_probe + dooz | yes |
| F-NEW-253 Class.isInstance/Bundle | canBeSaved reflection over platform classes | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** | F253PROBE 21/21 + W3PROBE W3-01..05 live; dooz saveable IAE 0 | no | no | no | no | none | fnew253_probe | yes |
| F-NEW-254 platform exception chain | CancellationException not Throwable | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** | W3-06..W3-09 PASS live | no | no | no | no | none | cont7w3_probe | yes |
| F-NEW-255 listIterator | shadow stub answered NULL for object-returning method | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** | W3-10..W3-12 PASS live | no | no | no | no | none | cont7w3_probe | yes |
| F-NEW-256 Compose draw → 0 canvas ops | dispatchDraw runs, Canvas translate-only | **CLASSIFIED → REFINED THIS WAVE (divergence proven deeper; not yet fixed)** | W4 ladder refutes faces (b)/(c); W4 trace proves the 1-node tree + mid-composition apply (see evidence/cont8/fnew256_w4_trace.json) | **YES — the one active render root** | no | no | no | refined evidence + ladder probes; NO blind patch | dooz | yes (anchor) |
| F-NEW-257 Bundle parcel-family content | putParcelable dropped values | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** | B-01..B-08 PASS live | no | no | no | no | none | fnew253_probe | yes |
| F-NEW-258 STRING_REF instanceof | `x instanceof String` false for string registers | **ROOT-CAUSED-FIXED, VERIFIED_CURRENT** | B-07 PASS live | no | no | no | no | none | fnew253_probe | yes |
| Dispatchers.Main / ServiceLoader / FastServiceLoader | generic provider discovery; no R8-name hacks | **MECHANISM VERIFIED_CURRENT; MainDispatcherLoader selection UNREACHED (PENDING)** | SLPOS/SLNEG PASS live this wave; W2 live evidence: dooz R8-renamed provider e6→m6 discovered via real APK entries; no `Lv;.o` intercept exists | mechanism no; selection unreached | no | no | no | probe re-run only | fnew252_probe | yes |
| Looper/Handler/MessageQueue/Choreographer | frame scheduling chain | **VERIFIED_CURRENT on the View path** (anchors/goldens pump frames through post/invalidate/draw); R-NEW-340 pump = PARTIAL-FIX as recorded | anchors 5/5×3; goldens 4/4 | View path no; Compose path YES via F-NEW-256 | no | — | no | none | opencalc/dooz/goldens | yes |
| resource provenance | white/black/placeholder screens | **VERIFIED_CURRENT** | §14 fish provenance: APK-entry dominant colors == framebuffer pixels (evidence/cont8/w4_resource_provenance.json) | no | no | no | no | new proof this wave | fishrings | yes |
| filesystem/install/data-root semantics | install/uninstall/data trees | **VERIFIED_CURRENT** (skill selftest OP-3/OP-10 identity + NOT_INSTALLED honesty) | 13/13 selftest live | no | no | no | no | none | skill fixture | yes |
| browser/JS data path | WebView family | **unchanged scope** (not exercised by W4 targets; no regression signal) | — | n/a | no | no | — | none | — | — |
| AssetManager/Resources/BitmapFactory | decode + inflate | **VERIFIED_CURRENT** | fish inflate + provenance; hello_widgets golden | no | no | no | no | none | fishrings | yes |
| View measure/layout laws | containers measured 0x0 historically | **VERIFIED_CURRENT** (S109/R347 laws hold; all View-world games render) | goldens 4/4 REAL_APP_CONTENT | no | no | no | no | none | 2048/snakedeluxe/minicraft/tetris | yes |
| Canvas/rendering bridge | onDraw replay into software framebuffer | **VERIFIED_CURRENT and PROVEN COLOR-EXACT this wave** | W4 ladder: drawRect/drawCircle/drawPath framebuffer pixels == paint colors; drawText glyphs; drawBitmap recorded-but-no-pixels for in-memory bitmaps (OBSERVED, §16-disciplined) | View path no; OBSERVED bitmap sub-gap | no | no | no | ladder probe | w4_ladder_probe | yes |
| Compose state → invalidation → recomposition | tracking IAE family | **F-NEW-252 fixed; deeper machinery live but stops at 1 node (F-NEW-256)** | W4 trace | via F-NEW-256 | no | — | no | none | dooz | yes |
| Compose LayoutNode → measure/layout → draw | 0 draw ops frontier | **F-NEW-256 refined first divergence (above)** | W4 trace + ladder | **YES** | no | no | no | evidence refinement | dooz | yes |

## Apps reconciled this wave

| App | Status at CURRENT HEAD |
|---|---|
| gmdice | SUCCESS, full-frame app-owned pixels, ad35f81bd02328b2 ×3 |
| chess | anchor b5a7a35d byte-identical (pre-existing recorded frontier incl. 3 deterministic uncaught NPEs at Ln0/k1;.c — recorded as the app's known state, NOT a new root, NOT a regression) |
| 2048 / Snake Deluxe / MiniCraft / Tetris / Snake-Neon | SUCCESS / REAL_APP_CONTENT (goldens 4/4 + W4 runs) |
| Dooz | composition clean; 1-node tree (F-NEW-256 refined); anchor d602648e ×3 |
| FishRings | **SCHEDULING CLASSIFIED**: Timer.schedule(5000ms)→virtual-time→GameActivity→REAL game content a341e3ad9092f640 ×3 with time-driven capture |
| FairyMahjong | SUPERSEDED + ARTIFACT-LOST (F-NEW-243/244 fixed historically, 76e097244767d6c3 ×3 recorded; APK lost in reset; re-supply to re-verify) |
| BlockBlast | ARTIFACT-LOST (tmp/s107_apks wiped by reset; historical evidence only) |
