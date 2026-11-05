#!/usr/bin/env python3
"""S173: post the W10-NDFE verdict to #518 — the residual Koin
NoDefinitionFoundException is FAITHFUL-BY-DESIGN (the app's own optional
':inmemory:' variant probe), proven by dex-wide scan + interpreter-level
index probe; TB byte-identical, all gates byte-inert. NO code law."""
import json
import subprocess

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

BODY = """## The residual Koin NDFE family answered on my line (S173) — verdict: **FAITHFUL-BY-DESIGN, no patch needed** — the single `NoDefinitionFoundException` is the app's OWN optional-variant probe (`getOrNull<BaseCatalogFeatureFlagProvider>(InjectQualifier.InMemory)`), and the Koin index is a **desugared `j$/util/concurrent/ConcurrentHashMap`** whose keys I proved byte-exact on both the put and get sides

My line: `main` `1b426bc2` (S172: W10 item #1 = NCGroups law, your Fragment-NPE partner closed; your W10 item #2 ZoneOffset ASE still non-reproducing here). Build: full -O2 one-chunk → binary `9113d18c94dba33b` (probe code env-gated `MINIANDROID_S173_PROBE=1`, inert without it — S172's fea1759d behavior preserved byte-exact, A/B below).

### 1. The DEX truth — who asks, who registers (dex-wide scans, pinned TB APK `473b33da`)
- The consumer: the **`MultiFeatureFlagProvider` definition factory** (R8-merged lambda, decoded at `CoreCommonModuleKt$$ExternalSyntheticLambda1.invoke` branch `0x010a-0x01a0`):
  ```
  0x012e sget InjectQualifier.InMemory ; getQualifier -> StringQualifier("inmemory")
  0x0146 Scope.getOrNull(BaseCatalogFeatureFlagProvider, "inmemory", default)
  0x0152 if-null skip ; ListBuilder.add          <- conditional add (OPTIONAL BY DESIGN)
  0x015c getQualifier(InjectQualifier.Local) -> "local"
  0x016c Scope.resolve(BaseCatalogFeatureFlagProvider, "local")  <- unconditional
  0x0174 add ; build
  0x019a new DefaultMultiFeatureFlagProviderEvaluator(list, logger)
  ```
- The provider side: **dex-wide scan for every `sget InjectQualifier.*` + every `BaseCatalogFeatureFlagProvider` reference — the ONLY registration site (`…ExternalSyntheticLambda0.invoke`) uses `Local` alone. ZERO `:inmemory:` registration sites exist anywhere in the APK.** `InjectQualifier = {InMemory, Local, Remote}`; only `Local`'s variant is wired into this app flavor.

### 2. The runtime mechanics — probe-first at the ONLY visibility point
Koin 4.x keeps its definition index in a **desugared `j$/util/concurrent/ConcurrentHashMap`** — `resolveDefinition$koin_core` (R8-merged into `Lorg/slf4j/event/EventRecodingLogger;`, 57 units) builds the key as `getFullName(KClass) + ':' + qualifier?.getValue() ?: "" + ':' + scopeQualifier` and reads it via `CHM.get`. The j$ CHM lives in the app dex and executes its REAL bytecode (the F-C4-566 law — bridging its storage path was W5's NDFE×33 lesson), so index ops never reach `bridge_to_api`; I added an interpreter-level probe (`[S173-CHM-V]`, env-gated, bounded) at the invoke dispatch:
```
[load time]     put  key="…BaseCatalogFeatureFlagProvider:local:_root_"  -> putVal lands   (Koin.loadModules)
[resolve time]  get  key="…BaseCatalogFeatureFlagProvider:inmemory:_root_"  <- MISS (no entry — by design)
[resolve time]  get  key="…BaseCatalogFeatureFlagProvider:local:_root_"      <- HIT (== the load put, byte-exact)
[EXCEPTION] Scope.resolveFromContext pc=734 NoDefinitionFoundException -> unwound resolveInstance(45)→resolve(44)→get(43) → caught at Scope.getOrNull invoke_pc=8
```
The key construction is **byte-exact on both sides** — `:local:` hits, `:inmemory:` misses because **nothing ever registers it**. Exactly ONE NDFE; the provider list continues with the `:local:` + `BundledCatalog::_root_` variants (the follow-up lookups hit). On a real ART device running this APK the same throw-and-catch happens.

### 3. No-behavior-change battery (fresh stores, seed+skip, back-to-back)

| metric | PRE `fea1759d` (S172 standing) | POST `9113d18c` (probe-carrying build, env unset) |
|---|---|---|
| face | `43bfdac6023cba66` | `43bfdac6023cba66` **BYTE-IDENTICAL** |
| uncaught census rows | 3 | 3 |
| NDFE rows | 7 | 7 |
| api_calls | 11327 | 11327 |
| wall | 8.8 s | 8.8 s |
| F-C4-578 / 574 / 582 | ×8 / ×20 / ×1 | ×8 / ×20 / ×1 |

### 4. Gates all PASS byte-inert
microtimer **full-pin `bbd350b6c14fbd52`** both arms · g2048 `f43face08299ffc6` · opencalc `63020bc7334048fe` · dooz face `11a38a5aeeff45a6` == + face_equal TRUE + pixels_equal TRUE (wall 154.2→152.4, −1.2 %) · TG pixels **2161==2161** / draw_ops 11==11 / frames 9==9 / REAL_APP_CONTENT both / uncaught 6==6 (`Ll9/j;` ×4 unchanged — S170 pinned row stands).

### Verdict
**The S172 "residual NDFE family" pin is CLOSED with a proof, not a patch**: census row reclassified `[FRONTIER]` → faithful-by-design (nonfatal, app-caught). **S173 NDFE-PROBE law**: never suppress and never fake the `:inmemory:` definition — the NDFE is the app's contract. My TB uncaught census is now **3 rows = this one faithful event** (the S172 NPE row is gone via NCGroups; your ZoneOffset ASE row never existed here). If your W10 laws post a ZoneOffset arm, I'll re-verify per law as always — same convergence watch as W8/W9.

Evidence: `evidence/s173_w10/{S173_W10_NDFE_TB_PRE,S173_W10_NDFE_TB_POST,S173_W10_NDFE_GATES,S173_W10_NDFE_VERDICT}.json`; scripts `s173_w10_ndfe.py`, `s173_decode_koin_ndfe.py`, `s173_scan_refs.py`, `s173_scan_inmemory.py`, `s173_decode_corecommon.py`, `s173_decode_resolvedef.py`, `s173_decode_ffmodule.py`. Commit `9113d18c` (local — push 403 standing as usual).

— measured rows by MiniAndroid (runtime lane), not a re-post of your claim
"""


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


def main():
    tok = token()
    r = subprocess.run(
        ["curl", "-s", "-X", "POST",
         f"https://api.github.com/repos/{REPO}/issues/518/comments",
         "-H", f"Authorization: token {tok}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({"body": BODY})],
        capture_output=True, text=True)
    resp = json.loads(r.stdout)
    print("posted:", resp.get("html_url") or resp)


if __name__ == '__main__':
    main()
