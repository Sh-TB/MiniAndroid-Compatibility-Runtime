#!/usr/bin/env python3
# cont33_registry.py — add F-NEW-291 + F-NEW-292 to root_registry.json
# (599 -> 601), dedup-checked.
import json

REG = "/home/z/my-project/root_registry.json"
with open(REG) as f:
    r = json.load(f)

ids = [x.get("id") for x in r["roots"]]
assert "F-NEW-291" not in ids, "F-NEW-291 already present — dedup check failed"
assert "F-NEW-292" not in ids, "F-NEW-292 already present — dedup check failed"
assert ids[-1] == "F-NEW-290", f"unexpected tail: {ids[-1]}"

e291 = {
    "id": "F-NEW-291",
    "status": "ROOT_CAUSED_FIXED",
    "title": "STRING.FORMAT LOCALE OVERLOAD: the EXP093 bridge read args[0] as the format string "
             "unconditionally — for the DEX 3-arg overload format(Locale, String, Object...) it "
             "consumed the Locale AS the format (fmt=''), pushed the real '%02d' + the varargs array "
             "into the argument list (the [EXP093-STRFMT] String.format(\"\", n=2) → \"\" log face), "
             "and every Locale-overload call answered the empty string — composeStopwatch Lwv;.p "
             "(format(Locale.US, '%02d', millis%1000) then substring(0,2)) threw "
             "StringIndexOutOfBoundsException (length=0; begin=0; end=2), the composition text pass "
             "died in catch-all churn (Lx30;.n/Lel;.j/Ld91;.c), and the frame stayed "
             "DEFAULT_BACKGROUND_ONLY.",
    "priority": "P1",
    "layer": "dalvik-engine/string-format",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-09, run/cont32+run/cont33: composeStopwatch "
                  "v1.9.1 vc1009011 sha256 dbf937ebbe7c0b3d on binary c280b243f880e7e6 after F-NEW-290): "
                  "Lwv;.p(J)Ljava/lang/String; (androguard decode) pc 0-11 = String.format(Locale.US, "
                  "\"%02d\", Arrays.copyOf([millis%1000])) — the DEX 3-arg Locale overload — pc 15 "
                  "substring(0,2). EXP093 (dalvik_engine.cpp:53280) read args[0] as fmt; the Locale "
                  "OBJECT_REF failed the STRING_REF check so fmt='' and the defensive else pushed "
                  "[fmt-string, array] as fargs (n=2). java_format_walk('') = ''. The SIOOBE is the app's "
                  "uncaught STR-BRIDGE face and its catch-all churn aborted the text pass. ART law: "
                  "java.lang.String.format(Locale l, String format, Object... args) formats with "
                  "args[1] as the format string and args[2] as the varargs array; the two overloads are "
                  "discriminated by DEX arg shape (the 2-arg form is (String, Object[]) so args[1] can "
                  "never be a String there).",
    "fix": "EXP093 overload discrimination by arg SHAPE (no name checks): fmt_idx/varargs_idx shift to "
           "(1,2) when args.size()>=3 && args[0].type != STRING_REF && args[1].type == STRING_REF; "
           "defensive non-array loop starts at varargs_idx. java_format_walk untouched (it already "
           "formats %02d with boxed Long). Probe fixtures/fnew291_probe (real aapt2/ECJ/D8): "
           "FMT-LOC-D2/SUB/2ARG/S/DINT = the Locale-overload contract incl. the exact Lwv;.p consumer "
           "shape; FMT-NOLOC-D2/ARR = the 2-arg regression arm. PRE x3 on c280b243f880e7e6: SUMMARY "
           "FAIL 2 pass 5 fail with FMT-LOC-SUB throwing the EXACT SIOOBE(length=0) face; POST x3 on "
           "fa7dd04c99364cad: SUMMARY PASS 7/0 (\"07\", \"50\", \"01:02\", \"x!\", \"42\"). Target x3: "
           "SIOOBE 1→0/run, EXP093 answers format(\"%02d\", n=1) → \"00\" (was format(\"\", n=2) → \"\").",
    "evidence": "evidence/cont33/FORMAT_LOCALE_FRONTIER.md; run/cont33/f291_pre_r1..3, f291_post_r1..3",
}
e292 = {
    "id": "F-NEW-292",
    "status": "ROOT_CAUSED_FIXED",
    "title": "LIBCORE INTERFACE HIERARCHY GAP (UUID + Enum family): the framework interface tables "
             "(F-NEW-236/F-NEW-253) had no row for java.util.UUID or java.lang.Enum, so "
             "Class.isInstance/instance-of answered FALSE for the Serializable edge on both — "
             "androidx DisposableSaveableStateRegistry.canBeSavedToBundle (whitelist Class[] "
             "{Serializable, Parcelable, String, SparseArray, Binder, Size, SizeF}, decoded from the "
             "upstream ui-android-1.11.4 AAR) rejected the rememberSaveable values: UUID "
             "(IAE '…cannot be saved using the current SaveableStateRegistry…' x51/run, value "
             "Ljava/util/UUID;@7220) and R8-renamed app enums Ll71; extends Ljava/lang/Enum; "
             "(same IAE x26/run) — Lh4;.onMeasure catch-all aborted the measure pass, ops=0, "
             "DEFAULT_BACKGROUND_ONLY.",
    "priority": "P1",
    "layer": "dalvik-engine/framework-hierarchy",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-09, run/cont33: composeStopwatch v1.9.1 "
                  "vc1009011 sha256 dbf937ebbe7c0b3d on binary fa7dd04c99364cad after F-NEW-291): the "
                  "app's real canBeSavedToBundle bytecode (renamed Laj0;.n) walks the whitelist via "
                  "Class.isInstance → F-103 law → dalvik_class_assignable(Ljava/util/UUID;, "
                  "Ljava/io/Serializable;) — identity no, DEX tables absent (platform class), F-NEW-253 "
                  "framework closure EMPTY (no UUID row) → false → IAE x51. Same for app enums: the "
                  "Serializable edge lives on the PLATFORM hop java.lang.Enum (libcore: public abstract "
                  "class Enum implements Comparable, Serializable) — the app class_def declares none and "
                  "the walk checked class_to_interfaces_ (DEX-only) at each hop, never the framework "
                  "tables. ART truth: BOTH saves succeed (UUID Serializable arm; every enum Serializable "
                  "via Enum). Upstream AAR decode (scripts/cont33_jvm_disasm.py, JVM bytecode): "
                  "canBeSavedToBundle = NOT(SnapshotMutableState-policy reject) ∧ NOT(Function∧"
                  "Serializable) ∧ whitelist isInstance walk {Serializable, Parcelable, String, "
                  "SparseArray, Binder, Size, SizeF}.",
    "fix": "One framework_class_interfaces block (view_ancestry.h): UUID row {Serializable, Comparable} + "
           "Enum row {Serializable, Comparable} (libcore source law, receiver-identity keyed, no name "
           "dispatch) + per-hop platform consult in dalvik_class_assignable's superclass walk "
           "(framework_implements(walk, to_desc) after the DEX-table check — intermediate platform hops "
           "see the same boot-classpath truth the F-NEW-253 tail gives from_desc). Probe "
           "fixtures/fnew292_probe: UUID-SER/INSTOF/CMP + ENUM-SER/INSTOF (Tick enum = the Ll71; shape) "
           "+ NEG-PARCEL/STR/CHARSEQ/ENUMSTR over-acceptance guards. PRE (UUID face x3 on "
           "fa7dd04c99364cad): FAIL 3 pass 3 fail, Serializable.isInstance(uuid)=false; PRE (enum face on "
           "c577629024f2a33b): ENUM-SER/INSTOF FAIL. POST x3 on 859557953a3b144c: SUMMARY PASS 9/0 "
           "(negatives honestly false). Target x3: IAE 51→0/run, status FAILURE→PARTIAL SUCCESS, "
           "FIRST PAINTED CONTENT — DIALOG-RENDER window painted, frame 5c4a0172628849ba → "
           "9afb2bd2606f303e x3 deterministic (divergence honestly MOVED: Lh4; ops=0, budget-halt "
           "unwinds at the 15 s harness clock).",
    "evidence": "evidence/cont33/FORMAT_LOCALE_FRONTIER.md; run/cont33/f292_pre_r1..3, f292_pre2_r1, "
                "f292_post_r1..3, f292_post2_r1..3, csw_post292b_r1..3",
}

r["roots"].append(e291)
r["roots"].append(e292)

if "status_counts" in r:
    sc = r["status_counts"]
    for k in ("ROOT_CAUSED_FIXED",):
        sc[k] = sc.get(k, 0) + 2

with open(REG, "w") as f:
    json.dump(r, f, indent=1, ensure_ascii=False)
print("registry now", len(r["roots"]), "roots (599 -> 601)")
