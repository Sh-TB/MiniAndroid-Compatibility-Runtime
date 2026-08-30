# OPEN_SOURCE_AUDIT_009 — Campaign 009 Open-Source Audit

Campaign: **CAMPAIGN 009 — OPEN-SOURCE-FIRST / GITHUB DEEP MINING / DIVERSE REAL APK MATRIX**
Date: 2026-08-30 · Environment recovery documented in `UNIFIED_009_INDEX.md` companion doc.

## 1. Method (law §45 — internet-first recovery)

Every decision in this campaign followed: `STOP ASSUMPTION → SEARCH INTERNET/GITHUB → READ SOURCE → BUILD CANDIDATE → COMPARE`. Concretely:

- GitHub CLI 2.62.0 installed (portable binary at `tools/gh/bin/gh`, anonymous — no credentials; per §1 no credentials were stored anywhere).
- Bulk verification used `git ls-remote HEAD` (API-quota-free) + raw `LICENSE` fetches; GitHub REST API used sparingly (60/h anonymous limit).
- AOSP oracles fetched live and read before implementing: `aosp-mirror/platform_frameworks_base @ 1cdfff555f4a` — `libs/androidfw/ResourceTypes.cpp` (`match()` @2909, `isBetterThan()` @2641, `isLocaleBetterThan()` @2520).
- Dooz source cloned: `yamin8000/Dooz @ 0c60e78b861a` (GPL-3.0), verified as the true source of `dooz.apk` (package `io.github.yamin8000.dooz`).
- PortableGL cloned + built: `rswinkle/PortableGL` (MIT).

## 2. Catalog totals

| Metric | Value |
|---|---|
| Candidate projects cataloged | **201** (target: 200+) |
| With live commit SHA (ls-remote this session) | **197** |
| With positively identified license | **188** |
| A=Adopt | 13 |
| B=Integrate/Wrap | 36 |
| C=Test/Oracle | 92 |
| D=Reject | 15 |
| E=Investigate Later | 45 |

Note: the Campaign-008 catalog (119 candidates) was **not present** in this environment; the catalog was rebuilt from scratch with fresh live verification. See `GITHUB_MINING_009.md`.

## 3. What was adopted/used this campaign

| Project | Commit | License | Use |
|---|---|---|---|
| aosp-mirror/platform_frameworks_base | 1cdfff555f4a | Apache-2.0 | Oracle for §6 ResTable_config semantics (read, then ported) |
| REAndroid/ARSCLib | f08adf80672c | Apache-2.0 | Category-A reference for ARSC config semantics (cross-checked field layout) |
| yamin8000/Dooz | 0c60e78b861a | GPL-3.0 | Source oracle for the Compose/Dooz track (read-only; no code copied — licenses incompatible with runtime embedding) |
| rswinkle/PortableGL | (live HEAD) | MIT | §24 GLES route — built + GLES2 shader pipeline PROVEN; adoption decision documented |
| androguard/androguard | 4573c8c111ba | Apache-2.0 | DEX census/demand profiling (§16/§17) — already proven in EXP-101/102, reused |
| Samsung/rlottie | 4307553814db | MIT (per upstream headers) | Pre-existing vendored build, regression-verified |
| libpng/libjpeg-turbo/libwebp/FreeType/HarfBuzz/FriBidi | live HEADs | permissive | Pre-existing linked libs, regression-verified |

## 4. Rejections this campaign (with reasons)

- `google/apk-patcher` — NOT-FOUND (404)
- `Tehreer/Tehreer` — NOT-FOUND (404); SheenBidi remains the alive sibling
- `mpg123` on GitHub — no credible mirror (official releases off-GitHub); need already covered by dr_mp3/minimp3 (category A)
- `robolectric/android-all` — not ls-remote-verifiable (artifacts ship via Maven); jars remain usable
- `GetStream/stream-chat-android` — proprietary source-available license; sample-only
- `Signal-Android`, `droidefense`, `ReVanced/revanced-patcher`, `GraxCode/dalvikgate`, `CalebFenton/simplify`, `FongMi/TV`, `gstreamer/gstreamer` — GPL/AGPL incompatible or out-of-scope weight (full list in catalog)
- `nextcloud/android` — LGPL + network-bound giant; poor corpus value per byte

## 5. Code written vs reused (§46 principle)

New custom code this campaign: **one subsystem** — `src/resources/res_config.{h,cpp}` (~640 LoC) — written ONLY after reading the AOSP oracle, because no C library exists that can be linked into the runtime to do ARSC config matching in-process (ARSCLib is Java). Everything else was reuse: oracle reads, existing tooling, existing decoders.

Net: +640 LoC config matcher; +94 LoC attach-dispatch glue; −~20 LoC deleted heuristic. The §29 reduction *opportunities* identified are documented in `CODE_REDUCTION_009.md` (custom PNGDecoder → already-linked libpng; overlapping audio decoder plans → dr_libs) — execution deferred with regression-rebaseline plan, honestly.

## 6. Environment recovery disclosure

This environment contained artifacts through UNIFIED_002 (archives 000/001/002, u007 GMDice run evidence) but **no UNIFIED_003..008 archives and no prior GITHUB_MINING catalog**. All Campaign-008 claims (119-project catalog, browser/API server state machine) could not be re-verified locally and are NOT counted in this campaign's numbers. §26–§28 (browser/API stress tests) were therefore **NOT RUN** — the referenced server does not exist in this environment; recorded honestly instead of simulated.
