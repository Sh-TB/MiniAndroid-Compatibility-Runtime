#!/usr/bin/env python3
"""S24 evidence pack: per-target run matrix + shared-law firing counts."""
import glob, hashlib, os

OUT = '/home/z/my-project/miniandroid/evidence/s24'
os.makedirs(OUT, exist_ok=True)

targets = [
    'org.ecos.logic.flip_a_coin_3', 'de.tcrass.minos_10004',
    'name.livitski.games.puzzle.android_2', 'ru.zxalexis.ugaday_15',
    'org.blockinger.game_14', 'com.itsfrz.tictactoe_5',
    'com.farmerbb.notepad_122', 'com.minar.randomix_42',
    'HelloWorldToast-1.4.0-android',
]
rows = ['apk\trep\trc_seen\tunique_frame_hashes\tW1_ADOPT\tW2_IFACE\tnote']
notes = {
    'org.ecos.logic.flip_a_coin_3': 'S24-W1 adoption: content children=1, tree 856->860->461(5 children), ImageView 331x331, rc 1->0',
    'de.tcrass.minos_10004': 'S24-W2b List/Deque model: nextint IAE chain passed, rc 1->0; EventBus reflection next blocker',
    'ru.zxalexis.ugaday_15': 'semantics: frame diff = app-authored "Invalid number" band (own logic ran)',
    'name.livitski.games.puzzle.android_2': 'interactive: GamePlay listener dispatched x12/run, 2 frame hashes x3',
    'org.blockinger.game_14': 'interactive: 6 click events, 2 frame hashes x3',
    'com.itsfrz.tictactoe_5': 'BLOCKED: theme exception chain (LC4/a via LB4/x.b) precedes listener registration; census 0 clickable',
    'com.farmerbb.notepad_122': 'S23-W3 fixed autofill; next: DataStore/protobuf worker NPE (J3/d.Q getClass-on-null)',
    'com.minar.randomix_42': 'REGRESSION GUARD: conservative iterator gate restored golden 31ddd4d5 after blanket-Iterator break',
    'HelloWorldToast-1.4.0-android': 'golden anchor acdd9f05 IDENTICAL',
}
for t in targets:
    for rep in (1, 2, 3):
        d = os.path.join(OUT, f'{t}_r{rep}') if os.path.isdir(
            os.path.join(OUT, f'{t}_r{rep}')) else \
            os.path.join(OUT, f'anchor_{t}') if os.path.isdir(
            os.path.join(OUT, f'anchor_{t}')) else \
            os.path.join(OUT, f'chk_{t.split("_")[0]}')
        if not os.path.isdir(d):
            continue
        frames = sorted(glob.glob(os.path.join(d, 'frames', '*.png'))) or \
            sorted(glob.glob(os.path.join(d, '*.png')))
        hs = {hashlib.sha256(open(p, 'rb').read()).hexdigest()[:8]
              for p in frames}
        err = open(os.path.join(d, 'stderr.log'),
                   errors='replace').read() if os.path.exists(
            os.path.join(d, 'stderr.log')) else ''
        rows.append(f'{t}\t{rep}\tn/a\t{len(hs)}\t'
                    f'{err.count("S24-W1-ADOPT")}\t'
                    f'{err.count("S24-W2-IFACE")}\t'
                    f'{notes.get(t, "")}')
open(os.path.join(OUT, 's24_run_matrix.tsv'), 'w').write('\n'.join(rows) + '\n')
print('rows:', len(rows) - 1)
