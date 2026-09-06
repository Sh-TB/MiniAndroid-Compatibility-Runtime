#!/usr/bin/env bash
# g10_restore_corpus.sh — restore frozen download/ corpus cache, one APK per
# curl with individual timeout; SHA-256 verified against apks.json (the frozen
# manifest used by fetch_corpus.py). Known G09 CORPUS-DRIFT (OpenLauncher) and
# dead-URL (TinyMusicPlayer) entries are reported, not fatal.
set -u
python3 - <<'EOF'
import json, hashlib, subprocess, sys
from pathlib import Path
ROOT = Path("/home/z/my-project")
man = json.loads((ROOT/"MiniAndroid-Compatibility-Runtime/miniandroid/tests/corpus/apks.json").read_text())
okn = failn = driftn = 0
for e in man["apks"]:
    dest = ROOT / e["local_path"]
    want, url, name = e["sha256"], e.get("download_url",""), e["name"]
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == want:
        print(f"FOUND   {name}"); okn += 1; continue
    if not url:
        print(f"SKIP    {name} (no url)"); failn += 1; continue
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["curl","-sL","--max-time","90","-A","Mozilla/5.0","-o",str(dest),url],
                       capture_output=True)
    if r.returncode != 0 or not dest.exists():
        print(f"MISSING {name} (curl rc={r.returncode})"); failn += 1; continue
    got = hashlib.sha256(dest.read_bytes()).hexdigest()
    if got == want:
        print(f"OK      {name}"); okn += 1
    else:
        print(f"DRIFT   {name} want {want[:16]} got {got[:16]}"); driftn += 1
print(f"\nsummary: ok={okn} drift={driftn} missing={failn}")
EOF
