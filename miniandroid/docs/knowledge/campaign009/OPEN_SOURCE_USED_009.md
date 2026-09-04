# OPEN_SOURCE_USED_009 — what was actually used, with provenance

Every entry: repository · verified commit · license · what it did in Campaign 009 · where the evidence lives.

## Directly used (live this session)

| # | Project | Commit | License | Use in this campaign | Evidence |
|---|---|---|---|---|---|
| 1 | aosp-mirror/platform_frameworks_base | `1cdfff555f4a` | Apache-2.0 | §6 oracle: `ResourceTypes.cpp` match()/isBetterThan()/isLocaleBetterThan() read from raw.githubusercontent and ported faithfully into `src/resources/res_config.cpp` | side-by-side function order documented in source comments; probe evidence in `APK_CONFIG_MATCHING_009` section of REGRESSION_009 |
| 2 | REAndroid/ARSCLib | `f08adf80672c` | Apache-2.0 | cross-check of ResTable_config field layout during offset-bug fix | catalog row; layout corrected after re-derivation (see below) |
| 3 | yamin8000/Dooz | `0c60e78b861a` | GPL-3.0 | Compose/Dooz track source oracle: confirmed Compose BOM 2026.06.01, Material3, module layout, MainActivity; confirmed APK version difference (APK main = `.content.MainActivity`, HEAD = `.ui.MainActivity`) | cloned at /tmp/dooz-src (session-local); findings in dooz_demand_profile.json |
| 4 | rswinkle/PortableGL | live HEAD (ls-remote-verified) | MIT | §24 GLES blocker route: cloned, header-only build with plain gcc, GLES2 vertex+fragment shader triangle rasterized (31,104 colored px) | `run/exp_uc009_gles/pgl_gles2_test.c` + result below |
| 5 | androguard/androguard | `4573c8c111ba` | Apache-2.0 | §16/§17 DEX demand mining on dooz + 10 new corpus APKs (class counts, GLES refs, Compose method surface) | `apk_demand_matrix.json` |
| 6 | fribidi/harfbuzz/freetype (system) | n/a (distro) | LGPL/MIT/FTL | unchanged typography stack — regression-verified via Telegram identical-SHA runs | REGRESSION_009 |

## Pre-existing vendored/linked (regression-verified, unchanged)

- Samsung/rlottie `4307553814db` (MIT) — static lib relinked, Telegram Lottie path stable
- libpng, libjpeg-turbo, libwebp (system libs, `-l` linked) — GMDice/Telegram screenshots byte-identical

## Key engineering facts established from open-source reads

1. **ResTable_config field offsets** (AOSP ResourceTypes.h): size@0, mcc@4, mnc@6, language@8, country@10, orientation@12, touchscreen@13, density@14(u16), keyboard@16, navigation@17, inputFlags@18, screenWidth@20, screenHeight@22, sdkVersion@24, minorVersion@26, screenLayout@28, uiMode@29, smallestScreenWidthDp@30, screenLayout2@32, colorMode@33, screenWidthDp@36, screenHeightDp@38, localeScript@40, localeVariant@44. (Our first draft was off-by-4 after inputFlags — caught by re-deriving from the fetched header BEFORE regression runs; see REGRESSION_009 §2.)
2. **match() rule**: density ALWAYS matches (scaled); entry sdkVersion > device → reject; entry screenSize bucket > device bucket → reject; sw/W/H dp over device → reject.
3. **isBetterThan() order**: imsi → locale → grammaticalInflection → layoutdir → smallestWidth → w/h-dp → screensize/long → round → gamut/hdr → orientation → uiMode → **density (closest above, prefer scale-down)** → touchscreen → keys/nav hidden → keyboard/nav → screenSize → version.
4. **DENSITY_ANY (anydpi) beats any concrete bucket** (PGL-independent AOSP rule) — proven live: Telegram `_menu_stream_comments_off_24` selects `[anydpi-v24]` over `[480dpi]`.
5. **AbstractComposeView.onAttachedToWindow → ensureCompositionCreated** is THE Compose attach hook (dooz DEX: declared on AbstractComposeView, inherited by ComposeView).

## License compliance position

- Runtime code adopts **no** GPL/AGPL source. Dooz source was used read-only as an oracle (clean-room boundary: semantics understood from AOSP/compose docs + DEX evidence; no GPL text copied).
- PortableGL is MIT — if adopted next campaign, its license notice will be vendored with the header (provenance row prepared in `LIBRARY_PROVENANCE_009.json`).
