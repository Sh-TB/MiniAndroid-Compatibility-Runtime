# S82 COMPATIBILITY INDEX — per-title compatibility tracker

Generated: 2026-09-22T05:56:23Z · Registry: `title_registry.json` (canonical, §3 freeze)

## §33 Dashboard answers

| QUESTION | COUNT |
|---|---|
| Title records | 202 |
| Games really executed | 25 |
| Apps really executed | 14 |
| Mandatory executed (P9, TimeLimit) | 2/2 |
| Only loaded (no frames) | 161 |
| Rendered (non-blank pixels) | 2 |
| Interactive (input response) | 0 |
| State changed (pixel-diff proven) | 0 |
| Graphics nontrivial | 1 |
| Image present in APK but 0 image pixels | 40 |
| Crashed / onCreate failure | 35 |
| Visually correlated (L3+) | 0 |
| Human verified (L5) | 0 (never self-granted, §31) |
| Open issues | see GitHub query `label:compatibility is:open` |
| Titles sharing a root cause | F-NEW-156: 35 · F-NEW-157: 1 |
| References with provenance | 177 OK / 25 NA |

## §52 Counts

```text
EXECUTED 41 · BLOCKED 4 · NOT_TESTED 157
STATE-NONBLANK 39 · STATE-RENDERED 1 · STATE-GRAPHICALLY-NONTRIVIAL 1
TAP_DISPATCHED 2 · INPUT_RESPONSE_PX 0 · PIXEL_DIFF_PROVEN 0
VISUAL_FAIL_VS_REFERENCE 31 · PARTIAL_PALETTE 4
HUMAN_VERIFIED 0 (L5 requires human review — never self-granted)
```

## Per-title index

| ID | TITLE | TYPE | PACKAGE | VERSION | ISSUE | STATUS | GRAPHICS | INPUT | STATE | VISUAL | F-ID | LAST TESTED |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GAME-001 | com.qwde.ccm | game | `com.qwde.ccm` | first | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-002 | com.astroloop.game | game | `com.astroloop.game` | 1.3 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-003 | app.halma | game | `app.halma` | 15.0 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | PARTIAL_PALETTE | F-NEW-156 | 981e656e |
| GAME-004 | com.jeffliu.balancetheball | game | `com.jeffliu.balancetheball` | 1.1.0 | — | GRAPHICALLY-NONTRIVIAL | NONTRIVIAL | TAP_DISPATCHED | NONE | PARTIAL_PALETTE | — | 981e656e |
| GAME-005 | crypto.o0o0o0o0o.games.black | game | `crypto.o0o0o0o0o.games.blackjack` | 0.29.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | NONE | F-NEW-156 | 981e656e |
| GAME-006 | eu.veldsoft.no.thanks | game | `eu.veldsoft.no.thanks` | 1.00 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | NONE | F-NEW-156 | 981e656e |
| GAME-007 | com.simondalvai.ball2box | game | `com.simondalvai.ball2box` | 4.1.9 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-008 | si.palcka.tarok | game | `si.palcka.tarok` | 1.0.7 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | NONE | — | 981e656e |
| GAME-009 | cos.premy.mines | game | `cos.premy.mines` | 1.7.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-010 | com.sidhant.puzzle | game | `com.sidhant.puzzle` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-011 | com.ivylopez.authsrng | game | `com.ivylopez.authsrng` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-012 | io.github.hathibelagal.mykan | game | `io.github.hathibelagal.mykanji` | 1.6 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-013 | io.github.ebraminio.bouncy | game | `io.github.ebraminio.bouncy` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-014 | de.tobiasbielefeld.solitaire | game | `de.tobiasbielefeld.solitaire` | 3.13 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | NONE | F-NEW-156 | 981e656e |
| GAME-015 | eu.quelltext.memory | game | `eu.quelltext.memory` | 1.7 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | — | 981e656e |
| GAME-016 | com.sidhant.queens | game | `com.sidhant.queens` | 1.0.8 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | — | 981e656e |
| GAME-017 | page.codeberg.lanticy.guanda | game | `page.codeberg.lanticy.guandan` | 1.2.2 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-018 | xyz.deepdaikon.quinb | game | `xyz.deepdaikon.quinb` | 1.2.5 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | — | 981e656e |
| GAME-019 | com.vayunmathur.games.solita | game | `com.vayunmathur.games.solitaire` | v2.6.5 | — | NONBLANK | NONE | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-020 | bim.app | game | `bim.app` | 16 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-021 | de.schwarz.boardgamepal | game | `de.schwarz.boardgamepal` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-022 | com.dash1971.maia_chess | game | `com.dash1971.maia_chess` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — | 981e656e |
| GAME-023 | org.secuso.privacyfriendlyba | game | `org.secuso.privacyfriendlybattleship` | 2.0.0 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-024 | com.kingalex.kingpong | game | `com.kingalex.kingpong` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-025 | com.vovagorodok.blichess | game | `com.vovagorodok.blichess` | 8.0.0+ble2.5.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-026 | io.itch.pirate_solitaire | game | `io.itch.pirate_solitaire` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-027 | com.dozingcatsoftware.dodge | game | `com.dozingcatsoftware.dodge` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-028 | com.helddertierwelt.mentalma | game | `com.helddertierwelt.mentalmath` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-029 | com.sidhant.bubbleshooter | game | `com.sidhant.bubbleshooter` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-030 | net.tigr.navyfleetbattle | game | `net.tigr.navyfleetbattle` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-031 | com.hazelhope.dubster.hamtes | game | `com.hazelhope.dubster.hamtest` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-032 | ca.rmen.nounours | game | `ca.rmen.nounours` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-033 | com.nima.triviaapp | game | `com.nima.triviaapp` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-034 | ru.wohlsoft.thextech.fdroid | game | `ru.wohlsoft.thextech.fdroid` | 1.3.7.3 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-035 | com.willie.mancala | game | `com.willie.mancala` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-036 | org.lichess.mobileV2 | game | `org.lichess.mobileV2` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-037 | de.georgsieber.ballbreak | game | `de.georgsieber.ballbreak` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-038 | com.quietgrid.app | game | `com.quietgrid.app` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-039 | com.octbit.rutmath | game | `com.octbit.rutmath` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-040 | com.galaxyrio.sudokusolver | game | `com.galaxyrio.sudokusolver` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-041 | org.lufebe16.pysolfc | game | `org.lufebe16.pysolfc` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-042 | com.kaeruct.raumballer | game | `com.kaeruct.raumballer` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-043 | com.sanskritbasics.memory | game | `com.sanskritbasics.memory` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-044 | com.smorgasbork.hotdeath | game | `com.smorgasbork.hotdeath` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-045 | com.serwylo.retrowars | game | `com.serwylo.retrowars` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-046 | org.opensurge2d.surgeengine | game | `org.opensurge2d.surgeengine` | 6.1.3.0-fdroid | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-047 | com.eightsines.firestrike.op | game | `com.eightsines.firestrike.opensource` | 2.0 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-048 | com.clavierhaus.gnubg | game | `com.clavierhaus.gnubg` | 1.0.2 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-049 | com.sidhant.arrowescape | game | `com.sidhant.arrowescape` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — | 981e656e |
| GAME-050 | com.vovagorodok.blidraughts | game | `com.vovagorodok.blidraughts` | 2.3.0+ble2.5.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-051 | com.yepgoryo.EggReturnsHome | game | `com.yepgoryo.EggReturnsHome` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — | 981e656e |
| GAME-052 | com.rocket9labs.boxcars | game | `com.rocket9labs.boxcars` | 1.4.9 | — | RENDERED | TEXT_ONLY | TAP_DISPATCHED | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| GAME-053 | io.github.johnathan.mineswee | game | `io.github.johnathan.minesweeper` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-054 | org.piepmeyer.gauguin | game | `org.piepmeyer.gauguin` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-055 | jwtc.android.chess | game | `jwtc.android.chess` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-056 | org.pipoypipagames.cowsreven | game | `org.pipoypipagames.cowsrevenge` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-057 | org.bobstuff.bobball | game | `org.bobstuff.bobball` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-058 | com.vayunmathur.games.alchem | game | `com.vayunmathur.games.alchemist` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-059 | ru.hyst329.openfool | game | `ru.hyst329.openfool` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-060 | org.codeberg.scovillo.bubble | game | `org.codeberg.scovillo.bubble` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-061 | com.towerillusion.abdal | game | `com.towerillusion.abdal` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-062 | com.sidhant.blockblast | game | `com.sidhant.blockblast` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-063 | org.quentin_bettoum.libremem | game | `org.quentin_bettoum.librememorygame` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-064 | com.fairytrick.fairymahjong | game | `com.fairytrick.fairymahjong` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-065 | com.tacticmaster | game | `com.tacticmaster` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-066 | com.joeld.minesweeper | game | `com.joeld.minesweeper` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-067 | com.adilhanney.ricochlime | game | `com.adilhanney.ricochlime` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-068 | com.dozingcatsoftware.cardsw | game | `com.dozingcatsoftware.cardswithcats` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-069 | eu.veldsoft.scribe4 | game | `eu.veldsoft.scribe4` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-070 | me.lecaro.breakout | game | `me.lecaro.breakout` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-071 | cube.run | game | `cube.run` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-072 | fr.arnaudguyon.spacevertex | game | `fr.arnaudguyon.spacevertex` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-073 | de.saschahlusiak.freebloks | game | `de.saschahlusiak.freebloks` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-074 | org.secuso.privacyfriendlyme | game | `org.secuso.privacyfriendlymemory` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-075 | paper.loop | game | `paper.loop` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-076 | dev.serwin.AnarchRE | game | `dev.serwin.AnarchRE` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-077 | com.dozingcatsoftware.mouse_ | game | `com.dozingcatsoftware.mouse_pounce` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-078 | com.sidhant.shikaku | game | `com.sidhant.shikaku` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-079 | eve.game.tracker | game | `eve.game.tracker` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-080 | com.sanskritbasics | game | `com.sanskritbasics` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-081 | eu.veldsoft.vitosha.blackjac | game | `eu.veldsoft.vitosha.blackjack` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-082 | com.mostafa.brickblast | game | `com.mostafa.brickblast` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-083 | com.fr.laboussole.track | game | `com.fr.laboussole.track` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-084 | eu.mokrzycki.learndigits | game | `eu.mokrzycki.learndigits` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-085 | com.game.asteroids_revenge | game | `com.game.asteroids_revenge` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-086 | paper.loop2 | game | `paper.loop2` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-087 | org.pgnapps.pk2 | game | `org.pgnapps.pk2` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-088 | org.secuso.privacyfriendlyda | game | `org.secuso.privacyfriendlydame` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-089 | com.itsfrz.tictactoe | game | `com.itsfrz.tictactoe` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-090 | nodomain.playmaker | game | `nodomain.playmaker` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-091 | com.chenyifaer.fafarunner | game | `com.chenyifaer.fafarunner` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-092 | org.secuso.privacyfriendlyso | game | `org.secuso.privacyfriendlysolitaire` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-093 | com.movietrivia.filmfacts | game | `com.movietrivia.filmfacts` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-094 | com.attenomy.janken | game | `com.attenomy.janken` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-095 | com.sidhant.nonogram | game | `com.sidhant.nonogram` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-096 | garden.lina.oblique_strategi | game | `garden.lina.oblique_strategies` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-097 | com.dozingcatsoftware.bouncy | game | `com.dozingcatsoftware.bouncy` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-098 | com.sidhant.triplematch | game | `com.sidhant.triplematch` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-099 | net.sourceforge.solitaire_cg | game | `net.sourceforge.solitaire_cg` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| GAME-100 | eu.veldsoft.tuty.fruty.slot | game | `eu.veldsoft.tuty.fruty.slot` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-001 | com.hfut.schedule | app | `com.hfut.schedule` | 4.21.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | NONE | F-NEW-156 | 981e656e |
| APP-002 | foehnix.widget | app | `foehnix.widget` | 4.0 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | NONE | F-NEW-156 | 981e656e |
| APP-003 | de.seemoo.at_tracking_detect | app | `de.seemoo.at_tracking_detection` | 3.1.2 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-004 | org.nitri.opentopo | app | `org.nitri.opentopo` | 1.38 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-005 | com.newsblur | app | `com.newsblur` | 15.0.4 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-006 | de.taz.android.app.free | app | `de.taz.android.app.free` | 2.1.2 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-007 | com.bupkis.tirailleur | app | `com.bupkis.tirailleur` | 1.0.0 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | — | 981e656e |
| APP-008 | io.github.aoc_normal | app | `io.github.aoc_normal` | 1.0 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-009 | fr.shiningcat.binclockwidget | app | `fr.shiningcat.binclockwidget` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-010 | net.diffengine.romandigitalc | app | `net.diffengine.romandigitalclock` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-011 | eu.weblibre.gecko | app | `eu.weblibre.gecko` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-012 | com.jherkenhoff.qalculate | app | `com.jherkenhoff.qalculate` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-013 | site.leos.apps.lespas | app | `site.leos.apps.lespas` | 2.11.5 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-014 | me.river.nightbell | app | `me.river.nightbell` | 3.12.0 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-015 | com.madlonkay.orgro | app | `com.madlonkay.orgro` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-016 | org.forkgram.classic | app | `org.forkgram.classic` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-017 | com.kompact | app | `com.kompact` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-018 | com.ma.tehro | app | `com.ma.tehro` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-019 | net.bible.android.activity | app | `net.bible.android.activity` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-020 | net.osmand.plus | app | `net.osmand.plus` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-021 | com.tutpro.baresip.plus | app | `com.tutpro.baresip.plus` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-022 | it.fast4x.riplay | app | `it.fast4x.riplay` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-023 | org.stingle.photos | app | `org.stingle.photos` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-024 | com.forrestguice.suntimeswid | app | `com.forrestguice.suntimeswidget` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-025 | com.vayunmathur.clock | app | `com.vayunmathur.clock` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-026 | com.luc4n3x.levyra | app | `com.luc4n3x.levyra` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-027 | com.firebirdberlin.nightdrea | app | `com.firebirdberlin.nightdream.noGms` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-028 | com.vagujhelyigergely.calcul | app | `com.vagujhelyigergely.calculatorm3` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-029 | com.hegocre.nextcloudpasswor | app | `com.hegocre.nextcloudpasswords` | 1.2.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-030 | com.chmouel.liseur | app | `com.chmouel.liseur` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-031 | protectedwp.safespace | app | `protectedwp.safespace` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-032 | dev.gpxit.app | app | `dev.gpxit.app` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-033 | com.srkovnar.legacyphotofram | app | `com.srkovnar.legacyphotoframe` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-034 | com.nfcarchiver.nfc_archiver | app | `com.nfcarchiver.nfc_archiver` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-035 | org.ojrandom.paiesque | app | `org.ojrandom.paiesque` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-036 | com.greenart7c3.nostrsigner | app | `com.greenart7c3.nostrsigner` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-037 | com.divinelink.scenepeek | app | `com.divinelink.scenepeek` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-038 | app.fedilab.castlab | app | `app.fedilab.castlab` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-039 | de.schliweb.makeacopy | app | `de.schliweb.makeacopy` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-040 | fr.corenting.convertisseureu | app | `fr.corenting.convertisseureurofranc` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-041 | io.paperterm.app | app | `io.paperterm.app` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-042 | org.ucam.ssb22.pinyinfdroid | app | `org.ucam.ssb22.pinyinfdroid` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-043 | com.kolakek.pimiwidget | app | `com.kolakek.pimiwidget` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-044 | is.xyz.mpv | app | `is.xyz.mpv` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-045 | orinasa.njarasoa.maripanatok | app | `orinasa.njarasoa.maripanatokana` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-046 | tibarj.tranquilstopwatch | app | `tibarj.tranquilstopwatch` | 1.12.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-047 | com.davidtakac.bura | app | `com.davidtakac.bura` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-048 | m.co.rh.id.a_news_provider | app | `m.co.rh.id.a_news_provider` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-049 | de.quaddyservices.dynamicnig | app | `de.quaddyservices.dynamicnightlight` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-050 | com.ominous.quickweather | app | `com.ominous.quickweather` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-051 | cn.rbc.termuc | app | `cn.rbc.termuc` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-052 | com.kaii.photos | app | `com.kaii.photos` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-053 | com.co3 | app | `com.co3` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-054 | com.crome.forecastpoint | app | `com.crome.forecastpoint` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-055 | com.metromusic | app | `com.metromusic` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-056 | com.bbzone.isitprime | app | `com.bbzone.isitprime` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-057 | com.vsmartcard.acardemulator | app | `com.vsmartcard.acardemulator` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-058 | com.iris.gallery | app | `com.iris.gallery` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-059 | com.adeeteya.digital_calcula | app | `com.adeeteya.digital_calculator` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-060 | lab.rreedd.oriens | app | `lab.rreedd.oriens` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-061 | org.godotengine.editor.v4 | app | `org.godotengine.editor.v4` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-062 | foss.cnugteren.nlweer | app | `foss.cnugteren.nlweer` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-063 | com.axiel7.anihyou | app | `com.axiel7.anihyou` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-064 | joshuatee.wx | app | `joshuatee.wx` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-065 | net.aliasvault.app | app | `net.aliasvault.app` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-066 | uk.org.boddie.android.weathe | app | `uk.org.boddie.android.weatherforecast` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-067 | de.phasenrauscher.bicyweathe | app | `de.phasenrauscher.bicyweather` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-068 | com.fixupxer | app | `com.fixupxer` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-069 | com.github.vauvenal5.yaga | app | `com.github.vauvenal5.yaga` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-070 | fr.ign.geoportail | app | `fr.ign.geoportail` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-071 | com.kylecorry.trail_sense | app | `com.kylecorry.trail_sense` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-072 | de.kaffeemitkoffein.tinyweat | app | `de.kaffeemitkoffein.tinyweatherforecastgermany` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-073 | dudeofx.eval | app | `dudeofx.eval` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-074 | it.rignanese.leo.slimfaceboo | app | `it.rignanese.leo.slimfacebook` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-075 | org.fossify.gallery | app | `org.fossify.gallery` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-076 | deckers.thibault.aves.libre | app | `deckers.thibault.aves.libre` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-077 | io.github.lordofpolls.shellw | app | `io.github.lordofpolls.shellwave` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-078 | org.fossify.clock | app | `org.fossify.clock` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-079 | com.justdeax.composeStopwatc | app | `com.justdeax.composeStopwatch` | 1.9.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156 | 981e656e |
| APP-080 | yetzio.yetcalc | app | `yetzio.yetcalc` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-081 | trailence.org | app | `trailence.org` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-082 | com.barghest.mesh | app | `com.barghest.mesh` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-083 | dev.otaj.zelp | app | `dev.otaj.zelp` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-084 | takagi.ru.monica.fdroid | app | `takagi.ru.monica.fdroid` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-085 | org.fossify.math | app | `org.fossify.math` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-086 | com.vicolo.chrono | app | `com.vicolo.chrono` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-087 | com.freetime.geoweather | app | `com.freetime.geoweather` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-088 | com.foxdebug.acode | app | `com.foxdebug.acode` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-089 | me.timeto.app | app | `me.timeto.app` | 2026.09.19 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | PARTIAL_PALETTE | F-NEW-156 | 981e656e |
| APP-090 | org.sherpr.app | app | `org.sherpr.app` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-091 | org.y20k.transistor | app | `org.y20k.transistor` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-092 | org.asafonov.weather | app | `org.asafonov.weather` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-093 | com.agatamessina.webinspecto | app | `com.agatamessina.webinspector` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-094 | com.fpf.smartscan | app | `com.fpf.smartscan` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-095 | org.billthefarmer.buses | app | `org.billthefarmer.buses` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-096 | dev.cipher.notes | app | `dev.cipher.notes` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-097 | io.github.x0b.rcx | app | `io.github.x0b.rcx` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — | 981e656e |
| APP-098 | com.google.android.stardroid | app | `com.google.android.stardroid` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-099 | duress.ultimate | app | `duress.ultimate` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| APP-100 | com.artifex.mupdf.viewer.app | app | `com.artifex.mupdf.viewer.app` | ? | — | NOT-LOADED | NONE | NONE | NONE | NONE | — |  |
| MAND-001 | se.tube42.p9.android | mandatory | `se.tube42.p9.android` | 0.1.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | VISUAL_FAIL_PALETTE | F-NEW-156,F-NEW-157 | 981e656e |
| MAND-002 | io.timelimit.android.aosp.di | mandatory | `io.timelimit.android.aosp.direct` | 7.7.1 | — | NONBLANK | IMAGE_GAP | TAP_DISPATCHED_NO_RESPONSE | NONE | PARTIAL_PALETTE | F-NEW-156 | 981e656e |