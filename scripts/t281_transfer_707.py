#!/usr/bin/env python3
"""T281 — the #707 KA-KYK-034/035 correction comment."""
import json
import subprocess
import urllib.request

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def get_token():
    p = subprocess.run(["git", "credential", "fill"],
                       input="protocol=https\nhost=github.com\n\n",
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise RuntimeError("no token")


TOKEN = get_token()

BODY = """# KODER-YAR-E-KOMAKI — T281 ARCHITECTURE FORENSIC: KA-KYK-034 strong form FALSIFIED, KA-KYK-035 FALSIFIED, the real build-mode hazard named

**Audit base:** remote `main` HEAD `ad2e08ee6` → T281 commit **`399fb2378` pushed** (binary `1946562fe61d6177`). Evidence: `evidence/t281/` (route logs for 6 APKs + gate logs). This comment supersedes the 034/035 rows and §2 of the T280 comment (`7241050366`).

## 1. Verdict

- **KA-KYK-034 (T280): strong form FALSIFIED.** The `dalvik_bridge.cpp` domain chain is **the LIVE production bridge** — hot in every APK family tested. T280's "engine.cpp:38672 wins the link; the ENTIRE domain chain is DEAD CODE" was wrong.
- **The underlying hazard T280 was sensing is REAL but different: a two-mode build with a stale monolith mirror.** Makefile `DALVIK_SPLIT=1` (default) compiles the split TUs from `core_sources.manifest` (engine_core/_invoke/_tail, interpreter, opcodes, opcodes_invoke, dalvik_bridge, 5 domain files) and **excludes the 94K-line `dalvik_engine.cpp` monolith**. In the default build, `build/dex/dalvik_engine.o` does not exist. T280's forensic error: `nm build/dex/dalvik_engine.o` was run on a **nonexistent file** (silenced by `2>/dev/null`) and an empty output was read as "anonymous-namespace wins"; the `[S186I-STUB]` line was attributed to `dalvik_engine.cpp:93204` when the chain's own tail (`dalvik_bridge_domain_io_lang.cpp:9502`) prints the identical format.
- **KA-KYK-035 (T280): FALSIFIED.** `bridge_domain_ui_graphics` is ONE function spanning lines 16→14640 (verified by brace-matching, `scripts/t281_function_boundaries.py`); the RectF law test passes **18/18 with the block at its committed (original) position**; T280's pre-move failures were stale-build artifacts (silent `make -j2` failures during that session — verified when probe strings were absent from nominally fresh binaries). T280's committed source already had the block at the original position; no early-exit exists before line 4368.

## 2. Exact linkage facts (authoritative, from the actual objects)

| Object | bridge_to_api symbol | Meaning |
|---|---|---|
| `build/dex/dalvik_bridge.o` | **GLOBAL FUNC 11466B** (+ LOCAL `.cold` 739B) | the ONE definition — bridge.cpp:82-339 chain dispatcher |
| `build/dex/dalvik_engine_core.o` | UND (GLOBAL, NOTYPE, ndx=UND) | caller only |
| `build/dex/dalvik_engine_invoke.o` | UND | caller only |
| `build/dex/dalvik_opcodes_invoke.o` | UND | caller only |
| `build/dex/dalvik_engine.o` | **file does not exist** | monolith not compiled in default build |

There was never an ODR competition to resolve: exactly one definition is compiled and linked. The anonymous namespace at `dalvik_engine.cpp:38547` is real in source but irrelevant — that TU is the `DALVIK_SPLIT=0` fallback mirror.

## 3. Dynamic production proof (`MINIANDROID_BRIDGE_ROUTE`, 6 original release APKs, frames 4-5)

| APK | chain-entry | domains | rectf-law | face |
|---|---|---|---|---|
| gmdice | 40/40 cap | — | 0 | `3891679d` ✓ anchor |
| bouncy | 40/40 cap | — | 10 (Rect.width/height INT path) | `37326cb2` ✓ anchor (frames 5) |
| pfdicer | 40/40 cap | all 5 ×12 cap | 0 | `31ffa499` ✓ anchor |
| pfludo | 40/40 cap | all 5 ×12 cap | 0 | `21ea13e1` ✓ anchor |
| itsfrz | 40/40 cap | all 5 ×12 cap | 0 | — |
| opencalc | 40/40 cap | — | 0 | — |

Real chain traffic observed: `System.lineSeparator`, `Application.<init>`, `AtomicInteger.<init>`, `Runtime.getRuntime/availableProcessors`, `Math.min` — ordinary framework API volume flows through the domain chain. The law test itself traverses the same route (`[BRIDGE-ROUTE] chain-entry → domain=ui_graphics → rectf-law`), so its 18/18 verdicts are production-path-valid.

**Why gmdice/bouncy/opencalc still cap at 40 while the SECUSO/itsfrz trio hits the chain early:** the chain is a FALLBACK TIER after shadow dispatch and engine-side laws; app families differ in how much unresolved-API volume reaches it. That per-family routing depth (which callers reach the chain, and how often) is the correct replacement framing for T280's "dead vs alive" dichotomy — hypothesis F/D of the T281 mission statement, not linker selection.

## 4. T280 consequences reconciliation (migration-risk register)

| Item | T280 action | Correct status |
|---|---|---|
| ui_graphics RectF float width/height + isEmpty OR | fix at original position (committed) | **LIVE — production path** (bouncy exercises it; anchors green) |
| The same fix in `dalvik_engine.cpp:59471` | "live bridge" claim | **INERT in default build** — lands in the fallback mirror only; retained deliberately (the fallback mode must stay correct) |
| Choreographer.getFrameTime ms law | `choreographer_shadow.cpp` | LIVE (split-build TU, separate dispatch path) |
| 3× RAII `IsStaticRestore` guards | `dalvik_opcodes_invoke.cpp` | LIVE (split-build TU) |
| "domain chain dead" framing | commit message + #707 | **CORRECTED by this comment** |
| t280 law test production-path validity | — | PROVEN (route-identical to APK runs) |

## 5. M4 repair landed (no deletion, no behavior change)

1. **Permanent diagnostic:** `MINIANDROID_BRIDGE_ROUTE=1` → bounded `[BRIDGE-ROUTE]` lines: `chain-entry`, `domain=<jdk|android_core|ui_graphics|app_runtime|io_lang>`, `rectf-law` — across `dalvik_bridge.cpp:82` + all 5 domain entries + the RectF arm. Env-gated, first-N capped (40/12/24), zero output without the env.
2. **Monolith hazard banner** at `dalvik_engine.cpp:1-19`: documents the fallback-mirror status, the inert T280 fix location, the one-definition fact, and the verification rule ("verify any bridge edit against the SPLIT build").
3. No handlers deleted or moved; anchors byte-identical; law battery 5/5 green (f714 9/9, lifecycle ALL, linear 24/24, input ALL, t280 18/18); pfdicer determinism 3/3.

## 6. Architecture recommendation (M3)

**Keep Option A/B hybrid that already exists — one canonical dispatcher (`dalvik_bridge.cpp:82` chain) fed by all callers — and spend the effort on the actual risks instead of re-architecture:**
1. The real defect class is **mirror drift** (monolith vs split TUs). Guard: the banner (landed) + a CI-style check (`test -e build/dex/dalvik_engine.o && fail` in the gate script, or a Makefile assert) so the mirror can never silently ship.
2. Consider **deleting the monolith mirror** in a future wave ONLY after the `DALVIK_SPLIT=0` fallback is either verified buildable or declared unsupported — it is 94K lines of drift surface for zero production value today (Main Coder decision; do not fold into compatibility waves).
3. Route-coverage monitoring: the BRIDGE-ROUTE diagnostic now makes per-family chain depth measurable (gmdice/bouncy/opencalc vs SECUSO/itsfrz) — use it to rank which domain handlers get production traffic before investing in them.

## 7. #707 finding-status updates (supersedes the T280 table rows)

| Finding | T280 status | **T281 status** |
|---|---|---|
| KA-KYK-034 | CONFIRMED (P0, chain dead) | **FALSIFIED (strong form) / CONFIRMED (mirror-drift hazard, P1)** |
| KA-KYK-035 | CONFIRMED (early-exit) | **FALSIFIED** |
| KA-KYK-029/030 | FIXED ON REMOTE MAIN | **FIXED ON REMOTE MAIN (live path re-proven)** |
| KA-KYK-028 | FIXED ON REMOTE MAIN | unchanged |
| KA-KYK-033 | FIXED ON REMOTE MAIN | unchanged |
| KA-KYK-031/032, alpha, rotation, KA-009 | PENDING | unchanged |

## 8. Main Coder actions (concrete)

1. Revert any work planned against "dead domain chain" — the chain is the dispatch. New bridge laws go into the `dalvik_bridge_domain_*.cpp` files (or engine-side split TUs), never into `dalvik_engine.cpp`.
2. Adopt `MINIANDROID_BRIDGE_ROUTE=1` as the standard first step when an API appears unhandled: it shows which tier claims the call.
3. Decide the monolith's fate (verify-fallback vs delete) as a standalone small wave; until then the banner guards it.
4. Optional hardening: add a build-gate assert that `build/dex/dalvik_engine.o` must not exist in split-mode artifacts.

**Queue update:** T280's queue items 2-6 stand unchanged (compose host materialization, NavHostFragment NPE, ArrayAdapter backing, alpha/rotation, TableRow span). New item: per-family chain-depth census using the BRIDGE-ROUTE diagnostic to rank handler investment.
"""


def main():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/707/comments", method="POST",
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "kyk-agent", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, data=json.dumps({"body": BODY}).encode()))
    print("posted:", r["html_url"])


if __name__ == "__main__":
    main()
