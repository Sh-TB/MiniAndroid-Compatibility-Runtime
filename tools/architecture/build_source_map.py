#!/usr/bin/env python3
"""build_source_map.py — §3 SOURCE ↔ RUNTIME CROSS-REFERENCE builder.

For every pinned open-source corpus APK:
  * source file inventory (from the pinned tarball, upstream/PROVENANCE.json)
  * DEX class inventory (from docs/foundation/dex_census/<pkg>.json)
  * source class ↔ DEX class mapping (package-path name match; R8-obfuscated
    classes are recorded as UNMAPPED — honest, no guessing)
  * method → android-API edges (census method_apis)
  * API → MiniAndroid live status (api_calls.json status per call)
  * runtime evidence (status, frame nonwhite peaks, view-tree nodes)

Output: docs/foundation/source_map.json (§3 machine-readable index).
"""
import json
import re
import time
from pathlib import Path

ROOT = Path("/home/z/my-project")
UP = ROOT / "upstream" / "corpus"
CENSUS = ROOT / "docs" / "foundation" / "dex_census"
LIVE = ROOT / "docs" / "foundation" / "live_runs.json"
OUT = ROOT / "docs" / "foundation" / "source_map.json"

JAVA_EXT = {".java", ".kt"}


def source_inventory(pkg_dir: Path) -> list[dict]:
    """All source files under the extracted tarball root."""
    src_root = pkg_dir / "src"
    if not src_root.exists():
        return []
    files = []
    for p in src_root.rglob("*"):
        if p.is_file() and p.suffix in JAVA_EXT:
            rel = str(p.relative_to(src_root))
            files.append({"path": rel, "pkg_dir": str(p.parent.relative_to(src_root))})
    return files


def class_key_from_path(rel_path: str) -> str | None:
    """…/app/src/main/java/eu/veldsoft/fish/rings/GameActivity.java
       → Leu/veldsoft/fish/rings/GameActivity;
    Package root = after the LAST java/ or kotlin/ segment (gradle law)."""
    m = re.match(r"^(?P<dir>.*)/(?P<cls>[A-Za-z_$][A-Za-z0-9_$]*)\.(?:java|kt)$",
                 rel_path)
    if not m:
        return None
    segs = m.group("dir").split("/")
    last = None
    for i, s in enumerate(segs):
        if s in ("java", "kotlin"):
            last = i
    pkg = "/".join(segs[last + 1:]) if last is not None else m.group("dir")
    if not pkg:
        return None
    return f"L{pkg}/{m.group('cls')};"


def main():
    live = json.loads(LIVE.read_text())
    live_by_apk = {r["apk"]: r for r in live.get("runs", [])}

    apps = []
    for prov_path in sorted(UP.glob("*/PROVENANCE.json")):
        prov = json.loads(prov_path.read_text())
        pkg = prov["package"]
        pkg_dir = prov_path.parent
        entry = {
            "apk": prov["apk"],
            "package": pkg,
            "source_repo": prov["source_repo"],
            "source_commit": prov["source_commit"],
            "provenance": str(prov_path),
        }
        src_files = source_inventory(pkg_dir)
        entry["source_files"] = len(src_files)
        entry["source_root"] = str(pkg_dir / "src")

        census_path = None
        for c in CENSUS.glob(f"{pkg}.json"):
            census_path = c
        if census_path is None:
            for c in CENSUS.glob("*.json"):
                if c.name.startswith("_"):
                    continue
                data = json.loads(c.read_text())
                if data.get("package") == pkg:
                    census_path = c
                    break
        dex_classes = []
        method_apis = {}
        if census_path:
            data = json.loads(census_path.read_text())
            # rebuild app class list from method_apis keys (they only contain
            # app classes) — plus a lighter re-parse is unnecessary; record
            # the census file + counts
            entry["census"] = str(census_path)
            entry["app_classes"] = data["app_classes"]
            entry["app_methods"] = data["app_methods"]
            entry["api_call_sites"] = data["api_call_sites"]
            method_apis = data.get("method_apis", {})
            dex_classes = sorted({k.split("->")[0] for k in method_apis})

        # map source files → DEX class descriptors
        s2d = {}
        for f in src_files:
            key = class_key_from_path(f["path"])
            if key:
                s2d[f["path"]] = {"dex_class": key,
                                  "dex_class_present": key in set(dex_classes)}
        entry["source_to_dex"] = s2d
        mapped = sum(1 for v in s2d.values() if v["dex_class_present"])
        entry["classes_mapped"] = mapped
        entry["mapping_coverage"] = (round(mapped / len(dex_classes), 3)
                                     if dex_classes else None)
        entry["mapping_note"] = (
            "name-based package-path match; R8/ProGuard-obfuscated classes "
            "(short names like La1;) are UNMAPPED by design — recorded, not guessed")

        # per-app API edges with live status
        lr = live_by_apk.get(prov["apk"], {})
        api_calls_path = Path(lr["dir"]) / "api_calls.json" if lr.get("dir") else None
        live_status = {}
        if api_calls_path and api_calls_path.exists():
            for c in json.loads(api_calls_path.read_text()):
                key = f"{c['class']}.{c['method']}"
                live_status[key] = c["status"]
        entry["runtime_status"] = lr.get("status")
        entry["max_frame_nonwhite"] = lr.get("max_frame_nonwhite")
        entry["view_tree_nodes"] = lr.get("view_tree_nodes")
        # method-level: keep the app's own methods and their framework targets
        per_method = {}
        for mkey, apis in list(method_apis.items())[:400]:
            androids = [a for a in apis if a.startswith("Landroid/")]
            if not androids:
                continue
            per_method[mkey] = {
                "android_apis": sorted(set(androids))[:20],
                "live_status": [live_status.get(a, None) for a in
                                sorted(set(androids))[:20]],
            }
        entry["method_api_edges"] = per_method
        entry["method_api_edges_note"] = (
            "live_status: status of the API when the runtime ran this APK "
            "(IMPLEMENTED/STUBBED) — null when not reached at runtime")
        apps.append(entry)

    OUT.write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "law": "§3 source↔runtime cross-reference: source file ↔ DEX class ↔ "
               "android API ↔ runtime status ↔ frame evidence",
        "apps": apps,
    }, indent=1))
    for a in apps:
        print(f'{a["apk"][:36]:38} src={a.get("source_files",0):4} '
              f'mapped={a.get("classes_mapped",0):4}/{a.get("app_classes",0):4} '
              f'frame={a.get("max_frame_nonwhite")}')


if __name__ == "__main__":
    main()
