# OPEN_SOURCE_REJECTED_009 — every rejection carries a reason

From the 201-candidate catalog, these are the explicit rejections (category D) plus rejections of candidate *routes* during engineering. Full machine-readable data: `OPEN_SOURCE_CATALOG_009.json`.

## Repos rejected (D)

| Repo | Reason |
|---|---|
| google/apk-patcher | NOT-FOUND (404 on ls-remote) |
| Tehreer/Tehreer | NOT-FOUND (404); sibling SheenBidi alive |
| mpg123 (GitHub mirror) | no credible official mirror; need covered by CC0 dr_mp3/minimp3 |
| APKLab/APKLab | VSCode UI wrapper around apktool/jadx; no unique engine |
| droidefense/engine | GPL-3.0 malware-analysis engine; license + scope |
| ReVanced/revanced-patcher | GPL-3.0; patching framework out of scope |
| GraxCode/dalvikgate | GPL-3.0 |
| CalebFenton/simplify | GPL-3.0 symbolic execution |
| GetStream/stream-chat-android | proprietary source-available; not adoptable |
| FongMi/TV | GPL-3.0 TV player; out of scope |
| nextcloud/android | LGPL + huge network-bound app; poor corpus value |
| signalapp/Signal-Android | AGPL-3.0; enormous; corpus value low vs cost |
| pserwylo/retrowars | superseded by retrowars/retrowars (canonical moved) |
| LottieFiles/dotlottie-web | web player; out of scope |
| robolectric/android-all | not a buildable repo (Maven-shipped jars); jars still usable as oracle — kept as C-oracle note |

## Routes rejected during engineering (evidence-based)

| Route | Evidence | Decision |
|---|---|---|
| SwiftShader source build (§24) | previous campaign: configure OK, compile >3GB RAM; this machine has 3GB total | rejected — physically infeasible here |
| Mesa (llvmpipe/lavapipe) | no root for apt install; source build hits the same RAM wall | rejected for this environment |
| ANGLE | layering requires a working Vulkan below it (SwiftShader) → same wall | deferred |
| Vendoring Dooz GPL source into runtime | GPL-3.0 vs runtime's permissive embedding needs | rejected — oracle-only use |
| Chromium/WebView for §L | no prebuilt headless WebView unit available in env; bgclock already exercises WebView-class rendering | deferred |
| Official compose-samples APKs (§12) | not published as APKs upstream; building them requires Android SDK/gradle absent here | documented as gap; Droid-ify + NewPipe (real Compose APKs) profiled instead |

## Adopted-with-conditions (A/B, not executed this campaign)

These are adopted-on-paper with integration plans, pending next-campaign execution: `nothings/stb` (image decode consolidation), `mackron/dr_libs` (audio decoder consolidation), `Tehreer/SheenBidi` (bidi+shape pipeline simplification study), `jserv/tinygl` (GLES1 fallback), `sqlite/sqlite` (canonical amalgamation). Conditions: license notice vendoring + regression re-baseline.
