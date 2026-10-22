#!/bin/bash
# cont155_train3_windowroot.sh — WINDOW_ROOT (NO_ROOT) cohort census over the 17
# known apps: run each (frames 3, max-seconds 20), extract the decisive marker:
#   A = activity.onCreate never dispatched (lifecycle gap)
#   B = uncaught at <Activity>.onCreate with app-side DI/Koin exception
#   C = AppCompat theme-gate IllegalStateException
#   D = other uncaught (named)
#   E = no uncaught at all (silent exit)
set -u
BIN=miniandroid/build/miniandroid
mkdir -p run/c155/t3
APKS=$(python3 -c "
import json
sc = json.load(open('run/c154/scorecard_final.json'))
for r in sc['rows']:
    if r.get('verdict') == 'NO_ROOT':
        a = r['apk']
        if '/' not in a: a = 'upload/fdroid_batch/' + a
        print(a)
")
for apk in $APKS; do
  name=$(basename "$apk" .apk)
  out="run/c155/t3/$name"
  log="$out.log"
  if [ -f "$log" ] && grep -q "FRAME-SEQ] done" "$log"; then echo "SKIP $name"; continue; fi
  timeout 60 $BIN run "$apk" --width 1080 --height 1920 --frames 3 --max-seconds 20 -o "$out" > /dev/null 2> "$log"
  rc=$?
  echo "rc=$rc $name"
done
echo "=== classification:"
python3 - << 'PY'
import json, re, os
sc = json.load(open('run/c154/scorecard_final.json'))
apks = {r['apk']: r['name'] for r in sc['rows'] if r.get('verdict') == 'NO_ROOT'}
res = {}
for apk, name in apks.items():
    base = os.path.basename(apk)[:-4]
    txt = ''
    for cand in (f'run/c155/t3/{base}.log', f'run/c155/t3_{base}.log'):
        if os.path.exists(cand):
            txt += open(cand, errors='replace').read()
    if not txt: res[name] = 'NO-LOG'; continue
    oncreate_ran = bool(re.search(r'method=onCreate', txt)) or \
                   bool(re.search(r'uncaught at caller [^ ]*\.onCreate', txt))
    uncaught = re.findall(r'EXC-PROPAGATE\] (\S+) uncaught at caller (\S+)', txt)
    theme_gate = 'You need to use a Theme.AppCompat theme' in txt
    koin = 'No definition found' in txt or 'Lb53;' in txt
    unc_at_oncreate = [e for e, c in uncaught if re.search(r'\.onCreate', c)]
    if not oncreate_ran:
        res[name] = 'A: onCreate-never-ran'
    elif theme_gate:
        res[name] = 'C: AppCompat theme-gate false-negative'
    elif koin:
        res[name] = 'B: app-DI (Koin) resolution failure'
    elif unc_at_oncreate:
        res[name] = f'D: {unc_at_oncreate[0][:44]} @ onCreate'
    elif uncaught:
        res[name] = f'D: {uncaught[0][0][:40]} @ {uncaught[0][1][:28]}'
    else:
        res[name] = 'E: silent (no uncaught, onCreate ran?)'
for name in sorted(res, key=lambda n: res[n]):
    print(f'  {res[name]:58s} {name}')
from collections import Counter
print('counts:', dict(Counter(v.split(':')[0] for v in res.values())))
PY
