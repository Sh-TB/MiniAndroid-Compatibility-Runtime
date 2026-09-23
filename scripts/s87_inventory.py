#!/usr/bin/env python3
"""S87 PHASE 0+1 — RECON + ACHIEVEMENT INVENTORY.

COUNT -> MAP -> CLASSIFY -> SHOW THE REAL STATE. No guessing, no deletion.
Outputs: docs/audit/S87_INVENTORY.json + stdout summary.
"""
import json, os, hashlib, sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/home/z/my-project")
OUT = {"generated_by": "scripts/s87_inventory.py", "phase": "S87 PHASE0+1"}

IMG_EXTS = {".png": "PNG", ".jpg": "JPG", ".jpeg": "JPG", ".gif": "GIF",
            ".webp": "WebP", ".bmp": "BMP", ".ppm": "PPM", ".pbm": "PBM",
            ".pgm": "PGM", ".xbm": "XBM", ".svg": "SVG", ".ico": "ICO"}

def sha256(p, _cache={}):
    if p in _cache: return _cache[p]
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    _cache[p] = h.hexdigest()
    return _cache[p]

# ---------------------------------------------------------------- A. images
img_rows = []
for dp, dns, fns in os.walk(REPO):
    dns[:] = [d for d in dns if d not in (".git", "node_modules")]
    for fn in fns:
        p = Path(dp) / fn
        ext = p.suffix.lower()
        if ext in IMG_EXTS:
            try: size = p.stat().st_size
            except OSError: continue
            img_rows.append({"path": str(p.relative_to(REPO)), "ext": IMG_EXTS[ext],
                             "size": size, "sha256": sha256(p)})

img_census = {
    "total_images": len(img_rows),
    "total_bytes": sum(r["size"] for r in img_rows),
    "by_format": {},
    "duplicates_by_sha256": [],
    "dup_bytes_wasted": 0,
}
by_fmt = defaultdict(lambda: {"count": 0, "bytes": 0})
for r in img_rows:
    by_fmt[r["ext"]]["count"] += 1
    by_fmt[r["ext"]]["bytes"] += r["size"]
img_census["by_format"] = {k: v for k, v in sorted(by_fmt.items(),
                                               key=lambda kv: -kv[1]["count"])}

sha_groups = defaultdict(list)
for r in img_rows: sha_groups[r["sha256"]].append(r["path"])
for s, paths in sha_groups.items():
    if len(paths) > 1:
        img_census["duplicates_by_sha256"].append(
            {"sha256_16": s[:16], "copies": len(paths),
             "wasted_bytes": img_rows[[r["path"] for r in img_rows].index(paths[0])]["size"] * (len(paths) - 1),
             "paths": paths})
        img_census["dup_bytes_wasted"] += img_rows[[r["path"] for r in img_rows].index(paths[0])]["size"] * (len(paths) - 1)
img_census["dup_groups"] = len(img_census["duplicates_by_sha256"])
OUT["image_census"] = img_census

# near-duplicates (perceptual, only among JPG/PNG/GIF < 2MB, cheap 16x16 ahash)
try:
    from PIL import Image
    ahash = {}
    near = []
    small = [r for r in img_rows if r["ext"] in ("JPG", "PNG", "GIF") and r["size"] < 2_000_000]
    for r in small:
        try:
            im = Image.open(REPO / r["path"]).convert("L").resize((16, 16))
            px = list(im.getdata())
            avg = sum(px) / len(px)
            bits = "".join("1" if v > avg else "0" for v in px)
            ahash[r["path"]] = bits
        except Exception:
            pass
    keys = list(ahash)
    seen = set()
    for i, a in enumerate(keys):
        if a in seen: continue
        grp = [a]
        for b in keys[i + 1:]:
            if b in seen: continue
            if sum(x != y for x, y in zip(ahash[a], ahash[b])) <= 8:
                grp.append(b); seen.add(b)
        if len(grp) > 1:
            near.append({"paths": grp})
    OUT["near_duplicates"] = {"method": "16x16 ahash, hamming<=8", "groups": len(near),
                              "examples": near[:25]}
except Exception as e:
    OUT["near_duplicates"] = {"error": str(e)}

# ------------------------------------------------------- B. directory census
def dir_census(rel):
    d = REPO / rel
    if not d.is_dir(): return None
    files, nbytes, nimg, ibytes = 0, 0, 0, 0
    for dp, dns, fns in os.walk(d):
        for fn in fns:
            p = Path(dp) / fn
            try: s = p.stat().st_size
            except OSError: continue
            files += 1; nbytes += s
            if p.suffix.lower() in IMG_EXTS:
                nimg += 1; ibytes += s
    return {"path": rel, "files": files, "bytes": nbytes,
            "images": nimg, "image_bytes": ibytes}

census_targets = ["docs/evidence", "docs/audit", "docs/knowledge", "docs/history",
                  "docs/corpus", "docs/compatibility", "docs/upstream", "docs/assets",
                  "docs/demos", "docs/releases", "docs/agent-index", "docs/root-searchlight",
                  "evidence", "run", "upload", "fixtures", "games", "upstream",
                  "examples", "docs/evidence/canonical"]
OUT["directory_census"] = [c for c in (dir_census(t) for t in census_targets) if c]

# per-session dirs under docs/evidence
sess = []
for p in sorted((REPO / "docs/evidence").iterdir()):
    if p.is_dir():
        c = dir_census(str(p.relative_to(REPO)))
        c["purpose"] = "session evidence"
        sess.append(c)
OUT["evidence_session_dirs"] = sess

# ------------------------------------------------- C. registry/record systems
systems = []

def add_system(name, records, unique_titles, purpose, canonical):
    systems.append({"file": name, "records": records, "unique_titles": unique_titles,
                    "purpose": purpose, "canonical": canonical})

reg = json.load(open(REPO / "docs/evidence/canonical/registry.json"))
titles = reg["titles"]
pkgs = [t["package"] for t in titles]
dup_pkgs = [k for k, v in Counter(pkgs).items() if v > 1]
add_system("docs/evidence/canonical/registry.json", len(titles),
           len(set(pkgs)), "per-title canonical achievement registry (generated+validated)",
           "YES — SSoT per S84 law")

ach = (REPO / "docs/ACHIEVEMENTS.md").read_text(errors="replace")
h3 = [l[4:].strip() for l in ach.splitlines() if l.startswith("### ")]
add_system("docs/ACHIEVEMENTS.md", len(h3), len(set(h3)),
           "human-readable achievement page (generated from canonical registry.json)",
           "derived-canonical")

canon_md = (REPO / "docs/evidence/CANONICAL_SCREENSHOTS.md").read_text(errors="replace")
rows = [l for l in canon_md.splitlines() if l.startswith("| ") and "---" not in l] [1:]
add_system("docs/evidence/CANONICAL_SCREENSHOTS.md", len(rows), len(rows),
           "machine-checkable canonical screenshot index (generated)", "derived-canonical")

exec_ach = (REPO / "docs/EXECUTION_ACHIEVEMENTS.md").read_text(errors="replace")
add_system("docs/EXECUTION_ACHIEVEMENTS.md", 0, 0,
           "SUPERSEDED S54 pointer (no records)", "NO — superseded")

root_reg = json.load(open(REPO / "root_registry.json"))
add_system("root_registry.json", root_reg["total"], "n/a (R-NEW-* ids)",
           "runtime root-cause registry (not a title registry)", "different axis")

for extra, desc in [
    ("docs/evidence/CURRENT_COMPATIBILITY_MATRIX.md", "older compatibility matrix"),
    ("docs/evidence/SCREENSHOT_INDEX.md", "old screenshot index S-era"),
    ("docs/evidence/SCREENSHOT_INDEX_013.md", "old screenshot index 013"),
    ("docs/evidence/SCREENSHOT_INDEX_S51.md", "old screenshot index S51"),
    ("docs/compatibility/APP_COMPATIBILITY_REGISTRY.md", "compat registry"),
    ("docs/compatibility/EXECUTION_MATRIX.md", "execution matrix"),
    ("docs/compatibility/COMPATIBILITY_CLOSURE_MATRIX.md", "closure matrix"),
]:
    p = REPO / extra
    if p.exists():
        txt = p.read_text(errors="replace")
        n = sum(1 for l in txt.splitlines() if l.startswith("| ") and "---" not in l)
        n = max(n - 1, 0)
        add_system(extra, n, "?", desc, "NO — legacy/parallel")
OUT["registry_systems"] = systems

# ---------------------------------------------------- D. title-level mapping
fmt_counter = Counter()
for t in titles:
    art = t.get("artifact") or ""
    fmt_counter[Path(art).suffix.lower() if art else "(none)"] += 1

lvl = Counter(f"L{t.get('level')}" for t in titles)
stat = Counter(t.get("status") for t in titles)
typ = Counter(t.get("type") for t in titles)

def flag_sum(f): return sum(1 for t in titles if t.get(f))

titles_map = {
    "total_records": len(titles),
    "unique_packages": len(set(pkgs)),
    "duplicate_packages": dup_pkgs,
    "by_type": dict(typ),
    "by_level": dict(sorted(lvl.items(), key=lambda kv: int(kv[0][1:]))),
    "by_status": dict(stat),
    "flags": {"launched": flag_sum("launched"), "rendered": flag_sum("rendered"),
              "interacted": flag_sum("interacted"), "state_changed": flag_sum("state_changed")},
    "with_canonical_artifact": sum(1 for t in titles if t.get("artifact")),
    "artifact_formats": dict(fmt_counter),
    "with_apk_sha256": sum(1 for t in titles if t.get("apk_sha256")),
    "with_source_link": sum(1 for t in titles if t.get("source") or t.get("upstream")),
    "without_achievement_text": sum(1 for t in titles if not t.get("proven")),
    "artifact_kinds": dict(Counter(t.get("artifact_kind") or "(none)" for t in titles)),
}
OUT["titles"] = titles_map

# artifact files on disk vs registry (registry + SHA256SUMS use repo-relative paths)
canon_dir = REPO / "docs/evidence/canonical"
disk_artifacts = {str(p.relative_to(REPO)) for p in canon_dir.iterdir()
                  if p.suffix.lower() in IMG_EXTS}
reg_artifacts = {t["artifact"] for t in titles if t.get("artifact")}
OUT["artifact_consistency"] = {
    "on_disk": len(disk_artifacts), "in_registry": len(reg_artifacts),
    "on_disk_not_in_registry": sorted(disk_artifacts - reg_artifacts),
    "in_registry_missing_on_disk": sorted(reg_artifacts - disk_artifacts),
}

# SHA verification of canonical artifacts
sums_file = canon_dir / "SHA256SUMS"
sha_ok, sha_bad, sha_missing = 0, [], []
if sums_file.exists():
    for line in sums_file.read_text().splitlines():
        if not line.strip(): continue
        h, _, name = line.partition(" ")
        name = name.strip().lstrip("*")
        p = REPO / name
        if not p.exists(): sha_missing.append(name); continue
        if sha256(p) == h.strip(): sha_ok += 1
        else: sha_bad.append(name)
    OUT["canonical_sha_verification"] = {"pinned": sha_ok + len(sha_bad) + len(sha_missing),
                                         "ok": sha_ok, "bad": sha_bad, "missing_on_disk": sha_missing}

# registry artifact_sha256 vs disk
mismatch = []
for t in titles:
    a = t.get("artifact"); h = t.get("artifact_sha256")
    if a and h and (REPO / a).exists():
        if not sha256(REPO / a).startswith(h[:16]):
            mismatch.append(a)
OUT["registry_sha_mismatches"] = mismatch

# ------------------------------------------- E. executed-but-unrecorded scan
executed_pkgs = set()
import re
pkg_re = re.compile(r"(?:apps|games)__([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)_\d+__L\d+|([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)_\d+__L\d+")
for dp, dns, fns in os.walk(REPO / "docs/evidence"):
    for fn in fns:
        m = pkg_re.search(fn)
        if m: executed_pkgs.add(m.group(1) or m.group(2))
reg_pkgs = set(pkgs) | {t["title"] for t in titles}
OUT["executed_vs_recorded"] = {
    "executed_pkgs_seen_in_evidence_filenames": len(executed_pkgs),
    "executed_not_in_registry": sorted(executed_pkgs - reg_pkgs)[:80],
    "count_executed_not_in_registry": len(executed_pkgs - reg_pkgs),
}

# ------------------------------------------------------- F. orphan analysis
md_texts = []
for dp, dns, fns in os.walk(REPO):
    dns[:] = [d for d in dns if d != ".git"]
    for fn in fns:
        if fn.endswith((".md", ".json", ".py", ".html")):
            try: md_texts.append((str(Path(dp).relative_to(REPO) / fn),
                                  (Path(dp) / fn).read_text(errors="replace")))
            except OSError: pass

def refcount(name):
    base = os.path.basename(name)
    c = 0; where = []
    for path, txt in md_texts:
        if base in txt:
            c += 1; where.append(path)
    return c, where[:5]

orphans, multi_ref = [], []
for r in img_rows:
    rc, where = refcount(r["path"])
    if rc == 0: orphans.append(r["path"])
    elif rc > 1: multi_ref.append({"path": r["path"], "refs": rc, "where": where})
OUT["orphan_images"] = {"count": len(orphans),
                        "under_docs_evidence": sum(1 for o in orphans if o.startswith("docs/evidence")),
                        "examples": orphans[:40]}
OUT["multi_referenced_images"] = {"count": len(multi_ref), "examples": multi_ref[:15]}

# GIF frame counts (canonical GIFs only, keep cheap)
gif_frames = {}
try:
    from PIL import Image
    for r in img_rows:
        if r["ext"] == "GIF" and r["size"] < 1_500_000:
            try:
                with Image.open(REPO / r["path"]) as im:
                    gif_frames[r["path"]] = getattr(im, "n_frames", 1)
            except Exception: pass
except Exception: pass
OUT["gif_frames"] = gif_frames

# --------------------------------------------------------------- write out
os.makedirs(REPO / "docs/audit", exist_ok=True)
with open(REPO / "docs/audit/S87_INVENTORY.json", "w") as f:
    json.dump(OUT, f, indent=1)

# --------------------------------------------------------------- summary
print("=" * 62)
print("S87 INVENTORY SUMMARY")
print("=" * 62)
print(f"images total: {img_census['total_images']}  ({img_census['total_bytes']/1e6:.1f} MB)")
for k, v in img_census["by_format"].items():
    print(f"  {k:5s} {v['count']:5d}  {v['bytes']/1e6:9.2f} MB")
print(f"dup groups: {img_census['dup_groups']}  wasted: {img_census['dup_bytes_wasted']/1e6:.2f} MB")
print(f"near-dup groups: {OUT['near_duplicates'].get('groups')}")
print("-" * 62)
for s in systems:
    print(f"{s['file']:60s} rec={s['records']:4d} uniq={s['unique_titles']!s:4s} canon={s['canonical']}")
print("-" * 62)
print(json.dumps(titles_map, indent=1)[:2000])
print("-" * 62)
print("artifact consistency:", json.dumps(OUT["artifact_consistency"]))
print("sha verification:", json.dumps(OUT.get("canonical_sha_verification", {})))
print("registry sha mismatches:", mismatch)
print("executed-not-recorded:", OUT["executed_vs_recorded"]["count_executed_not_in_registry"],
      OUT["executed_vs_recorded"]["executed_not_in_registry"][:25])
print("orphan images:", OUT["orphan_images"]["count"],
      "(docs/evidence:", OUT["orphan_images"]["under_docs_evidence"], ")")
print("multi-referenced:", OUT["multi_referenced_images"]["count"])
print("gif frames:", json.dumps(gif_frames))
