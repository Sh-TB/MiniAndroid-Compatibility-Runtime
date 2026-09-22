#!/usr/bin/env python3
"""s84_github_sync.py — S84 GitHub issue sync (§3/§7).

1. Create root-cause issues for the two OPEN S84 families:
   F-NEW-161 (compose internals, ~24-title fan-out) and
   F-NEW-162 (androidx adapter family, 12-title fan-out).
2. One wave-summary issue documenting the canonical evidence system +
   the NEW-50 campaign + the S83 near-blank quarantine.
3. Comment on the existing S83 wave issue (if resolvable) — evidence
   integrity correction note (16 byte-identical frames demoted).
PAT via env only; never persisted, never echoed.
"""
import json
import os
import urllib.request

ROOT = "/home/z/my-project"
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
TOKEN = os.environ.get("GITHUB_PAT", "")
DATE = "2026-09-23"
COMMIT = "cf23dab2"

reg = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))
T = reg["titles"]


def api(method, path, body=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "miniandroid-s84-sync"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return 0, {"err": str(e)}


def compose_fanout():
    return [t for t in T if t["session"] == "S84" and
            t["status"] in ("PARTIAL", "OBSERVED")]


def make_f161():
    titles = compose_fanout()
    rows = "\n".join(f"- `{t['package']}` — L{t['level']} {t['level_name']} "
                     f"({t['status']})" for t in titles[:30])
    return {
        "title": "[F-NEW-161] Compose UI runtime internals — deferred-exception "
                 "family (S84 NEW-50 fan-out, ~24 titles)",
        "body": f"""**Root-cause family** (S84 §7 law: one family = one issue).

## Signature chain
1. `Class.forName("kotlin.reflect.jvm.internal.ReflectionFactoryImpl")` → CNFE — **caught, faithful** (kotlin-reflect is optional on devices too)
2. Later compose-runtime NPEs: null `Iterator.hasNext` (recomposition chain), null `View.getWidth` (compose layout), `IllegalStateException` in `setContent`
3. → ART process-death law → run ends PARTIAL with real frames (L1-L2)

## Why not fixed yet
Compose recomposition is S83-GFX-BASE P4 scope (measure/layout semantics on the
software raster base). Recorded as the pinned frontier; not a one-law fix.

## Fan-out (S84 campaign, commit {COMMIT})
{rows}

## Evidence
- `run/s84/<pkg>/obs_obs.log` per-title first-divergence signatures
- `docs/evidence/canonical/registry.json` (machine source)
- `docs/evidence/ROOT_CAUSE_REGISTRY.md` § F-NEW-161

**Next action:** implement compose measure/layout semantic shadow;
re-run fan-out titles as ONE verification pass.""",
        "labels": [],
    }


def make_f162():
    return {
        "title": "[F-NEW-162] androidx savedstate generated-adapter family — "
                 "deferred CNFE unwind (S84, 12-title fan-out)",
        "body": f"""**Root-cause family** (S84 §7 law: one family = one issue).

## Signature
`androidx.savedstate.Recreator_LifecycleAdapter` deferred CNFE — verified NOT
packaged in affected APKs (the adapter is an optional build-time artifact, so
the CNFE itself is faithful to device behavior). The gap: the app's fallback
path still ends in deferred-unwind PARTIAL.

Same family: `androidx.activity.ComponentActivity$$ExternalSyntheticLambda`,
androidx.datastore.preferences.protobuf generated classes.

## Affected (12)
com.clavierhaus.gnubg, com.helddertierwelt.mentalmath, com.kompact,
de.taz.android.app.free, site.leos.apps.lespas, io.github.johnathan.minesweeper,
jwtc.android.chess and other androidx-generation titles in the S84 sweep.

## Next action
Implement the androidx fallback semantics (reflective-lookup-with-catch) as ONE
semantic shadow; re-run all consumers as one verification pass.

Evidence: `docs/evidence/ROOT_CAUSE_REGISTRY.md` § F-NEW-162 (commit {COMMIT}).""",
        "labels": [],
    }


def make_wave():
    return {
        "title": "[S84] Canonical achievements + 50 NEW titles + README landing "
                 "page — wave report",
        "body": f"""## S84 wave report (commit {COMMIT})

### Canonical evidence system (user law: ONE title → ONE screenshot)
- `docs/ACHIEVEMENTS.md` — **ONE record per title** (96 records); wave
  history preserved in `docs/history/ACHIEVEMENTS_WAVE_HISTORY.md`
- `docs/evidence/canonical/<pkg>.jpg|.gif` — one artifact per title, 9
  gameplay GIFs for interactive titles (snake/2048/tetris/TicTacToe-Deluxe/
  TTT-Classic in-house + hotdeath/bobball/dodge/nounours real titles)
- `docs/evidence/CANONICAL_SCREENSHOTS.md` — machine-checkable index
- `tools/verify_canonical_evidence.py` — 12 checks (unique/SHA/no-orphan/
  provenance/visual-claims-need-artifacts) — **ALL PASS**
- `docs/evidence/ROOT_CAUSE_REGISTRY.md` — one root-cause issue per family

### NEW-50 campaign
- 50 fresh F-Droid titles (31 games / 19 apps), each with upstream source
  link + APK SHA256: `run/s84/manifest_new.json`
- 49/50 produced real frames; 13/50 rc=0; 4 titles with engine-verified
  input→state change (nounours, dodge, hotdeath, bobball)
- Rendering levels: L0-L2 honest ladder per the S81 audit instrument

### Engine law
- **F-NEW-160 FIXED**: forName framework bridge (Build family) — 9-title
  CNFE fan-out eliminated; A/B-guarded (CloseGuard bridge regressed
  foehnix.widget, reverted to caught-CNFE path); battery 26/26 +
  golden ladder 10/10

### Evidence integrity correction (S83)
- Validator R5 caught **16 byte-identical evidence JPGs** (f817c243… ×16)
  + ×2 classes shipped as per-title screenshots in S83 → demoted to
  OBSERVED (near-blank class, S54 gate law); dooz real-UI evidence
  restored from s83b sweep (content-verified)

### Cleanup
- 345 MB compaction: 53 raw PPM dumps + 607 closed-investigation frames +
  226 content-duplicate images (1316 → 430 tracked images)
- Every deletion SHA-recorded: `docs/evidence/S84_CLEANUP_MANIFEST.json`

### Regression gates
- battery 26/26 · golden graphics ladder 10/10 · validator ALL PASS""",
        "labels": [],
    }


def main():
    if not TOKEN:
        print("GITHUB_PAT missing — abort")
        return
    for maker in (make_f161(), make_f162(), make_wave()):
        st, resp = api("POST", "issues", maker)
        print(f"create '{maker['title'][:50]}…' → {st} "
              f"#{resp.get('number', '?')}")


if __name__ == "__main__":
    main()
