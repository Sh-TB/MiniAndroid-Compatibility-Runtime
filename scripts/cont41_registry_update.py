#!/usr/bin/env python3
"""CONT-41 — registry update: R-NEW-550 (Uri authority field-first),
R-NEW-551 (AssetManager.list missing-path IOException, never null),
R-NEW-552 (ServiceWorkerController singleton) — the capacitor/cordova
family laws; concealmobile census crossing."""
import json

PATH = "/home/z/my-project/root_registry.json"
rows = json.load(open(PATH))
ids = {r["id"] for r in rows}

new_rows = [
    {
        "id": "R-NEW-550",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "dalvik/bridge_to_api (android.net.Uri accessor family)",
        "date": "2026-10-26",
        "title": "Uri.getAuthority/getHost answered NULL for builder-built Uris (the law re-parsed the longest string field instead of reading the stored authority) — capacitor's UriMatcher.addURI then NPE'd on authority.contains('*') at token level i==-1",
        "root_cause": "The #371-phase-B1 getAuthority law read the LONGEST string field as `raw` and ran parse_content_uri(raw) — for a BUILDER-built Uri (R-NEW-537 fields: scheme=http, authority=localhost, path=/) raw='localhost', parse failed, auth empty -> NULL. Live face (4-title capacitor family: subster/voyager/how2vote/leradar): WebViewLocalServer.createHostingDetails -> registerUriForScheme(http) -> register(uri2, handler) -> UriMatcher.addURI(scheme, authority, path, code); Capacitor's matcher walks token level i==-1 = AUTHORITY and invokes authority.contains('*') (addURI pc=0x62, register operands decoded with the new cont41_disasm_regs.py tool) -> NPE on the null -> registerUriForScheme pc=0x1a unwind -> createHostingDetails -> hostAssets -> Bridge.<init> death. The earlier F141-DIAG 'addURI p1=null' reading was the SCHEME — but getScheme returned 'http' (the [R537-GS] trace proved it); the REAL null receiver was the AUTHORITY (the loop's i==-1 arm).",
        "fix": "FIELD-FIRST LAW: getAuthority/getHost read the stored 'authority' field first (the R-NEW-537 setter/build convention); when absent/empty, fall back to the parse_content_uri(raw) channel unchanged (parse()-built Uris carry uri_raw). Same law body now reads scheme/authority/path/query/uri_raw fields distinctly. toString also synthesized the AOSP form for builder Uris ([scheme://][authority][path][?query][#fragment]) with uri_raw still winning when present (the old longest-string raw answered 'localhost').",
        "evidence": "MINIANDROID_URI_DEBUG traces ([R537-SET] absence + [R537-GS] scheme=http) + cont41_disasm_regs.py register-true decode of UriMatcher.addURI (the i==-1 -> authority arm at pc=0x62). Post-fix subster census 6648 -> 7027 IMPLEMENTED; the registerUriForScheme unwinds GONE from all 4 family titles.",
        "honest_frontier": "the webview CONTENT layer (QuickJS/HTML5 render of the app's assets) is the family's next gate — titles run clean to the Bridge but paint no pixels yet (verdict DEFAULT_BACKGROUND_ONLY, APP_PIXELS).",
        "family": "android.net.Uri accessor family (F-104/S107/R-NEW-537/537b -> R-NEW-550)",
    },
    {
        "id": "R-NEW-551",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "dalvik/bridge_to_api + try_recursive_invoke twin (AssetManager.list)",
        "date": "2026-10-26",
        "title": "AssetManager.list answered NULL for a missing asset path ('AOSP documented quirk' — WRONG) — the capacitor getFilesContent array-length then NPE'd (ARR-LEN-NULL), uncaught by its IOException handler, killing the whole JSExport bootstrap",
        "root_cause": "Both list() channels (bridge 62664 + the try_recursive twin) returned make_null() when the assets dir was absent ('AOSP documented quirk: list on a missing dir -> null'). Real AOSP AssetManager.list(String) NEVER returns null: a missing path throws IOException ('Unable to list asset file'). Live face: JSExport.getCordovaPluginJS -> getFilesContent(ctx, 'public/plugins') -> AssetManager.list -> NULL -> array-length NPE at pc=13 (SYNTH-EXC ARR-LEN-NULL) -> the app's IOException catch cannot catch NPE -> unwound getCordovaPluginJS -> loadWebView -> Bridge.<init> (all 4 capacitor titles).",
        "fix": "R-NEW-551 MISSING-PATH LAW in BOTH channels: missing asset path -> throw_deferred IOException('Unable to list asset file <dir>') — the app's own handler catches it (deferred handler @0x48 confirmed in voyager) and the chain advances; existing-file -> empty array (R-NEW-538 kept); existing dir -> children.",
        "evidence": "voyager SYNTH-EXC chain flip: pre = R551 null channel -> f141 null-recv at Bridge.loadWebView pc=141; post = IOException caught by the app handler at getFilesContent 0x48. Post-R552 subster/voyager runs: ZERO EXC-UNWIND rows.",
        "honest_frontier": "titles now reach the Bridge cleanly; the webview pixel layer (the QuickJS HTML engine driving CapacitorWebView) is the next structural gate for the family.",
        "family": "AssetManager.list family (R-NEW-538 -> R-NEW-551)",
    },
    {
        "id": "R-NEW-552",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework/android_shadows (android.webkit provider singletons)",
        "date": "2026-10-26",
        "title": "ServiceWorkerController.getInstance() answered null (no shadow, no claim) — Capacitor Bridge.loadWebView's setServiceWorkerClient NPE'd on the null receiver at pc=141 (ROOT-057 CookieManager-family sibling)",
        "root_cause": "android.webkit.ServiceWorkerController had NO shadow claim and NO law: getInstance() fell to the generic-miss null. Capacitor's Bridge.loadWebView (every capacitor boot) calls swController.setServiceWorkerClient(...) — null receiver -> f141-null-recv NPE at loadWebView pc=141 -> Bridge.<init> unwind -> Builder.create -> BridgeActivity.load/onCreate APP BOUNDARY (voyager/how2vote/leradar/subster).",
        "fix": "Shadow singleton law (mirrors ROOT-057): getInstance materializes ONE process-wide ServiceWorkerController; setServiceWorkerClient stores the client field faithfully (heap set_object_ref_field); getServiceWorkerWebSettings materializes a second never-null settings singleton; getServiceWorkerClient reads back. handles_class claims both Landroid/webkit/ServiceWorkerController; and ServiceWorkerWebSettings;.",
        "evidence": "[R552] singleton materialized o798 in voyager; voyager stub census 7431 -> 7850 IMPLEMENTED; ZERO EXC-UNWIND in the whole 40s run; verdict face DEFAULT_BACKGROUND_ONLY / APP_PIXELS (webview content layer = the named next gate).",
        "honest_frontier": "webview HTML/JS content rendering (the S109 engine driving the CapacitorWebView surface) — the family's titles are now crash-free to the Bridge; pixels are the frontier.",
        "family": "webkit provider singleton family (ROOT-057 CookieManager -> ROOT-053 WebViewPackageInfo -> R-NEW-552)",
    },
    {
        "id": "R-NEW-553",
        "status": "FIXED-CENSUS-CROSSING",
        "priority": "P1",
        "layer": "batch-50 census (concealmobile — the cordova family)",
        "date": "2026-10-26",
        "title": "concealmobile 0 -> REAL UI (census crossing) — the cordova SystemWebView.init NPE family member advanced to content by the R-NEW-550/551/552 wave",
        "root_cause": "concealmobile's deepest face was Lorg/apache/cordova/engine/SystemWebView;.init NPE (the cordova sibling of the capacitor family): the same Uri/asset/webkit-provider null channels starved the cordova engine's bootstrap.",
        "fix": "The three family laws (R-NEW-550 authority field-first, R-NEW-551 list-IOException, R-NEW-552 ServiceWorkerController singleton) together advanced the title past its bootstrap.",
        "evidence": "CONT-41 batch-50 census at the post-552 binary: 50/50 rows, CONTENT ROWS 13 -> 14 (concealmobile NEW CROSSING), 13/13 prior content rows BYTE-EXACT RETAINED (evidence/cont41/batch50_census.json + scripts/cont41_retention.py VERDICT PASS). Regression wall at the same binary: anchors 6/6 BYTE-EXACT (opencalc 63020bc7 / chess 3f7e6707 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176), games 7/7 EXACT-TO-PIN.",
        "honest_frontier": "14 content rows of 50; the remaining 36 blanks cluster into the XmlPullParser family (gecko/lumolight/sopadeletras), the Fragment lifecycle family (aegis/batterymonitor/notepad), and 6 zero-unwind titles — the named next trains.",
        "family": "capacitor/cordova bootstrap family (R-NEW-537 -> 550/551/552 -> R-NEW-553)",
    },
]

added = 0
for r in new_rows:
    if r["id"] not in ids:
        rows.append(r)
        added += 1

json.dump(rows, open(PATH, "w"), ensure_ascii=False, indent=1)
print(f"registry {len(rows)-added} -> {len(rows)} (+{added}) id-unique={len({r['id'] for r in rows}) == len(rows)}")
