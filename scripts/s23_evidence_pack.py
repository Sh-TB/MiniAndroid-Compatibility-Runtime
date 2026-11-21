#!/usr/bin/env python3
"""S23 evidence pack: APK SHA-256s + interaction summary TSV."""
import hashlib, glob, os, subprocess

HAND = '/home/z/my-project/upload/handoff_apks'
OUT = '/home/z/my-project/miniandroid/evidence/s23'

targets = [
    'name.livitski.games.puzzle.android_2.apk',
    'ru.zxalexis.ugaday_15.apk',
    'org.blockinger.game_14.apk',
    'com.farmerbb.notepad_122.apk',
    'com.itsfrz.tictactoe_5.apk',
    'org.ecos.logic.flip_a_coin_3.apk',
    'com.attenomy.janken_1.apk',
    'tech.gaskell.diceroller_1_debug.apk',
    'com.ivylopez.authsrng_6.apk',
    'de.tcrass.minos_10004.apk',
    'io.github.herrerad85.tallybook_94.apk',
]

with open(os.path.join(OUT, 's23_apk_sha256.tsv'), 'w') as f:
    f.write('apk\tsha256\tsize_bytes\n')
    for a in targets:
        p = os.path.join(HAND, a)
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        f.write(f'{a}\t{h}\t{os.path.getsize(p)}\n')
print('sha256 table written')

# interaction summary: per run — rc, frame count, unique hashes, dispatched
rows = ['apk\trep\trc\tframes\tunique_frame_hashes\tclick_dispatched\tLC_provide\tGSS_class']
for base in ('name.livitski.games.puzzle.android_2', 'ru.zxalexis.ugaday_15',
             'org.blockinger.game_14', 'com.itsfrz.tictactoe_5',
             'com.farmerbb.notepad_122', 'com.attenomy.janken_1'):
    for rep in (1, 2, 3):
        d = os.path.join(OUT, f'{base}_r{rep}')
        if not os.path.isdir(d):
            continue
        frames = sorted(glob.glob(os.path.join(d, 'frames', '*.png'))) or \
            sorted(glob.glob(os.path.join(d, '*.png')))
        hs = {hashlib.sha256(open(p, 'rb').read()).hexdigest()[:8]
              for p in frames}
        err = open(os.path.join(d, 'stderr.log'), errors='replace').read()
        dispatched = err.count('result=DISPATCHED') + \
            err.count('XMLCLICK] onClick dispatched')
        lc = err.count('S22-LC-PROVIDE') + err.count('S23-W1-PROVIDE')
        gss = err.count('S23-W3-GSS-CLASS')
        rc = 0 if ' rc=0' in subprocess.run(
            ['true'], capture_output=True).stderr.decode() else 'n/a'
        rows.append(f'{base}\t{rep}\tn/a\t{len(frames)}\t{len(hs)}\t'
                    f'{dispatched}\t{lc}\t{gss}')
with open(os.path.join(OUT, 's23_interaction_summary.tsv'), 'w') as f:
    f.write('\n'.join(rows) + '\n')
print('interaction summary written:', len(rows) - 1, 'rows')
