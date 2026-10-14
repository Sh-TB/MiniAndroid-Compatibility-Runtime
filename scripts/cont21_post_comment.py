#!/usr/bin/env python3
"""CONT-21 — post the ARCH-001 Execution Family Matrix wave report to Issue #384."""
import subprocess, json, urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
ISSUE = 384

proc = subprocess.run(["git", "credential", "fill"],
                      input="url=https://github.com\n\n",
                      capture_output=True, text=True)
token = None
for line in proc.stdout.splitlines():
    if line.startswith("password="):
        token = line.split("=", 1)[1]

HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

BODY = r"""# CONT-21 wave report — ARCH-001 Execution Family Matrix built; #1 shared primitive FIXED (component-info identity chain) + Thread UEH law FIXED

Binary lineage: `b6ee41e77acb88ec` (CONT-20) → **`882b7cdf389aabc3`** (commit `937b6d60`). Registry 581 → **585**. Full matrix: `evidence/cont21/EXECUTION_FAMILY_MATRIX.md`; A–I report: `evidence/cont21/CONT21_FAMILY_WAVE.md`.

## A — Family Matrix

14 representatives across 7 families inventoried (package/version/ABI/apk-sha256) and runtime-traced (`run/cont21/family_inventory.json`, `family_paths.json`):

| Family | Representatives | Result |
|---|---|---|
| F1 Base/View | opencalc, stopwatch, chessclock, unote, microtimer | unote/microtimer/opencalc REAL_APP_CONTENT (anchors ×3 byte-identical); stopwatch startup-fatal pre-fix → rc 0 post-fix |
| F2 2D Canvas/View | g2048, tictactoe_deluxe, real-APK tictactoe (libGDX) | g2048/ttt_deluxe REAL_APP_CONTENT ×3; real tictactoe traced to GLSurfaceView20 EGL face |
| F3 SurfaceView/game-loop | bouncy, flappycow, fishrings | flappycow SUCCESS (636 colors); bouncy FRAME_CAPTURED (145 colors); fishrings = scheduling face (classified) — actual paths differentiated, not assumed |
| F4 Messaging | telegram 12.10.5, forkgram 12.10.8 (family evidence, NOT separate executors) | both rc 1→0 post-fix; UI-init family faces remain (honest) |
| F5 Social/media | none in corpus | honest NO-TARGET record (whatsapp.apk = 5.6KB stub artifact) |
| F6 Compose | dooz 23 | rc 1→0; APP BOUNDARY 2→0; anchor stable |
| F7 WebView/HTML5 | minibrowser VC2 rebuilt canonical (`d606fa140bc2aad4`) | SUCCESS, content render (222 colors / 31,208 nondom px) |

## B/C — First divergences + shared-primitive clustering (BEFORE fixes)

Cluster scan over 14 run logs (`scripts/cont21_cluster_scan.py`):

- **P1 — component-info identity chain: `PackageManager.getProviderInfo` REC-MISS → `providerInfo.metaData` iget NPE** in the androidx.startup process-start chain. Hits **5 targets across 3 execution families** (opencalc, stopwatch, forkgram, telegram, dooz) — FATAL pre-UI in stopwatch. THE #1 shared primitive.
- **P2 — Thread UncaughtExceptionHandler null** (kotlinx coroutine report path `Llo;.K pc=0x52`) — the registered CONT-20 F-NEW-272 P0.
- P3–P10 clustered only, NOT fixed (kotlin-reflect handled face; Telegram-engine ContactsController family-internal; native-ABI extraction; SurfaceHolder identity (bouncy); chessclock Uri-null single-target; **data-path duplication P8** (storage law → registered F-NEW-276); **ServiceInfo.metaData P9** (sibling → F-NEW-275); libGDX surface/input).

## D/E — Source-first laws + minimal generic fix (dalvik_engine.cpp/.h only, zero app checks)

1. **F-NEW-273 ROOT-CAUSED+FIXED** (three laws on the existing abstraction):
   - `ComponentName.<init>(pkg,cls)` producer law (was REC-MISS → empty identity);
   - `PackageManager.getProviderInfo(ComponentName, flags)` consumer law — manifest `manifest_provider_identity_` resolution, ProviderInfo seed (name/packageName/authority/authorities/grantUriPermissions + metaData from `component_meta_data_`, the same tables the S1-PROVIDER install path uses), **NameNotFoundException via throw_deferred when absent** (AOSP: never returns null);
   - `BaseBundle.keySet()/containsKey()/isEmpty()` law (bundle: namespace; never-null keySet).
2. **F-NEW-272 ROOT-CAUSED+FIXED**: Thread UEH family — per-thread handler map + **non-null lazy default `RuntimeInit$KillApplicationHandler`** (AOSP RuntimeInit law) + `[UEH-DEFAULT]` log contract; process-death modeling stays with the F-016 machinery.

Upstream authority: AOSP PackageManager/BaseBundle/Thread laws + the **live app DEX law** (cont11_rawscan disassembly of dooz's `InitializationProvider.onCreate`: `getProviderInfo(new ComponentName(...), 128)` → `iget metaData` (no null-check — upstream trusts the PM contract) → `keySet().iterator()`).

## F — Runtime proof

- dooz: `[F273-PROVINFO] androidx.startup.InitializationProvider metaData entries=3`; ProviderInfo.metaData NPE GONE; keySet face GONE; `[UEH-DEFAULT] FATAL EXCEPTION caller=Llo;.K`; **APP BOUNDARY 2→0, rc 1→0**; anchor `d602648e8e401895` ×3 zero-drift. Remaining uncaught = exactly one: `Lwg0;.y pc=17 iget Lrf1;.f on null` → registered **F-NEW-274 (P0)**.
- stopwatch (the P1 fatal case): rc 1→0, no APP BOUNDARY, startup completes.
- opencalc/telegram/forkgram: rc 1→0 each, screenshots byte-identical (zero drift).

## G — Regression at `882b7cdf389aabc3`

anchors 18/18 ×3 BYTE-IDENTICAL; probes rebuilt canonically at this container (`scripts/cont21_build_probes.sh`): fcol 20/20 (incl. K19/K20), f259 7/7, f259g 12/13 (known honest L), f266 6/6, f268 12/12; g2048 anchor MATCH.

## H — Coverage decision

- **BASE (fixed)**: F-NEW-271 (CONT-20), F-NEW-272, F-NEW-273.
- **BASE candidates (registered, unfixed)**: F-NEW-274 (savedstate chain, P0), F-NEW-275 (GET_SERVICES sibling, P1), F-NEW-276 (data-path duplication, P2 — hits 5+ targets in the logs).
- **FAMILY/APP-SPECIFIC candidates (clustered only)**: ContactsController, native-ABI extraction, SurfaceHolder identity, chessclock Uri null, libGDX surface/input. No single-APK fix was auto-promoted to generic.

## I — Remaining work

F-NEW-274 (dooz P0, same source-first workflow) → F-275 → F-276 → F-265 measure-pass completion → F-267 tap bridge. Family candidates stay clustered until a second target hits them.

Honest status: dooz stays PARTIAL (frame-truth DEFAULT_BACKGROUND_ONLY); F4 = LOADED; F5 = UNEXECUTED; no unsupported DONE anywhere.
"""

req = urllib.request.Request(
    f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments",
    data=json.dumps({"body": BODY}).encode(),
    headers={**HDRS, "Content-Type": "application/json"}, method="POST")
try:
    r = urllib.request.urlopen(req, timeout=60)
    print("comment:", json.loads(r.read())["html_url"])
except Exception as e:
    print("post failed:", e)
