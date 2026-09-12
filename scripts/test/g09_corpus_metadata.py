#!/usr/bin/env python3
"""
scripts/test/g09_corpus_metadata.py — G09 Phase 1 corpus metadata freezer.

For every APK in the G09 corpus, extracts frozen metadata WITHOUT executing it:
  * package / versionCode / versionName          (aapt2 dump badging)
  * minSdk / targetSdk / application-label        (aapt2 dump badging)
  * launchable-activity + full activity list      (aapt2 dump xmltree manifest)
  * intent-filter actions per activity            (implicit-intent surface)
  * AppCompat / AndroidX / Compose / support-lib  (DEX string census)
  * setOnClickListener / setOnLongClickListener /
    android:onClick / setOnKeyListener census     (interaction surface)
  * APK SHA-256

Output: one JSON per APK under <out>/ + a combined g09_corpus_registry.json.
No APK binaries are written into the git repository (registry is metadata only).

Usage:
  python3 scripts/test/g09_corpus_metadata.py <apk> [<apk> ...] --out <dir> [--name ID=relpath,...]
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

AAPT2 = Path(__file__).resolve().parents[2] / "tools" / "aapt2" / "aapt2"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def aapt2_badging(apk: Path) -> dict:
    out = subprocess.run([str(AAPT2), "dump", "badging", str(apk)],
                         capture_output=True, text=True, timeout=120)
    info = {}
    for line in out.stdout.splitlines():
        if line.startswith("package:"):
            m = re.search(r"name='([^']*)'", line)
            info["package"] = m.group(1) if m else None
            m = re.search(r"versionCode='([^']*)'", line)
            info["versionCode"] = m.group(1) if m else None
            m = re.search(r"versionName='([^']*)'", line)
            info["versionName"] = m.group(1) if m else None
        elif line.startswith("minSdkVersion:"):
            info["minSdk"] = line.split(":", 1)[1].strip().strip("'")
        elif line.startswith("targetSdkVersion:"):
            info["targetSdk"] = line.split(":", 1)[1].strip().strip("'")
        elif line.startswith("application-label:"):
            info["label"] = line.split(":", 1)[1].strip().strip("'")
        elif line.startswith("launchable-activity:"):
            m = re.search(r"name='([^']*)'", line)
            info["launchable_activity"] = m.group(1) if m else None
        elif line.startswith("sdkVersion:"):
            info["compile_sdk"] = line.split(":", 1)[1].strip().strip("'")
    return info


def manifest_tree(apk: Path) -> dict:
    """Parse aapt2 xmltree of AndroidManifest.xml via an indentation-depth
    state machine → activities/services + intent-filter actions + app attrs."""
    out = subprocess.run(
        [str(AAPT2), "dump", "xmltree", "--file", "AndroidManifest.xml", str(apk)],
        capture_output=True, text=True, timeout=120)
    activities = []          # each: {name, exported, filters:[{actions,categories}]}
    app_attrs = {}
    elem_stack = []          # list of (depth, element_name, payload_dict)
    for raw in out.stdout.splitlines():
        if not raw.strip():
            continue
        em = re.match(r"^(\s*)E: ([\w.-]+) \(line=(\d+)\)", raw)
        if em:
            depth, elem = len(em.group(1)), em.group(2)
            while elem_stack and elem_stack[-1][0] >= depth:
                elem_stack.pop()
            payload = None
            if elem in ("activity", "activity-alias"):
                payload = {"kind": elem, "name": None, "exported": None,
                           "filters": [], "target": None}
                activities.append(payload)
            elif elem == "intent-filter":
                payload = {"kind": "intent-filter", "actions": [], "categories": []}
                for d, e, p in reversed(elem_stack):
                    if p and p.get("kind") in ("activity", "activity-alias"):
                        p["filters"].append(payload)
                        break
            elif elem in ("action", "category"):
                payload = {"kind": elem, "name": None}
            elem_stack.append((depth, elem, payload))
            continue
        line = raw.rstrip()
        am = re.match(r"^\s*A: .*:(?P<attr>[\w.]+)\(0x[0-9a-f]+\)=\(?\"?(?P<val>[^\")]*)", line)
        if am:
            attr, val = am.group("attr"), am.group("val")
        else:
            am2 = re.match(r"^\s*A: .*:(?P<attr>[\w.]+)\(0x[0-9a-f]+\)=.*", line)
            if not am2:
                continue
            attr, val = am2.group("attr"), ""
        # find owning element = innermost payload on the stack
        owner = None
        for d, e, p in reversed(elem_stack):
            if p is not None:
                owner = p
                break
        if owner is None:
            continue
        if owner.get("kind") in ("activity", "activity-alias"):
            if attr == "name" and owner["name"] is None:
                owner["name"] = val
            elif attr == "exported":
                owner["exported"] = ("true" if "0xffffffff" in line
                                     else ("false" if "0x00000000" in line else val))
        elif owner.get("kind") in ("action", "category") and attr == "name":
            owner["name"] = val
            # bubble up into the enclosing intent-filter
            for d, e, p in reversed(elem_stack):
                if p and p.get("kind") == "intent-filter":
                    (p["actions"] if owner["kind"] == "action"
                     else p["categories"]).append(val)
                    break
        elif owner.get("kind") == "activity-alias" and attr == "targetActivity":
            owner["target"] = val
    # application-level attrs of interest
    return {"activities": activities, "application_attrs": app_attrs}


def dex_census(apk: Path) -> dict:
    """String-level census across classes*.dex (binary substring scan)."""
    census = {
        "dex_files": 0,
        "appcompat": False, "androidx_core": False, "support_v7": False,
        "compose": False, "material": False,
        "set_on_click": False, "set_on_long_click": False,
        "start_activity": False, "start_activity_for_result": False,
        "set_result": False, "handler_postdelayed": False,
        "view_classes": [],
    }
    probes = {
        "appcompat": b"Landroidx/appcompat/",
        "androidx_core": b"Landroidx/core/",
        "support_v7": b"Landroid/support/v7/",
        "compose": b"Landroidx/compose/",
        "material": b"Lcom/google/android/material/",
        "set_on_click": b"setOnClickListener",
        "set_on_long_click": b"setOnLongClickListener",
        "start_activity": b"startActivity",
        "start_activity_for_result": b"startActivityForResult",
        "set_result": b"setResult",
        "handler_postdelayed": b"postDelayed",
    }
    view_probe = re.compile(rb"Landroid/widget/(Button|TextView|ImageView|CheckBox|"
                            rb"RadioButton|SeekBar|EditText|LinearLayout|FrameLayout|"
                            rb"GridLayout|ListView|GridView|Toast|ScrollView);")
    seen_views = set()
    try:
        with zipfile.ZipFile(apk) as z:
            dex_names = [n for n in z.namelist()
                         if re.match(r"classes\d*\.dex$", n)]
            census["dex_files"] = len(dex_names)
            for n in dex_names:
                blob = z.read(n)
                for key, probe in probes.items():
                    if probe in blob:
                        census[key] = True
                for m in view_probe.finditer(blob):
                    seen_views.add("android.widget." + m.group(1).decode())
    except Exception as e:  # noqa: BLE001
        census["error"] = str(e)
    census["view_classes"] = sorted(seen_views)
    return census


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("apks", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rel", default=None,
                    help="comma list ID=relative/path.apk recorded in registry")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    relmap = {}
    if args.rel:
        for pair in args.rel.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                relmap[k] = v

    registry = []
    for apk in args.apks:
        apk = Path(apk)
        if not apk.exists():
            print(f"MISSING {apk}", file=sys.stderr)
            continue
        entry = {
            "apk_file": apk.name,
            "sha256": sha256(apk),
            **aapt2_badging(apk),
        }
        tree = manifest_tree(apk)
        entry["activities"] = tree["activities"]
        entry["n_activities"] = len([a for a in tree["activities"] if a["name"]])
        dex = dex_census(apk)
        entry["dex"] = dex
        # classification per G09 §1
        entry["uses_appcompat"] = bool(dex["appcompat"] or dex["support_v7"])
        entry["uses_compose"] = bool(dex["compose"])
        entry["multi_activity"] = entry["n_activities"] > 1
        implicit = [a for a in tree["activities"]
                    for f in a["filters"]
                    if any(x not in ("android.intent.action.MAIN",
                                     "android.intent.action.VIEW")
                           for x in f["actions"])]
        entry["non_launcher_intent_filters"] = len(
            [f for a in tree["activities"] for f in a["filters"]])
        entry["interactive_surface"] = bool(
            dex["set_on_click"] or dex["set_on_long_click"])
        entry["result_api_surface"] = bool(
            dex["start_activity_for_result"] or dex["set_result"])
        outpath = outdir / f"{apk.stem}.meta.json"
        outpath.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
        registry.append(entry)
        print(f"META {apk.name}: pkg={entry.get('package')} "
              f"acts={entry['n_activities']} appcompat={entry['uses_appcompat']} "
              f"compose={entry['uses_compose']} interactive={entry['interactive_surface']}")
    regpath = outdir / "g09_corpus_registry.json"
    regpath.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    print(f"registry: {regpath} ({len(registry)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
