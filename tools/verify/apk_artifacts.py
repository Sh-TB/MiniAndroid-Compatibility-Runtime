#!/usr/bin/env python3
"""Shared APK/DEX/ARSC artifact factory — ONE parse, MANY root queries.
Cache key: sha256(apk) + tool_version (speed-addendum §18).
Artifacts: artifacts/apk/<sha8>/ {zip_index.json, dex_index.json, arsc_summary.json,
manifest_badging.txt, artifact_manifest.json}
Tool output = EVIDENCE, not root-proof (brief §2)."""
import hashlib, json, os, struct, subprocess, sys, time, zipfile

TOOL_VERSION = "apk_artifacts/1.1"
HERE = os.path.dirname(os.path.abspath(__file__))            # <repo>/tools/verify
REPO = os.path.dirname(os.path.dirname(HERE))                # repo root

def _find_aapt2():
    """Resolution chain: MINIAAPT2 env → in-repo tools/aapt2 → bootstrap TOOLS dir → PATH.
    The toolchain binaries are NOT committed (scripts/bootstrap_toolchain.sh restores them
    at ${TOOLS:-/home/z/my-project/tools}); this chain is honest about where they live."""
    env = os.environ.get("MINIAAPT2")
    if env and os.path.exists(env):
        return env
    bootstrap = os.environ.get("MINITOOLS",
                               os.path.join(os.path.dirname(REPO), "tools"))
    for cand in (os.path.join(REPO, "tools", "aapt2", "aapt2"),
                 os.path.join(bootstrap, "aapt2", "aapt2")):
        if os.path.exists(cand):
            return cand
    return "aapt2"

AAPT2 = _find_aapt2()
OUT_BASE = os.environ.get("MINIARTIFACTS", os.path.join(REPO, "artifacts", "apk"))

def sha256_file(p, block=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()

def dex_header_index(data):
    """DEX header + index counts (spec: source/dexformat.html)."""
    if data[:4] != b"dex\n":
        return None
    def u32(off): return struct.unpack_from("<I", data, off)[0]
    def u4hex(off): return "0x%08x" % u32(off)
    return {
        "magic_ok": True, "checksum": u4hex(8), "header_size": u32(36),
        "endian_tag": u4hex(40), "link_size": u32(20),
        "string_ids_size": u32(56), "type_ids_size": u32(64),
        "proto_ids_size": u32(72), "field_ids_size": u32(80),
        "method_ids_size": u32(88), "class_defs_size": u32(96),
        "data_size": u32(104),
    }

def arsc_summary(data):
    """resources.arsc header summary (RES_TABLE_TYPE header)."""
    if len(data) < 12:
        return {"error": "arsc too small"}
    typ, hdr_sz, size = struct.unpack_from("<HHI", data, 0)
    pkg_count = struct.unpack_from("<I", data, 8)[0]
    return {"type": "0x%04x" % typ, "header_size": hdr_sz, "file_size": size,
            "package_count": pkg_count}

def build(apk_path, force=False):
    t0 = time.time()
    apk_sha = sha256_file(apk_path)
    key = hashlib.sha256((apk_sha + TOOL_VERSION).encode()).hexdigest()[:8]
    out = os.path.join(OUT_BASE, key)
    manifest = os.path.join(out, "artifact_manifest.json")
    if os.path.exists(manifest) and not force:
        with open(manifest) as f:
            prev = json.load(f)
        prev["cache"] = "HIT"
        return out, prev
    os.makedirs(out, exist_ok=True)
    arts = {}
    with zipfile.ZipFile(apk_path) as z:
        names = z.namelist()
        zip_index = [{"name": n, "size": i.file_size, "compressed": i.compress_size}
                     for n, i in zip(names, z.infolist())]
        json.dump(zip_index, open(os.path.join(out, "zip_index.json"), "w"), indent=0)
        arts["zip_entries"] = len(zip_index)
        dexes = [n for n in names if n.endswith(".dex")]
        dex_index = {}
        for d in dexes:
            h = dex_header_index(z.read(d))
            if h:
                h["classes"] = h["class_defs_size"]
                dex_index[d] = h
        json.dump(dex_index, open(os.path.join(out, "dex_index.json"), "w"), indent=1)
        arts["dex_files"] = len(dexes)
        arts["total_methods"] = sum(d["method_ids_size"] for d in dex_index.values())
        arts["total_classes"] = sum(d["class_defs_size"] for d in dex_index.values())
        if "resources.arsc" in names:
            s = arsc_summary(z.read("resources.arsc"))
            json.dump(s, open(os.path.join(out, "arsc_summary.json"), "w"), indent=1)
            arts["arsc"] = s
        arts["native_libs"] = [n for n in names if n.endswith(".so")]
    # manifest badging via the repo's own aapt2 (reuse, don't reinvent)
    badging = os.path.join(out, "manifest_badging.txt")
    r = subprocess.run([AAPT2, "dump", "badging", apk_path], capture_output=True, text=True, timeout=60)
    open(badging, "w").write(r.stdout if r.returncode == 0 else "aapt2 dump failed rc=%d" % r.returncode)
    arts["manifest_badging_ok"] = r.returncode == 0
    info = {"tool_version": TOOL_VERSION, "apk": os.path.basename(apk_path),
            "apk_sha256": apk_sha, "cache_key": key, "cache": "MISS",
            "artifacts": arts, "duration_ms": int((time.time() - t0) * 1000)}
    json.dump(info, open(manifest, "w"), indent=1)
    return out, info

if __name__ == "__main__":
    apk = sys.argv[1]
    out, info = build(apk, force="--force" in sys.argv)
    print(json.dumps({"artifact_dir": out, **info}, indent=1))
