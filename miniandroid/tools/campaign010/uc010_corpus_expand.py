#!/usr/bin/env python3
"""CAMPAIGN 010 R23 — corpus expansion toward 30+ real APKs.
Adds diverse-category F-Droid APKs (WebView / RTL / Compose-M3 / lists /
settings) to the EXTERNAL cache. Zero binaries in the repo — registry only.
"""
import json, os, subprocess, hashlib, sys

CACHE = os.path.expanduser("~/.cache/miniandroid/apks")
os.makedirs(CACHE, exist_ok=True)

# (name, package, category, note)
NEW = [
    ("klar",            "org.mozilla.klar",                     "webview",     "WebView browser ( GeckoView fallback? no — WebView-based Klar )"),
    ("persiancalendar", "com.byagowi.persiancalendar",          "rtl",         "Persian/RTL calendar app (Material, RTL-first)"),
    ("kvaesitso",       "de.mm20.launcher2.release",            "compose_m3",  "Compose Material3 launcher (heavy Compose)"),
    ("opentracks",      "de.dennisguse.opentracks",             "lists_stats", "RecyclerView/stats/settings-heavy tracker"),
    ("markor",          "net.gsantner.markor",                  "editor",      "text/Markdown editor (forms, dialogs)"),
    ("loophabit",       "org.isoron.uhabits",                   "database",    "Room/SQLite + custom views + reminders"),
]

REG_PATH = os.path.join(CACHE, "uc010_registry.json")
reg = []
if os.path.exists(REG_PATH):
    reg = json.load(open(REG_PATH))
have = {r["package"] for r in reg}

def fdroid_latest(package):
    url = f"https://f-droid.org/api/v1/packages/{package}"
    try:
        out = subprocess.run(["curl", "-sf", "--max-time", "30", url],
                             capture_output=True, text=True, timeout=40).stdout
        d = json.loads(out)
        return d.get("suggestedVersionCode"), d.get("suggestedVersionName")
    except Exception:
        return None, None

for name, pkg, cat, note in NEW:
    if pkg in have:
        print(f"[ave ] {name}")
        continue
    vc, vn = fdroid_latest(pkg)
    if not vc:
        print(f"[SKIP] {name}: no fdroid api result")
        continue
    url = f"https://f-droid.org/repo/{pkg}_{vc}.apk"
    out = os.path.join(CACHE, f"{pkg}_{vc}.apk")
    print(f"[get ] {name} vc{vc} ...", end=" ", flush=True)
    r = subprocess.run(["curl", "-sfL", "--max-time", "500", "-o", out, url], timeout=520)
    if r.returncode != 0 or not os.path.exists(out):
        print("FAIL")
        continue
    sha = hashlib.sha256(open(out, "rb").read()).hexdigest()
    sz = os.path.getsize(out)
    reg.append({
        "name": name, "package": pkg, "versionCode": vc, "versionName": vn,
        "category": cat, "note": note, "source": url,
        "sha256": sha, "size": sz, "file": os.path.basename(out),
    })
    print(f"ok {sz/1e6:.1f}MB sha16={sha[:16]}")
    with open(REG_PATH, "w") as f:
        json.dump(reg, f, indent=1)

with open(REG_PATH, "w") as f:
    json.dump(reg, f, indent=1)
print(f"\nregistry: {REG_PATH} entries={len(reg)}")
