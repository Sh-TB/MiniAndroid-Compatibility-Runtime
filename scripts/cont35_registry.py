#!/usr/bin/env python3
# cont35_registry.py — add F-NEW-294/295/296 to root_registry.json
# (602 -> 605), dedup-checked.
import json

REG = "/home/z/my-project/root_registry.json"
with open(REG) as f:
    r = json.load(f)

ids = [x.get("id") for x in r["roots"]]
assert "F-NEW-294" not in ids and "F-NEW-295" not in ids \
    and "F-NEW-296" not in ids, "dedup check failed — one of the ids already present"
assert ids[-1] == "F-NEW-293", f"unexpected tail: {ids[-1]}"

e294 = {
    "id": "F-NEW-294",
    "status": "ROOT_CAUSED_FIXED",
    "title": "AOSP TYPEFACE STATIC LAW MISSING: the engine had NO Typeface law "
             "anywhere — sget-object Typeface.DEFAULT hit [SGET-MISS] and answered "
             "NULL (no platform-constant synthesis row for Landroid/graphics/Typeface;), "
             "and the static create(String,int)/create(Typeface,int)/create(Typeface,"
             "int,boolean)/defaultFromStyle(int) family fell to the typed-default stub "
             "(also NULL). AOSP Typeface.java declares the constants as static finals "
             "built by create() in <clinit> (DEFAULT=create(null,0), DEFAULT_BOLD="
             "create(null,BOLD), SANS_SERIF/SERIF/MONOSPACE) and every create/"
             "defaultFromStyle overload is @NonNull (unknown/empty/null family falls "
             "back to the default family).",
    "priority": "P1",
    "layer": "framework/graphics-typeface",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-10, run/cont35: composeStopwatch "
                  "v1.9.1 vc1009011 sha256 dbf937ebbe7c0b3d baseline x3 on binary 702813ff2d5d8be8 "
                  "== the CONT-34 record): exactly ONE [SGET-MISS] key=Landroid/graphics/Typeface;"
                  ".DEFAULT per run, then [SYNTH-EXC] f141-null-recv NPE \"Attempt to invoke virtual "
                  "method 'Ljava/lang/Object;.getClass' on a null object reference\" at Lk6;.<init> "
                  "pc=409 (R8-obfuscated AndroidParagraphIntrinsics) — the Kotlin platform-type `!!` "
                  "check compiled as invoke-virtual getClass() BEFORE check-cast Typeface. Decode "
                  "(androguard instruction-level): FontListFontFamilyTypefaceAdapter.resolve "
                  "(Lt10;.a/.b) wraps the platform typeface into TypefaceResult(value=Luh1;.e, "
                  "immediate=Luh1;.f); with a NULL DEFAULT the value field is null and the consumer's "
                  "getClass() NPE kills the text pass every run (the Compose stopwatch view Lh4; "
                  "stays onDraw ops=0).",
    "fix": "TWO generic laws, no name dispatch beyond the class: (1) sget-object constant "
           "synthesis row for Landroid/graphics/Typeface; {DEFAULT, DEFAULT_BOLD, SANS_SERIF, "
           "SERIF, MONOSPACE} — real heap Typeface objects carrying __typeface_family__/"
           "__typeface_style__ (AOSP clinit values), cached per static_key so identity holds, "
           "same shape as the Boolean/Locale/StandardCharsets arms; (2) bridge_to_api static "
           "law: create(String,int)/create(Typeface,int)/create(Typeface,int,boolean API 28+)/"
           "defaultFromStyle(int) — per-request-cached non-null Typeface objects, null/empty/"
           "unknown family falls back to 'sans-serif', weight/italic carried for the API 28+ "
           "form. Probe fixtures/fnew294_probe (real aapt2/ECJ/D8): TF-DEFAULT (THE SGET-MISS "
           "row), TF-CONST-FAMILY, TF-CONSUMER-SHAPE (the exact pc=409 getClass-then-cast twin), "
           "TF-CREATE-STR/NULLFAM/EMPTY/TF/3ARG, TF-DFS, TF-CREATE-IDEM (same-request identity). "
           "PRE x3 on 702813ff2d5d8be8: SUMMARY FAIL 0/10 (got=null everywhere; the consumer "
           "row threw the recorded NPE). POST x3 on the fix binary: SUMMARY PASS 10/0.",
    "evidence": "evidence/cont35/TEXT_PIPELINE_FRONTIER.md; runs run/cont35/{csw_baseline,"
                "f294_pre_r1..3,f294_post_r1..3,csw_post294_r1..3}; probe fixtures/fnew294_probe "
                "committed + wired into scripts/w4_build_probes.sh (standing battery).",
    "fixed_in": "CONT-35 (binary d354e40ba5e6a6d9, pre-295/296)",
    "fanout": "every app that resolves the DEFAULT font family through the Compose text "
              "pipeline (AndroidParagraphIntrinsics) or Paint text setup; the platform-"
              "constant law family (Boolean/Locale/Charset/Environment/Collections/"
              "Typeface) is now complete for the graphics/text stack.",
    "date": "2026-10-10",
}

e295 = {
    "id": "F-NEW-295",
    "status": "ROOT_CAUSED_FIXED",
    "title": "FRAMEWORK ENUM TABLE GAP (android.text.Layout$Alignment): the 371-CLOSEOUT "
             "generic values()/valueOf() law is TABLE-DRIVEN — an enum class with no "
             "kOrdinals rows still answers NULL for values(). Layout$Alignment had no "
             "rows, so the Compose text-layout alignment resolver (Ljd1;.<clinit> in "
             "composeStopwatch) died at its first array-length: values() returned NULL "
             "-> NPE \"Attempt to get length of null array\" at pc=6, one per run.",
    "priority": "P1",
    "layer": "framework/text-enum-table",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-10, run/cont35/csw_post294_r1..3): "
                  "after F-NEW-294 the f141 pc=409 face moved onward to [SYNTH-EXC] ARR-LEN-NULL "
                  "at Ljd1;.<clinit> pc=6. Decode (androguard + a proper field-ref decode of the "
                  "toolchain's android-34.jar): Ljd1;.<clinit> calls Layout.Alignment.values(), "
                  "searches the array for the NAMES \"ALIGN_LEFT\"/\"ALIGN_RIGHT\" and falls back "
                  "to the ALIGN_NORMAL sget — but the platform class has exactly THREE constants "
                  "(ALIGN_NORMAL=0, ALIGN_OPPOSITE=1, ALIGN_CENTER=2, decoded instruction-level "
                  "from the jar clinit; no ALIGN_LEFT/RIGHT members exist on this API level), and "
                  "with no kOrdinals rows the 371-CLOSEOUT values() arm found no constants and "
                  "answered NULL before the search could even run.",
    "fix": "THREE kOrdinals table rows (the AOSP declaration order decoded from the "
           "android-34.jar clinit): ALIGN_NORMAL=0, ALIGN_OPPOSITE=1, ALIGN_CENTER=2. The "
           "generic values()/valueOf() machinery (371-CLOSEOUT) then answers every accessor "
           "from the same table the sget constant law uses — identity coherent by construction. "
           "Probe fixtures/fnew295_probe: LA-VALUES-SIZE (the array-length twin), LA-VALUES-ORDER "
           "(the decoded AOSP order), LA-VALUES-ITER (the exact Ljd1;.<clinit> name-search + "
           "ALIGN_NORMAL fallback shape), LA-SGET (sget/values identity), LA-VALUEOF (+identity), "
           "LA-VALUEOF-NEG (unknown name -> IAE, j.l.Enum law). PRE x3 on d354e40ba5e6a6d9: "
           "SUMMARY FAIL 0/6 (\"len=null-arr\"; the iter row threw the recorded NPE). POST x3: "
           "SUMMARY PASS 6/0.",
    "evidence": "evidence/cont35/TEXT_PIPELINE_FRONTIER.md; runs run/cont35/{csw_post294_r1..3,"
                "f295_pre_r1..3,f295_post_r1..3,csw_post295_r1..3}; probe fixtures/fnew295_probe "
                "committed + wired into scripts/w4_build_probes.sh.",
    "fixed_in": "CONT-35 (binary e974e0204624854e, pre-296)",
    "fanout": "every framework enum the engine has no rows for still answers NULL from "
              "values() — the law is table-driven by design; new consumer enums are one "
              "table block each (Layout$Alignment done this wave; the AOSP jar clinit is "
              "the decode source of record).",
    "date": "2026-10-10",
}

e296 = {
    "id": "F-NEW-296",
    "status": "ROOT_CAUSED_FIXED",
    "title": "AOSP LINEBREAKCONFIG BUILDER OBJECT LAW MISSING (android.graphics.text, "
             "API 33+; Builder API 34): new LineBreakConfig$Builder() allocated but the "
             "engine had NO law for the fluent setters, so setLineBreakStyle(...) returned "
             "the typed-default NULL and the chain broke at the SECOND link (the recorded "
             "NPE is AT setLineBreakWordStyle, not at the first setter). AOSP LineBreak"
             "Config.java: Builder() defaults (STYLE_NONE/WORD_STYLE_NONE), setters FLUENT "
             "(@NonNull return this), build() @NonNull.",
    "priority": "P1",
    "layer": "framework/graphics-text-linebreak",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-10, run/cont35/csw_post295_r1..3): "
                  "after F-NEW-295 the face moved onward to [SYNTH-EXC] f141-null-recv \"Attempt "
                  "to invoke virtual method 'Landroid/graphics/text/LineBreakConfig$Builder;."
                  "setLineBreakWordStyle' on a null object reference\" at Lb1;.n pc=0. Decode "
                  "(androguard): the Compose StaticLayout.Builder applier (Llw;.i) gates on "
                  "SDK >= 33 and runs new Builder().setLineBreakStyle(s).setLineBreakWordStyle(w)"
                  ".build() (Lb1;.a/.b/.n/.c) then StaticLayout$Builder.setLineBreakConfig "
                  "(Lb1;.i) — with no setter law the fluent chain received null at the first "
                  "setter and NPE'd at the second; the probe row LBC-FLUENT reproduced the exact "
                  "break shape (first setter OK on the non-null builder, second NPE on the null "
                  "return).",
    "fix": "TWO generic laws: (1) bridge_to_api LineBreakConfig$Builder object law (same "
           "family as AudioAttributes$Builder): <init> seeds the builder fields, "
           "setLineBreakStyle/setLineBreakWordStyle store + return THIS, build() allocates a "
           "real LineBreakConfig carrying __lbc_style__/__lbc_word_style__; (2) "
           "StaticLayout$Builder whitelist + storage arm for setLineBreakConfig (API 33+ "
           "fluent setter, stored opaque like the other builder fields). Probe "
           "fixtures/fnew296_probe: LBC-CHAIN (the exact Llw;.i shape — pre-fix threw the "
           "recorded NPE), LBC-BUILD, LBC-FLUENT (identity-welded chain), LBC-CONSTS "
           "(STYLE_NONE=0/WORD_STYLE_NONE=0), LBC-NEG (per-instance builders). PRE x3 on "
           "e974e0204624854e: SUMMARY FAIL 2/3. POST x3: SUMMARY PASS 5/0.",
    "evidence": "evidence/cont35/TEXT_PIPELINE_FRONTIER.md; runs run/cont35/{csw_post295_r1..3,"
                "f296_pre_r1..3,f296_post_r1..3,csw_post296_r1..3}; probe fixtures/fnew296_probe "
                "committed + wired into scripts/w4_build_probes.sh.",
    "fixed_in": "CONT-35 (binary 6508a51d01b54280)",
    "fanout": "every Compose text view on the SDK>=33 gate builds a LineBreakConfig through "
              "this chain; the StaticLayout$Builder.setLineBreakConfig whitelist row covers "
              "the StaticLayout-side consumer family.",
    "date": "2026-10-10",
}

r["roots"].append(e294)
r["roots"].append(e295)
r["roots"].append(e296)
with open(REG, "w") as f:
    json.dump(r, f, indent=2, ensure_ascii=False)
print("registry:", len(ids), "->", len(r["roots"]))
print("tail:", [x["id"] for x in r["roots"][-3:]])
