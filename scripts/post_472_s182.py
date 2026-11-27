#!/usr/bin/env python3
"""Post the S182 hidden-achievements reconciliation to issue #472 (the living
MASTER ACHIEVEMENT LEDGER). Token from git credential helper; never printed.
Verifies by re-fetch."""
import json, subprocess

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BODY = """# S182 HIDDEN ACHIEVEMENTS RECOVERY — 9 REAL_APP_CONTENT candidates reconciled on current HEAD `96878de83`

**Trigger (user):** the S182 mosaic (`evidence/s182_mosaic/S182_MOSAIC.png`) shows apps/games that never made the achievement reports — "چرا فراموش کردی اینا رو". Full reconciliation report committed at `evidence/s182_recheck/S182_RECONCILIATION.md` (pushed with this audit); raw battery JSON + APK SHA receipts alongside.

## Why they were omitted — the audit answer

Cross-checking `registry.json` / `ACHIEVEMENTS.md` / `README.md`: **six of the nine titles (uturn, pfdicer, librecontactsbackup, wocheneinkauf, textpad, peri) have ZERO mentions anywhere**; gmdice/bouncy/pfsolitaire have standing entries. Root cause: the S182 battery results were tracked (`evidence/s182_minimal2/S182_BATTERY.json`) but the registry/ACHIEVEMENTS reconciliation step was never executed for six titles — **a reporting failure, not an evidence failure**. The S182 CLOSED_AUDIT audited issue closures, not the ledger, so the gap survived five waves.

## Reconciliation matrix (all 9 re-run THIS session, original battery protocol, fresh stores)

| Package | Historical (S182, 5d7edcdb) | Current HEAD 96878de83 | Verdict |
|---|---|---|---|
| de.duenndns.gmdice | REAL face `3891679dff449331` px 182,535 | **face BYTE-IDENTICAL**, px 182,535, unc 0 | HOLDS EXACTLY |
| com.dozingcatsoftware.bouncy | REAL px 978,380, **unc 18** | REAL px 1,095,220, **unc 0** | HOLDS, IMPROVED |
| org.secuso.privacyfriendlydicer | REAL face `31ffa499c59e3e41` | **face BYTE-IDENTICAL**, unc 12 nonfatal | HOLDS |
| org.secuso.privacyfriendlysolitaire | REAL face `88dbb4a719dbc8d4` px 58,212 | **face BYTE-IDENTICAL**, unc 0 | HOLDS EXACTLY |
| com.maxistar.textpad | REAL face `27f44f4647bf76f2` px 2,418 | **face BYTE-IDENTICAL**, px 2,418, unc 0 | HOLDS EXACTLY |
| com.ashkanrafiee.librecontactsbackup | REAL px 1,214,501 | REAL px 720,117 (drift), unc 4 | HOLDS (drift to reconcile) |
| ac.stresa.uturn | REAL px 10,782 | DEFAULT_BACKGROUND_ONLY, unc 8 | **REGRESSED** |
| app.wocheneinkauf | REAL px 44,227 | DEFAULT_BACKGROUND_ONLY, unc 33 | **REGRESSED** |
| app.simple.peri | REAL px 325,303 (61s) | DEFAULT_BACKGROUND_ONLY, unc 33 | **REGRESSED** |

**6/9 still REAL_APP_CONTENT today (4 byte-identical faces — the strongest determinism proof); 3/9 no longer reproduce.** The three regressions (uturn, wocheneinkauf, peri — all Compose-generation apps) share ONE named root cause, extracted from this session's traces: **`IllegalStateException` unwound in `androidx.compose.ui.platform.AbstractComposeView.internalOnMeasure$ui` / `.onMeasure`** — the known Compose-measure DEX-emulation frontier (S27-RECON bottleneck class), not three separate bugs. The historical evidence stands; the regression is on current HEAD and stays open at that frontier.

## Provenance receipts (nothing assumed)

- APK identities: gmdice `1621eda11b5dbc0c…`, bouncy `ffda0d9cb0b1b2aa…` (canonical_apks), and the 7 fdroid_batch APKs **restored byte-exact from `f-droid.org/repo`** after the sandbox recycle lost them from disk — versioned F-Droid artifacts are immutable; SHA256 receipts committed (`evidence/s182_recheck/apk_shas.txt`, `s182_restore_receipt.txt`). No APK rebuilt from source.
- Protocol: the original `s182_minimal2_battery.py` law, unchanged (real-dalvik, fresh store per title, frames=5, trace+census).
- Recommendations in the committed report: registry + ACHIEVEMENTS rows for all nine (6 current-verified, 3 historical/regressed with the named blocker), README claim updates only after registry rows land, **no closures without re-verification**, drift rows get the next census pass.

Labels: 6/9 VERIFIED-CURRENT (4 BYTE-IDENTICAL), 1/9 HOLDS-IMPROVED, 3/9 REGRESSED-COMPOSE-FRONTIER (root cause named), OMISSION ROOT-CAUSED (reporting gap, 6 titles), NO-VERDICT-FABRICATED.
"""

def token():
    inp = "protocol=https\nhost=github.com\n\n"
    out = subprocess.run(["git", "credential", "fill"], input=inp, capture_output=True,
                         text=True, cwd="/home/z/my-project")
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):]
    raise SystemExit("no token")

def api(path, data=None):
    t = token()
    cmd = ["curl", "-sS", "-m", "60", "-H", f"Authorization: token {t}",
           "-H", "Accept: application/vnd.github+json", f"https://api.github.com{path}"]
    if data is not None:
        cmd += ["-d", json.dumps(data)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(p.stdout)

res = api(f"/repos/{REPO}/issues/472/comments", {"body": BODY})
if "id" in res:
    print("POSTED comment id:", res["id"])
    print("html_url:", res.get("html_url"))
    chk = api(f"/repos/{REPO}/issues/comments/{res['id']}")
    ok = "BYTE-IDENTICAL" in (chk.get("body") or "")
    print("VERIFY re-fetch: id:", chk.get("id") == res["id"], "| content present:", ok,
          "| len:", len(chk.get("body") or ""))
else:
    print("POST FAILED:", json.dumps(res)[:400])
