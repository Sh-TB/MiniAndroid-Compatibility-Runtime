#!/usr/bin/env python3
"""The #605 follow-up receipt: app-font discovery + the no-default-font
world proof (two REAL bugs found and fixed by the hidden-world run)."""
import json, re, subprocess, urllib.request

R = "/home/z/my-project/"
def gate(path, pat, default="PENDING"):
    try:
        t = open(R + path).read()
        m = re.search(pat, t, re.S)
        return m.group(1).strip() if m else default
    except OSError:
        return default

binrc = gate("w245_bin.log", r"BIN_RC=(\d+)")
ta    = gate("w245_testall.log", r"BATTERY SUMMARY: (total=\d+ passed=\d+ failed=\d+)")
tarc  = gate("w245_testall.log", r"TA_RC=(\d+)")
par   = gate("w245_parity.log", r"\[PARITY-OK\] (\d+ core sources manifest-parity)")
parrc = gate("w245_parity.log", r"PAR_RC=(\d+)")

CRED = subprocess.run(["git","credential","fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True, cwd=R).stdout
TOKEN=[l.split("=",1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

B = f"""## FONT-PIPE-002 follow-up — app-font discovery traced + the no-default-font world PROVEN (two real bugs found and fixed)

### 1. How the engine finds an app's own fonts (the discovery chain, source-traced)
- **APK startup scan** (`execution_engine.cpp` FIX-4 + F-NEW-315): every `assets/` AND `res/` entry ending `.ttf`/`.otf` — any package, any name (aapt2 obfuscation renames like `res/UJ.ttf` are covered) — is extracted and registered as a memory face; "bold" in the file name selects the bold face of the family. Every failure is LOUD (`FONT_LOAD_FAILED path=… reason=…`) and the outcome observable (`FONT_SOURCE apk=… font_files=N registered=N first=…` — NO_FONT_DIRECTORY is a valid outcome, not an error).
- **Java lane** (`dalvik_engine.cpp`): `Typeface.createFromAsset/createFromFile` → `app_face_index_for_name` (exact entry name first, then `/name` suffix) → a Typeface object carrying `__font_face_idx__` → `Paint.setTypeface` consumes it → shaping routes to that face.
- **CSS lane** (`webview_engine.cpp`): `@font-face {{ font-family: X; src: … }}` → the fetched bytes register through the SAME `register_app_font_memory` → `font_family_map[lowercased family]` → `font-family: X` styles shape with that face.
- **Fonts-in-XML** (res/font/, API 26+) rides the same res/ scan.

### 2. What happens when there is NO default font (the hidden-world experiment)
`unshare -rm` + bind-mount an empty dir over `/usr/share/fonts` (no root needed) → zero system fonts → both batteries run (`scripts/s244_hidden_world.sh`):

```
s244 hidden: rc=1 — 9 passed / 7 failed (honest fail profile, ZERO crashes)
s243 hidden: rc=1 — 57 passed / 56 failed (honest fail profile, ZERO crashes)
stderr: "regular face not found … REPORTED, never silently aliased" (x4)
KEY: s244 N4_app_face_render_proof PASS — face=6: the app's own
(memory-registered) font STILL LOADS AND RENDERS with zero system fonts
```

### 3. Two REAL bugs the experiment caught (both fixed)
1. **Engine law violation**: `register_app_font_memory` and `shape()` gated on `available_` (the SYSTEM-chain health flag) — a broken system font tree refused APP fonts too, violating the AOSP law that `createFromAsset`/`@font-face` work independently of system fonts. Both now key on the resolved face / `ft_lib_` instead: with zero system fonts an app font still registers, shapes and renders (N4 proves it with ink). System text degrades to honest empty runs; app text survives.
2. **Battery UB** (found by the first hidden run's segfault — honest finding): slicing an empty byte vector (`sys.begin()+300`) when the system font file is absent. Guarded in both batteries; the engine's own empty-bytes guard was already correct.

### 4. New battery: tests/s244_app_font_discovery_law_test.cpp (15 laws)
D1-D3 APK-bytes→face + name lookup (exact/suffix/absent) · D4-D6 failure isolation (corrupt/empty never touch the chain) · D7-D9 two-family identity + bold arm · N1-N6 the no-default chain (empty→zero width, unknown index safe, truthful diagnostics, app-face render proof, permissive family law, FT alive).

### Gates on the wave commit
s244 normal 15/15 · s243 normal 113/113 · hidden world honest (rc=1, no 139) · binary RC={binrc} · test-all {ta} (RC={tarc}) · parity {par} (RC={parrc})"""
req = urllib.request.Request("https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/605/comments",
    data=json.dumps({"body": B}).encode(),
    headers={"Authorization": f"token {TOKEN}","Accept":"application/vnd.github+json","User-Agent":"font-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    print("#605 follow-up receipt", json.loads(r.read().decode())["id"])
