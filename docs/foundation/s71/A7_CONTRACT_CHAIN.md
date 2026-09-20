# A7 — S71 FORENSIC CHAIN (Manifest label/icon generic contract)

## Chain (per mandate: AndroidManifest → resource reference → ARSC → package
## metadata → application → activity → rendered UI)

1. PARSE (manifest_reader.cpp:477 `application_label = get_attribute_value(attrs,"label")`;
   :822 `extract_attr("android:label")`): label captured as the RAW reference
   string (`@0x…` / `@string/…`). `android:icon` is NEVER parsed (no icon
   field anywhere in manifest_reader.h).
2. RESOLVE: the raw reference is never run through the ARSC. The resolution
   law itself EXISTS and is proven (F-136 ARSC-first string law; A2 reference
   law) — manifest attributes simply never consume it.
3. PACKAGE METADATA: `ApplicationInfo` (dalvik_engine.cpp:24768) is a bare
   `get_or_create_singleton` — no label/icon fields materialized. Note: the
   guard is `class_name.find("Context")/find("Activity")` — itself an
   instance of the S71 ANCESTRY-ROOT substring-dispatch law (the
   forensic_classification ANCESTRY-ROOT[ctx-pm] FALSE-UNSERVED row:
   MultiDexApplication.getApplicationInfo misses this guard).
4. CONSUMERS: `application_label` has ZERO runtime consumers (rg over src:
   parser + header only). `getApplicationLabel` / `loadIcon` /
   PackageManager label APIs do not exist. No title-bar surface exists.
5. RENDERED UI: nothing renders the label or icon on HEAD.

## Corrected impact claim

The S66-era "visual: activity title bar shows raw @0x…" is NOT reproducible
on HEAD: with no consumer and no title bar, the raw string surfaces only in
engine.log (:510/:832), not in pixels. The honest impact is "app identity
metadata absent", not "identity rendered wrong".

## Final classification (S71 nine-way)

- A7 = **PARTIAL / TRUE-MISSING split**:
  - parse level: PARTIAL (label captured raw; icon not parsed)
  - law level: TRUE-MISSING — the generic contract "manifest reference
    attributes resolve through ARSC at consume time (AOSP PackageParser +
    Resources.resolveReference; pkg-local + android: namespace fallback)"
    plus its consumer law (PackageManager.getApplicationLabel /
    ApplicationInfo label fields; icon → Bitmap/DRAWABLE-LAW surface).
- NOT app-specific: the contract is generic launcher-identity law.
- Fixture path unchanged (f53_manifest_label); implementation naturally
  bundles with (a) the ANCESTRY-ROOT dispatch fix (getApplicationInfo guard)
  and (b) DRAWABLE-LAW for icon.

Evidence: miniandroid/src/apk/manifest_reader.{h,cpp};
miniandroid/src/dex/dalvik_engine.cpp:24766-24775; docs/foundation/s71/
forensic_classification.json (ANCESTRY-ROOT[ctx-pm] row).
