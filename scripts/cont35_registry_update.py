#!/usr/bin/env python3
"""CONT-35 — registry update: F-NEW-531..535 (the batch-50 blank-family laws).

User directive: «ادامه حل مشکل برنامه و بازی ۵۰ توسط ابزار ها» — continue
fixing the 50 programs/games problems using tools.
"""
import json
from pathlib import Path

REG = Path("/home/z/my-project/root_registry.json")
roots = json.load(open(REG))
ids = {r["id"] for r in roots}
print("before:", len(roots), "id-unique:", len(ids) == len(roots))

NEW = [
    {
        "id": "F-NEW-531",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "dalvik/collections-regex (java.util.regex.Matcher group law)",
        "date": "2026-10-26",
        "title": "Matcher.group(i) answered \"\" instead of NULL for "
                 "non-participating groups — the cordova/capacitor AllowList "
                 "family (5 census titles) died in MalformedURLException",
        "root_cause":
            "CONT-35 batch-50 census family: subster/voyager/how2vote/leradar"
            "/concealmobile all died AllowList.addAllowListEntry → "
            "MalformedURLException. Live CL-TRACE + w8 raw decode: "
            "AllowList$URLPattern.<init> parses the port group — "
            "Integer.parseInt(\"\") NumberFormatException at pc=97 (caught) "
            "→ the app's own catch throws MalformedURLException(\"Port must "
            "be a number\") at pc=140. The port group DID NOT PARTICIPATE "
            "(`https://host` has no :port) — real libcore group(i) returns "
            "NULL for non-participating groups and cordova's `port == null` "
            "check would have skipped parseInt. Engine defect: the find/"
            "matches law stored non-participating groups as \"\" and group() "
            "always returned a string — the matched/unmatched distinction "
            "was erased.",
        "fix": "find/matches law now ALSO stores a per-group participation "
               "flag (group<i>_m bool; groupCount unchanged — it counts "
               "STRING fields only); group(i) law: IndexOutOfBoundsException "
               "when i is outside the last match's group range (libcore IOOBE "
               "law), NULL when the group exists but did not participate, "
               "matched text otherwise. No app-specific or R8-specific code.",
        "evidence": "evidence/cont35/ (CL-TRACE subster chain "
                    "[THROWABLE-MSG] MalformedURLException 'Port must be a "
                    "number' caller=URLPattern.<init> pc=140; post-fix all 5 "
                    "titles advanced past the AllowList family — next-layer "
                    "pluginInitialize faces recorded); batch50_census.json "
                    "(13 content rows byte-exact retained)",
        "fanout": "subster, voyager, how2vote, leradar, concealmobile (5 "
                  "census titles) + every regex caller reading optional "
                  "groups",
    },
    {
        "id": "F-NEW-532",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "resources/theme (Resources.getColorStateList attr law)",
        "date": "2026-10-26",
        "title": "Resources.getColorStateList(attr_id) had no theme-attr "
                 "resolution — Material colorSurfaces chains answered null",
        "root_cause":
            "best_deskclock ×16 Resources$NotFoundException: "
            "ResourcesCompat.getColorStateList(getValue branch) → "
            "getXml(attr_id) → 371-GETXML-NOTFOUND. An ATTR id (0x7f04xxxx, "
            "e.g. attr/colorSurfaceContainer) has NO value outside a theme; "
            "real Android resolves it through the applied theme to the "
            "concrete @color. The F-NEW-383 getColorStateList law resolved "
            "only the direct ARSC value (no theme stage) → null → the "
            "androidx null-fallback re-entered the legacy getXml inflate "
            "path → NotFound uncaught → onCreate dead.",
        "fix": "getColorStateList law now consults resolve_theme_attr_typed "
               "(the SAME authority the F-093 obtainStyledAttributes / "
               "F-141f resolveAttribute laws use) FIRST — one theme "
               "authority, one contract; REFERENCE chains deref bounded 4; "
               "the direct-ARSC path is the unchanged fallback for non-attr "
               "ids.",
        "evidence": "run/cont35/v2_bdc..v8_bdc traces (the getXml family "
                    "face GONE post-fix; deskclock advanced to the prefs "
                    "migration layer, then the app-internal b4 IAE); "
                    "aapt2 dump: 0x7f040139 = attr/colorSurfaceContainer "
                    "with @color/m3_sys_color_*_surface_container present",
        "fanout": "best_deskclock (+ amaze/aegis same-family NotFound rows) "
                  "+ every Material themed-color consumer",
    },
    {
        "id": "F-NEW-533",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "dalvik/bridge_to_api (javax.net factory family; F-NEW-516 "
                 "never-null battery L5)",
        "date": "2026-10-26",
        "title": "javax.net.SocketFactory.getDefault / SSLSocketFactory."
                 "getDefault answered null — okhttp3 Platform.getSocketFactory "
                 "null-check idiom NPE killed OkHttpClient.Builder.<init>",
        "root_cause":
            "awagam census face: okhttp3/internal/platform/Platform;"
            ".getSocketFactory pc=4 is the R8 null-check idiom "
            "(`getDefault().getClass()`); the engine had NO SocketFactory/"
            "SSLSocketFactory getDefault law → null → NullPointerException "
            "→ OkHttpClient.Builder.<init> dead → every okhttp consumer in "
            "the app died at clinit time. OpenJDK/JCA contract: getDefault() "
            "NEVER answers null (a default factory is demand-created from "
            "the platform provider).",
        "fix": "L5 of the F-NEW-516 never-null platform-factory battery: "
               "bridge law allocates a never-null factory object for "
               "SocketFactory.getDefault and SSLSocketFactory.getDefault "
               "(deterministic heap object, [F533-L5] row).",
        "evidence": "run/cont35/v2_awagam trace ([F533-L5] "
                    "SocketFactory.getDefault -> oid=4197 never-null law "
                    "fires; the awagam face advanced past Platform."
                    "getSocketFactory to the next app face); w8 decode of "
                    "Platform.getSocketFactory (8 units, getClass idiom)",
        "fanout": "awagam + every okhttp/okio consumer (okhttp is the most "
                  "deployed Android HTTP stack — census-wide lever)",
    },
    {
        "id": "F-NEW-534",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "resources/theme (Resources.getValue attr law; closes the "
                 "F-NEW-513 law's own named gap)",
        "date": "2026-10-26",
        "title": "Resources.getValue(attr_id) answered the raw attr-decl int "
                 "(datatype=0x10) instead of the theme's value — "
                 "ResourcesCompat took the XML-inflate branch and died",
        "root_cause":
            "best_deskclock live [F513-GETVALUE] rows: "
            "getValue(0x7f040139)=datatype 0x10 (raw attr-decl INT). The "
            "F-NEW-513 law comment itself recorded the gap: 'ATTRIBUTE refs "
            "resolve through the theme — unmodeled here'. The R8'd androidx "
            "branch (`type∈[0x1c..0x1f] → valueOf; else XML inflate`) took "
            "the else → res.getXml(attr_id) → Resources$NotFound ×16 per "
            "launch → DeskClock.onCreate dead. Same family rows on amaze "
            "(×6) and aegis (×2).",
        "fix": "getValue law consults resolve_theme_attr_typed FIRST (attr "
               "ids live only in the 0x7f04xxxx type space — plain "
               "color/drawable ids are disjoint, so the theme attempt is a "
               "no-op for them); resolveRefs REFERENCE deref walk preserved; "
               "the direct-ARSC path keeps its exact historical semantics as "
               "the fallback.",
        "evidence": "run/cont35/v3_bdc trace ([F513-GETVALUE] datatype=0x10 "
                    "pre-fix); v4_bdc (NotFound family GONE post-fix, "
                    "deskclock advanced past the prefs-migration layer); "
                    "regression wall anchors 6/6 byte-exact at the final "
                    "binary",
        "fanout": "best_deskclock, amaze, aegis + every "
                  "ResourcesCompat/getValue attr consumer",
    },
    {
        "id": "F-NEW-535",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "dalvik/bridge_to_api (Context storage-migration family)",
        "date": "2026-10-26",
        "title": "Context.moveSharedPreferencesFrom / moveDatabaseFrom had "
                 "NO engine law — androidx PreferenceManager migration "
                 "'failed' and its warn-logger re-entered the helper "
                 "(M3-19 cycle stub → getBoolean NPE)",
        "root_cause":
            "best_deskclock post-534 face: SharedPreferences.getBoolean on "
            "null. Chain: the androidx PreferenceManager device-protected "
            "migration helper (zo.u) is EXACTLY Context."
            "moveSharedPreferencesFrom (w8 decode: 5 units) — the missing "
            "law answered the generic missing-call shape → 'Failed to "
            "migrate shared preferences' warn path → the warn's own logger "
            "(yg0.i) reads the debug key via xg0.K → re-enters the "
            "still-running helper → the M3-19 active-cycle stub answered "
            "null → NPE. AOSP ContextImpl: best-effort move, answers TRUE "
            "when the source file does not exist (nothing to move is not a "
            "failure); same-thread re-entrancy is safe (monitor semantics) — "
            "the engine's cycle guard only exists because the missing law "
            "made the app recurse.",
        "fix": "moveSharedPreferencesFrom + moveDatabaseFrom bridge law: "
               "TRUE (the single-data-root model cannot produce the "
               "source-exists-move-IO-fails shape; identity law S99 keeps "
               "the per-name prefs object).",
        "evidence": "run/cont35/v5_bdc..v8_bdc ([F535-MOVE] rows; deskclock "
                    "advanced past the prefs family to the app-internal "
                    "b4/q60 IAE face)",
        "fanout": "best_deskclock + every androidx PreferenceManager "
                  "device-protected-storage migration (targetSdk 24+ "
                  "direct-boot family)",
    },
]

added = 0
for r in NEW:
    if r["id"] not in ids:
        roots.append(r)
        ids.add(r["id"])
        added += 1
json.dump(roots, open(REG, "w"), indent=1, ensure_ascii=False)
print(f"added {added}; after:", len(roots),
      "id-unique:", len({r['id'] for r in roots}) == len(roots))
