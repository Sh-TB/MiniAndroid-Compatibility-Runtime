#!/usr/bin/env python3
"""S124: fetch the ORIGINAL framework law sources for theme/template loading.

The user directive: search the internet, find how the ORIGINAL framework
loads app themes/templates, and build the runtime base on it.

Authoritative sources (AOSP frameworks/base, main branch):
  1. Resources.java       — Resources.Theme / ThemeImpl (applyStyle overlay law)
  2. ResourcesImpl.java   — Theme creation, getTheme
  3. LayoutInflater.java  — the XML template loading law (Factory/Factory2)
  4. AssetManager2.cpp    — ResolveAttribute (the 5-step resolution order)
  5. TypedArray.java      — obtainStyledAttributes consumer law
android.googlesource.com serves raw files base64-encoded via ?format=TEXT.
"""
import base64
import sys
import urllib.request

FILES = {
    "ResourcesImpl.java": "core/java/android/content/res/ResourcesImpl.java",
    "LayoutInflater.java": "core/java/android/view/LayoutInflater.java",
    "TypedArray.java": "core/java/android/content/res/TypedArray.java",
}
BASE = "https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/"

out_dir = "/tmp/s124_aosp"
import os
os.makedirs(out_dir, exist_ok=True)

for name, path in FILES.items():
    url = BASE + path + "?format=TEXT"
    try:
        raw = urllib.request.urlopen(url, timeout=60).read()
        text = base64.b64decode(raw).decode("utf-8", "replace")
        out = os.path.join(out_dir, name)
        with open(out, "w") as f:
            f.write(text)
        print(f"OK {name}: {len(text)} bytes -> {out}")
    except Exception as e:
        print(f"FAIL {name}: {e}", file=sys.stderr)

# AssetManager2.cpp lives in libs/androidfw
for name, path in {
    "AssetManager2.cpp": "libs/androidfw/AssetManager2.cpp",
    "AssetManager2.h": "include/androidfw/AssetManager2.h",
}.items():
    url = BASE + path + "?format=TEXT"
    try:
        raw = urllib.request.urlopen(url, timeout=60).read()
        text = base64.b64decode(raw).decode("utf-8", "replace")
        out = os.path.join(out_dir, name)
        with open(out, "w") as f:
            f.write(text)
        print(f"OK {name}: {len(text)} bytes -> {out}")
    except Exception as e:
        print(f"FAIL {name}: {e}", file=sys.stderr)
