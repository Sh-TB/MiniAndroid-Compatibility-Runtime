#!/usr/bin/env python3
"""S209b — extract the LAST coder comment (latest delivery) per key issue,
with diagnostics on every gh() failure."""
import json, subprocess, sys, time
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s209')

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def gh(url):
    r = subprocess.run(["curl", "-s", "-m", "60",
                        "-H", f"Authorization: token {token()}",
                        "-H", "Accept: application/vnd.github+json",
                        url], capture_output=True, text=True)
    time.sleep(0.5)
    if r.returncode != 0 or not r.stdout.strip():
        print(f"   [gh] rc={r.returncode} empty stdout", file=sys.stderr)
        return None
    try:
        return json.loads(r.stdout)
    except Exception as e:
        print(f"   [gh] parse fail: {e} head={r.stdout[:120]!r}", file=sys.stderr)
        return None

def main():
    sweep = json.load(open(OUT / 's209_coder_sweep.json'))
    issues = {int(k): v for k, v in sweep['issues'].items()}
    out = {}
    for n in sorted(issues):
        v = issues[n]
        if v.get('total', 0) == 0:
            continue
        pages = (v['total'] + 99) // 100
        cs = gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100&page={pages}")
        if not isinstance(cs, list):
            print(f"#{n}: FETCH-FAIL page={pages}")
            continue
        coders = [c for c in cs if c.get('user', {}).get('login') != 'Sh-TB']
        if not coders:
            # fall back: scan all pages
            allc = []
            for pg in range(1, pages + 1):
                b = gh(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100&page={pg}")
                if isinstance(b, list):
                    allc.extend(b)
            coders = [c for c in allc if c.get('user', {}).get('login') != 'Sh-TB']
            if not coders:
                print(f"#{n}: no coder comments at all")
                continue
        last = coders[-1]
        out[n] = {'id': last['id'], 'user': last['user']['login'],
                  'at': last['created_at'], 'len': len(last['body']),
                  'body': last['body']}
        print(f"#{n}: last-coder c={last['id']} by={last['user']['login']} "
              f"at={last['created_at']} len={len(last['body'])}")
        print(f"   head: {last['body'][:200].replace(chr(10), ' | ')}")
    (OUT / 's209_last_coder_deliveries.json').write_text(json.dumps(out, indent=1))
    print(f"saved {len(out)} deliveries")

if __name__ == "__main__":
    main()
