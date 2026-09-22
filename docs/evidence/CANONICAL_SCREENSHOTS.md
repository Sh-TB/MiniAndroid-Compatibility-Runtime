# Canonical Screenshot Index (machine-checkable)

S84/S85 law: **ONE title → ONE canonical screenshot** (interactive titles →
ONE gameplay GIF). Generated from `registry.json` — the single source of
truth. Validate with `python3 tools/verify_canonical_evidence.py`.

- Rows with a screenshot: canonical artifact on disk, SHA256-pinned in
  [canonical/SHA256SUMS](canonical/SHA256SUMS).
- Rows with "—": honest text-only records (the near-blank engine-default
  shell class is never shipped as visual evidence — S54 gate law, S85
  hardening). Evidence lives in the session logs referenced from
  [docs/ACHIEVEMENTS.md](../ACHIEVEMENTS.md).

| Title | Type | Package | Source | APK SHA256 (16) | Screenshot | Screenshot SHA256 (16) | Level | State Change | Issue/Root cause |
|---|---|---|---|---|---|---|---|---|---|
| uNote | app | `app.varlorg.unote` | F-Droid | be91103f0e7db443 | [app.varlorg.unote.jpg](canonical/app.varlorg.unote.jpg) | 0926d80c165221c8 | L2 | — | S83 |
| at.techbee.jtx | app | `at.techbee.jtx` | [F-Droid](https://f-droid.org/en/packages/at.techbee.jtx/) | 92fbd67fd935b52b | — (text record, S54 gate) | — | L1 | — | — |
| com.aurora.store | app | `com.aurora.store` | [F-Droid](https://f-droid.org/en/packages/com.aurora.store/) | fd9c75d90d0f4a7c | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| com.beemdevelopment.aegis | app | `com.beemdevelopment.aegis` | [F-Droid](https://f-droid.org/en/packages/com.beemdevelopment.aegis/) | 0eecec45de0da3ff | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| DeskClock | app | `com.best.deskclock` | F-Droid | — | — (text record, S54 gate) | — | L2 | — | S83 |
| Bnyro Clock | app | `com.bnyro.clock` | F-Droid | — | — (text record, S54 gate) | — | L2 | — | S83 |
| PMK-61 Calculator | app | `com.cax.pmk` | [src](https://github.com/xvadim/pmk-android) | — | [com.cax.pmk.jpg](canonical/com.cax.pmk.jpg) | 245ae472e4b390d1 | L6 | — | see session report (S62-S65 spotligh |
| Chess Clock | app | `com.chessclock.android` | F-Droid | 5ca6f2c54c05efe7 | [com.chessclock.android.jpg](canonical/com.chessclock.android.jpg) | c3209486dd0ab332 | L0 | — | S83 |
| com.drdisagree.colorblendr | app | `com.drdisagree.colorblendr` | [F-Droid](https://f-droid.org/en/packages/com.drdisagree.colorblendr/) | a30ea8f14ea9d634 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| com.forrestguice.suntimeswidget | app | `com.forrestguice.suntimeswidget` | [F-Droid](https://f-droid.org/en/packages/com.forrestguice.suntimeswidget/) | bd0fbe51f684895d | — (text record, S54 gate) | — | L2 | — | — |
| com.fsck.k9 | app | `com.fsck.k9` | [F-Droid](https://f-droid.org/en/packages/com.fsck.k9/) | 92cd3a81c7a8d066 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| com.gh4a | app | `com.gh4a` | [F-Droid](https://f-droid.org/en/packages/com.gh4a/) | 66711fd47c0c0e65 | [com.gh4a.jpg](canonical/com.gh4a.jpg) | 29a8df4536d8222e | L2 | — | F-NEW-162 |
| com.hegocre.nextcloudpasswords | app | `com.hegocre.nextcloudpasswords` | [F-Droid](https://f-droid.org/en/packages/com.hegocre.nextcloudpasswords/) | b8ee43950d3fd847 | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| com.hfut.schedule | app | `com.hfut.schedule` | [F-Droid](https://f-droid.org/en/packages/com.hfut.schedule/) | bc2b586a58bd6eba | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| com.jherkenhoff.qalculate | app | `com.jherkenhoff.qalculate` | [F-Droid](https://f-droid.org/en/packages/com.jherkenhoff.qalculate/) | 31366f4dd3e750e5 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| com.justdeax.composeStopwatch | app | `com.justdeax.composeStopwatch` | [F-Droid](https://f-droid.org/en/packages/com.justdeax.composeStopwatch/) | dbf937ebbe7c0b3d | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| com.kompact | app | `com.kompact` | [F-Droid](https://f-droid.org/en/packages/com.kompact/) | 9aacd0015ccd9aad | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| com.kunzisoft.keepass.libre | app | `com.kunzisoft.keepass.libre` | [F-Droid](https://f-droid.org/en/packages/com.kunzisoft.keepass.libre/) | 862f87a30baef061 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| com.ma.tehro | app | `com.ma.tehro` | [F-Droid](https://f-droid.org/en/packages/com.ma.tehro/) | f5dbd2a88dfe9e64 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| com.maltaisn.notes.sync | app | `com.maltaisn.notes.sync` | [F-Droid](https://f-droid.org/en/packages/com.maltaisn.notes.sync/) | 176deff1189734d0 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| NewsBlur | app | `com.newsblur` | F-Droid | — | — (text record, S54 gate) | — | L2 | — | S83 |
| com.nononsenseapps.notepad | app | `com.nononsenseapps.notepad` | [F-Droid](https://f-droid.org/en/packages/com.nononsenseapps.notepad/) | ed44d7aff78498a5 | — (text record, S54 gate) | — | L0 | — | F-NEW-162 |
| com.sebiai.glyphport | app | `com.sebiai.glyphport` | [F-Droid](https://f-droid.org/en/packages/com.sebiai.glyphport/) | c95f8ca470b565fc | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| com.trianguloy.urlchecker | app | `com.trianguloy.urlchecker` | [F-Droid](https://f-droid.org/en/packages/com.trianguloy.urlchecker/) | ddcbf344519bff30 | [com.trianguloy.urlchecker.gif](canonical/com.trianguloy.urlchecker.gif) | ba1ae97c8e92dcf6 | L2 | YES | F-NEW-161 |
| com.vagujhelyigergely.calculatorm3 | app | `com.vagujhelyigergely.calculatorm3` | [F-Droid](https://f-droid.org/en/packages/com.vagujhelyigergely.calculatorm3/) | b224f071f7d34f76 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| com.vayunmathur.clock | app | `com.vayunmathur.clock` | [F-Droid](https://f-droid.org/en/packages/com.vayunmathur.clock/) | 143f8f7437486434 | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| de.danoeh.antennapod | app | `de.danoeh.antennapod` | [F-Droid](https://f-droid.org/en/packages/de.danoeh.antennapod/) | 3f43a4337a693cdb | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| GameMasterDice | app | `de.duenndns.gmdice` | F-Droid | 1621eda11b5dbc0c | [de.duenndns.gmdice.jpg](canonical/de.duenndns.gmdice.jpg) | 1f38135926fa07e4 | L2 | — | S83 |
| de.markusfisch.android.binaryeye | app | `de.markusfisch.android.binaryeye` | [F-Droid](https://f-droid.org/en/packages/de.markusfisch.android.binaryeye/) | 428c26249c706bd7 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| de.schildbach.wallet | app | `de.schildbach.wallet` | [F-Droid](https://f-droid.org/en/packages/de.schildbach.wallet/) | bc6d078854a74281 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| de.seemoo.at_tracking_detection | app | `de.seemoo.at_tracking_detection` | [F-Droid](https://f-droid.org/en/packages/de.seemoo.at_tracking_detection/) | 583fc839caff840e | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| de.taz.android.app.free | app | `de.taz.android.app.free` | [F-Droid](https://f-droid.org/en/packages/de.taz.android.app.free/) | 86f14e1101e7f989 | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| dev.lexip.hecate | app | `dev.lexip.hecate` | [F-Droid](https://f-droid.org/en/packages/dev.lexip.hecate/) | 7e98bf1cf2a9e4a4 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| MicroTimer | app | `dubrowgn.microtimer` | F-Droid | 79c6f730f64886e7 | [dubrowgn.microtimer.jpg](canonical/dubrowgn.microtimer.jpg) | 060e42e488c0f17e | L2 | — | S83 |
| eu.faircode.email | app | `eu.faircode.email` | [F-Droid](https://f-droid.org/en/packages/eu.faircode.email/) | 1e59bd1d82ccdf0a | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| foehnix.widget | app | `foehnix.widget` | [F-Droid](https://f-droid.org/en/packages/foehnix.widget/) | 960913f40cefe5f4 | — (text record, S54 gate) | — | L2 | — | — |
| fr.corenting.convertisseureurofranc | app | `fr.corenting.convertisseureurofranc` | [F-Droid](https://f-droid.org/en/packages/fr.corenting.convertisseureurofranc/) | 257295104823c970 | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| io.github.aoc_normal | app | `io.github.aoc_normal` | [F-Droid](https://f-droid.org/en/packages/io.github.aoc_normal/) | 7d049e2276f0c1ae | — (text record, S54 gate) | — | L0 | — | — |
| Shopping List Calc | app | `io.github.buildsbyben.shoppinglistcalc` | [src](https://github.com/buildsbyben/shopping-list-calc) | — | [io.github.buildsbyben.shoppinglistcalc.jpg](canonical/io.github.buildsbyben.shoppinglistcalc.jpg) | 57b3ca45c8ff83c6 | L9 | — | see session report (S62-S65 spotligh |
| TimeLimit | app | `io.timelimit.android.aosp.direct` | F-Droid | — | — (text record, S54 gate) | — | L2 | — | S83 |
| it.niedermann.nextcloud.deck | app | `it.niedermann.nextcloud.deck` | [F-Droid](https://f-droid.org/en/packages/it.niedermann.nextcloud.deck/) | e7152b3062658082 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| me.river.nightbell | app | `me.river.nightbell` | [F-Droid](https://f-droid.org/en/packages/me.river.nightbell/) | e4972ad68a155033 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| me.timeto.app | app | `me.timeto.app` | [F-Droid](https://f-droid.org/en/packages/me.timeto.app/) | cff24d4b5043e268 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| Simple Stopwatch | app | `omegacentauri.mobi.simplestopwatch` | F-Droid | b3ec1a5ec24ce53b | [omegacentauri.mobi.simplestopwatch.jpg](canonical/omegacentauri.mobi.simplestopwatch.jpg) | 60c1f2f03ca5d9c6 | L2 | — | S83 |
| Notes (billthefarmer) | app | `org.billthefarmer.notes` | F-Droid | 82cf8bc44c163748 | [org.billthefarmer.notes.jpg](canonical/org.billthefarmer.notes.jpg) | c67b0f528032b839 | L2 | — | S83 |
| SigGen | app | `org.billthefarmer.siggen` | [src](https://github.com/billthefarmer/sig-gen) | — | [org.billthefarmer.siggen.jpg](canonical/org.billthefarmer.siggen.jpg) | 338c5a8687d371c2 | L5 | — | see session report (S62-S65 spotligh |
| Heading Calculator | app | `org.debian.eugen.headingcalculator` | F-Droid | 274ec873098eea51 | [org.debian.eugen.headingcalculator.jpg](canonical/org.debian.eugen.headingcalculator.jpg) | 4de2a3f8f8b8c429 | L2 | — | S83 |
| org.dystopia.email | app | `org.dystopia.email` | [F-Droid](https://f-droid.org/en/packages/org.dystopia.email/) | e1545a2f2d3aab4b | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| org.fossify.clock | app | `org.fossify.clock` | [F-Droid](https://f-droid.org/en/packages/org.fossify.clock/) | 43cf9f0ec45f1f1f | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| org.fossify.gallery | app | `org.fossify.gallery` | [F-Droid](https://f-droid.org/en/packages/org.fossify.gallery/) | ae7e699599e81f70 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| org.fossify.notes | app | `org.fossify.notes` | [F-Droid](https://f-droid.org/en/packages/org.fossify.notes/) | 5a56e0e39cc488e1 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| org.nitri.opentopo | app | `org.nitri.opentopo` | [F-Droid](https://f-droid.org/en/packages/org.nitri.opentopo/) | 0fa0362afc6f8f0c | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| org.secuso.privacyfriendlyactivitytracker | app | `org.secuso.privacyfriendlyactivitytracker` | [F-Droid](https://f-droid.org/en/packages/org.secuso.privacyfriendlyactivitytracker/) | e4041cb724f97f48 | — (text record, S54 gate) | — | L1 | — | — |
| org.secuso.privacyfriendlynotes | app | `org.secuso.privacyfriendlynotes` | [F-Droid](https://f-droid.org/en/packages/org.secuso.privacyfriendlynotes/) | 71e874f45fa4655f | — (text record, S54 gate) | — | L1 | — | — |
| org.tasks | app | `org.tasks` | [F-Droid](https://f-droid.org/en/packages/org.tasks/) | ed972cc1cec3456a | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| Telegram | app | `org.telegram.messenger.web` | [src](https://github.com/DrKLO/Telegram) | b6a13e876a8abfde | — (text record, S54 gate) | — | L1 | — | Telegram |
| org.y20k.transistor | app | `org.y20k.transistor` | [F-Droid](https://f-droid.org/en/packages/org.y20k.transistor/) | 762f4fe86bca8a66 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| P9 (tube42) | app | `se.tube42.p9.android` | F-Droid | — | — (text record, S54 gate) | — | L2 | — | S83 |
| site.leos.apps.lespas | app | `site.leos.apps.lespas` | [F-Droid](https://f-droid.org/en/packages/site.leos.apps.lespas/) | be129b43f84752e4 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| tibarj.tranquilstopwatch | app | `tibarj.tranquilstopwatch` | [F-Droid](https://f-droid.org/en/packages/tibarj.tranquilstopwatch/) | 7bc31fae5cd2e9d8 | — (text record, S54 gate) | — | L2 | — | F-NEW-160 |
| TicTacToe3D self-aware fixture | fixture | `org.miniandroid.helloworld` | [src](https://github.com/Applibered/HelloWorldSelfAware) | — | [org.miniandroid.helloworld.jpg](canonical/org.miniandroid.helloworld.jpg) | 83720c1028f832d0 | L6 | — | see session report (S62-S65 spotligh |
| Halma | game | `app.halma` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| bim.app | game | `bim.app` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| ca.rmen.nounours | game | `ca.rmen.nounours` | [F-Droid](https://f-droid.org/en/packages/ca.rmen.nounours/) | 0e7da7b17b63d727 | [ca.rmen.nounours.gif](canonical/ca.rmen.nounours.gif) | 24a19ed30eda6be3 | L2 | YES | F-NEW-160 |
| Anuto TD | game | `ch.logixisland.anuto` | [src](https://github.com/jogishop/AnutoTD) | — | [ch.logixisland.anuto.jpg](canonical/ch.logixisland.anuto.jpg) | f876a103e2eae2f1 | L5 | — | see session report (S62-S65 spotligh |
| com.ahorcado | game | `com.ahorcado` | [F-Droid](https://f-droid.org/en/packages/com.ahorcado/) | 7f4df3878508804b | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| Astroloop | game | `com.astroloop.game` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| Tirailleur | game | `com.bupkis.tirailleur` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| com.clavierhaus.gnubg | game | `com.clavierhaus.gnubg` | [F-Droid](https://f-droid.org/en/packages/com.clavierhaus.gnubg/) | a951da343ca91f10 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| Vector Pinball (bouncy) | game | `com.dozingcatsoftware.bouncy` | [F-Droid](https://f-droid.org/en/packages/com.dozingcatsoftware.bouncy/) | ffda0d9cb0b1b2aa | [com.dozingcatsoftware.bouncy.gif](canonical/com.dozingcatsoftware.bouncy.gif) | d96b48d7e8667b5b | L2 | YES | — |
| com.dozingcatsoftware.dodge | game | `com.dozingcatsoftware.dodge` | [F-Droid](https://f-droid.org/en/packages/com.dozingcatsoftware.dodge/) | a5687d1bad7b2927 | [com.dozingcatsoftware.dodge.gif](canonical/com.dozingcatsoftware.dodge.gif) | 3ca88c8da8a90bc3 | L2 | YES | F-NEW-160 |
| FireStrike | game | `com.eightsines.firestrike.opensource` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| TicTacToe Classic | game | `com.emmanuelmess.tictactoe` | [src](F-Droid com.emmanuelmess.tictactoe) | 16510d7cb5dbcf7d | [com.emmanuelmess.tictactoe.gif](canonical/com.emmanuelmess.tictactoe.gif) | b6811a17d271d5dc | L2 | YES | S83 |
| com.galaxyrio.sudokusolver | game | `com.galaxyrio.sudokusolver` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| com.games.boardgames.aeonsend | game | `com.games.boardgames.aeonsend` | [F-Droid](https://f-droid.org/en/packages/com.games.boardgames.aeonsend/) | 9dbd85782b534a58 | — (text record, S54 gate) | — | L0 | — | — |
| com.github.m374lx.alexvsbus | game | `com.github.m374lx.alexvsbus` | [F-Droid](https://f-droid.org/en/packages/com.github.m374lx.alexvsbus/) | ecec13afdae16e9f | — (text record, S54 gate) | — | L1 | — | — |
| com.helddertierwelt.mentalmath | game | `com.helddertierwelt.mentalmath` | [F-Droid](https://f-droid.org/en/packages/com.helddertierwelt.mentalmath/) | 68af653d1dc0b184 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| Balance the Ball | game | `com.jeffliu.balancetheball` | F-Droid | 6180534b151e4d50 | [com.jeffliu.balancetheball.jpg](canonical/com.jeffliu.balancetheball.jpg) | bfb8f34224084ad4 | L2 | — | S83 |
| com.kaeruct.raumballer | game | `com.kaeruct.raumballer` | [F-Droid](https://f-droid.org/en/packages/com.kaeruct.raumballer/) | e0eb9a7dfbd82162 | — (text record, S54 gate) | — | L0 | — | F-NEW-160 |
| com.kingalex.kingpong | game | `com.kingalex.kingpong` | [F-Droid](https://f-droid.org/en/packages/com.kingalex.kingpong/) | 9545a66697a83c25 | — (text record, S54 gate) | — | L0 | — | — |
| 2048 | game | `com.miniandroid.g2048` | [src](in-house (games/2048)) | 1b1c602a5f0a2723 | [com.miniandroid.g2048.gif](canonical/com.miniandroid.g2048.gif) | d613d30fce792406 | L2 | YES | S83 |
| Snake Deluxe | game | `com.miniandroid.snakedeluxe` | [src](in-house (games/snake-deluxe)) | — | [com.miniandroid.snakedeluxe.gif](canonical/com.miniandroid.snakedeluxe.gif) | f2dd621c662526fa | L3 | YES | S83 |
| Mini Tetris | game | `com.miniandroid.tetris` | [src](in-house (games/mini-tetris)) | cb2818dfe6c6cadb | [com.miniandroid.tetris.gif](canonical/com.miniandroid.tetris.gif) | 927d966a5a7397a8 | L3 | YES | S83 |
| TicTacToe Deluxe (دوز) | game | `com.miniandroid.tictactoedeluxe` | [src](in-house (games/tictactoe-deluxe)) | — | [com.miniandroid.tictactoedeluxe.gif](canonical/com.miniandroid.tictactoedeluxe.gif) | ade32b621e90fb27 | L3 | YES | S83 |
| com.mufradat.africaquiz | game | `com.mufradat.africaquiz` | [F-Droid](https://f-droid.org/en/packages/com.mufradat.africaquiz/) | 649282d36bd5c237 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| com.octbit.rutmath | game | `com.octbit.rutmath` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| com.qwde.ccm | game | `com.qwde.ccm` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| Boxcars | game | `com.rocket9labs.boxcars` | F-Droid | — | — (text record, S54 gate) | — | L1 | — | S83 |
| com.sanskritbasics.memory | game | `com.sanskritbasics.memory` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| com.serwylo.babydots | game | `com.serwylo.babydots` | [F-Droid](https://f-droid.org/en/packages/com.serwylo.babydots/) | 582d536d0aa435b5 | — (text record, S54 gate) | — | L1 | — | — |
| RetroWars | game | `com.serwylo.retrowars` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| com.sidhant.bubbleshooter | game | `com.sidhant.bubbleshooter` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| com.sidhant.puzzle | game | `com.sidhant.puzzle` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| Queens | game | `com.sidhant.queens` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| Ball2Box | game | `com.simondalvai.ball2box` | F-Droid | — | — (text record, S54 gate) | — | L0 | — | S83 |
| com.smorgasbork.hotdeath | game | `com.smorgasbork.hotdeath` | [F-Droid](https://f-droid.org/en/packages/com.smorgasbork.hotdeath/) | 8e6c19ead1795fa5 | [com.smorgasbork.hotdeath.gif](canonical/com.smorgasbork.hotdeath.gif) | d6fdff53adfaa6fa | L2 | YES | — |
| com.towerillusion.abdal | game | `com.towerillusion.abdal` | [F-Droid](https://f-droid.org/en/packages/com.towerillusion.abdal/) | 50be6be690faaa59 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| com.trianguloy.adnihilation | game | `com.trianguloy.adnihilation` | [F-Droid](https://f-droid.org/en/packages/com.trianguloy.adnihilation/) | ae531b495cc39b21 | [com.trianguloy.adnihilation.jpg](canonical/com.trianguloy.adnihilation.jpg) | 541a877382de1031 | L2 | — | F-NEW-161 |
| com.vayunmathur.games.alchemist | game | `com.vayunmathur.games.alchemist` | [F-Droid](https://f-droid.org/en/packages/com.vayunmathur.games.alchemist/) | 88a0ac6f06e9c57f | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| Solitaire (vayunmathur) | game | `com.vayunmathur.games.solitaire` | F-Droid | — | — (text record, S54 gate) | — | L2 | — | S83 |
| com.vovagorodok.blichess | game | `com.vovagorodok.blichess` | [F-Droid](https://f-droid.org/en/packages/com.vovagorodok.blichess/) | 3ae86223a7043951 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| com.vovagorodok.blidraughts | game | `com.vovagorodok.blidraughts` | [F-Droid](https://f-droid.org/en/packages/com.vovagorodok.blidraughts/) | f7f4582fa24607d8 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| Mancala | game | `com.willie.mancala` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| Mines (premy) | game | `cos.premy.mines` | F-Droid | 18faef7028457f4d | [cos.premy.mines.jpg](canonical/cos.premy.mines.jpg) | f73b3c57ca712dd2 | L2 | — | VERIFIED |
| Blackjack | game | `crypto.o0o0o0o0o.games.blackjack` | F-Droid | — | — (text record, S54 gate) | — | L0 | — | S83 |
| OpenSudoku | game | `cz.romario.opensudoku` | [src](https://github.com/romario333/opensudoku) | — | [cz.romario.opensudoku.jpg](canonical/cz.romario.opensudoku.jpg) | 1478e902a245a829 | L5 | — | see session report (S62-S65 spotligh |
| de.georgsieber.ballbreak | game | `de.georgsieber.ballbreak` | [F-Droid](https://f-droid.org/en/packages/de.georgsieber.ballbreak/) | e6e9f37293d3aaac | [de.georgsieber.ballbreak.jpg](canonical/de.georgsieber.ballbreak.jpg) | b3c8930369dfe0b7 | L2 | — | — |
| Solitaire (Bielefeld) | game | `de.tobiasbielefeld.solitaire` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| dev.lonami.klooni | game | `dev.lonami.klooni` | [F-Droid](https://f-droid.org/en/packages/dev.lonami.klooni/) | 55641cdb5dba7f30 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| eu.quelltext.counting | game | `eu.quelltext.counting` | [F-Droid](https://f-droid.org/en/packages/eu.quelltext.counting/) | 98fe65f21ff8e519 | — (text record, S54 gate) | — | L0 | — | — |
| Memory | game | `eu.quelltext.memory` | F-Droid | 4dd3957983e3c3f3 | [eu.quelltext.memory.jpg](canonical/eu.quelltext.memory.jpg) | 1f36d707ec9f685c | L0 | — | S83 |
| Fish Rings | game | `eu.veldsoft.fish.rings` | [src](https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid) | — | [eu.veldsoft.fish.rings.jpg](canonical/eu.veldsoft.fish.rings.jpg) | 28c952a6e1657b02 | L10 | — | see session report (S62-S65 spotligh |
| FreeKlondike | game | `eu.veldsoft.free.klondike` | [src](https://github.com/VelbazhdSoftwareLLC/FreeKlondike) | — | [eu.veldsoft.free.klondike.jpg](canonical/eu.veldsoft.free.klondike.jpg) | 7dd689bf2d692980 | L10 | — | see session report (S62-S65 spotligh |
| No Thanks! | game | `eu.veldsoft.no.thanks` | F-Droid | — | — (text record, S54 gate) | — | L1 | — | S83 |
| TriPeaks | game | `eu.veldsoft.tri.peaks` | [src](https://github.com/VelbazhdSoftwareLLC/TriPeaks) | — | [eu.veldsoft.tri.peaks.jpg](canonical/eu.veldsoft.tri.peaks.jpg) | 8e1d41a151898010 | L10 | — | see session report (S62-S65 spotligh |
| io.github.divverent.aaaaxy | game | `io.github.divverent.aaaaxy` | [F-Droid](https://f-droid.org/en/packages/io.github.divverent.aaaaxy/) | 976ebc08571af97d | — (text record, S54 gate) | — | L1 | — | — |
| io.github.ebraminio.bouncy | game | `io.github.ebraminio.bouncy` | [F-Droid](https://f-droid.org/en/packages/io.github.ebraminio.bouncy/) | a509db2afda544f6 | — (text record, S54 gate) | — | L0 | — | — |
| io.github.hathibelagal.mykanji | game | `io.github.hathibelagal.mykanji` | [F-Droid](https://f-droid.org/en/packages/io.github.hathibelagal.mykanji/) | b20274a0885d03ba | — (text record, S54 gate) | — | L0 | — | — |
| io.github.johnathan.minesweeper | game | `io.github.johnathan.minesweeper` | [F-Droid](https://f-droid.org/en/packages/io.github.johnathan.minesweeper/) | 3b52a2fd21c4b418 | — (text record, S54 gate) | — | L1 | — | F-NEW-160 |
| io.github.rotundtapir.fivehundred | game | `io.github.rotundtapir.fivehundred` | [F-Droid](https://f-droid.org/en/packages/io.github.rotundtapir.fivehundred/) | db215475793097c0 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| Dooz (tic-tac-toe) | game | `io.github.yamin8000.dooz` | [src](F-Droid io.github.yamin8000.dooz) | d81292cd346dcb23 | — (text record, S54 gate) | — | L1 | — | R-NEW-344 |
| io.itch.pirate_solitaire | game | `io.itch.pirate_solitaire` | [F-Droid](https://f-droid.org/en/packages/io.itch.pirate_solitaire/) | b9fbe6023d8696b6 | — (text record, S54 gate) | — | L0 | — | F-NEW-160 |
| ir.hsn6.tpb | game | `ir.hsn6.tpb` | [F-Droid](https://f-droid.org/en/packages/ir.hsn6.tpb/) | 37ffc01c030e3d24 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| Chess (jwtc) | game | `jwtc.android.chess` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| name.boyle.chris.sgtpuzzles | game | `name.boyle.chris.sgtpuzzles` | [F-Droid](https://f-droid.org/en/packages/name.boyle.chris.sgtpuzzles/) | 6b36d5537984523c | — (text record, S54 gate) | — | L1 | — | — |
| net.sourceforge.solitaire_cg | game | `net.sourceforge.solitaire_cg` | [F-Droid](https://f-droid.org/en/packages/net.sourceforge.solitaire_cg/) | — | — (text record, S54 gate) | — | L1 | — | — |
| Navy Fleet Battle | game | `net.tigr.navyfleetbattle` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| OPMT (One More Time…) | game | `one.scarecrow.games.OPMT` | [src](https://github.com/scarecrowgames/OneMoreTimePuzzleGame) | — | [one.scarecrow.games.OPMT.jpg](canonical/one.scarecrow.games.OPMT.jpg) | 17aa411b313a5aa2 | L2 | — | PARTIAL |
| org.andstatus.game2048 | game | `org.andstatus.game2048` | [F-Droid](https://f-droid.org/en/packages/org.andstatus.game2048/) | 2d6707624623fe88 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| org.asafonov.accelerace | game | `org.asafonov.accelerace` | [F-Droid](https://f-droid.org/en/packages/org.asafonov.accelerace/) | fe705a1599e6ce0c | — (text record, S54 gate) | — | L0 | — | — |
| org.bobstuff.bobball | game | `org.bobstuff.bobball` | [F-Droid](https://f-droid.org/en/packages/org.bobstuff.bobball/) | fd43009a7ffdfaf8 | [org.bobstuff.bobball.gif](canonical/org.bobstuff.bobball.gif) | 788ce033de1ae0c3 | L2 | YES | — |
| org.lufebe16.pysolfc | game | `org.lufebe16.pysolfc` | [F-Droid](https://f-droid.org/en/packages/org.lufebe16.pysolfc/) | 5b8ba9abc4c11ba0 | — (text record, S54 gate) | — | L1 | — | Kivy |
| org.mattvchandler.a2050 | game | `org.mattvchandler.a2050` | [F-Droid](https://f-droid.org/en/packages/org.mattvchandler.a2050/) | 98a0e75e589c3190 | — (text record, S54 gate) | — | L1 | — | F-NEW-161 |
| org.og8.a1tox | game | `org.og8.a1tox` | [F-Droid](https://f-droid.org/en/packages/org.og8.a1tox/) | 34895a84a638d53b | — (text record, S54 gate) | — | L0 | — | — |
| Surge Engine (OpenSurge) | game | `org.opensurge2d.surgeengine` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| org.secuso.privacyfriendly2048 | game | `org.secuso.privacyfriendly2048` | [F-Droid](https://f-droid.org/en/packages/org.secuso.privacyfriendly2048/) | 02c799d3d582669d | — (text record, S54 gate) | — | L1 | — | — |
| PFBattleship | game | `org.secuso.privacyfriendlybattleship` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| org.secuso.privacyfriendlydame | game | `org.secuso.privacyfriendlydame` | [F-Droid](https://f-droid.org/en/packages/org.secuso.privacyfriendlydame/) | 41727c0121fef8ab | — (text record, S54 gate) | — | L1 | — | — |
| org.secuso.privacyfriendlymemory | game | `org.secuso.privacyfriendlymemory` | [F-Droid](https://f-droid.org/en/packages/org.secuso.privacyfriendlymemory/) | 82f83d9ea572240a | — (text record, S54 gate) | — | L1 | — | — |
| org.secuso.privacyfriendlysolitaire | game | `org.secuso.privacyfriendlysolitaire` | [F-Droid](https://f-droid.org/en/packages/org.secuso.privacyfriendlysolitaire/) | b0e2adf991f94982 | — (text record, S54 gate) | — | L1 | — | — |
| org.secuso.privacyfriendlysudoku | game | `org.secuso.privacyfriendlysudoku` | [F-Droid](https://f-droid.org/en/packages/org.secuso.privacyfriendlysudoku/) | 1aff917f4ac9952b | — (text record, S54 gate) | — | L1 | — | — |
| org99managers.futsal_edition | game | `org99managers.futsal_edition` | [F-Droid](https://f-droid.org/en/packages/org99managers.futsal_edition/) | c9eeea657951f694 | — (text record, S54 gate) | — | L1 | — | F-NEW-162 |
| Guandan | game | `page.codeberg.lanticy.guandan` | F-Droid | — | — (text record, S54 gate) | — | L2 | — | S83 |
| TheXTech (SuperTux-like) | game | `ru.wohlsoft.thextech.fdroid` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| Tarok | game | `si.palcka.tarok` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
| x653.all_in_gold | game | `x653.all_in_gold` | [F-Droid](https://f-droid.org/en/packages/x653.all_in_gold/) | 01f04f99173ead82 | [x653.all_in_gold.jpg](canonical/x653.all_in_gold.jpg) | 658d0a2825cce720 | L2 | — | — |
| xyz.deepdaikon.quinb | game | `xyz.deepdaikon.quinb` | — | — | — (text record, S54 gate) | — | L1 | — | no prior root cause — rendered at cu |
