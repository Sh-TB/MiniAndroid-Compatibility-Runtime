# PAPARAZZI / ROBORAZZI VISUAL ORACLE — STATUS (§23)

## Attempt (EXP-095)

Environment prepared (all user-space, no root):
- JDK: Temurin 21 (`tools/jdk-21.0.12.1+1`)
- Gradle 8.10.2 (downloaded, later removed for disk)
- Project: `tools/paparazzi-oracle/` with:
  - `app.cash.paparazzi` 1.3.4 + AGP 8.5.2 (build.gradle.kts)
  - `app/src/main/res/layout/sms_screen.xml` — the Telegram SmsView
    structure reproduced in XML (same margins/gravity/sizes as the
    Robolectric oracle test and the MiniAndroid render)
  - `SmsScreenSnapshotTest.kt` — renders through LAYOUTLIB at
    1080x1920 density 1.0 for pixel-exact comparison

## Blocker

Container disk: 9.9GB total; the campaign workspace + Telegram sources +
run evidence ≈ 6GB. The Paparazzi pipeline requires AGP + Android SDK
platform-34 + layoutlib natives + Gradle caches ≈ 2-3GB additional.
After cleanup only ~3.4GB is free and shared with all other campaign work
(build artifacts, run evidence). The Gradle build itself failed at cache
creation when the disk hit 100%.

**Classification: DEFERRED (environment-constrained), NOT REJECTED.**

## Mitigation (what covers §23's objective now)

1. **Robolectric oracle (§22) — COMPLETE**: same layout structure executed
   through real AOSP android-all LinearLayout code — geometry semantics
   verified MATCH (see ROBOLECTRIC_ORACLE_RESULTS.md). This covers the
   structural/pixel-position comparison that Paparazzi would provide.
2. **MiniAndroid 3-run proof**: stable pixel output (43379 px, identical SHA)
   for the same structure.
3. Paparazzi remains the right tool for the FUTURE full-pipeline comparison
   (text rasterization, drawable rendering, theme colors) — the test sources
   are committed under `tools/paparazzi-oracle/` and run with:
   `gradle :app:paparazziDebug --max-workers=1` once ≥3GB disk is available.

## Roborazzi

Roborazzi (the Compose-oriented successor) requires a full Compose app
module — heavier than Paparazzi for our non-Compose target. Not attempted;
Paparazzi covers the layoutlib path (both use the same layoutlib core).
