#!/usr/bin/env python3
"""S61 Runtime Spotlight Corpus — Phase A fetcher.

F-Droid API-driven fetch: for every candidate package, query
https://f-droid.org/api/v1/packages/<pkg> for the suggested version code,
download the repo APK into apk_cache/spotlight/, and record SHA256 +
size + source URL into the corpus manifest (JSON).

Zero-APK-in-repo law: APKs live in apk_cache/ (gitignored); only the
manifest + coverage matrix are committed.

Usage: python3 scripts/s61_spotlight_fetch.py [--max N]
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

REPO = '/home/z/my-project'
DEST = os.path.join(REPO, 'apk_cache', 'spotlight')
MANIFEST = os.path.join(REPO, 'docs', 'corpus', 'spotlight_manifest.json')

# Runtime Spotlight candidates. Each entry: (f-droid package id, capability
# tags). Tags follow the campaign capability families (see the coverage
# matrix doc). Selection rule: maximize NEW capability coverage per app
# (spotlight selection algorithm), prefer small classic View-based apps.
CANDIDATES = [
    # ── Simple Games Spotlight subset ──
    ('com.uberspot.a2048', ['game', 'canvas', 'touch-swipe', 'animation', 'game-loop', 'state-machine']),
    ('com.dozingcatsoftware.bouncy', ['game', 'canvas', 'physics', 'touch', 'game-loop', 'threading']),
    ('org.secuso.privacyfriendlysolitaire', ['game', 'touch', 'state-machine', 'card-layout', 'dialog']),
    ('org.secuso.privacyfriendly2048', ['game', 'grid-layout', 'touch-swipe', 'state-machine', 'sqlite']),
    ('org.secuso.privacyfriendlyminesweeper', ['game', 'grid-layout', 'touch', 'state-machine', 'timer']),
    ('de.tobiasbielefeld.solitaire', ['game', 'touch', 'state-machine', 'animation', 'preferences']),
    ('com.gauravjassal.rockpaper', ['game', 'touch', 'state-machine']),
    ('org.pixeldroid.pixel_dungeon_2', ['game', 'canvas', 'touch', 'multi-screen', 'sqlite']),
    ('com.nkanaev.numberpaint', ['game', 'canvas', 'touch']),
    ('org.riellocke.sevenwondersscorekeeper', ['game', 'dialog', 'preferences', 'multi-screen']),
    ('fr.rboisbande.score', ['game', 'dialog', 'preferences']),
    ('jp.sekf.kqueue.game', ['game', 'canvas', 'touch']),
    ('com.devictor.dsmilingwood', ['game', 'canvas', 'touch', 'animation']),
    ('de.j4velin.ultimateChase', ['game', 'canvas', 'sensor', 'touch']),
    ('name.boyle.chris.sgtpuzzles', ['game', 'canvas', 'touch', 'multi-screen', 'state-machine']),
    ('org.piepmatzhuhn.memorygame', ['game', 'memory-card', 'touch', 'animation', 'preferences']),
    ('at.tomomas.2048', ['game', 'touch-swipe', 'state-machine']),
    ('com.thirtydays.bomb', ['game', 'timer', 'touch', 'vibrate']),
    ('org.fussballspielen.tipp', ['game', 'networking', 'listview']),
    ('com.hobbyone.moviedb', ['networking', 'listview', 'imageview']),
    # ── Utility apps: classic View / lifecycle / storage families ──
    ('org.billthefarmer.diary', ['listview', 'sqlite', 'preferences', 'date-widgets', 'menu']),
    ('org.billthefarmer.viewer', ['webview', 'imageview', 'intent', 'multi-screen']),
    ('org.billthefarmer.tuner', ['canvas', 'audio', 'custom-view', 'threading']),
    ('org.billthefarmer.timber', ['custom-view', 'canvas']),
    ('org.billthefarmer.weather', ['networking', 'json', 'listview', 'preferences']),
    ('org.billthefarmer.expense', ['sqlite', 'dialog', 'menu', 'listview']),
    ('org.billthefarmer.calc', ['custom-view', 'touch', 'state-machine']),
    ('org.billthefarmer.highlight', ['webview', 'textview', 'scrolling']),
    ('org.billthefarmer.markdown', ['webview', 'markdown', 'textview', 'intent']),
    ('org.billthefarmer.clipboard', ['clipboard', 'textview', 'edittext']),
    ('org.billthefarmer.speaker', ['audio', 'threading', 'custom-view']),
    ('org.billthefarmer.ringtones', ['audio', 'listview', 'storage']),
    ('org.billthefarmer.sync', ['networking', 'threading']),
    ('org.billthefarmer.shorty', ['intent', 'shortcut', 'textview']),
    ('org.billthefarmer.accordion', ['custom-view', 'canvas', 'touch', 'audio']),
    ('de.duenndns.mtmusic', ['audio', 'listview', 'service', 'threading']),
    ('de.duenndns.sslmemo', ['sqlite', 'networking', 'edittext', 'listview']),
    ('dubrowgn.waketime', ['alarm', 'dialog', 'preferences', 'service']),
    ('org.debian.eugen.scaleimageview', ['imageview', 'touch-zoom', 'matrix']),
    ('org.ligi.passandroid', ['storage', 'json', 'listview', 'imageview']),
    ('org.ligi.tracedroid', ['storage', 'listview', 'logcat']),
    ('com.blogspot.app4mobile.lifecalc', ['sqlite', 'listview']),
    ('com.jarsilio.android.wildlog', ['sqlite', 'camera', 'listview', 'storage']),
    ('com.nkanaev.lunula', ['webview', 'calendar', 'sqlite']),
    ('org.secuso.privacyfriendlynotes', ['sqlite', 'edittext', 'listview', 'dialog', 'multi-screen']),
    ('org.secuso.privacyfriendlytodolist', ['sqlite', 'recycler-view', 'dialog', 'alarm']),
    ('org.secuso.privacyfriendlyactivitytracker', ['sqlite', 'service', 'sensor', 'listview']),
    ('org.secuso.privacyfriendlyweather', ['networking', 'json', 'listview', 'sqlite', 'preferences']),
    ('org.secuso.privacyfriendlynetmonitor', ['networking', 'listview', 'service', 'sqlite']),
    ('org.secuso.privacyfriendlypaindiary', ['sqlite', 'fragment', 'viewpager', 'dialog']),
    ('org.secuso.privacyfriendlybackupsolitaire', ['game', 'touch', 'state-machine', 'sqlite']),
    ('org.secuso.privacyfriendlycodescanner', ['camera', 'dialog', 'intent', 'beep']),
    ('org.secuso.privacyfriendlytrainingplan', ['sqlite', 'listview', 'dialog']),
    ('org.secuso.privacyfriendlypbackup', ['storage', 'dialog']),
    ('org.secuso.privacyfriendlyflashlight', ['camera', 'service', 'widget', 'touch']),
    ('org.secuso.privacyfriendlyrockpaperscissors', ['game', 'touch', 'state-machine', 'animation']),
    ('org.secuso.privacyfriendlytictactoe', ['game', 'touch', 'state-machine', 'multi-player']),
    ('org.secuso.privacyfriendlyludo', ['game', 'canvas', 'touch', 'state-machine', 'dialog']),
    ('org.secuso.privacyfriendlyrideplanner', ['networking', 'listview', 'intent']),
    ('org.secuso.privacyfriendlyoffice', ['sqlite', 'listview', 'dialog']),
    ('org.secuso.privacyfriendlycipher', ['edittext', 'textview', 'spinner', 'state-machine']),
    ('org.secuso.privacyfriendlymanager', ['listview', 'storage']),
    ('org.secuso.privacyfriendlyfooddiary', ['sqlite', 'listview', 'imageview', 'dialog']),
    ('org.secuso.privacyfriendlyskygs', ['sqlite']),
    ('org.secuso.privacyfriendly интервальна', ['timer']),
    ('me.ghobadh.sample', []),
    ('com.varlorg.unote_u', []),
    ('org.zephyrsoft.trackworktime', ['sqlite', 'service', 'alarm', 'listview', 'preferences']),
    ('com.github.axet.bookreader', ['storage', 'listview', 'preferences', 'scrolling']),
    ('com.github.axet.tonebadge', ['audio', 'service']),
    ('com.github.axet.smsgate', ['service', 'networking', 'sms']),
    ('com.github.axet.sound', ['audio', 'listview']),
    ('com.github.axet.duper', ['storage', 'listview']),
    ('net.gaast.giggity', ['networking', 'sqlite', 'listview', 'alarm']),
    ('net.gaast.deoxide', ['networking', 'listview']),
    ('at.linuxnet.saferplan', ['sqlite', 'listview', 'preferences']),
    ('org.liberty.android.fantastiskmemo', ['sqlite', 'edittext', 'listview']),
    ('com.bubble.zerolith', []),
    ('ru.hakovellow.teacherload', ['sqlite', 'listview']),
    ('es.wolfi.app.passman', ['networking', 'listview', 'preferences']),
    ('cz.muni.fi.xklinec.whitecards', ['dialog', 'state-machine']),
    ('com.artifex.mupdfdemo', ['pdf', 'scrolling', 'custom-view']),
    ('com.manichord.mgit', ['networking', 'sqlite', 'listview', 'threading']),
    ('eu.lindenbaum.ball', ['game', 'canvas', 'sensor', 'touch', 'game-loop']),
    ('org.landrovar.harmony', ['game', 'canvas', 'touch', 'game-loop']),
    ('com.dozingcatsoftware.cameraapp', ['camera']),
    ('hu.vmiklos.plees_tracker', ['sqlite', 'service', 'listview', 'chart']),
    ('io.github.domstolene.application', []),
    ('it.feio.android.omninotes', ['sqlite', 'fragment', 'listview', 'preferences', 'dialog']),
    ('jp.yokomark.logoview', ['imageview', 'custom-view']),
    ('org.kde.kdeconnect_tp', ['networking', 'service', 'listview']),
    ('com.nutomicsyncthingandroid', ['service', 'networking', 'listview']),
    ('de.stuffit.app', []),
    ('net.sylvek.sharemyposition', ['networking', 'gps', 'service']),
    ('fr.gouv.etalab.mastodon', ['networking', 'listview', 'imageview', 'recycler-view']),
    # ── Wave 2 (S61, capability-driven sweep; probed via the F-Droid API) ──
    ('org.secuso.privacyfriendlyrockpaperscissors', ['game', 'touch', 'state-machine', 'animation']),
    ('org.secuso.privacyfriendlytictactoe', ['game', 'touch', 'state-machine']),
    ('org.secuso.privacyfriendlysnake', ['game', 'canvas', 'touch', 'game-loop']),
    ('org.secuso.privacyfriendlymemory', ['game', 'memory-card', 'touch', 'animation']),
    ('org.secuso.privacyfriendlycompass', ['sensor', 'canvas', 'custom-view']),
    ('org.secuso.privacyfriendlymetricconverter', ['calc', 'listview', 'spinner']),
    ('org.secuso.privacyfriendlyinvestmentcalculator', ['calc', 'listview']),
    ('org.secuso.privacyfriendlyirc', ['networking', 'service', 'listview']),
    ('org.secuso.privacyfriendlyfinance', ['sqlite', 'listview', 'fragment']),
    ('org.secuso.privacyfriendlyhealth', ['sqlite', 'listview']),
    ('org.quantumbadger.redreader', ['networking', 'listview', 'recycler-view', 'imageview', 'markdown']),
    ('com.mendhak.gpslogger', ['gps', 'service', 'storage', 'listview', 'preferences']),
    ('org.ligi.survivalmanual', ['webview', 'listview', 'scrolling', 'search']),
    ('de.blinkt.openvpn', ['service', 'networking', 'jni', 'preferences']),
    ('com.fsck.k9', ['networking', 'sqlite', 'service', 'listview', 'intent']),
    ('org.totschnig.myexpenses', ['sqlite', 'listview', 'dialog', 'export']),
    ('com.nononsenseapps.notepad', ['sqlite', 'listview', 'fragment', 'dialog', 'sync']),
    ('org.dmfs.tasks', ['sqlite', 'sync', 'widget', 'listview']),
    ('com.ghostsq.commander', ['storage', 'listview', 'custom-view', 'multi-screen']),
    ('org.yaaic', ['networking', 'sqlite', 'listview', 'service']),
    ('com.quran.labs.androidquran', ['audio', 'imageview', 'viewpager', 'storage']),
    ('de.grobox.liberario', ['networking', 'listview', 'fragment']),
    ('com.github.yeriomin.yalpstore', ['networking', 'listview', 'preferences']),
    ('org.billthefarmer.mididriver', ['audio', 'jni', 'service', 'threading']),
    ('org.billthefarmer.organelle', ['audio', 'custom-view', 'canvas']),
    ('org.billthefarmer.stories', ['listview', 'storage', 'textview']),
    ('org.billthefarmer.feed', ['networking', 'xml', 'listview']),
    ('org.billthefarmer.zigzag', ['canvas', 'custom-view', 'touch']),
    ('org.billthefarmer.money', ['sqlite', 'listview', 'dialog']),
    ('org.billthefarmer.levels', ['canvas', 'custom-view', 'audio', 'sensor']),
    ('org.billthefarmer.siggen', ['audio', 'custom-view', 'canvas', 'threading']),
    ('org.billthefarmer.piper', ['audio', 'custom-view']),
    ('com.better.alarm', ['alarm', 'service', 'listview', 'preferences']),
    ('com.philliphsu.clock2', ['alarm', 'listview', 'dialog', 'service']),
    ('org.ligi.blexplorer', ['bluetooth', 'listview', 'service']),
    ('org.pocketworkstation.pckeyboard', ['ime', 'service', 'custom-view', 'preferences']),
    ('de.tobiasbielefeld.bubblelevel', ['sensor', 'custom-view', 'canvas']),
    ('com.android2.calculator3', ['custom-view', 'touch', 'state-machine']),
    ('eu.veldsoft.sokoban', ['game', 'canvas', 'touch', 'state-machine']),
    ('eu.veldsoft.tictactoe3d', ['game', 'canvas', 'touch', 'state-machine']),
    ('com.stoutner.privacybrowser', ['webview', 'listview', 'preferences', 'dialog']),
    ('com.jens.automation2', ['service', 'sqlite', 'listview', 'preferences']),
    ('com.simplemobiletools.calculator', ['custom-view', 'touch', 'state-machine', 'preferences']),
    ('com.simplemobiletools.clock', ['alarm', 'listview', 'service', 'dialog']),
    ('com.simplemobiletools.draw', ['canvas', 'custom-view', 'touch', 'storage']),
    ('com.simplemobiletools.flashlight', ['camera', 'service', 'widget']),
    ('com.simplemobiletools.filemanager', ['storage', 'listview', 'dialog', 'preferences']),
    ('com.simplemobiletools.musicplayer', ['audio', 'service', 'listview']),
    ('com.simplemobiletools.notes', ['edittext', 'storage', 'preferences', 'widget']),
    ('com.simplemobiletools.gallery', ['imageview', 'storage', 'listview', 'viewpager']),
    ('net.fabiszewski.ulogger', ['gps', 'networking', 'service', 'sqlite']),
    ('de.j4velin.wallpaper.changer', ['wallpaper', 'imageview', 'service']),
    ('com.vrem.wifianalyzer', ['wifi', 'canvas', 'graph', 'listview']),
    ('me.sheimi.sgit', ['networking', 'jni', 'listview', 'storage']),
    ('org.sufficientlysecure.keychain', ['crypto', 'listview', 'sqlite', 'intent']),
    ('com.urbandroid.sleep', ['service', 'sensor', 'alarm']),
    ('com.ustwo.lander', ['game', 'canvas', 'wallpaper', 'animation', 'game-loop']),
    ('de.westnordost.streetcomplete', ['map', 'canvas', 'sqlite', 'dialog']),
    ('de.schildbach.wallet', ['crypto', 'networking', 'sqlite', 'service']),
    ('de.ph1b.audiobook', ['audio', 'service', 'listview', 'storage']),
    ('de.mm20.launcher2.release', ['launcher', 'listview', 'recycler-view', 'preferences']),
    ('de.kaffeemitkoffein.tinyweatherforecastgermany', ['networking', 'listview', 'canvas', 'widgets']),
    ('de.j4velin.fitnesscharts', ['sensor', 'chart', 'sqlite']),
    ('de.ponyhof.rechentrainer', ['game', 'calc', 'state-machine', 'preferences']),
    ('de.trevor.minecart', ['game', 'touch']),
    ('de.wintermute.spaceinv', ['game', 'canvas', 'touch', 'game-loop']),
    ('de.thomasluehr.scoreboard', ['canvas', 'custom-view']),
    ('de.titans.chip8', ['game', 'canvas', 'touch', 'state-machine']),
    ('de.tobiasbielefeld.ck3timer', ['timer', 'dialog', 'preferences']),
    ('de.treichel.schwimmen', ['game', 'touch', 'state-machine', 'card-layout']),
    ('de.nubignum.malefiz', ['game', 'canvas', 'touch', 'state-machine']),
    ('de.starchild.fourconnect', ['game', 'touch', 'state-machine']),
    ('de.fgerbig.spacegui', ['game', 'canvas', 'touch']),
    ('de.joergjahnke.game.android.blasterki', ['game', 'canvas', 'touch']),
    ('de.marshal.hexruler', ['game', 'canvas', 'touch']),
    ('de.serosoft.quickdevtrivial', ['game', 'state-machine']),
    ('de.spieleck.app.nfs9', ['game', 'state-machine']),
    ('com.thunderrabbit.mtglife', ['game', 'touch', 'state-machine']),
    ('hu.vmiklos.plees_tracker', ['sqlite', 'service', 'listview', 'chart']),
    ('net.sourceforge.opencamera', ['camera', 'canvas', 'custom-view', 'preferences']),
    ('org.secuso.privacyfriendlysketching', []),
    ('com.github.wrdlbrnft.searchablelists', ['listview', 'search']),
    ('com.xlythe.calculator.material', ['custom-view', 'touch', 'state-machine']),
    ('com.markuspage.android.atimetracker', ['sqlite', 'listview', 'menu']),
    ('com.nolanlawson.logcat', ['logcat', 'listview', 'service']),
    ('org.andstatus.app', ['networking', 'listview', 'service']),
    ('com.irccloud.android', ['networking', 'listview', 'service']),
    ('org.primftpd', ['service', 'networking', 'storage']),
    ('eu.basicairdata.graziano.gpslogger', ['gps', 'service', 'chart']),
    ('com.dozukm.dozukm', []),
    ('org.secuso.privacyfriendlystaffmembers', ['sqlite', 'listview']),
    ('org.secuso.privacyfriendlystaffbase', []),
    ('org.secuso.privacyfriendlyscribbler', []),
    ('org.secuso.privacyfriendlypin', ['dialog', 'state-machine']),
    ('org.secuso.privacyfriendlycodescanner', ['camera', 'dialog', 'intent']),
    ('org.secuso.privacyfriendlyquicksettings', []),
    ('org.secuso.privacyfriendlyweather', ['networking', 'json', 'listview', 'sqlite', 'preferences']),
]


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'MiniAndroid-Spotlight/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main():
    os.makedirs(DEST, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    manifest = {'schema': 'spotlight-corpus-v1', 'generated': time.strftime('%Y-%m-%d'),
                'source': 'https://f-droid.org', 'apps': []}
    if os.path.exists(MANIFEST):
        try:
            old = json.load(open(MANIFEST))
            known = {a['package']: a for a in old.get('apps', [])}
        except Exception:
            known = {}
    else:
        known = {}

    max_n = 999
    if '--max' in sys.argv:
        max_n = int(sys.argv[sys.argv.index('--max') + 1])

    ok = fail = 0
    for pkg, tags in CANDIDATES:
        if ok >= max_n:
            break
        entry = known.get(pkg)
        dest = os.path.join(DEST, pkg + '.apk')
        if entry and os.path.exists(dest) and entry.get('sha256') == sha256(dest):
            manifest['apps'].append(entry)
            ok += 1
            continue
        # S61 resume law: an APK already on disk from an interrupted run is
        # registered with its REAL hash — no refetch needed.
        if entry is None and os.path.exists(dest) and os.path.getsize(dest) > 1024:
            entry = {
                'package': pkg,
                'version_code': None,
                'name': pkg,
                'capabilities': tags,
                'source_url': f'https://f-droid.org/repo/{pkg}.apk',
                'sha256': sha256(dest),
                'size_bytes': os.path.getsize(dest),
                'recovered_from_partial_run': True,
            }
            manifest['apps'].append(entry)
            ok += 1
            print('OK*   %s (recovered, %d KiB)' % (pkg, entry['size_bytes'] // 1024))
            continue
        try:
            api = json.loads(fetch(f'https://f-droid.org/api/v1/packages/{pkg}'))
            vcode = api.get('suggestedVersionCode')
            if not vcode:
                raise ValueError('no suggested version')
            url = f'https://f-droid.org/repo/{pkg}_{vcode}.apk'
            data = fetch(url, timeout=120)
            with open(dest + '.part', 'wb') as f:
                f.write(data)
            os.replace(dest + '.part', dest)
            entry = {
                'package': pkg,
                'version_code': vcode,
                'name': api.get('name', pkg),
                'capabilities': tags,
                'source_url': url,
                'sha256': hashlib.sha256(data).hexdigest(),
                'size_bytes': len(data),
            }
            manifest['apps'].append(entry)
            ok += 1
            print(f'OK    {pkg} v{vcode} ({len(data)//1024} KiB)')
        except Exception as e:
            fail += 1
            print(f'FAIL  {pkg}: {e}')
            manifest.setdefault('unavailable', []).append(
                {'package': pkg, 'reason': str(e)[:120]})
    manifest['count'] = len(manifest['apps'])
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    json.dump(manifest, open(MANIFEST, 'w'), indent=1)
    print(f'\nfetched={ok} failed={fail} manifest={MANIFEST}')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


if __name__ == '__main__':
    main()
