# Runtime Spotlight Corpus — Coverage Matrix (Phase A, S61)

Canonical corpus registry: `docs/corpus/spotlight_manifest.json` (SHA-verified
manifest) + `docs/corpus/spotlight_results.json` (execution results).
Selection law: capability coverage, not randomness — every app carries
capability tags; the sweep records the honest L-level the runtime reaches.

## Phase A execution summary

| Metric | Value |
|--------|-------|
| F-Droid apps fetched (SHA-verified) | 53 |
| Apps executed in the S61 sweep | 52 |
| Pre-existing corpus apps (executed in earlier sessions, evidence retained) | 9 |
| **Total corpus (Phase A)** | **61** |
| L-level distribution (sweep) | L1=3, L2=39, L4=3, L5=7 |

L-level law: L0 container, L1 DEX/class loading, L2 lifecycle, L3 ViewTree,
L4 resources+geometry, L5 drawing/framebuffer, L6 input→state, L7 interactive.

## Executed corpus (S61 sweep, per-app evidence)

| Package | L | render nodes | non-white px | errors | capabilities (selection reason) |
|---------|---|--------------|--------------|--------|--------------------------------|
| de.schildbach.wallet | L5 | 7 | 5695 | 32 | crypto, networking, sqlite, service |
| org.billthefarmer.accordion | L5 | 52 | 935172 | 0 | custom-view, canvas, touch, audio |
| org.billthefarmer.diary | L5 | 5 | 2073600 | 0 | listview, sqlite, preferences, date-widgets, menu |
| org.billthefarmer.shorty | L5 | 13 | 44684 | 0 | intent, shortcut, textview |
| org.billthefarmer.siggen | L5 | 20 | 47809 | 0 | audio, custom-view, canvas, threading |
| org.billthefarmer.tuner | L5 | 7 | 1823360 | 0 | canvas, audio, custom-view, threading |
| org.pocketworkstation.pckeyboard | L5 | 12 | 208440 | 0 | ime, service, custom-view, preferences |
| com.ghostsq.commander | L4 | 1 | 0 | 6 | storage, listview, custom-view, multi-screen |
| com.jens.automation2 | L4 | 4 | 0 | 0 | service, sqlite, listview, preferences |
| net.gaast.giggity | L4 | 3 | 0 | 9 | networking, sqlite, listview, alarm |
| com.better.alarm | L2 | 0 | 0 | 32 | alarm, service, listview, preferences |
| com.fsck.k9 | L2 | 0 | 0 | 20 | networking, sqlite, service, listview, intent |
| com.manichord.mgit | L2 | 0 | 0 | 21 | networking, sqlite, listview, threading |
| com.mendhak.gpslogger | L2 | 0 | 0 | 32 | gps, service, storage, listview, preferences |
| com.nononsenseapps.notepad | L2 | 0 | 0 | 7 | sqlite, listview, fragment, dialog, sync |
| com.simplemobiletools.flashlight | L2 | 0 | 0 | 5 | camera, service, widget |
| com.vrem.wifianalyzer | L2 | 0 | 0 | 32 | wifi, canvas, graph, listview |
| de.blinkt.openvpn | L2 | 0 | 0 | 28 | service, networking, jni, preferences |
| de.grobox.liberario | L2 | 0 | 0 | 32 | networking, listview, fragment |
| de.kaffeemitkoffein.tinyweatherforecastgermany | L2 | 0 | 0 | 0 | networking, listview, canvas, widgets |
| de.mm20.launcher2.release | L2 | 0 | 0 | 0 | launcher, listview, recycler-view, preferences |
| de.ph1b.audiobook | L2 | 0 | 0 | 16 | audio, service, listview, storage |
| de.tobiasbielefeld.solitaire | L2 | 0 | 0 | 32 | game, touch, state-machine, animation, preferences |
| de.westnordost.streetcomplete | L2 | 0 | 0 | 32 | map, canvas, sqlite, dialog |
| es.wolfi.app.passman | L2 | 0 | 0 | 32 | networking, listview, preferences |
| fr.gouv.etalab.mastodon | L2 | 0 | 0 | 21 | networking, listview, imageview, recycler-view |
| hu.vmiklos.plees_tracker | L2 | 0 | 0 | 32 | sqlite, service, listview, chart |
| name.boyle.chris.sgtpuzzles | L2 | 0 | 0 | 0 | game, canvas, touch, multi-screen, state-machine |
| net.fabiszewski.ulogger | L2 | 0 | 0 | 32 | gps, networking, service, sqlite |
| net.sourceforge.opencamera | L2 | 0 | 0 | 32 | camera, canvas, custom-view, preferences |
| org.andstatus.app | L2 | 0 | 0 | 21 | networking, listview, service |
| org.dmfs.tasks | L2 | 0 | 0 | 32 | sqlite, sync, widget, listview |
| org.kde.kdeconnect_tp | L2 | 0 | 0 | 27 | networking, service, listview |
| org.ligi.passandroid | L2 | 0 | 0 | 32 | storage, json, listview, imageview |
| org.ligi.survivalmanual | L2 | 0 | 0 | 32 | webview, listview, scrolling, search |
| org.primftpd | L2 | 0 | 0 | 32 | service, networking, storage |
| org.quantumbadger.redreader | L2 | 0 | 0 | 14 | networking, listview, recycler-view, imageview, markdown |
| org.secuso.privacyfriendlyactivitytracker | L2 | 0 | 0 | 0 | sqlite, service, sensor, listview |
| org.secuso.privacyfriendlyludo | L2 | 0 | 0 | 0 | game, canvas, touch, state-machine, dialog |
| org.secuso.privacyfriendlymemory | L2 | 0 | 0 | 0 | game, memory-card, touch, animation |
| org.secuso.privacyfriendlyminesweeper | L2 | 0 | 0 | 0 | game, grid-layout, touch, state-machine, timer |
| org.secuso.privacyfriendlynotes | L2 | 0 | 0 | 0 | sqlite, edittext, listview, dialog, multi-screen |
| org.secuso.privacyfriendlypaindiary | L2 | 0 | 0 | 0 | sqlite, fragment, viewpager, dialog |
| org.secuso.privacyfriendlypin | L2 | 0 | 0 | 6 | dialog, state-machine |
| org.secuso.privacyfriendlysketching | L2 | 0 | 0 | 0 | — |
| org.secuso.privacyfriendlytodolist | L2 | 0 | 0 | 32 | sqlite, recycler-view, dialog, alarm |
| org.sufficientlysecure.keychain | L2 | 0 | 0 | 17 | crypto, listview, sqlite, intent |
| org.totschnig.myexpenses | L2 | 0 | 0 | 15 | sqlite, listview, dialog, export |
| org.zephyrsoft.trackworktime | L2 | 0 | 0 | 32 | sqlite, service, alarm, listview, preferences |
| com.dozingcatsoftware.bouncy | L1 | 0 | 0 | 0 | game, canvas, physics, touch, game-loop |
| org.secuso.privacyfriendly2048 | L1 | 0 | 0 | 0 | game, grid-layout, touch-swipe, state-machine, sqlite |
| org.secuso.privacyfriendlysolitaire | L1 | 0 | 0 | 0 | game, touch, state-machine, card-layout, dialog |

## Pre-existing corpus (earlier sessions; regression battery governs)

| App | Source | L reached (best) | Evidence |
|-----|--------|------------------|----------|
| io.github.yamin8000.dooz v23 | F-Droid / github.com/yamin8000/Dooz | L2+ (Compose creation chain closed S57-S60; draw chain wired S61) | docs/evidence/s60_r380/, s61_r381/ |
| io.github.yamin8000.dooz v18 | F-Droid | L2+ healthy frame loop | run/s60_v18_reg |
| org.billthefarmer.notes | F-Droid | L7 read chain (F-085) | docs/evidence/s56* |
| app.varlorg.unote | F-Droid | L6 input→navigation | docs/evidence/s56_unote |
| de.duenndns.gmdice | F-Droid | L7 dice render on click | docs/evidence/campaign014/gmdice |
| com.chessclock.android | F-Droid | L7 clock state switch (80,289 px) | docs/evidence/campaign3_chessclock* |
| dubrowgn.microtimer | F-Droid | L4-L5 (battery corpus) | miniandroid/tests/corpus/apks.json |
| omegacentauri.mobi.simplestopwatch | F-Droid | L4-L5 (battery corpus) | miniandroid/tests/corpus/apks.json |
| org.debian.eugen.headingcalculator | F-Droid | L4-L5 (battery corpus) | miniandroid/tests/corpus/apks.json |

## Simple Games Spotlight subset (executed)

| Game | L | Note |
|------|---|------|
| org.secuso.privacyfriendlyminesweeper | L2 | grid + timer; lifecycle dispatched |
| de.tobiasbielefeld.solitaire | L2 | full solitaire suite; lifecycle dispatched |
| name.boyle.chris.sgtpuzzles | L2 | puzzle collection (JNI native core); lifecycle dispatched |
| org.secuso.privacyfriendlyludo | L2 | board game with dialogs; lifecycle dispatched |
| org.secuso.privacyfriendlymemory | L2 | memory pairs; lifecycle dispatched |
| com.dozingcatsoftware.bouncy | L1 | libGDX/SurfaceView game — DEX loads; lifecycle wall is the corpus finding |
| org.secuso.privacyfriendlysolitaire | L1 | card state machine; lifecycle wall |
| org.secuso.privacyfriendly2048 | L1 | swipe/SQLite; lifecycle wall |

Games from the pre-existing corpus (deeper evidence: GM Dice L7, ChessClock
L7, TicTacToe golden 9/9 interaction+determinism) — see ACHIEVEMENTS.

## Honest capability-coverage findings

1. The billthefarmer classic-View family reaches L5 (real framebuffer
   content) in seconds — the runtime's measure/layout/draw path is
   production-grade for classic View trees.
2. Modern androidx/RecyclerView/Compose apps reach L2 (lifecycle) but not
   L3+: their view trees are built by DEX-driven runtime code whose
   volume (cold class inits + invoke tree) exceeds the sweep budget —
   the same law R-NEW-381 faces on dooz v23.
3. The L1 trio (Bouncy/libGDX, two Solitaire suites) stops before
   lifecycle completion — candidate frontier faces for future sessions,
   registered via the corpus results (not silently dropped).

## Phase B (100 apps)

Not attempted this session: the 53-app fetch + 52-app sweep consumed the
session's execution budget. The fetch pipeline is idempotent — extend the
candidate list and re-run `scripts/s61_spotlight_fetch.py` then
`scripts/s61_spotlight_run.py`.


## S62 games update (2026-09-19) — first L6 + the fragment blocker family

| App | S61 L | S62 change |
|---|---|---|
| com.dozingcatsoftware.bouncy | L1 | **L6 PROVEN** (run/s62_bouncy_l6, --click-count 6): 6/6 clicks dispatched into real DEX XML-onClick handlers on BouncyActivity (scoreViewClicked, doPreviousTable, doQuit, hideHighScore); 7 frames; render-state transition proven by frame SHA pair 4219c5116ea2 (frames 0-2) -> 52e4ddacc8ac (frames 3-6). Not claimed L7 (no multi-round game-loop interaction proof). Evidence: docs/evidence/s62_r381/ |
| org.secuso.privacyfriendlyminesweeper | L2 | BLOCKED at R-NEW-331: FragmentManager.ensureExecReady ISE "not been attached to a host" at SplashActivity.onCreate -> app-boundary unwind |
| org.secuso.privacyfriendlymemory | L2 | BLOCKED at R-NEW-331 (same face) |
| org.secuso.privacyfriendly2048 | L2 | BLOCKED at R-NEW-331 (same face) |

The fragment host attach law (R-NEW-331) is now the single generic gate for
4+ spotlight games AND the Telegram init face (csearch cross-evidence).
L-level discipline unchanged: 61 registered apps; L-levels restated only
from run artifacts.
