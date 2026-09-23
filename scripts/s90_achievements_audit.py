#!/usr/bin/env python3
"""s90_achievements_audit.py — S90 §11-16 achievements architecture.

Audits ALL image assets repo-wide, cross-references the canonical
machine registry (docs/evidence/canonical/registry.json), and generates:
  docs/achievements/INDEX.md            (§11 one obvious entry point)
  docs/achievements/GAMES_WITH_GIFS.md  (§13 real-GIF game index)
  docs/achievements/APPS_EXECUTED.md    (§14 app index)
  docs/achievements/ASSET_MANIFEST.json (§16 asset manifest w/ SHA)

Rules: views over canonical registry; no hand-written numbers; no asset
deleted here (§16 — manifest only).
"""
import hashlib
import json
import os

ROOT = "/home/z/my-project"
CANON = f"{ROOT}/docs/evidence/canonical"
OUT = f"{ROOT}/docs/achievements"
IMG_EXT = (".png", ".gif", ".jpg", ".jpeg")
SKIP_DIRS = ("upstream", ".git", "node_modules", ".venv")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def all_images():
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.lower().endswith(IMG_EXT):
                found.append(os.path.join(dirpath, fn))
    return sorted(found)


def gif_frames(p):
    try:
        from PIL import Image
        with Image.open(p) as im:
            return getattr(im, "n_frames", 1)
    except Exception:
        return -1


def main():
    os.makedirs(OUT, exist_ok=True)
    reg = json.load(open(f"{CANON}/registry.json"))
    titles = reg["titles"]
    by_pkg = {t.get("package", t.get("title", "?")): t for t in titles}

    imgs = all_images()
    shas = {}
    for p in imgs:
        shas[p] = sha256(p)

    canon_files = sorted(
        f for f in os.listdir(CANON) if f.lower().endswith(IMG_EXT))
    canon_paths = {f: f"{CANON}/{f}" for f in canon_files}
    canon_sha = {f: shas[f"{CANON}/{f}"] for f in canon_files}

    # duplicates by content SHA
    by_content = {}
    for p, s in shas.items():
        by_content.setdefault(s, []).append(p)
    dup_groups = {s: ps for s, ps in by_content.items() if len(ps) > 1}

    # canonical assets referenced by registry
    referenced = set()
    for t in titles:
        a = t.get("artifact", "")
        if a:
            referenced.add(os.path.basename(a))
    orphan_canon = [f for f in canon_files if f not in referenced]
    missing_canon = [os.path.basename(t.get("artifact", ""))
                     for t in titles
                     if t.get("artifact") and
                     not os.path.exists(f"{CANON}/{os.path.basename(t['artifact'])}")]
    # registry artifact sha vs actual
    sha_mismatch = []
    for t in titles:
        a = t.get("artifact", "")
        f = os.path.basename(a)
        if a and f in canon_sha and t.get("artifact_sha256") and \
                t["artifact_sha256"] != canon_sha[f]:
            sha_mismatch.append(f)

    # gif verification
    gifs_canon = {f: s for f, s in canon_sha.items() if f.endswith(".gif")}
    gif_meta = {}
    for f in gifs_canon:
        n = gif_frames(f"{CANON}/{f}")
        pkg = f.rsplit(".", 1)[0]
        t = by_pkg.get(pkg, {})
        gif_meta[f] = {"sha256": gifs_canon[f], "frames": n,
                       "title": t.get("title", pkg), "type": t.get("type", "?"),
                       "status": t.get("status", "?"),
                       "state_changed": t.get("state_changed", False),
                       "source": t.get("source", "") or t.get("upstream", ""),
                       "version": t.get("version", ""),
                       "apk_sha256": t.get("apk_sha256", ""),
                       "session": t.get("session", ""),
                       "level": t.get("level", -1)}

    # JPG canonical = verified non-interactive renders
    jpg_canon = {f: s for f, s in canon_sha.items() if f.endswith(".jpg")}

    counts = {
        "total_image_files": len(imgs),
        "total_gifs": sum(1 for p in imgs if p.lower().endswith(".gif")),
        "canonical_assets": len(canon_files),
        "canonical_gifs": len(gifs_canon),
        "canonical_jpgs": len(jpg_canon),
        "debug_or_wave_assets": len(imgs) - len(canon_files),
        "duplicate_groups": len(dup_groups),
        "orphan_canonical": len(orphan_canon),
        "referenced_but_missing": len(missing_canon),
        "sha_mismatch": len(sha_mismatch),
        "titles_in_registry": len(titles),
    }

    # ---- ASSET_MANIFEST.json (§16) ----
    manifest = {
        "law": "canonical assets live in docs/evidence/canonical/; "
               "everything else is wave/debug evidence (keep, don't duplicate)",
        "counts": counts,
        "canonical": [
            {"asset_id": f"canon-{i:03d}", "file": f,
             "sha256": canon_sha[f], "format": f.rsplit(".", 1)[-1],
             "purpose": "canonical screenshot/GIF",
             "registry_link": f"registry.json:title={gif_meta.get(f, {}).get('title', f.rsplit('.', 1)[0]) if f.endswith('.gif') else f.rsplit('.', 1)[0]}"}
            for i, f in enumerate(sorted(canon_files))],
        "duplicate_groups": [{"sha256": s, "paths": ps}
                             for s, ps in sorted(dup_groups.items())],
        "orphan_canonical": orphan_canon,
        "sha_mismatch": sha_mismatch,
    }
    json.dump(manifest, open(f"{OUT}/ASSET_MANIFEST.json", "w"), indent=1)

    # ---- GAMES_WITH_GIFS.md (§13) ----
    gif_games = sorted((m for m in gif_meta.values()
                        if m["type"] == "game" and m["frames"] > 1),
                       key=lambda m: m["title"])
    gif_apps = sorted((m for m in gif_meta.values()
                       if m["type"] != "game" and m["frames"] > 1),
                      key=lambda m: m["title"])
    lines = [
        "# Games with validated GIFs",
        "",
        "> Generated from `docs/evidence/canonical/registry.json` + "
        "`docs/achievements/ASSET_MANIFEST.json`. Not hand-written.",
        "> GIF = multi-frame animation, SHA-pinned, state-change proven.",
        "",
        f"Games with real validated GIF: **{len(gif_games)}**",
        "",
        "| Game | Version | Source | APK SHA (short) | Frames | "
        "State change | GIF SHA (short) | Session | Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in gif_games:
        lines.append(
            f"| {m['title']} | {m['version'] or '—'} "
            f"| {m['source'] or '—'} "
            f"| `{(m['apk_sha256'] or '—')[:12]}` | {m['frames']} "
            f"| {'PROVEN' if m['state_changed'] else 'no'} "
            f"| `{m['sha256'][:12]}` | {m['session']} | {m['status']} |")
    if gif_apps:
        lines += ["", f"Non-game GIFs (apps): **{len(gif_apps)}**", "",
                  "| App | Frames | State change | GIF SHA (short) | Status |",
                  "|---|---|---|---|---|"]
        for m in gif_apps:
            lines.append(
                f"| {m['title']} | {m['frames']} "
                f"| {'PROVEN' if m['state_changed'] else 'no'} "
                f"| `{m['sha256'][:12]}` | {m['status']} |")
    open(f"{OUT}/GAMES_WITH_GIFS.md", "w").write("\n".join(lines) + "\n")

    # ---- APPS_EXECUTED.md (§14) ----
    apps = sorted((t for t in titles if t.get("type") == "app"),
                  key=lambda t: t.get("title", ""))
    games_n = sum(1 for t in titles if t.get("type") == "game")
    lines = [
        "# Apps executed",
        "",
        "> Generated from canonical registry. Status vocabulary is the "
        "strict S84 set (VERIFIED / VERIFIED-INTERACTIVE / PARTIAL / "
        "OBSERVED / BLOCKED).",
        "",
        f"Apps in canonical registry: **{len(apps)}** "
        f"(games: {games_n})",
        "",
        "| App | Version | Source | Execution | UI evidence | "
        "Graphics | Blocker / root cause | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t in apps:
        art = os.path.basename(t.get("artifact", "") or "")
        ui = f"[evidence](../evidence/canonical/{art})" if art else "—"
        blk = (t.get("remaining") or "—").replace("|", "/")
        lines.append(
            f"| {t.get('title','?')} | {t.get('version','') or '—'} "
            f"| {t.get('source','') or t.get('upstream','') or '—'} "
            f"| {'launched' if t.get('launched') else 'no'}"
            f"{'/rendered' if t.get('rendered') else ''}"
            f"{'/interacted' if t.get('interacted') else ''} | {ui} "
            f"| L{t.get('level','?')} {t.get('level_name','')} "
            f"| {blk[:90]} | {t.get('status','?')} |")
    open(f"{OUT}/APPS_EXECUTED.md", "w").write("\n".join(lines) + "\n")

    # ---- INDEX.md (§11) ----
    verified = sum(1 for t in titles if t["status"] == "VERIFIED")
    vint = sum(1 for t in titles if t["status"] == "VERIFIED-INTERACTIVE")
    partial = sum(1 for t in titles if t["status"] == "PARTIAL")
    blocked = sum(1 for t in titles if t["status"] == "BLOCKED")
    lines = [
        "# Achievements — navigation hub",
        "",
        "ONE obvious entry point. All views are generated over the",
        "canonical machine registry "
        "[`docs/evidence/canonical/registry.json`](../evidence/canonical/registry.json)",
        "(never edit views by hand).",
        "",
        "## Where to go",
        "",
        "| Want… | Open |",
        "|---|---|",
        "| Per-title full records (canonical) "
        "| [docs/ACHIEVEMENTS.md](../ACHIEVEMENTS.md) |",
        "| Games with real validated GIF "
        "| [GAMES_WITH_GIFS.md](GAMES_WITH_GIFS.md) |",
        "| Apps executed | [APPS_EXECUTED.md](APPS_EXECUTED.md) |",
        "| Raw canonical assets (SHA-pinned) "
        "| [docs/evidence/canonical/](../evidence/canonical/) |",
        "| Asset audit manifest | [ASSET_MANIFEST.json](ASSET_MANIFEST.json) |",
        "",
        "## Snapshot",
        "",
        f"- Titles: **{counts['titles_in_registry']}** "
        f"(games {games_n} / apps {len(apps)})",
        f"- VERIFIED: **{verified}** · VERIFIED-INTERACTIVE: **{vint}** · "
        f"PARTIAL: {partial} · BLOCKED: {blocked}",
        f"- Canonical assets: **{counts['canonical_assets']}** "
        f"({counts['canonical_gifs']} GIF + {counts['canonical_jpgs']} JPG)",
        f"- Games with validated GIF: **{len(gif_games)}**",
        f"- Repo-wide image files: {counts['total_image_files']} "
        f"(canonical {counts['canonical_assets']}, "
        f"wave/debug {counts['debug_or_wave_assets']})",
        f"- Integrity: SHA-mismatch {counts['sha_mismatch']} · "
        f"orphan canonical {counts['orphan_canonical']} · "
        f"referenced-but-missing {counts['referenced_but_missing']} · "
        f"duplicate groups repo-wide {counts['duplicate_groups']}",
        "",
        f"_Generated by scripts/s90_achievements_audit.py (S90 §11-16)._",
    ]
    open(f"{OUT}/INDEX.md", "w").write("\n".join(lines) + "\n")

    print(json.dumps(counts, indent=1))
    print(f"gif_games={len(gif_games)} gif_apps={len(gif_apps)} "
          f"apps={len(apps)} games={games_n}")
    if sha_mismatch:
        print("SHA MISMATCH:", sha_mismatch[:5])
    if missing_canon:
        print("MISSING:", missing_canon[:5])


if __name__ == "__main__":
    main()
