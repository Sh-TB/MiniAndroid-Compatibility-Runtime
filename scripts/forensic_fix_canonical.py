#!/usr/bin/env python3
"""forensic_fix_canonical.py — close the R4/R10 FAILs found by the #365
forensic audit:

R4  eu.veldsoft.fish.rings had TWO canonical artifacts (stale S65 jpg + the
    S91 interactive GIF). Law: interactive titles get ONE GIF. Registry now
    points at the GIF; the stale jpg is removed.
R10 com.miniandroid.browser / com.miniandroid.browser.zai GIFs existed on
    disk (real S100 executions, README-linked) but had NO registry rows.
    They are registered here with the provenance recorded in
    docs/evidence/s100_browser/ (APK SHA ee3cc2e6..., 3-run deterministic).

Counts in ACHIEVEMENTS.md / README are synchronized (148 -> 150 titles).
"""
import hashlib, json, os, re

ROOT = "/home/z/my-project"
CAN = f"{ROOT}/docs/evidence/canonical"
REG = f"{CAN}/registry.json"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


reg = json.load(open(REG))
titles = reg["titles"]
by_pkg = {t["package"]: t for t in titles}

# --- R4: fish.rings -> GIF as the ONE canonical artifact -------------------
fish = by_pkg["eu.veldsoft.fish.rings"]
gif_rel = "docs/evidence/canonical/eu.veldsoft.fish.rings.gif"
fish["artifact"] = gif_rel
fish["artifact_kind"] = ".gif"
fish["artifact_sha256"] = sha256(f"{ROOT}/{gif_rel}")
stale_jpg = f"{CAN}/eu.veldsoft.fish.rings.jpg"
if os.path.exists(stale_jpg):
    os.remove(stale_jpg)
    print("removed stale", stale_jpg)

# --- R10: register the two real S100 browser executions --------------------
if "com.miniandroid.browser" not in by_pkg:
    browser = {
        "id": "com.miniandroid.browser",
        "package": "com.miniandroid.browser",
        "title": "Mini Browser (example.com over TLS)",
        "type": "app",
        "status": "VERIFIED",
        "evidence_level": "E5",
        "source": "in-house source games/simple-browser/ (S100)",
        "session": "S100",
        "apk_sha256": "ee3cc2e6812c61801890c4d422b1c6d5e631fb69396231ed2327b0292bd350f3",
        "artifact": "docs/evidence/canonical/com.miniandroid.browser.gif",
        "artifact_kind": ".gif",
        "artifact_sha256": sha256(f"{ROOT}/docs/evidence/canonical/com.miniandroid.browser.gif"),
        "note": "Real HTTPS GET example.com (HTTP 200, 559 bytes), 12,087 px "
                "state change, 3/3 byte-identical runs (S100 runs 5-7).",
    }
    titles.append(browser)
    print("registered com.miniandroid.browser")

if "com.miniandroid.browser.zai" not in by_pkg:
    zai = {
        "id": "com.miniandroid.browser.zai",
        "package": "com.miniandroid.browser.zai",
        "title": "Mini Browser (z.ai 307 redirect over TLS)",
        "type": "app",
        "status": "VERIFIED",
        "evidence_level": "E5",
        "source": "in-house source games/simple-browser/ (S100 zai leg)",
        "session": "S100",
        "apk_sha256": "ee3cc2e6812c61801890c4d422b1c6d5e631fb69396231ed2327b0292bd350f3",
        "artifact": "docs/evidence/canonical/com.miniandroid.browser.zai.gif",
        "artifact_kind": ".gif",
        "artifact_sha256": sha256(f"{ROOT}/docs/evidence/canonical/com.miniandroid.browser.zai.gif"),
        "note": "Same simplebrowser APK (same SHA), z.ai target: 307 -> chat.z.ai "
                "redirect followed end-to-end over TLS, HTTP 200, 15,727 bytes "
                "(S102 HEADER-OWS-TRIM law).",
    }
    titles.append(zai)
    print("registered com.miniandroid.browser.zai")

reg["generated"] = "2026-10-03 forensic sync (issue #365 R4/R10 closure)"
json.dump(reg, open(REG, "w"), indent=1)
print("registry titles:", len(titles))

# --- CANONICAL_SCREENSHOTS.md rows ------------------------------------------
idx_path = f"{ROOT}/docs/evidence/CANONICAL_SCREENSHOTS.md"
body = open(idx_path, encoding="utf-8").read()
rows = []
if "`eu.veldsoft.fish.rings`" in body:
    body = body.replace(
        "[eu.veldsoft.fish.rings.jpg](docs/evidence/canonical/eu.veldsoft.fish.rings.jpg)",
        "[eu.veldsoft.fish.rings.gif](docs/evidence/canonical/eu.veldsoft.fish.rings.gif)")
    body = body.replace("eu.veldsoft.fish.rings.jpg", "eu.veldsoft.fish.rings.gif")
for pkg, title, gif in (
    ("com.miniandroid.browser", "Mini Browser", "com.miniandroid.browser.gif"),
    ("com.miniandroid.browser.zai", "Mini Browser z.ai", "com.miniandroid.browser.zai.gif"),
):
    if f"`{pkg}`" not in body:
        rows.append(f"| {title} | app | `{pkg}` | [in-house](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/tree/main/games/simple-browser) | — | [{gif}](docs/evidence/canonical/{gif}) | ee3cc2e6812c6180… | L10 | — | S100 |")
if rows:
    body = body.rstrip("\n") + "\n" + "\n".join(rows) + "\n"
open(idx_path, "w", encoding="utf-8").write(body)
print("CANONICAL_SCREENSHOTS.md updated; added", len(rows), "rows")

# --- ACHIEVEMENTS.md records (R11) + totals ---------------------------------
ach_path = f"{ROOT}/docs/ACHIEVEMENTS.md"
ach = open(ach_path, encoding="utf-8").read()
add = []
for pkg, title, gif, note in (
    ("com.miniandroid.browser", "Mini Browser", "com.miniandroid.browser.gif",
     "Real HTTPS GET example.com; 3/3 byte-identical; 12,087 px state change."),
    ("com.miniandroid.browser.zai", "Mini Browser z.ai", "com.miniandroid.browser.zai.gif",
     "307 redirect to chat.z.ai followed over TLS; 15,727 bytes rendered."),
):
    if pkg not in ach:
        add.append(f"\n## {title} (`{pkg}`)\n\n- Status: VERIFIED (E5, S100)\n- {note}\n- Canonical evidence: [GIF](evidence/canonical/{gif}) · session record [S100](evidence/s100_browser/README.md)\n")
if add:
    ach = ach.rstrip("\n") + "\n" + "\n".join(add) + "\n"
ach = ach.replace("Titles: **148** (87 games, 60 apps, 1 fixtures) — 33 added in S84",
                  "Titles: **150** (88 games, 61 apps, 1 fixtures) — 33 added in S84; 2 browser titles registered at forensic sync (#365)")
ach = ach.replace("- VERIFIED: **34** ·", "- VERIFIED: **36** ·")
ach = ach.replace("Canonical screenshots: **148** (12 GIF + 24 JPG)",
                  "Canonical screenshots: **150** (14 GIF + 24 JPG)")
open(ach_path, "w", encoding="utf-8").write(ach)
print("ACHIEVEMENTS.md synchronized")

# --- README count row --------------------------------------------------------
rm_path = f"{ROOT}/README.md"
rm = open(rm_path, encoding="utf-8").read()
rm = rm.replace("**148** (87 games · 60 apps · 1 fixture)", "**150** (88 games · 61 apps · 1 fixture)")
open(rm_path, "w", encoding="utf-8").write(rm)
print("README synchronized")
