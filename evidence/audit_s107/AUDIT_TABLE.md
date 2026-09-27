# S107 closure-wave audit — all 128 closed tickets re-verified

Method: for every ticket closed in the S107 wave (closure comment "fresh S107 run
evidence at HEAD `1818a325`"), the committed screenshots were re-opened and measured:
resolution, unique colors, entropy, dominant-color fraction, non-background ratio,
content bounding box, edge density, SHA-256; then each image was visually inspected
(contact sheets `contact_sheet_1..4.png`) and checked against the closure comment.
Closure rule of the original wave = unique-colors count only -> violates the project
visual-verification rules; blank/near-blank images are FAIL, not PASS.

## Verdict totals

| verdict | count |
|---|---|
| NEAR_BLANK | 77 |
| BACKGROUND_ONLY | 29 |
| BLANK_SCREEN | 11 |
| VERIFIED_3RUN (kept CLOSED) | 4 |
| WRONG_SCREEN | 3 |
| OTHER | 2 |
| NO_MEANINGFUL_PIXELS | 1 |
| RESOURCE_NOT_RENDERED | 1 |
| **TOTAL** | **128** |

## Per-ticket ledger

| issue | package | audit verdict | reason code | colors | non-bg ratio | entropy | bbox |
|---|---|---|---|---|---|---|---|
| #141 | `com.kompact` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #142 | `com.ma.tehro` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #143 | `net.bible.android.activity` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #145 | `com.tutpro.baresip.plus` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #146 | `it.fast4x.riplay` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #147 | `org.stingle.photos` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #148 | `com.forrestguice.suntimeswidget` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #149 | `com.vayunmathur.clock` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #150 | `com.luc4n3x.levyra` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #151 | `com.firebirdberlin.nightdream.noGms` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #152 | `com.vagujhelyigergely.calculatorm3` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #153 | `com.hegocre.nextcloudpasswords` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #154 | `com.chmouel.liseur` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #155 | `protectedwp.safespace` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #159 | `org.ojrandom.paiesque` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #160 | `com.greenart7c3.nostrsigner` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00187 | 0.021 | [0, 0, 1079, 1919] |
| #161 | `com.divinelink.scenepeek` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #162 | `app.fedilab.castlab` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #163 | `de.schliweb.makeacopy` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #164 | `fr.corenting.convertisseureurofranc` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #165 | `io.paperterm.app` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #166 | `org.ucam.ssb22.pinyinfdroid` | PENDING_3RUN_CONTENT_BOTH | VERIFIED_3RUN (kept CLOSED) | 208 | 0.01503 | 0.146 | [0, 51, 963, 703] |
| #167 | `com.kolakek.pimiwidget` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #168 | `is.xyz.mpv` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00187 | 0.021 | [0, 0, 1079, 1919] |
| #169 | `orinasa.njarasoa.maripanatokana` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #170 | `tibarj.tranquilstopwatch` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #171 | `com.davidtakac.bura` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #177 | `com.co3` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #178 | `com.crome.forecastpoint` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #179 | `com.metromusic` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #180 | `com.bbzone.isitprime` | PENDING_3RUN_CONTENT_BOTH | OTHER | 208 | 0.02065 | 0.157 | [0, 63, 703, 254] |
| #181 | `com.vsmartcard.acardemulator` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #182 | `com.iris.gallery` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #183 | `com.adeeteya.digital_calculator` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #184 | `lab.rreedd.oriens` | PENDING_3RUN_CONTENT_BOTH | OTHER | 6 | 0.32433 | 0.998 | [0, 0, 1079, 1799] |
| #185 | `org.godotengine.editor.v4` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #186 | `foss.cnugteren.nlweer` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #187 | `com.axiel7.anihyou` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #189 | `net.aliasvault.app` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #190 | `uk.org.boddie.android.weatherforecast` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00187 | 0.021 | [0, 0, 1079, 1919] |
| #191 | `de.phasenrauscher.bicyweather` | REOPEN_NEAR_BLANK | NEAR_BLANK | 251 | 0.00226 | 0.029 | [0, 0, 152, 112] |
| #192 | `com.fixupxer` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #193 | `com.github.vauvenal5.yaga` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #194 | `fr.ign.geoportail` | REOPEN_BLANK_SOLID | BLANK_SCREEN | 2 | 0.0 | -0.0 | None |
| #195 | `com.kylecorry.trail_sense` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #196 | `de.kaffeemitkoffein.tinyweatherforecastgermany` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #197 | `dudeofx.eval` | PENDING_3RUN_CONTENT_BOTH | NO_MEANINGFUL_PIXELS | 3 | 0.05469 | 0.314 | [0, 1815, 1079, 1919] |
| #198 | `it.rignanese.leo.slimfacebook` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #199 | `org.fossify.gallery` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #200 | `deckers.thibault.aves.libre` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #201 | `io.github.lordofpolls.shellwave` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #202 | `org.fossify.clock` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #203 | `com.justdeax.composeStopwatch` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00187 | 0.021 | [0, 0, 1079, 1919] |
| #204 | `yetzio.yetcalc` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #205 | `trailence.org` | PENDING_3RUN_CONTENT_BOTH | WRONG_SCREEN | 208 | 0.01506 | 0.127 | [0, 908, 1079, 1029] |
| #206 | `com.barghest.mesh` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #207 | `dev.otaj.zelp` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #208 | `takagi.ru.monica.fdroid` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00187 | 0.021 | [0, 0, 1079, 1919] |
| #210 | `com.vicolo.chrono` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #211 | `com.freetime.geoweather` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00187 | 0.021 | [0, 0, 1079, 1919] |
| #212 | `com.foxdebug.acode` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #213 | `me.timeto.app` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #214 | `org.sherpr.app` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #215 | `org.y20k.transistor` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #216 | `org.asafonov.weather` | REOPEN_NEAR_BLANK | NEAR_BLANK | 192 | 0.00171 | 0.022 | [1, 95, 405, 122] |
| #217 | `com.agatamessina.webinspector` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #218 | `com.fpf.smartscan` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #219 | `org.billthefarmer.buses` | REOPEN_NEAR_BLANK | NEAR_BLANK | 50 | 0.00348 | 0.043 | [14, 1726, 1075, 1916] |
| #220 | `dev.cipher.notes` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #221 | `io.github.x0b.rcx` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #222 | `com.google.android.stardroid` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #223 | `duress.ultimate` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #224 | `com.artifex.mupdf.viewer.app` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #64 | `com.galaxyrio.sudokusolver` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #65 | `org.lufebe16.pysolfc` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #66 | `com.kaeruct.raumballer` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #67 | `com.sanskritbasics.memory` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #68 | `com.smorgasbork.hotdeath` | PENDING_3RUN_CONTENT_BOTH | VERIFIED_3RUN (kept CLOSED) | 634 | 0.10782 | 0.74 | [25, 156, 1059, 1259] |
| #69 | `com.serwylo.retrowars` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #70 | `org.opensurge2d.surgeengine` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #71 | `com.eightsines.firestrike.opensource` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #72 | `com.clavierhaus.gnubg` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #73 | `com.sidhant.arrowescape` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #74 | `com.vovagorodok.blidraughts` | PENDING_3RUN_CONTENT_BOTH | WRONG_SCREEN | 219 | 0.01507 | 0.129 | [0, 908, 1079, 1029] |
| #75 | `com.yepgoryo.EggReturnsHome` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #76 | `com.rocket9labs.boxcars` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00187 | 0.021 | [0, 0, 1079, 1919] |
| #77 | `io.github.johnathan.minesweeper` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #79 | `jwtc.android.chess` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #80 | `org.pipoypipagames.cowsrevenge` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #81 | `org.bobstuff.bobball` | PENDING_3RUN_CONTENT_BOTH | VERIFIED_3RUN (kept CLOSED) | 476 | 0.37189 | 1.067 | [42, 56, 1037, 1016] |
| #82 | `com.vayunmathur.games.alchemist` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #83 | `ru.hyst329.openfool` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #84 | `org.codeberg.scovillo.bubble` | PENDING_3RUN_CONTENT_BOTH | WRONG_SCREEN | 1234 | 0.47813 | 1.43 | [0, 501, 1079, 1418] |
| #85 | `com.towerillusion.abdal` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #86 | `com.sidhant.blockblast` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #87 | `org.quentin_bettoum.librememorygame` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #88 | `com.fairytrick.fairymahjong` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #89 | `com.tacticmaster` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #90 | `com.joeld.minesweeper` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #91 | `com.adilhanney.ricochlime` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #96 | `fr.arnaudguyon.spacevertex` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #97 | `de.saschahlusiak.freebloks` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #98 | `org.secuso.privacyfriendlymemory` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #99 | `paper.loop` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #100 | `dev.serwin.AnarchRE` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #101 | `com.dozingcatsoftware.mouse_pounce` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #102 | `com.sidhant.shikaku` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #103 | `eve.game.tracker` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #104 | `com.sanskritbasics` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #105 | `eu.veldsoft.vitosha.blackjack` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #106 | `com.mostafa.brickblast` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #107 | `com.fr.laboussole.track` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #108 | `eu.mokrzycki.learndigits` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
| #109 | `com.game.asteroids_revenge` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #111 | `org.pgnapps.pk2` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #112 | `org.secuso.privacyfriendlydame` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #113 | `com.itsfrz.tictactoe` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #114 | `nodomain.playmaker` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #115 | `com.chenyifaer.fafarunner` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #116 | `org.secuso.privacyfriendlysolitaire` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #117 | `com.movietrivia.filmfacts` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #118 | `com.attenomy.janken` | REOPEN_BACKGROUND_ONLY | BACKGROUND_ONLY | 3 | 0.00048 | 0.006 | [0, 0, 178, 104] |
| #119 | `com.sidhant.nonogram` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #120 | `garden.lina.oblique_strategies` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #121 | `com.dozingcatsoftware.bouncy` | PENDING_3RUN_CONTENT_BOTH | VERIFIED_3RUN (kept CLOSED) | 494 | 0.47245 | 1.431 | [0, 0, 1079, 1919] |
| #122 | `com.sidhant.triplematch` | REOPEN_NEAR_BLANK | NEAR_BLANK | 2 | 0.01132 | 0.089 | [0, 0, 488, 47] |
| #123 | `net.sourceforge.solitaire_cg` | PENDING_3RUN_CONTENT_BOTH | RESOURCE_NOT_RENDERED | 179 | 0.00792 | 0.084 | [27, 1136, 1079, 1909] |
| #124 | `eu.veldsoft.tuty.fruty.slot` | REOPEN_BLANK_MONOCHROME | BLANK_SCREEN | 1 | 0.0 | -0.0 | None |
