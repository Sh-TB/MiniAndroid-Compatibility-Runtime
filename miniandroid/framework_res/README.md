# framework_res — the ORIGINAL framework resource table (package 0x01)

S124 THEME/TEMPLATE LOADING BASE.

`resources.arsc` is the resource table of a real **framework-res.apk**
(Android 16 / API 36, package `android`, id 0x01) — the ORIGINAL framework
resource base every Android app's themes/templates resolve against
(AOSP AssetManager2 multi-package law: ApkAssets[framework-res, app]).

- Source: framework-res.apk (sha of the zip downloaded from the public
  LineageOS-framework mirror repo loveahimsa21479/FrameworkResApk;
  badging: `package: name='android' versionCode='36' versionName='16'`).
- Core theme ids are FROZEN since API 21 and were verified against AOSP
  main `core/res/res/values/public-final.xml` (Theme.Material 0x01030224,
  Theme.Material.Light 0x01030237, Widget.Material.Button 0x01030258,
  buttonStyle 0x01010048, textViewStyle 0x01010084, ...).
- The full framework-res.apk (32MB, with drawable FILES) is kept locally
  next to this file but NOT committed (git budget); the runtime only
  needs `resources.arsc` — framework DRAWABLE file references resolve to
  an honest miss and fall back to the app's own drawables / generated
  attr-default table.
- Loader: `ResourceRuntime::ensure_framework_resources()` (paths tried:
  $MINIANDROID_FRAMEWORK_ARSC, <exe_dir>/../framework_res/resources.arsc,
  <exe_dir>/framework_res/resources.arsc, ./framework_res/resources.arsc,
  ./miniandroid/framework_res/resources.arsc).
- Parser notes (S124 laws in arsc_parser.cpp): SPARSE (0x01) /
  OFFSET16 (0x02) ResTable_type encodings, flags byte at offset 9,
  staged duplicate-package chunks skipped (first-id-wins).
