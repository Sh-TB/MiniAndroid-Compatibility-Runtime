# OPEN SOURCE AUDIT — UNIFIED_008 (methodology + catalog summary, charter §2/§23/§35)

## Method

The environment exposed NO `gh` CLI and api.github.com's unauthenticated
quota (60/h, shared IP) was exhausted — so discovery/verification used the
**git protocol** directly:

```
git ls-remote https://github.com/<owner>/<repo>.git HEAD
```

This returns the real HEAD commit hash without any API quota, proving (a) the
repository exists and (b) pinning the exact version we inspected. For the
deeper adoptions the artifact itself was pulled:

| artifact | channel |
|---|---|
| ARSCLib-1.4.0.jar | GitHub releases (redirect discovery: /releases/latest → tag V1.4.0) |
| apktool_3.0.3.jar | GitHub releases |
| androguard 4.1.4 | pip |
| swiftshader @ 694585a | git clone --depth 1 |
| OpenJDK 21.0.5+11 (Temurin) | GitHub releases tarball |

## Scorecard (charter §23) — applied to the A/B class

| project | license | build | tests | platform | size | integration | benefit | score |
|---|---|---|---|---|---|---|---|---|
| ARSCLib | Apache-2.0 | jar ready | library CLI built here | JVM | 1.5MB | external oracle | high | **9/10** |
| Apktool | Apache-2.0 | jar ready | decode ran | JVM | 20MB | external oracle | high | **9/10** |
| androguard | Apache-2.0 | pip | 14/15 in UNIFIED_002 + production now | python | 20MB | data pipeline | high | **9/10** |
| SwiftShader | Apache-2.0 | cmake configure OK | compile BLOCKED (env) | C++ | 300MB src | JNI/shim | high (later) | **7/10** |
| Compose MP | Apache-2.0 | gradle | not runnable here | JVM | huge | bridge needed | high (later) | **4/10 (for this env)** |
| rlottie | MIT | static built | on-screen proven | C++ | 2MB | linked | already paying off | **9/10** |
| FriBidi/HarfBuzz/FreeType | LGPL/MIT/FTL | system | runtime-proven | C++ | system | linked | core text stack | **9/10** |
| nlohmann/json | MIT | header | runtime-proven | C++ | 1 file | vendored | core | **9/10** |

Full per-entry dispositions (A/B/C/D) with HEAD commits:
`run/u008_oracle/opensource_catalog.json` — **119 candidates, 114
verified-by-commit, 5 documented upstream-elsewhere**.
Disposition counts: **A=19 adopt, B=26 integrate/reference, C=52 useful for
tests, D=22 rejected**.

## Categories covered (charter §3–§21)

ARSC/AXML · resource system · binary XML/manifest · Compose · UI/rendering ·
text/font · image/drawable · 9-patch/shape/vector · animation · audio ·
3D/GLES · GLES bridge · DEX/bytecode tooling · APK analysis · view/event/input ·
handler/looper · browser/agent (job queue/REST/persistence) · agent tooling.

## Provenance rule compliance (§35)

- every imported artifact: recorded in `LIBRARY_PROVENANCE_008.json`
- licenses: all permissive or correctly attributed; **ultralight REJECTED on
  license audit** (the §29 kill-switch actually fired once)
- vendored footprint: unchanged (nlohmann single-header only) — heavy tools
  stay OUTSIDE the archive per §30/§32
