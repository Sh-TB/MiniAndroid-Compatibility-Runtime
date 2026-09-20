#!/usr/bin/env python3
"""s71_forensic.py — S71 FOUNDATION FORENSIC TRIAGE (Rule 0: classify, don't implement).

Forensic pipeline per §2 of the S71 mandate, applied to the S70 LIVE-STUB
surface (136) + P0 (10). Uses ONLY S70 artifacts + the fresh S71 live traces
(run/s71_live — same canonical recipe as s69_live_runs.sh):

  API → STATIC EVIDENCE (dex_census sites × APKs)
      → LIVE TRACE EVIDENCE (fresh per-call records: args, return, caller pc)
      → ENGINE SOURCE (handler-pair existence from graph/functions.json +
        manually-verified guard bodies cited by file:line)
      → DISPATCH PATH (bridge-handler | interpreter-DEX-body | intrinsic |
        object-model)
      → INTRINSIC PATH? (does the opcode/object model make the stub moot?)
      → UPSTREAM CONTRACT (upstream_oracle.json)
      → REAL CONSUMERS (fresh-trace apps × events)
      → TEST COVERAGE (tested_by fixtures)
      → FINAL CLASSIFICATION ∈ {TRUE-MISSING, FALSE-UNSERVED, INTRINSIC,
        IMPLEMENTED-CORRECT, IMPLEMENTED-WRONG, PARTIAL, DEAD/UNREACHABLE,
        APP-SPECIFIC, UNKNOWN}

Usage: s71_forensic.py [--json OUT] [--only SUBSTR]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/z/my-project")
GDIR = ROOT / "docs" / "foundation"

# ── forensic resolution table ───────────────────────────────────────────────
# Each entry: engine source evidence (file:line), dispatch path, and the
# S71 final classification with the law that justifies it. Produced by
# manual guard-body review (S71 W3) — NOT by name matching alone.
RESOLUTION = {
    # ── P0 ──
    "Ljava/lang/Enum;.valueOf": {
        "dispatch": "bridge (called from compiler-generated concrete-enum "
                    "valueOf bodies, which the interpreter runs as DEX)",
        "source": "dalvik_engine.cpp:28737-28790 enum law handles "
                  "<init>/compareTo/ordinal/name/toString only; valueOf falls "
                  "to the default type-null stub",
        "upstream": "libcore/ojluni java.lang.Enum.valueOf(Class,String): "
                    "null type/name → NPE; non-enum class → IAE; unknown name "
                    "→ IAE 'No enum constant …'; else the shared constant",
        "classification": "TRUE-MISSING",
        "silent_wrong": True,
        "note": "260 static sites are INSIDE compiler-generated concrete "
                "valueOf(String) DEX bodies (census dooz23: 74 sites; e.g. "
                "Lal0;->valueOf runs Enum.valueOf(Class,String) via bridge). "
                "Default stub returns NULL → every string→enum parse fails "
                "silently downstream.",
        "family": "ENUM-LAW",
    },
    "Ljava/lang/String;.<init>": {
        "dispatch": "bridge (invoke-direct on new-instance'd String object)",
        "source": "no String;<init> guard anywhere in dalvik_engine.cpp "
                  "(rg 'String;\" && method == \"<init>\"' → 0 hits); only "
                  "instance methods (length/charAt/…) have handlers",
        "upstream": "libcore/ojluni String.java ctors: ([C) / ([C,II) copy "
                    "chars; ([B,Charset)/( [B,String) decode; (String) copy",
        "classification": "TRUE-MISSING",
        "silent_wrong": True,
        "note": "81 sites; dominant overloads ([C III)=39, ([C)=10, "
                "([B charset …)=20. new-instance allocates an empty heap "
                "String; <init> stub leaves content empty → downstream "
                "length/charAt/append see empty string (silent, not a crash).",
        "family": "STRING-CTOR-LAW",
    },
    "Landroid/widget/TextView;.setTextSize": {
        "dispatch": "bridge handler EXISTS and applies px "
                    "(EXT-AOSP-002) but never sets status=IMPLEMENTED / "
                    "returns true → bookkeeping STUBBED",
        "source": "dalvik_engine.cpp:20437-20480 (AOSP TextView.java@1cdfff55 "
                  "L4720-4762); guard matches method name for ANY class "
                  "(Button/CheckBox/EditText inherit the same path)",
        "upstream": "AOSP TextView.setTextSp + TypedValue.applyDimension "
                    "COMPLEX_UNIT_SP × scaledDensity",
        "classification": "PARTIAL",
        "silent_wrong": False,
        "note": "behavior may apply; trace records STUBBED for all 5 "
                "setTextSize variants (TextView/Button/CheckBox/EditText). "
                "Bookkeeping defect + unproven px path (needs fixture "
                "evidence before trusting). NOT a clean TRUE-MISSING.",
        "family": "TEXTSIZE-FAMILY",
    },
    "Ljava/util/List;.contains": {
        "dispatch": "bridge after F-068 runtime-class-first walk misses",
        "source": "contains handlers exist ONLY for TreeSet "
                  "(dalvik_engine.cpp:27182) and SharedPreferences (:23731); "
                  "no List/ArrayList/Collection contains guard",
        "upstream": "OpenJDK ArrayList.contains(o): o==null ? scan for null : "
                    "o.equals(element) scan",
        "classification": "TRUE-MISSING",
        "silent_wrong": True,
        "note": "53 sites + Collection.contains 48 sites. Default stub "
                "returns FALSE (Z law) → membership checks silently wrong. "
                "Receiver runtime class is frequently a shadow/synthesized "
                "ArrayList → runtime-class walk cannot find a DEX body.",
        "family": "COLLECTION-ELEMENTS-LAW",
    },
    "Ljava/util/Arrays;.sort": {
        "dispatch": "bridge — no guard at all",
        "source": "rg 'method == \"sort\"' → 0 hits; Arrays has asList (:20698) "
                  "and fill (:21307) only",
        "upstream": "OpenJDK Arrays.sort: dual-pivot quicksort (primitives) / "
                    "TimSort (objects, stable); POST-STATE law: array is "
                    "permuted into total order",
        "classification": "TRUE-MISSING",
        "silent_wrong": True,
        "note": "45 sites × 6 APKs. Void return → default stub hides that the "
                "array was never permuted → silent wrong order downstream "
                "(scores, leaderboards, timers).",
        "family": "ARRAYS-ORDER-LAW",
    },
    "Ljava/util/LinkedHashSet;.<init>": {
        "dispatch": "bridge — no HashSet/LinkedHashSet guard",
        "source": "rg 'HashSet' → comment only (:19505)",
        "upstream": "OpenJDK LinkedHashSet: insertion-ordered set backed by "
                    "linked hash buckets; Collection ctor copies + dedups",
        "classification": "TRUE-MISSING",
        "silent_wrong": True,
        "note": "35 sites × 4 APKs; ctor stub → set stays EMPTY → add/contains/"
                "iterate silently wrong (dedup loops never dedup).",
        "family": "COLLECTION-ELEMENTS-LAW",
    },
    "Ljava/lang/ThreadLocal;.get": {
        "dispatch": "bridge — no ThreadLocal guard anywhere",
        "source": "rg '\"Ljava/lang/ThreadLocal;\"' → 0 hits (only "
                  "ThreadLocalRandom F-086 exists)",
        "upstream": "OpenJDK ThreadLocal: per-thread map keyed by the "
                    "ThreadLocal instance; get → initial value after set; "
                    "unset → initialValue (null unless overridden)",
        "classification": "TRUE-MISSING",
        "silent_wrong": True,
        "note": "get 30 + set 20 + <init> 27 sites × 4 APKs. get→null default "
                "poisons every lazy-init/computeIfAbsent-via-TL pattern; "
                "set→void hides state loss.",
        "family": "THREADLOCAL-LAW",
    },
    "Ljava/lang/ThreadLocal;.<init>": {"family": "THREADLOCAL-LAW",
        "classification": "TRUE-MISSING", "silent_wrong": True,
        "note": "same family root as ThreadLocal.get/set — one law.",
        "dispatch": "bridge — no guard", "source": "see ThreadLocal.get",
        "upstream": "OpenJDK ThreadLocal.<init>"},
    "Ljava/lang/ThreadLocal;.set": {"family": "THREADLOCAL-LAW",
        "classification": "TRUE-MISSING", "silent_wrong": True,
        "note": "same family root as ThreadLocal.get.",
        "dispatch": "bridge — no guard", "source": "see ThreadLocal.get",
        "upstream": "OpenJDK ThreadLocal.set"},
    "Ljava/util/Random;.<init>": {
        "dispatch": "bridge ctor stub + WORKING nextInt law",
        "source": "Random.<init> has no guard, but nextInt IS implemented "
                  "(F-086 dalvik_engine.cpp:21077-21125, deterministic policy)",
        "upstream": "OpenJDK Random(seed): split-mix64 per next(); this "
                    "runtime pins a deterministic seed law (documented)",
        "classification": "PARTIAL",
        "silent_wrong": False,
        "note": "ctor no-op is harmless because nextInt keys on class+args, "
                "not heap state; classification PARTIAL (ctor unbookkeeped, "
                "behavior served by F-086). verify nextInt live in gmdice.",
        "family": "RANDOM-LAW",
    },
}

# platform-optional subsystems: no runtime equivalent by architecture
INTRINSIC_SUBSTR = (
    "Ljavax/microedition/khronos/egl/",   # GL path — software renderer runtime
    "Landroid/app/Notification",          # notification subsystem absent
    "Landroid/app/NotificationManager;",
    "Landroid/media/SoundPool;",          # audio subsystem absent
)

# app-defined receiver classes misattributed as APIs
APP_PREFIXES = ("Lapp/", "Lcom/", "Lde/", "Ldubrowgn/", "Lfishrings/",
                "Lg10;", "Lho;", "Lone/", "Lio/github/yamin8000/",
                "Lopmt/", "Lnet/", "Lorg/myapp/")

# ── S71 W5 ROOT LAW #1: substring-dispatch → ancestry-dispatch ─────────────
# 39 Context/Activity-family guards in dalvik_engine.cpp use
# class_name.find("Context")/find("Activity") — NOT ancestry. Android law
# (AOSP Context.java): Application/Service extend Context; Activity extends
# ContextThemeWrapper extends Context. Any framework method dispatched with a
# receiver whose RUNTIME class is an app subclass (or Application) misses the
# guard → type-default stub. Covers Application.* records AND the app-class
# records (inherited framework methods, e.g. GameMasterDice.getResources,
# NoteMain.getWindow). The census hid these under app class names (S70
# already flagged "substring-dispatch families invisible" — this is the
# runtime-dispatch twin of that extractor defect).
ANCESTRY_ROOT = {
    "Landroid/app/Application;.getCacheDir": ("getCacheDir", "io-file"),
    "Landroid/app/Application;.getDatabasePath": ("getDatabasePath", "io-file"),
    "Landroid/app/Application;.getSystemService": ("getSystemService", "ctx-svc"),
    "Landroid/app/Application;.getTheme": ("getTheme", "theme"),
    "Lapp/varlorg/unote/NoteMain;.getWindow": ("getWindow", "window"),
    "Lapp/varlorg/unote/NoteMain;.setTheme": ("setTheme", "theme"),
    "Lapp/varlorg/unote/NoteMain;.registerForContextMenu": ("registerForContextMenu", "menu"),
    "Lcom.dozingcatsoftware.bouncy.GLFieldView;.getHolder": None,  # genuine GL surface law, not context
    "Lcom/dozingcatsoftware/bouncy/BouncyActivity;.getAssets": ("getAssets", "assets"),
    "Lcom/dozingcatsoftware/bouncy/BouncyActivity;.getBaseContext": ("getBaseContext", "ctx-wrapper"),
    "Lcom/dozingcatsoftware/bouncy/BouncyActivity;.registerReceiver": ("registerReceiver", "ctx-svc"),
    "Lcom/dozingcatsoftware/bouncy/BouncyActivity;.requestWindowFeature": ("requestWindowFeature", "window"),
    "Lcom/dozingcatsoftware/bouncy/BouncyActivity;.setVolumeControlStream": ("setVolumeControlStream", "window"),
    "Lde/duenndns/gmdice/GameMasterDice;.getResources": ("getResources", "res"),
    "Lde/duenndns/gmdice/GameMasterDice;.setListAdapter": ("setListAdapter", "list-activity"),
    "Lde/duenndns/gmdice/GameMasterDice;.setTitle": ("setTitle", "activity"),
    "Ldubrowgn/microtimer/MainActivity;.setShowWhenLocked": ("setShowWhenLocked", "window"),
    "Ldubrowgn/microtimer/MainActivity;.setTurnScreenOn": ("setTurnScreenOn", "window"),
    "Lio/github/yamin8000/dooz/ui/App;.getApplicationContext": ("getApplicationContext", "ctx-wrapper"),
    "Lio/github/yamin8000/dooz/ui/MainActivity;.getFragmentManager": ("getFragmentManager", "activity"),
    "Lio/github/yamin8000/dooz/ui/MainActivity;.getLastNonConfigurationInstance": ("getLastNonConfigurationInstance", "activity"),
    "Lone/scarecrow/games/OPMT/MainMenu;.getWindow": ("getWindow", "window"),
    "Landroid/support/multidex/MultiDexApplication;.getApplicationInfo": ("getApplicationInfo", "ctx-pm"),
}

# ── S71 W5: family resolution for platform UNKNOWNs (source-scanned) ──────
FAMILY_ROWS = {
    # WINDOW-CHROME family (0 handlers each; software-renderer runtime)
    "Landroid/view/Window;.setStatusBarColor": ("WINDOW-CHROME", "INTRINSIC"),
    "Landroid/view/Window;.setNavigationBarColor": ("WINDOW-CHROME", "INTRINSIC"),
    "Landroid/view/Window;.setStatusBarContrastEnforced": ("WINDOW-CHROME", "INTRINSIC"),
    "Landroid/view/Window;.setNavigationBarContrastEnforced": ("WINDOW-CHROME", "INTRINSIC"),
    "Landroid/view/Window;.setDecorFitsSystemWindows": ("WINDOW-CHROME", "INTRINSIC"),
    "Landroid/view/Window;.getInsetsController": ("WINDOW-CHROME", "TRUE-MISSING"),
    "Landroid/view/Window;.getAttributes": ("WINDOW-CHROME", "TRUE-MISSING"),
    "Landroid/view/WindowManager;.getDefaultDisplay": ("WINDOW-CHROME", "TRUE-MISSING"),
    "Landroid/view/View;.setSystemUiVisibility": ("WINDOW-CHROME", "INTRINSIC"),
    "Landroid/view/View;.getSystemUiVisibility": ("WINDOW-CHROME", "TRUE-MISSING"),
    "Landroid/view/SurfaceHolder;.setFormat": ("WINDOW-CHROME", "INTRINSIC"),
    "Landroid/view/View;.getViewTreeObserver": ("VIEWOBSERVER-LAW", "TRUE-MISSING"),
    "Landroid/view/View;.getResources": ("VIEW-RES-LAW", "TRUE-MISSING"),
    # WIDGET-BEHAVIOR family (0 handlers; state/listener laws)
    "Landroid/widget/CheckBox;.setChecked": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/CheckBox;.setOnCheckedChangeListener": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/CheckBox;.setTextSize": ("TEXTSIZE-FAMILY", "PARTIAL"),
    "Landroid/widget/EditText;.setTextSize": ("TEXTSIZE-FAMILY", "PARTIAL"),
    "Landroid/widget/Button;.setTextSize": ("TEXTSIZE-FAMILY", "PARTIAL"),
    "Landroid/widget/EditText;.addTextChangedListener": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/Button;.getBackground": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/Button;.setTransformationMethod": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/GridView;.setAdapter": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/GridView;.setOnItemClickListener": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/ListView;.setAdapter": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/ListView;.setOnItemClickListener": ("WIDGET-LISTENER-LAW", "TRUE-MISSING"),
    "Landroid/widget/ListView;.setDivider": ("WIDGET-LISTENER-LAW", "INTRINSIC"),
    "Landroid/widget/ListView;.setDividerHeight": ("WIDGET-LISTENER-LAW", "INTRINSIC"),
    # COLLECTIONS family (0 handlers; silent-wrong via type-default law)
    "Ljava/util/BitSet;.<init>": ("BITSET-LAW", "TRUE-MISSING"),
    "Ljava/util/ArrayDeque;.<init>": ("COLLECTION-ELEMENTS-LAW", "TRUE-MISSING"),
    "Ljava/util/PriorityQueue;.<init>": ("COLLECTION-ELEMENTS-LAW", "TRUE-MISSING"),
    "Ljava/util/TreeMap;.<init>": ("COLLECTION-ELEMENTS-LAW", "TRUE-MISSING"),
    "Ljava/util/TreeMap;.ceilingEntry": ("COLLECTION-ELEMENTS-LAW", "TRUE-MISSING"),
    "Ljava/util/TreeMap;.size": ("COLLECTION-ELEMENTS-LAW", "TRUE-MISSING"),
    # IO/NIO family
    "Ljava/io/ByteArrayOutputStream;.<init>": ("BAOS-LAW", "TRUE-MISSING"),
    "Ljava/io/ByteArrayOutputStream;.write": ("BAOS-LAW", "TRUE-MISSING"),
    "Ljava/io/ByteArrayOutputStream;.toByteArray": ("BAOS-LAW", "TRUE-MISSING"),
    "Ljava/nio/ByteOrder;.nativeOrder": ("NIO-LAW", "TRUE-MISSING"),
    "Ljava/nio/ByteBuffer;.allocateDirect": ("NIO-LAW", "TRUE-MISSING"),
    # CONCURRENCY family
    "Ljava/lang/Thread;.interrupted": ("THREAD-STATE-LAW", "TRUE-MISSING"),
    # MISC-JAVA
    "Ljava/lang/Long;.getLong": ("PROPS-LAW", "TRUE-MISSING"),
    "Ljava/lang/Runtime;.getRuntime": ("RUNTIME-LAW", "TRUE-MISSING"),
    # FRAMEWORK-DATA family
    "Landroid/net/Uri;.parse": ("URI-LAW", "TRUE-MISSING"),
    "Landroid/os/Bundle;.<init>": ("BUNDLE-LAW", "TRUE-MISSING"),
    "Landroid/content/Intent;.getExtras": ("BUNDLE-LAW", "TRUE-MISSING"),
    "Landroid/content/IntentFilter;.<init>": ("INTENTFILTER-LAW", "TRUE-MISSING"),
    "Landroid/util/TypedValue;.<init>": ("TYPEDVALUE-LAW", "TRUE-MISSING"),
    "Landroid/util/TypedValue;.applyDimension": ("TYPEDVALUE-LAW", "TRUE-MISSING"),
    "Landroid/content/pm/PackageManager;.hasSystemFeature": ("PKG-FEATURE-LAW", "TRUE-MISSING"),
    "Landroid/os/PowerManager;.isIgnoringBatteryOptimizations": ("PKG-FEATURE-LAW", "INTRINSIC"),
    "Landroid/app/KeyguardManager;.requestDismissKeyguard": ("PKG-FEATURE-LAW", "INTRINSIC"),
    # GRAPHICS-MISC
    "Landroid/graphics/drawable/ShapeDrawable;.<init>": ("DRAWABLE-LAW", "TRUE-MISSING"),
    "Landroid/graphics/drawable/ShapeDrawable;.getPaint": ("DRAWABLE-LAW", "TRUE-MISSING"),
    "Landroid/graphics/drawable/ShapeDrawable;.setShape": ("DRAWABLE-LAW", "TRUE-MISSING"),
    "Landroid/graphics/drawable/shapes/RectShape;.<init>": ("DRAWABLE-LAW", "TRUE-MISSING"),
    # DB/JSON
    "Landroid/database/sqlite/SQLiteDatabase;.equals": ("OBJECT-EQUALS-LAW", "IMPLEMENTED-WRONG"),
    "Lorg/json/JSONObject;.keys": ("JSON-LAW", "TRUE-MISSING"),
    # support no-op paths
    "Landroid/app/Application;<super>.attachBaseContext": ("SUPER-CALL-BOOKKEEPING", "IMPLEMENTED-CORRECT"),
    "Landroid/app/Application;<super>.onCreate": ("SUPER-CALL-BOOKKEEPING", "IMPLEMENTED-CORRECT"),
}

# <unknown>.method correlation table (S71 W5: trace-level api_class defect;
# behavior VARIES per method — real handler vs type-default decided by the
# fresh-trace return values)
UNKNOWN_METHOD_ROWS = {
    "getClass": ("OBJECT-CLASS-LAW", "TRUE-MISSING",
                 "14× null in dooz23 — Object.getClass F-088 exists but its "
                 "receiver coverage misses these objects; behavior gap real"),
    "getDeclaredField": ("REFLECTION-LAW", "PARTIAL",
                         "31 events return Field objects (reflection law "
                         "partially serves); needs audit of which fields"),
    "equals": ("OBJECT-EQUALS-LAW", "TRUE-MISSING",
               "7× false — identity equals law missing on unknown-class receivers"),
    "getName": ("CLASS-LAW", "FALSE-UNSERVED",
                 "returns real value 'dubrowgn.microtimer…' — handler ran; "
                 "trace api_class=<unknown> is a recording defect only"),
    "getColor": ("RES-COLOR-LAW", "FALSE-UNSERVED",
                 "returns real color -16248824 — served; recording defect"),
    "length": ("STRING-LAW", "FALSE-UNSERVED",
               "returns 22 — served; recording defect"),
    "contains": ("COLLECTION-ELEMENTS-LAW", "TRUE-MISSING",
                 "5× false type-default — real miss"),
    "startsWith": ("STRING-LAW", "TRUE-MISSING",
                   "5× false type-default — real miss"),
    "order": ("NIO-LAW", "TRUE-MISSING", "4× null — ByteBuffer.order miss"),
    "asIntBuffer": ("NIO-LAW", "TRUE-MISSING", "4× null — real miss"),
    "split": ("STRING-LAW", "PARTIAL", "5 events; String.split exists for "
              "some shapes — arg-shape gap"),
    "setColorFilter": ("DRAWABLE-LAW", "TRUE-MISSING", "5× void default"),
    "isInstance": ("OBJECT-CLASS-LAW", "TRUE-MISSING", "3× false default"),
    "getParentFile": ("IO-FILE-LAW", "TRUE-MISSING", "3× null default"),
    "getConfiguration": ("CTX-SVC-LAW", "PARTIAL", "2 events return object"),
    "isAnonymousClass": ("CLASS-LAW", "TRUE-MISSING", "2× false default"),
    "isArray": ("CLASS-LAW", "TRUE-MISSING", "2× false default"),
    "isLocalClass": ("CLASS-LAW", "TRUE-MISSING", "2× false default"),
    "isPrimitive": ("CLASS-LAW", "TRUE-MISSING", "2× false default"),
    "beginTransaction": ("FRAGMENT-TX-LAW", "TRUE-MISSING", "2× void default"),
    "commit": ("FRAGMENT-TX-LAW", "TRUE-MISSING", "2× void/bool default"),
    "executePendingTransactions": ("FRAGMENT-TX-LAW", "TRUE-MISSING", "2× default"),
    "findFragmentByTag": ("FRAGMENT-TX-LAW", "TRUE-MISSING", "2× null default"),
    "addOnDrawListener": ("VIEWOBSERVER-LAW", "TRUE-MISSING", "1× void default"),
    "availableProcessors": ("RUNTIME-LAW", "TRUE-MISSING", "1× 0 default"),
    "list": ("IO-FILE-LAW", "TRUE-MISSING", "1× null default"),
    "longValue": ("BOXING-LAW", "TRUE-MISSING", "1× 0 default"),
    "resolveAttribute": ("THEME-LAW", "TRUE-MISSING", "1× default"),
    "set": ("MAP-LAW", "TRUE-MISSING", "1× void default"),
    "setMargins": ("LAYOUT-LAW", "TRUE-MISSING", "1× void default"),
    "setStatusBarColor": ("WINDOW-CHROME", "INTRINSIC", "cosmetic in this runtime"),
    "getRefreshRate": ("WINDOW-CHROME", "PARTIAL", "returns 0.0 — harmless default"),
}


def load(p, d=None):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else d


def is_platform(api):
    return api.startswith(("Landroid/", "Ljava/", "Lkotlin", "Lj$/"))


def is_app_defined(api):
    cls = api.split(".", 1)[0] if "." in api else api
    if api.startswith("<unknown>"):
        return False
    return cls.startswith(APP_PREFIXES)


def main():
    only = None
    args = sys.argv[1:]
    if "--only" in args:
        only = args[args.index("--only") + 1]

    kg = load(GDIR / "knowledge_graph.json", {})
    apis = kg.get("apis", {})
    stubs = {k: v for k, v in apis.items()
             if v.get("status") in ("LIVE-STUB", "LIVE-PARTIAL")
             or k in RESOLUTION}

    # fresh live traces (S71 re-run)
    fresh = defaultdict(list)   # api -> [(apk, call)]
    for d in sorted((ROOT / "run" / "s71_live").glob("*/api_calls.json")):
        apk = d.parent.name + ".apk"
        for c in load(d, []):
            fresh[c.get("api", "?")].append((apk, c))

    # handler-pair existence from the S70 extractor (class×method pairs the
    # dispatcher's guard extraction found)
    served = load(GDIR / "graph" / "served_api.json", {"pairs": []})
    served_pairs = defaultdict(list)
    for p in served.get("pairs", []):
        served_pairs[f"{p['class']}.{p['method']}"].append(
            f"{p['tu']}:{p['line']}")

    records = []
    for api, g in sorted(stubs.items()):
        if only and only not in api:
            continue
        ev = fresh.get(api, [])
        st_counts = Counter(c.get("status") for _, c in ev)
        ret_vals = Counter(str(c.get("return_value"))[:24] for _, c in ev
                           if c.get("return_value"))
        arg_shapes = Counter(
            (c.get("descriptor") or "?") for _, c in ev)
        res = RESOLUTION.get(api, {})
        cls = res.get("classification")
        fam = res.get("family", "")
        note = res.get("note", "")

        # ── S71 W5 root law #1: ancestry dispatch ──
        if not cls and api in ANCESTRY_ROOT:
            entry = ANCESTRY_ROOT[api]
            if entry is None:
                pass  # handled by other tables
            else:
                mname, msub = entry
                fam = f"ANCESTRY-ROOT[{msub}]"
                has_guard = mname in (
                    "getCacheDir", "getSystemService", "getResources",
                    "getWindow", "getApplicationContext", "getApplicationInfo")
                if has_guard:
                    cls = "FALSE-UNSERVED"
                    note = ("guard body EXISTS (substring-scoped to "
                            "Context/Activity); app/Application receiver "
                            "misses it → ancestry-dispatch root law fixes "
                            "WITHOUT a new body")
                else:
                    cls = "TRUE-MISSING"
                    note = ("no guard body; ancestry dispatch is necessary "
                            "but a method law must also be written")

        # ── S71 W5: platform family rows ──
        if not cls and api in FAMILY_ROWS:
            fam, cls = FAMILY_ROWS[api]
            note = "family source-scan (S71 W5): see s71 report §families"

        # ── S71 W5: <unknown> method correlation ──
        if not cls and api.startswith("<unknown>."):
            m = api.split(".", 1)[1]
            if m in UNKNOWN_METHOD_ROWS:
                fam, cls, unote = UNKNOWN_METHOD_ROWS[m]
                note = unote
            else:
                cls = "UNKNOWN"
                note = "no correlation row — needs caller-context review"

        # ── mechanical first-pass for entries without a resolution row ──
        if not cls:
            if api.startswith("<unknown>"):
                cls = "TRACE-RESOLUTION-ARTIFACT"
                note = ("<unknown> class in trace exporter — receiver/class "
                        "resolution failed at recording time; behavior may "
                        "still be served (must correlate by method)")
            elif is_app_defined(api):
                cls = "APP-SPECIFIC"
                note = ("receiver class is app-defined; not a platform "
                        "foundation API (runtime-class walk miss or "
                        "misattributed receiver)")
            elif any(s in api for s in INTRINSIC_SUBSTR):
                cls = "INTRINSIC"
                note = ("subsystem has no equivalent in this runtime's "
                        "architecture (software renderer / no audio / no "
                        "notification daemon)")
            elif not is_platform(api):
                cls = "APP-SPECIFIC"
                note = "non-platform class"
            elif g.get("live_calls", 0) == 0 and not ev:
                cls = "UNKNOWN"
                note = "no fresh live event; needs targeted fixture"
            elif served_pairs.get(api.replace(";", "").replace("/", ".")):
                cls = "PARTIAL"
                note = "static guard pair exists; live still stubbed — arg-shape or receiver gap"
            else:
                cls = "UNKNOWN"
                note = ("no resolution row and no static guard pair — "
                        "needs manual forensic review")
        records.append({
            "api": api,
            "old_status": g.get("status"),
            "classification": cls,
            "family": fam,
            "silent_wrong": res.get("silent_wrong",
                                    bool(g.get("noop_flags"))),
            "dispatch": res.get("dispatch", ""),
            "source_evidence": res.get("source", ""),
            "upstream": res.get("upstream", ""),
            "static_sites": g.get("fanout", 0),
            "static_apks": len(g.get("by_apk", {})),
            "live_calls_s70": g.get("live_calls", 0),
            "live_calls_s71": len(ev),
            "live_status_s71": dict(st_counts),
            "live_apks_s71": sorted({a for a, _ in ev}),
            "live_return_values": dict(ret_vals.most_common(4)),
            "live_descriptor_shapes": dict(arg_shapes.most_common(4)),
            "tested_by": g.get("tested_by", []),
            "upstream_docs": g.get("upstream_docs", []),
            "noop_flags": g.get("noop_flags", []),
            "note": note,
        })

    out = {
        "generated": "S71 FORENSIC TRIAGE",
        "pipeline": "static → live-trace → engine-source → dispatch → "
                    "intrinsic → upstream → consumers → tests → class",
        "records": records,
    }
    dest = GDIR / "s71" / "forensic_classification.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest} ({len(records)} records)")

    # console matrix
    by = Counter(r["classification"] for r in records)
    print("\n=== FORENSIC BREAKDOWN of the S70 LIVE-STUB surface ===")
    for k, n in by.most_common():
        print(f"  {n:>4}  {k}")
    print("\n=== per-record (classification, live evidence) ===")
    for r in records:
        print(f"  [{r['classification']:<24}] {r['api'][:64]} "
              f"s70live={r['live_calls_s70']} s71live={r['live_calls_s71']} "
              f"sites={r['static_sites']}"
              + ("  SILENT-WRONG" if r["silent_wrong"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
