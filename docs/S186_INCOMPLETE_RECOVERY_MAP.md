# S186 — Incomplete Recovery Map (Wave 1d, measured)

Inputs: S107 face census n=129; S186c stuck battery n=41 (engine: post-S186b (GATE-A box2d verified)); laws applied: {"S186b": "box2d GATE-A verified (bouncy byte-exact vs S183b pin)", "S186d": "File.toString law in Object.toString bridge + stringify helper", "S186e": "Object.equals law (erased receiver) + CHAR-typed delimiter fix in indexOf/lastIndexOf"}

## Population (measured)

| census tier | count |
|---|---|
| C_TEXT_ON_FLAT | 76 |
| FLAT_TWO_TONE_OR_BLANK | 43 |
| B_STRUCTURED | 10 |

| battery tier (41 stuck re-run) | count |
|---|---|
| FLAT_TWO_TONE_OR_BLANK | 34 |
| B_STRUCTURED | 5 |
| A_RICH | 2 |

## Ranked generic capabilities (PART 8 priority score)

| # | capability | affected | score /100 | status proof |
|---|---|---|---|---|
| 1 | AndroidX/framework class-init (lifecycle, savedstate, fragment, datastore, appcompat, OnBackPressedDispatcher, FragmentContainerView) | 54-title headroom (S185) + 6 F-ANDROIDX in battery | **73** | S186f: foehnix #126 + aoc #132 uncaught 10->0; S186e solitaire #43 13->0 |
| 2 | null-semantics class-init family (F-NPE 15 diverse: flutter embedding, capacitor, gomobile go/Seq, liballeg, kotlin Intrinsics) | 15 titles in battery | **59** | S186C_COMPLETION_MATRIX families |
| 3 | B6 image decode -> real Bitmap pixels (structured content flattening) | 10 B_STRUCTURED faces in s107 census (14 faces one fix away per S185) | **48** | S107_FACE_CENSUS tiers; S183 graphics depth |
| 4 | GLES/EGL/surface semantics for native game family | 10-title native/GL cluster (S185); A_RICH only 2/41 in battery | **50** | S186c battery tiers; halma #27 + p9 #225 A_RICH |
| 5 | audio end-to-end (B7 OpenSL ES -> OpenAL Soft bridge) | B7 cluster + every game with sound assets; zero real-APK audio proof today | **32** | audit: 2 decode paths linked, 0 proofs |
| 6 | TLS/conscrypt JNI (F-NATIVE) | 1 direct + all HTTPS titles | **35** | taz -> conscrypt UnsatisfiedLinkError (battery) |
| 7 | resource resolution (F-RES) | 1 (astroloop FontManager Resources$NotFound) | **27** | battery |

## Family details (first failing stage, exact frames)

### #1 AndroidX/framework class-init (lifecycle, savedstate, fragment, datastore, appcompat, OnBackPressedDispatcher, FragmentContainerView)

- com.vayunmathur.games.solitaire #43 (IllegalStateException @androidx/datastore/core/DataStoreImpl$$ExternalSyntheticLambda0.invoke)
- com.eightsines.firestrike.opensource #71 (NullPointerException @androidx/appcompat/app/c.attachBaseContext)
- com.clavierhaus.gnubg #72 (IllegalStateException @androidx/datastore/preferences/core/PreferenceDataStoreFactory$create$delegate$1.invoke)
- foehnix.widget #126 (NullPointerException @androidx/activity/OnBackPressedDispatcher.updateBackInvokedCallbackState)
- io.github.aoc_normal #132 (NullPointerException @androidx/activity/OnBackPressedDispatcher.updateBackInvokedCallbackState)
- tibarj.tranquilstopwatch #170 (NullPointerException @androidx/fragment/app/FragmentContainerView.<init>)

### #2 null-semantics class-init family (F-NPE 15 diverse: flutter embedding, capacitor, gomobile go/Seq, liballeg, kotlin Intrinsics)

- io.timelimit.android.aosp.direct #226 (NullPointerException @t9/h.<init>)
- page.codeberg.lanticy.guandan #41 (NullPointerException @page/codeberg/lanticy/guandan/net/NsdHelper.<init>)
- xyz.deepdaikon.quinb #42 (NullPointerException @io/flutter/embedding/engine/a.<init>)
- org.opensurge2d.surgeengine #70 (NullPointerException @org/liballeg/android/AllegroActivity.<init>)
- com.vovagorodok.blidraughts #74 (NullPointerException @com/getcapacitor/JSExport.getPluginJS)
- de.tobiasbielefeld.solitaire #38 (NullPointerException @android/support/design/widget/NavigationView.<init>)
- bim.app #44 (NullPointerException @v1/b.<init>)
- com.vovagorodok.blichess #49 (NullPointerException @com/getcapacitor/JSExport.getPluginJS)
- com.rocket9labs.boxcars #76 (NullPointerException @go/Seq$GoRefQueue.<init>)
- de.seemoo.at_tracking_detection #127 (NullPointerException @y30.b)
- com.hfut.schedule #125 (NullPointerException @com/hfut/schedule/logic/util/sys/datetime/DateTimeManager.<clinit>)
- com.newsblur #129 (NullPointerException @ga/f.get)
- site.leos.apps.lespas #137 (NullPointerException @kotlin/jvm/internal/Intrinsics.throwUninitializedPropertyAccessException)
- com.hegocre.nextcloudpasswords #153 (NullPointerException @sk3.c)
- me.timeto.app #213 (NullPointerException @f33.w)

### #6 TLS/conscrypt JNI (F-NATIVE)

- de.taz.android.app.free #130 (UnsatisfiedLinkError @org/conscrypt/Conscrypt.checkAvailability)

### #7 resource resolution (F-RES)

- com.astroloop.game #26 (unknown @)

## 0-uncaught but flat (silent recovery queue — Rule 5: flat is not success)


## Two-tone/blank faces in battery (34 titles)

- io.timelimit.android.aosp.direct
- com.qwde.ccm
- com.astroloop.game
- com.simondalvai.ball2box
- si.palcka.tarok
- com.sidhant.queens
- page.codeberg.lanticy.guandan
- xyz.deepdaikon.quinb
- com.vayunmathur.games.solitaire
- org.opensurge2d.surgeengine
- com.eightsines.firestrike.opensource
- com.vovagorodok.blidraughts
- com.clavierhaus.gnubg
- io.github.hathibelagal.mykanji
- de.tobiasbielefeld.solitaire
- org.secuso.privacyfriendlybattleship
- bim.app
- ru.wohlsoft.thextech.fdroid
- com.vovagorodok.blichess
- com.rocket9labs.boxcars
- foehnix.widget
- de.seemoo.at_tracking_detection
- com.hfut.schedule
- com.newsblur
- org.nitri.opentopo
- com.bupkis.tirailleur
- io.github.aoc_normal
- site.leos.apps.lespas
- de.taz.android.app.free
- com.hegocre.nextcloudpasswords
- tibarj.tranquilstopwatch
- me.river.nightbell
- com.justdeax.composeStopwatch
- me.timeto.app

## Directive PART 9 required corpus cross-check

Required-test titles map to evidence dirs: batch367_rerun (tictactoedeluxe, snake, snakeneon run dirs exist), S183b faces (emmanuelttt/bouncy/stacktower3d), S119 (snakeneon capture, snake_real_score2). Apps (Telegram/Nextcloud/Organic Maps/VLC) live in S107/S115 census rows.
