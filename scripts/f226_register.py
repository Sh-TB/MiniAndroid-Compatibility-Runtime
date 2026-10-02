#!/usr/bin/env python3
"""Register F-NEW-222..227 in root_registry.json (user campaign §A-§H wave)."""
import json

R = "/home/z/my-project/root_registry.json"
d = json.load(open(R))
roots = d["roots"] if isinstance(d, dict) else d
have = {r.get("id") for r in roots}

NEW = [
    {
        "id": "F-NEW-222",
        "status": "IMPLEMENTED",
        "priority": "P0",
        "layer": "framework/collections-empty-factory",
        "title": "COLLECTIONS EMPTY-FACTORY LAW: Collections.emptyMap()/emptySet() had NO handler — the bridge fallback answered UNSET, `move-result-object v1` stored an unset register, and the R8 horizontal-merge synthetic ctor <init>(Ljava/lang/Object; I Ljava/lang/Object;)V iput-object'd it into the merged host's field (opencalc LA/h; obj#1232 b=<unset> captured via FIELD-TRACE) → z() Map.get on null → NPE → MainActivity.onCreate APP-BOUNDARY death.",
        "law": "OpenJDK Collections.java: emptyMap()/emptySet() return the SAME shared EMPTY_MAP/EMPTY_SET singleton as the static fields (identity law); every read succeeds per the R-NEW-397 Empty-family contract. Law: the factory routes to the R-NEW-397 singleton (same static_field_storage_ key 'Ljava/util/Collections;.EMPTY_MAP'/'.EMPTY_SET' so == holds across sget and method paths), materialized with __array_length__=0 + __iterator_pos__=0.",
        "evidence": "[F-NEW-222] Collections.emptyMap → shared singleton obj#976 (opencalc run rc NPE→gone); FIELD-TRACE captured put-obj LA/h;.<init> LA/h;.b obj#1232 value=<unset> before fix",
        "fanout": "every Gson/R8-release app that calls Collections.emptyMap/emptySet (Gson factories, DI providers)",
        "test": "opencalc 3-run rc=0 sha=2291d74de0b6bac5 x3 deterministic; goldens byte-identical (dooz/headingcalc/microtimer/whatsapp); laws130 51/51",
        "source": "user campaign §B/§F + opencalc vc53 face",
        "current": "IMPLEMENTED",
        "risk": "",
        "fix": "engine F-039 law extended: emptyMap/emptySet branches with R-NEW-397 singleton identity",
        "after": "opencalc advanced NPE → IAE (next face) with no APP-BOUNDARY NPE",
        "before": "NPE Map.get on null at LA/h;.z pc=12 → MainActivity.onCreate death",
        "aff": [],
    },
    {
        "id": "F-NEW-223",
        "status": "IMPLEMENTED",
        "priority": "P0",
        "layer": "storage/external-volume",
        "title": "VIRTUAL EXTERNAL-STORAGE VOLUME + HONEST FILE CREATION LAW: android.os.Environment had NO handler (getExternalStorageDirectory/State/PublicDirectory/isExternalStorageEmulated/Removable/getRootDirectory/getDataDirectory all REC-MISS) and the File creation family (mkdir/mkdirs/createNewFile) was an EXP-043 pretend-true stub that created NOTHING — the honest R-NEW-346 exists() then read ABSENT and the app died on /storage/emulated/0.",
        "law": "AOSP Environment.java: every device has a primary EMULATED external volume at /storage/emulated/0, state MEDIA_MOUNTED ('mounted'), non-removable; the volume mount point exists from boot. Law: the runtime emulates the volume as a VIRTUAL MOUNT backed by <data_root>/storage/emulated/0 (one sandbox root, deterministic); File metadata laws translate the mount prefix before touching the host filesystem; mkdir/mkdirs/createNewFile REALLY create (create_directories/touch) and answer honestly; Environment.MEDIA_* String constants seeded per AOSP values.",
        "evidence": "user-captured face: app onCreate died because /storage/emulated/0 'does not exist'; [F-NEW-223] Environment statics now answer; FILE-META/mkdir law creates real dirs under the sandbox backing store",
        "fanout": "every app probing external storage at startup (OpenJDK-era storage paths, calculator history, camera/gallery apps)",
        "test": "opencalc/simulation + sandbox: exists() true on the mount point without app mkdirs; mkdirs→exists consistency; goldens byte-identical; laws130 51/51",
        "source": "user campaign §H (CRITICAL)",
        "current": "IMPLEMENTED",
        "risk": "",
        "fix": "host_path_for_virtual_volume prefix translation in R-NEW-346 + honest creation law; Environment static laws + MEDIA_* sget seeds",
        "after": "storage probes answer mounted/exists deterministically under the sandbox",
        "before": "File.exists('/storage/emulated/0')=false; Environment REC-MISS",
        "aff": [],
    },
    {
        "id": "F-NEW-224",
        "status": "IMPLEMENTED",
        "priority": "P1",
        "layer": "dex/descriptor-canonicalization",
        "title": "ONE CANONICAL DESCRIPTOR NORMALIZATION LAW: the four spellings (Landroidx/foo/Bar; / androidx.foo.Bar / androidx/foo/Bar / Landroidx.foo.Bar;) resolved differently — the shared normalizer only handled the L-dotted form, bare-dotted and L-dotted spellings passed through raw, and the superclass hierarchy map stored names in whatever form the toolchain emitted.",
        "law": "Every hierarchy/lookup consumer (superclass walk, method/field/ctor resolution, shadow lookup, View/LayoutParams/framework detection) compares ONLY the canonical internal form Lslashed;. normalize_class_desc handles all four forms (idempotent; primitives/arrays untouched); class_to_superclass_ ingests canonicalized keys AND values at both ingestion points (primary + secondary-DEX).",
        "evidence": "user evidence: parent class names stored with dots instead of slashes broke superclass resolution; ingestion now canonical",
        "fanout": "all hierarchy walks and R8-renamed/renamed-superclass APKs",
        "test": "laws130 51/51; goldens byte-identical (no drift from normalization alone)",
        "source": "user campaign §B",
        "current": "IMPLEMENTED",
        "risk": "",
        "fix": "normalize_class_desc full-form law + canonical ingestion",
        "after": "all four spellings resolve identically",
        "before": "bare-dotted superclasses passed through raw",
        "aff": [],
    },
    {
        "id": "F-NEW-225",
        "status": "IMPLEMENTED",
        "priority": "P0",
        "layer": "reflection/generic-type-identity",
        "title": "GENERIC-TYPE + FRAMEWORK-REFLECTION FAMILY (4 sub-laws): (225a) Field.getGenericType() unbridged → null → Gson TypeToken.get(null) IAE; (225b) framework classes have no DEX body so getDeclaredConstructor(ArrayList,[]) threw NoSuchMethodException (JDK default ctors objectively exist); (225c) Class.getGenericSuperclass() unbridged → null fed TypeToken (plus the JDK collection hierarchy was absent from the framework table); (225d) CLASS_REF if-eq compared mint ref_ids (fresh per token) so `clsA == clsB` never held — Gson getBoundFields loop guard `raw != Object.class` never terminated → getGenericSuperclass(Object)=null → TypeToken(null) IAE → MainActivity.onCreate death.",
        "law": "OpenJDK Field.java: getGenericType NEVER null — no signature metadata → exactly getType() (erased Class). OpenJDK Class.java: getGenericSuperclass null ONLY for Object/interfaces/primitives; else the direct superclass token (erased leg; ParameterizedType leg = registered follow-up). Reflection: public no-arg framework ctors mint Constructor records (JDK default-ctor law). ART: a class has ONE Class object — CLASS_REF if-eq compares canonical descriptors (F-NEW-224 form), completing F-NEW-218/F-069. JDK collection hierarchy edges (ArrayList→AbstractList→AbstractCollection→Object, HashMap→AbstractMap, TextPaint→Paint, ...) added to the shared table.",
        "evidence": "stack e1/d.g ← j1/a.<init> ← f1/m.b (pc=0x132 getGenericType / pc=0x406 getGenericSuperclass); [F-NEW-225c] climb ArrayList→AbstractList→AbstractCollection→Object; [F-NEW-225d] probe showed if-ne same-desc NO + if-eq YES flipping ShowTime.nextActivity/onResume",
        "fanout": "every Gson-serialized app, every reflective framework ctor lookup, every `cls == X.class` token compare",
        "test": "opencalc 3-run rc=0 x3 (NPE/IAE family gone); ssw 3-run new ART-correct flow f48ae6d467d1e746 x3; laws130 51/51; dooz/headingcalc/microtimer/whatsapp byte-identical",
        "source": "user campaign §B/§F-adjacent + opencalc vc53 + ssw faces",
        "current": "IMPLEMENTED (Signature/ParameterizedType parsing leg registered as follow-up)",
        "risk": "",
        "fix": "Field.getGenericType erased fallback; framework default-ctor minting; getGenericSuperclass erased law + hierarchy edges; CLASS_REF descriptor identity in if-eq/if-ne",
        "after": "Gson adapter chain completes; token identity ART-correct",
        "before": "IAE 'Expected a Class, ParameterizedType, or GenericArrayType, but <null> is of type null'",
        "aff": ["F-NEW-218"],
    },
    {
        "id": "F-NEW-226",
        "status": "IMPLEMENTED",
        "priority": "P0",
        "layer": "framework/view-paint-identity",
        "title": "VIEW PAINT IDENTITY LAW: TextView.getPaint() unbridged → NULL → TextPaint.measureText NPE at ssw MyChrono.setFractionView pc=23 (face became reachable after F-NEW-225d removed the token-identity-masked relaunch loop — the OLD golden SHA encoded the wrong-branch flow).",
        "law": "AOSP TextView.java: the view owns ONE TextPaint created at construction; getPaint() returns that SAME object for the view's lifetime (identity contract, like BitmapDrawable.getPaint). Law: per-receiver lazy TextPaint heap object stored as __view_text_paint__; Paint.setTextSize records __text_size_px__ on the paint (default 16sp→42px at the 2.625 density law); TextPaint IS-A Paint edge added to the hierarchy table.",
        "evidence": "225d bisect isolated the face; getPaint law + measureText law → ssw rc=0, real UI frame x3",
        "fanout": "every custom view scaling/metrics code through getPaint (animation scaling, text fitting)",
        "test": "ssw 3-run rc=0 x3 f48ae6d467d1e746 deterministic; goldens byte-identical elsewhere; laws130 51/51",
        "source": "user campaign §A regression requirement + ssw face",
        "current": "IMPLEMENTED",
        "risk": "",
        "fix": "getPaint TextView-family law with per-view identity",
        "after": "setFractionView runs; launcher flow renders real UI",
        "before": "getPaint null → measureText NPE → onCreate death",
        "aff": [],
    },
    {
        "id": "F-NEW-227",
        "status": "IMPLEMENTED",
        "priority": "P1",
        "layer": "graphics/paint-measuretext",
        "title": "PAINT.MEASURETEXT LAW: Paint/TextPaint.measureText had NO handler for any overload — every text-metrics probe answered the generic fallback.",
        "law": "AOSP Paint.java: measureText returns the advance width of the text subset — 0 for an empty range, positive for non-empty text. Deterministic law: 0.5em per code unit driven by the paint's recorded __text_size_px__ (the software runtime has no freetype metric on this bridge; the OBJECT/STATE law — non-null, positive, deterministic — is what app layout logic depends on, same boundary as the audio no-op).",
        "evidence": "ssw setFractionView measureText(String,I,I) now answers; layout scaling logic runs",
        "fanout": "every app measuring text for layout/scaling",
        "test": "ssw 3-run deterministic; laws130 51/51",
        "source": "user campaign §I companion",
        "current": "IMPLEMENTED (shaper-integrated metrics = follow-up)",
        "risk": "",
        "fix": "measureText (String)/(String,I,I) law with paint-size state",
        "after": "positive deterministic widths",
        "before": "unbridged fallback",
        "aff": [],
    },
]

added = 0
for n in NEW:
    if n["id"] not in have:
        roots.append(n)
        added += 1
if isinstance(d, dict):
    d["roots"] = roots
    json.dump(d, open(R, "w"), indent=1, ensure_ascii=False)
else:
    json.dump(roots, open(R, "w"), indent=1, ensure_ascii=False)
print(f"registered {added} new roots; total {len(roots)}")
