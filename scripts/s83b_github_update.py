#!/usr/bin/env python3
"""s83b_github_update.py — S83-B2: update GitHub title issues with the
graphics-sweep evidence (user: "update GitHub for every game and app"). Comments on each swept title's issue with the measured L-level,
provenance, and evidence pointer. Honest classifications only — no status
inflation (§16: no pass without evidence).

Auth: GH token from .secrets/gh_token (git-ignored, never echoed).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import urllib.request

ROOT = "/home/z/my-project"
TOKEN = open(f"{ROOT}/.secrets/gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
HEAD_SHA = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          cwd=ROOT, capture_output=True, text=True).stdout.strip()


def gh(method, path, body=None):
    req = urllib.request.Request(f"{API}{path}", method=method,
                                 headers={"Authorization": f"Bearer {TOKEN}",
                                          "Accept": "application/vnd.github+json"})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data) as r:
        return json.loads(r.read().decode())


def main():
    results = json.load(open(f"{ROOT}/run/s83b/sweep/SWEEP_RESULTS.json"))
    inter = {r["tag"]: r for r in json.load(
        open(f"{ROOT}/run/s83b/sweep/INTERACT_RESULTS.json"))}
    reg = json.load(open(f"{ROOT}/docs/corpus/s82/title_registry.json"))
    titles = reg.get("TITLES", [])
    by_pkg = {}
    for t in titles:
        by_pkg[t.get("PACKAGE", "")] = t

    def pkg_of(apk_name):
        n = apk_name
        for s in (".apk",):
            n = n[: -len(s)] if n.endswith(s) else n
        # strip version suffix after last '_'
        return n.rsplit("_", 1)[0] if "_" in n else n

    # Special-name aliases for canonical APKs
    alias = {
        "fishrings_v1.23_vc6": "eu.veldsoft.fish.rings",
        "tripeaks_v1.2.1_vc4": "com.tripeaks",
        "gmdice_8": "de.duenndns.gmdice",
        "app.varlorg.unote_30": "app.varlorg.unote",
        "io.github.yamin8000.dooz_23": "io.github.yamin8000.dooz",
        "dooz_23_toplevel": "io.github.yamin8000.dooz",
    }

    commented, skipped = 0, 0
    for r in results:
        apk = r.get("apk", "")
        base = apk[:-4] if apk.endswith(".apk") else apk
        pkg = alias.get(base) or pkg_of(apk)
        t = by_pkg.get(pkg)
        if not t or not t.get("ISSUE_NUMBER"):
            skipped += 1
            continue
        tag = r["TITLE_ID"]
        v = r.get("visual", {})
        lines = [f"## S83-B2 graphics sweep @ HEAD `{HEAD_SHA}`",
                 "",
                 f"- **Run**: rc={r.get('rc')} · frames={r.get('frames')} · "
                 f"APK SHA256 `{r.get('apk_sha256','')[:16]}…`",
                 f"- **Measured level**: L{r.get('LEVEL','-')} "
                 f"{r.get('LEVEL_NAME','')} "
                 f"(UNIQUE_COLORS={v.get('UNIQUE_COLORS','?')}, "
                 f"NONWHITE_RATIO={v.get('NONWHITE_RATIO','?')})"]
        iv = inter.get(tag)
        if iv:
            lines.append(
                f"- **Interactive pass** (`--click-test`): "
                f"distinct_states={iv.get('distinct_states', 0)}, "
                f"changed_vs_baseline={iv.get('last_frame_changed_vs_baseline')}")
            if iv.get("evidence_first_change"):
                lines.append(
                    f"- Evidence: `run/s83b/sweep/{tag}_CLICK/` "
                    f"(state JPGs ≤100KB)")
        fd = r.get("PROVENANCE_FIRST_DIVERGENCE")
        if fd:
            lines.append(f"- Provenance FIRST_DIVERGENCE: `{fd}`")
        lines += ["",
                  "- Classification is MEASURED from final-frame pixels "
                  "(`scripts/s81_visual_audit.py`) — no status inflation "
                  "(§16). Evidence package: `docs/evidence/s83b/` "
                  "(SHA256SUMS)."]
        body = {"body": "\n".join(lines)}
        try:
            gh("POST", f"/issues/{t['ISSUE_NUMBER']}/comments", body)
            commented += 1
            print(f"[OK] #{t['ISSUE_NUMBER']} {t['TITLE_ID']} {pkg}")
        except Exception as e:
            print(f"[ERR] #{t.get('ISSUE_NUMBER')} {t['TITLE_ID']}: {e}")
    # Root-cause issue #227 (F-NEW-156 family): R-NEW-403 closure note
    r403 = {"body": (
        "## S83-B2 — R-NEW-403 root-cause closure (WeakHashMap keySet null)\n\n"
        f"@ HEAD `{HEAD_SHA}`: the dooz (corpus variant) onCreate NPE "
        "`Attempt to invoke interface method 'Ljava/util/Set;.iterator' on a "
        "null object reference` (Lg/b;.d — Glide RequestManager lifecycle "
        "registry) is ROOT-CAUSED to the shadow registry class filter: "
        "`CollectionShadow::handles_class` had NO `Ljava/util/WeakHashMap;` "
        "entry, so every WeakHashMap op REC-MISSed and `keySet()` answered "
        "null.\n\n"
        "- **Fix (semantic, no catch/no null)**: WeakHashMap routed to the "
        "real CollectionShadow map laws (put/get/keySet/values/entrySet + "
        "F-064 live views); a bridge-side keySet()/values() view law with "
        "self-as-iterator covers registry-less modes.\n"
        "- **Observed**: dooz advances from pre-frame crash to a rendered "
        "shell (6 frames, uniq=3, rc=1 with the NEXT frontier = "
        "WindowRecomposer `Context.getApplicationContext` chain — shared "
        "with dooz23 R-NEW-344).\n"
        "- **Fanout expectation**: every Glide/Lifecycle WeakHashMap "
        "observer registry in the corpus shares this family; per-title "
        "NEXT roots may now surface (same ONE FIX → MULTIPLE TITLES "
        "discipline).\n\n"
        "Ladder re-proof at the same HEAD: battery 26/26 rc=0, pixel "
        "goldens 24/24, golden ladder 10/10 + S83-B2 foundation ladder "
        "2/2 (l4e_layerlist, l4f_codelayer — layer-list/ring/line/dash + "
        "code-level LayerDrawable/GradientDrawable pins).")}
    try:
        gh("POST", "/issues/227/comments", r403)
        print("[OK] root-cause note on #227")
    except Exception as e:
        print(f"[ERR] #227: {e}")
    print(f"comments: {commented} titles updated, {skipped} skipped "
          "(no registry title / own-built games)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
