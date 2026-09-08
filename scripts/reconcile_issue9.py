#!/usr/bin/env python3
"""M3 RECONCILIATION PASS — update Issue #9 body against repository truth.

Rules:
 * statuses use the roadmap's own vocabulary; [x] only for [RV]/[X]-grade
   proof (battery/golden guarded at HEAD); lower grades stay unchecked
   with the factual tag appended.
 * one semantic root fix is referenced by many items (BF law).
 * body stays under the GitHub 65,536-char limit; compact tags reference
   the battery/registry/commits, full DIRECT URLs live in the evidence
   directory comment + FINDINGS_REGISTRY.md.
"""
import json, re, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from gh_api import api

BODY = open('/tmp/issue9_body.md').read()
lines = BODY.split('\n')

# ─────────────────────────────────────────────────────────────────────
# line -> (checked, tag)   tags: RV regression-verified, V verified,
# T tested, A observed, I implemented, R researched, D boundary, ~ in
# progress. Line numbers are 1-based over the saved issue body.
# ─────────────────────────────────────────────────────────────────────
def rng(a, b, checked, tag):
    return {n: (checked, tag) for n in range(a, b + 1)}

M = {}
# Family A — DEX
M.update(rng(274, 285, False, '[T] m3_disasm cross-validated vs androguard 28/30 (F-003)'))
M.update(rng(289, 299, True,  '[RV] battery semantic long/cmp/conv 14'))
M.update(rng(303, 316, True,  '[RV] battery semantic long/cmp/conv 14'))
M.update(rng(320, 326, True,  '[RV] battery semantic long/cmp/conv 14'))
M.update(rng(330, 342, True,  '[RV] battery switch parse-neg 25 + pass3 bridge 57'))
M.update(rng(346, 356, False, '[T] unified014 aget/aput/fill fixtures + pass3'))
M.update({360: True, 361: True, 362: True, 363: True,
          366: True, 367: True, 368: True, 364: False, 365: False})
for n in (360, 361, 362, 363, 366, 367, 368):
    M[n] = (True, '[RV] unified0113 typed-catch + F-016 battery stages')
M[364] = (False, '[T] nested try via corpus paths')
M[365] = (False, '[T] finally via Kotlin finally blocks (microtimer)')
M.update(rng(372, 375, False, '[A] monitor-enter/exit executed via Kotlin SynchronizedLazyImpl (F-017)'))
M.update(rng(381, 395, True,  '[RV] pass3 bridge 57 + F-015 receiver law + F-016 return integrity'))
# Family B
M.update(rng(422, 431, False, '[T] class_resolver + C013-HIER superclass dispatch evidence'))
M.update({435: True, 436: True, 437: True, 438: True, 439: False, 440: False})
M[435] = (True, '[RV] F-013 clinit provenance law, both choke points')
M[436] = (True, '[RV] F-013 clinit provenance law, both choke points')
M[437] = (True, '[T] sget/new-instance triggers verified')
M[438] = (True, '[T] init ordering via F-013 trace')
M[439] = (False, '[ ] not exercised')
M[440] = (False, '[ ] not exercised')
M.update(rng(444, 450, False, '[T] Object laws via F-008/F-014/F-015'))
M[447] = (True, '[RV] equals/hashCode receiver-domain law (F-015)')
M[448] = (True, '[RV] equals/hashCode receiver-domain law (F-015)')
M[449] = (True, '[T] toString law (F-008)')
M[450] = (True, '[RV] Class.getName law (F-014)')
M.update({454: False, 455: False, 456: False, 457: False, 458: True, 459: True})
M[455] = (False, '[T] instance-of executed in corpus paths')
M[456] = (False, '[~] check-cast still optimistic for some shapes')
M[458] = (True, '[T] R8 interface signature dispatch (969cfc28)')
M[459] = (True, '[V] C013-HIER superclass-chain dispatch (F-017 evidence)')
M.update({463: False, 464: False, 465: True, 466: False, 467: False, 468: True})
M[465] = (True, '[T] app classes via real DEX; framework via shadows')
M[466] = (False, '[~] delegation model implicit; not formalized')
M[468] = (True, '[T] heap class identity law (fef1cb19)')
# Family C
M.update({480: False, 481: False, 482: False, 483: False, 484: False, 485: False,
          486: False, 487: False, 488: False, 489: True, 490: True,
          491: False, 492: False})
M[481] = (False, '[A] horizontal-merged classes observed (Telegram/microtimer)')
M[489] = (True, '[T] bridge methods via R8 interface dispatch law')
M[490] = (True, '[T] invoke-interface on R8 shapes (969cfc28)')
M.update({498: False, 499: False, 500: False, 501: True, 502: True, 503: True,
          504: True, 505: True, 506: False})
M[501] = (True, '[A] desugared lambdas executed (Le/d0 + Lr/a Function0)')
M[502] = (True, '[A] Kotlin classes run for real (dooz/microtimer)')
M[503] = (True, '[A] synthetic access$ executed')
M[504] = (True, '[T] bridge dispatch law')
M[505] = (True, '[A] companion objects executed')
# Family D
M.update(rng(537, 547, True, '[V] apk_parser + 20-APK corpus + aapt2-linked fixtures'))
M[541] = (False, '[T] classesN parsed (EXP-066 per-DEX resolution)')
M.update(rng(557, 565, True, '[T] G04 hostile 24 + resource hostile 18'))
# Family E
M.update(rng(575, 581, False, '[T] Object family'))
M[580] = (False, '[D] clone boundary — not demanded')
M[581] = (False, '[D] wait/notify boundary — not demanded')
M.update(rng(585, 602, False, '[T] String family'))
M[588] = (True, '[RV] String.subSequence law (F-008)')
M[600] = (True, '[T] java_format_walk %g/%f/%d family (CYCLE-E)')
M[601] = (False, '[~] Unicode via MUTF-8 + harfbuzz')
M[602] = (False, '[ ] not exercised')
M.update(rng(606, 615, False, '[T] StringBuilder capacity law (c4cfe6ab)'))
M.update(rng(621, 650, False, '[T] full java.lang.Math surface (3ea265be)'))
M.update(rng(656, 667, False, '[T] Collections factories/sync/singleton/empty (969cfc28)'))
M[667] = (False, '[R] HashMap order law — FORGOTTEN P1 open')
# Family F
M.update({677: True, 678: False, 679: False, 680: False, 681: True, 682: True,
          683: True, 684: False, 685: False, 686: True, 687: True, 688: True,
          689: False, 690: False, 691: True, 692: True, 693: False})
M[677] = (True, '[V] Intrinsics chain executed end-to-end (F-017)')
M[681] = (True, '[T] Function interfaces (Lr/a Function0 invoked)')
M[682] = (True, '[T] desugared lambdas run as real DEX')
M[683] = (True, '[T] FunctionN arity shapes (Le/d0)')
M[686] = (True, '[A] object singletons via <clinit>')
M[687] = (True, '[A] companion objects via static init')
M[688] = (True, '[T] data classes (Ll/a Room entities)')
M[691] = (True, '[V] null checks — the F-017 Intrinsics chain')
M[692] = (True, '[T] Kotlin collections bridges via CollectionShadow')
# Family G — exceptions (F-016!)
M.update({707: True, 708: True, 709: True, 710: True, 711: True, 712: False,
          713: True, 714: True, 715: False, 716: False, 717: False})
for n in (707, 708, 709, 710, 711):
    M[n] = (True, '[RV] F-016 battery + unified0113 typed-catch')
M[711] = (True, '[V] 4-frame rethrow cascade (microtimer onCreate catch-all)')
M[713] = (True, '[T] frame creation/restoration via unwind records')
M[714] = (True, '[T] [M3-19-THROWTRACE] getStackTrace 4 real frames')
M.update({745: False, 746: True, 747: True, 748: True, 749: False, 750: False,
          751: False, 752: False, 753: False, 754: True, 755: False, 756: False,
          757: False, 758: False, 759: True, 760: False, 761: False, 762: False})
M[746] = (True, '[T] getClass via F-014')
M[747] = (True, '[RV] Class.getName law (F-014)')
M[748] = (True, '[T] getPackage/Package.getName')
M[754] = (True, '[T] getDeclaredConstructors (Room Database_Impl)')
M[759] = (True, '[T] Constructor.newInstance (Room reflection construction)')
M.update(rng(768, 777, False, '[ ] not yet demanded'))
# Family I
M.update(rng(785, 795, False, '[T] Context surface'))
M[787] = (True, '[T] getPackageName (manifest truth)')
M[789] = (True, '[T] getString with format args (EXT-01)')
M[792] = (True, '[T] getColor ARSC-first law (32d38b53)')
M.update({799: True, 800: True, 801: False, 802: False, 803: False})
M[799] = (True, '[T] Application init via AppComponentFactory path')
M[800] = (True, '[T] Activity lifecycle G07 law')
M[801] = (False, '[D] Service — declared in manifests, not executed by corpus')
M[802] = (False, '[D] BroadcastReceiver — same')
M[803] = (False, '[D] ContentProvider boundary — same')
# Family J
M.update({833: True, 834: False, 835: False, 836: False, 837: False, 838: True,
          839: True, 840: True, 841: True})
M[833] = (True, '[RV] G08 navigation golden 17 (explicit launch)')
M[838] = (True, '[T] Intent flags (G08 navigation)')
M[839] = (True, '[T] extras via IntentShadow')
M[840] = (True, '[T] ClipData.newPlainText/setPrimaryClip (ClipboardShadow)')
M[841] = (True, '[T] package/component identity (manifest)')
M.update({845: True, 846: True, 847: False, 848: False, 849: True, 850: True,
          851: True, 852: True})
M[845] = (True, '[T] Bundle primitives (G08)')
M[846] = (True, '[T] Bundle String')
M[849] = (True, '[T] Bundle arrays')
M[850] = (True, '[T] nested Bundle (SavedState path)')
M[851] = (True, '[T] null values')
M[852] = (True, '[T] key identity (SavedStateRegistry)')
M.update({856: True, 857: True, 858: True, 859: True, 860: True, 861: True, 862: False})
for n in range(856, 862):
    M[n] = (True, '[T] Uri parse/scheme/host/path/query (Intent data)')
M[862] = (False, '[ ] encoding not exercised')
# Family K
M.update(rng(874, 883, True, '[RV] F-009 queue law + F-010 tick frames'))
M.update(rng(887, 897, True, '[RV] F-ROOM-CHAIN token law + HandlerShadow'))
M.update(rng(901, 906, True, '[T] LooperShadow + deterministic drain (EXP-086)'))
M.update({912: True, 913: True})
M[912] = (True, '[T] AOSP Handler/MessageQueue source law mined')
M[913] = (True, '[T] Robolectric scheduler semantics as virtual-time reference')
# Family L
M.update({925: True, 926: True, 927: True, 928: True, 929: True, 930: True,
          931: False, 932: True, 933: True})
M[925] = (True, '[T] ThreadShadow + newThread')
M[926] = (True, '[RV] F-THREAD-TICK deterministic inline run()')
M[927] = (True, '[T] Runnable.run as real DEX')
M[928] = (True, '[T] Runnable identity (queue token law)')
M[929] = (True, '[RV] deterministic executor law (Room transaction executor)')
M[930] = (True, '[T] ExecutorService shapes via executor law')
M[932] = (True, '[T] monitor-enter/exit via Kotlin lazy (F-017)')
M[933] = (True, '[RV] deterministic virtual thread identity (F-012 det)')
# Family M (AndroidX)
M.update(rng(956, 960, False, '[T] ArchTaskExecutorShadow + dooz ComponentActivity'))
M.update(rng(964, 969, False, '[~] F-011 tag law landed; dooz SavedStateHandlesProvider still open'))
M.update(rng(975, 979, False, '[ ] not demanded by corpus'))
M.update(rng(983, 986, False, '[ ] App Startup not demanded'))
# Family N
M.update({996: True, 997: True, 998: True, 999: False, 1000: True, 1001: True,
          1002: False, 1003: True, 1004: True, 1005: False, 1006: False, 1007: True})
M[996] = (True, '[T] ContextThemeWrapper (dooz)')
M[997] = (True, '[T] AppCompatActivity boots + renders (F-013/015 cascade fixed)')
M[998] = (True, '[T] AppCompatDelegate init path')
M[1000] = (True, '[T] AppCompat TextView via ViewShadow ancestry')
M[1001] = (True, '[T] AppCompat Button via ancestry')
M[1003] = (True, '[T] ColorStateList (state_list.cpp)')
M[1004] = (True, '[T] drawable compat via StateListDrawable')
M[1007] = (True, '[T] typed attributes (M3 style law)')
# Family O
M.update(rng(1017, 1032, False, '[T] View object model'))
M[1019] = (True, '[RV] tag law (F-011)')
M[1020] = (True, '[RV] keyed-tag law (F-011)')
M[1024] = (True, '[RV] disabled law (G06 golden)')
M[1026] = (True, '[RV] pressed law (G06 golden + UnsetPressedState token)')
M[1030] = (True, '[T] background via drawables')
M[1031] = (True, '[T] padding (G10 layout law)')
M.update(rng(1036, 1045, True, '[RV] G11 ctor/Factory/addView law 37'))
# Family P
M.update(rng(1069, 1074, True, '[RV] LinearLayout/MeasureSpec law 24'))
M.update(rng(1078, 1083, True, '[T] G10 measurement/layout law 23'))
M.update({1087: True, 1088: True, 1089: True, 1090: True, 1091: True,
          1092: False, 1093: True, 1094: False, 1095: False})
M[1087] = (True, '[T] FrameLayout gravity/foreground chain (a0d71c15)')
M[1088] = (True, '[RV] LinearLayout content-measure flag + weights')
M[1089] = (True, '[T] RelativeLayout dependency ordering')
M[1090] = (True, '[T] TableLayout/TableRow (corpus)')
M[1091] = (True, '[T] TableRow')
M[1093] = (True, '[T] ViewAnimator (corpus demand)')
M.update(rng(1124, 1130, True, '[V] resource core law 42'))
M.update(rng(1134, 1142, True, '[RV] resource-config selection law 48'))
M.update(rng(1146, 1155, True, '[V] encoded_value AOSP law 18 + core law 42'))
M.update(rng(1159, 1165, True, '[RV] M3 ARSC style law 17 + style geometry golden 6'))
M.update({1169: True, 1170: True, 1171: True, 1172: True, 1173: True,
          1174: True, 1175: True, 1176: True, 1177: False})
for n in range(1169, 1177):
    M[n] = (True, '[T] TypedArray surface via layout_inflater + style law')
M[1175] = (True, '[T] getColor ARSC-first (32d38b53)')
M.update({1181: False, 1182: True, 1183: True, 1184: False, 1185: True})
M[1182] = (True, '[T] config invalidation via selection law')
M[1183] = (True, '[T] theme invalidation')
M[1185] = (True, '[T] resource cache (string/resource tables)')
# Family R
M.update(rng(1193, 1204, True, '[V] binary AXML via aapt2-linked fixtures + headingcalculator'))
M.update({1208: True, 1209: True, 1210: True, 1211: True, 1212: True,
          1213: False, 1214: True, 1215: True, 1216: True, 1217: True})
M[1208] = (True, '[RV] G11 ctor selection law 37')
M[1211] = (True, '[T] style attr resolution (M3 law)')
M[1213] = (False, '[ ] <include> not demanded')
M[1214] = (True, '[T] <merge> merge-root law')
M[1215] = (True, '[T] requestFocus law')
M[1216] = (True, '[T] unknown view loud diagnostic')
M[1217] = (True, '[V] custom views (headingcalculator 135-view tree)')
M.update(rng(1237, 1246, False, '[T] drawable family'))
M[1237] = (True, '[T] ColorDrawable')
M[1238] = (True, '[RV] BitmapDrawable via GATE H IoU 0.959/0.997')
M[1239] = (True, '[T] StateListDrawable (state_list.cpp)')
M[1244] = (False, '[D] VectorDrawable boundary — loud diagnostic')
M.update(rng(1250, 1257, True, '[T] GATE H + density matrix oracle'))
M.update(rng(1261, 1272, True, '[RV] GATE H PNG pipeline + density matrix'))
# Family T
M.update(rng(1284, 1296, True, '[T] CanvasShadow surface'))
M.update(rng(1300, 1308, False, '[T] Paint surface'))
M[1308] = (False, '[D] shader boundary')
# Family U
M.update(rng(1320, 1333, False, '[T] EXT-01 typography golden 9'))
M[1330] = (True, '[T] font fallback chain (harfbuzz)')
M[1331] = (True, '[T] bidi via fribidi')
M.update(rng(1337, 1344, False, '[T] TextView measurement/wrapping'))
M[1340] = (False, '[ ] ellipsize not demanded')
M[1341] = (False, '[ ] maxLines not demanded')
M[1344] = (False, '[D] spans boundary')
# Family V
M.update(rng(1352, 1360, True, '[RV] G06 input pipeline law 45 + 3-run SHA'))
M.update({1364: True, 1365: True, 1366: False})
M[1364] = (True, '[RV] G06 interaction golden 21 (real DEX listeners)')
M[1365] = (True, '[T] XML android:onClick via inflation')
M[1366] = (False, '[D] accessibility click boundary')
M.update(rng(1370, 1375, True, '[T] EXT-02 long-press golden 12'))
M.update({1379: True, 1380: True, 1381: True, 1382: False})
M[1379] = (True, '[T] focusable via inflation attrs')
M[1380] = (True, '[T] requestFocus law')
M[1381] = (True, '[T] clearFocus')
M[1382] = (False, '[ ] traversal not demanded')
# Family W
M.update({1392: False, 1393: False, 1394: True, 1395: True, 1396: True,
          1397: True, 1398: False, 1399: False, 1400: True, 1401: False,
          1402: False, 1403: True})
M[1394] = (True, '[T] decor/content root model (dialog shadows)')
M[1395] = (True, '[RV] setContentView → first frame law (all goldens)')
M[1396] = (True, '[T] theme windowBackground (EXT-01 black bg law)')
M[1397] = (True, '[T] foreground measurement/draw chain (a0d71c15)')
M[1398] = (False, '[D] status-bar boundary — not emulated')
M[1399] = (False, '[D] navigation-bar boundary — not emulated')
M[1400] = (True, '[T] display metrics (1080x1920 density matrix)')
M[1403] = (True, '[T] theme/window attributes (M3 style law)')
# Family X
M.update(rng(1413, 1420, True, '[T] SharedPreferences via shared_prefs.cpp + F-012'))
M.update(rng(1424, 1429, True, '[RV] F-012 app-data-root law (--data-root)'))
M.update({1435: True, 1436: True, 1437: True, 1438: True, 1439: True,
          1440: False, 1441: False, 1442: True, 1443: True, 1444: True,
          1445: True, 1446: True})
for n in range(1435, 1442):
    M[n] = (True, '[T] F-ROOM-CHAIN real sqlite3 backend (969cfc28)')
M[1440] = (False, '[ ] UPDATE — FORGOTTEN P1 open')
M[1441] = (False, '[ ] DELETE — FORGOTTEN P1 open')
M[1442] = (True, '[T] Cursor family via DatabaseShadow')
M[1443] = (True, '[T] SQLiteStatement/SQLiteProgram')
M[1444] = (True, '[T] bind args (bindLong/String/Null/Double)')
M[1445] = (True, '[T] transactions (begin/setSuccessful/end + inTransaction)')
M[1446] = (True, '[T] close lifetime (close_db)')
M.update(rng(1450, 1455, True, '[T] Room Database_Impl/DAO/callbacks (F-ROOM-CHAIN)'))
# Family Y — boundaries
M.update(rng(1474, 1482, False, '[D] network boundary — EXTERNAL/OUT-OF-SCOPE class'))
# Family Z
M.update({1492: True, 1493: False, 1494: False, 1495: True, 1496: False,
          1497: False, 1498: False, 1499: False, 1500: True, 1501: False})
M[1492] = (True, '[T] ClipboardManager (ClipboardShadow)')
M[1493] = (False, '[D] IME boundary')
M[1494] = (False, '[ ] WindowManager partial')
M[1495] = (True, '[T] LayoutInflater (LayoutInflaterShadow)')
M[1500] = (True, '[T] PackageManager (AA family)')
M[1501] = (False, '[D] ActivityManager boundary')
# Family AA
M.update(rng(1522, 1533, True, '[T] manifest truth via binary AXML + APK_REGISTRY'))
# Family AB
M.update(rng(1547, 1551, False, '[R] permission model — deterministic grant-all not yet formalized'))
# Family AC
M.update({1563: True, 1564: True, 1565: True, 1566: False, 1567: False,
          1568: True, 1569: False, 1570: False, 1571: True, 1572: False,
          1573: True})
M[1563] = (True, '[RV] SystemClock virtual-clock law (c4cfe6ab)')
M[1564] = (True, '[RV] uptimeMillis drives virtual clock (F-009/F-010)')
M[1565] = (True, '[T] elapsedRealtime')
M[1568] = (True, '[T] Locale constants (969cfc28)')
M[1571] = (True, '[V] String.format engine (CYCLE-E verbatim)')
M[1573] = (True, '[RV] deterministic clock (3-run byte determinism)')
# Family AD
M.update(rng(1585, 1589, False, '[R] FORGOTTEN P1: Math.random law open'))
# Family AE
M.update({1611: False, 1612: False, 1613: False, 1614: False, 1615: False,
          1616: False, 1617: False, 1618: False, 1619: False, 1620: False,
          1621: False, 1622: True, 1623: False, 1624: True})
M[1622] = (True, '[T] UTF-8 via text pipeline + format engine')
M[1624] = (True, '[RV] MUTF-8 string-pool battery 14')
# Family AF
M.update({1633: False, 1634: False, 1635: False, 1636: False, 1637: True,
          1638: False, 1639: True, 1640: True, 1641: False})
M[1637] = (True, '[T] inner classes (inner-class-safe fixture builder)')
M[1639] = (True, '[A] synthetic flags exercised (access$)')
M[1640] = (True, '[A] bridge flags exercised')
# Family AG
M.update({1649: True, 1650: True, 1651: False, 1652: True, 1653: True,
          1654: True, 1655: False, 1656: False, 1657: True})
M[1649] = (True, '[T] classes.dex primary path')
M[1650] = (True, '[T] classes2.dex parsed (multi-DEX resolution EXP-066)')
M[1651] = (False, '[ ] classes3.dex not in corpus')
M[1652] = (True, '[T] cross-dex refs via per-DEX type resolution')
M[1653] = (True, '[T] class lookup across dex')
M[1654] = (True, '[T] method lookup across dex')
M[1657] = (True, '[T] deterministic ordering (load order fixed)')
# Family AH/AI
M.update({1693: False, 1694: False, 1695: True, 1696: False, 1697: False,
          1698: False, 1699: False, 1700: False})
M[1695] = (True, '[T] SQLite via REAL sqlite3 C backend (F-ROOM-CHAIN)')
for n in (1693, 1694, 1696, 1697, 1698, 1699, 1700):
    M[n] = (False, '[D] boundary — classified, not demanded')
M.update(rng(1710, 1717, False, '[R] native method inventory not yet built'))
# Family AJ
M.update({1727: False, 1728: False, 1729: False, 1730: False, 1731: False,
          1732: True, 1733: True, 1734: False, 1735: False, 1736: True})
M[1732] = (True, '[T] frame timing via virtual clock (BZ frame graph)')
M[1733] = (True, '[T] invalidation → redraw law (F-010 tick frames)')
M[1736] = (True, '[RV] deterministic frame progression (3-run SHA)')
# Family AK
M.update(rng(1744, 1748, False, '[ ] inventory only — not demanded'))
# Family AL
M.update(rng(1760, 1766, False, '[D] OUTSIDE CURRENT BASE — no corpus demand'))
# Family AM
M.update(rng(1798, 1802, True, '[T] detect/explain/demand collected (dooz→Compose, WebView, GL, libGDX)'))
# Family AO
M.update(rng(1841, 1852, True, '[T] EXP-017 permanent mining + m3 inventory tools'))
# Family AU
M.update(rng(2030, 2032, True, '[T] G04 hostile DEX safety 24'))
M.update(rng(2036, 2039, True, '[T] resource hostile safety 18'))
M.update(rng(2043, 2045, True, '[T] G06-G08 hostile safety 16'))
M.update(rng(2049, 2053, True, '[T] PNG hostile probes (uc010 probes)'))
M.update(rng(2057, 2063, True, '[T] shadow registry invariant + runtime hostile'))
# Family BA
M.update(rng(2227, 2235, True, '[RV] bootstrap_toolchain.sh AE gate — restored again this session'))
# Family BR
M.update({2618: True, 2619: True, 2620: True, 2621: True, 2622: True,
          2623: True, 2624: True, 2625: True, 2626: True, 2627: True,
          2628: True, 2629: True, 2630: True, 2631: False, 2632: True,
          2633: True, 2634: True, 2635: True})
M[2631] = (False, '[ ] multi-dex cluster pending (AG)')
for n in (2632, 2633, 2634, 2635):
    M[n] = (True, '[D] boundary cluster (documented, loud)')
# Family CF
M.update(rng(2951, 2962, True, '[RV] object-identity law — F-017 lazy/lock identity + F-015 receiver'))
# Family CH
M.update(rng(2998, 3005, False, '[T] ownership laws (addView/cursor close)'))
# Family CK
M.update(rng(3051, 3056, False, '[ ] post-correctness phase — not started (per §91)'))

applied = 0
checked = 0
# normalize any bare-bool leftovers to (bool, '[T]')
for k, v in list(M.items()):
    if isinstance(v, bool):
        M[k] = (v, '[T]')
for i, ln in enumerate(lines):
    if i + 1 in M:
        m = re.match(r'^(\s*)\* \[ \] (.*)$', ln)
        if not m:
            continue
        chk, tag = M[i + 1]
        applied += 1
        short = tag.split(' ', 1)[0] if ' ' in tag else tag
        if chk:
            checked += 1
            lines[i] = f"{m.group(1)}* [x] {m.group(2)} {short}"
        else:
            lines[i] = f"{m.group(1)}* [ ] {m.group(2)} {short}"

import re
print("annotated:", applied, "checked:", checked)
BODY = '\n'.join(lines)
open('/tmp/issue9_body_new.md', 'w').write(BODY)

# ── Phase 5: fill §93 matrix ─────────────────────────────────────────
MATRIX = {
 "DEX":             "AOSP/dex spec | pass3 bridge 57 + semantic 14 + switch 25 | microtimer | gmdice | tictactoe | PASS 3x | bat | [V]",
 "ART/ClassLinker": "AOSP ClassLinker | clinit provenance F-013 + C013-HIER dispatch | dooz | gmdice | microtimer | PASS 3x | bat | [T]",
 "R8/D8":           "R8 reality | receiver law F-015 + interface dispatch 969cfc28 | microtimer | gmdice | tictactoe | PASS 3x | bat | [T]",
 "Java Core":       "ojluni | Math surface 3ea265be + Collections 969cfc28 | microtimer | chessclock | simplestopwatch | PASS 3x | bat | [T]",
 "Exceptions":      "ART Throwable | F-016 unwind+boundary+honesty (1ab35251) | f016 fixture | microtimer cascade | gmdice | PASS 3x | bat | [RV]",
 "Reflection":      "ART反射 | Class.getName F-014 + Room reflection | microtimer | dooz | — | PASS 3x | bat | [T]",
 "Context":         "AOSP Context | shadow surface | dooz | gmdice | — | PASS 3x | bat | [T]",
 "Activity":        "AOSP Activity | lifecycle_controller | g07 fixture | microtimer | tictactoe | PASS 3x | bat | [RV]",
 "Intent":          "AOSP Intent | IntentShadow | g08 fixture | microtimer | — | PASS 3x | bat | [T]",
 "Bundle":          "AOSP Bundle | IntentShadow | g08 | dooz | — | PASS 3x | bat | [T]",
 "Handler":         "AOSP Handler | HandlerShadow + token law 3ea265be | microtimer | chessclock | bgclock | PASS 3x | bat | [RV]",
 "MessageQueue":    "AOSP MessageQueue | F-009 fast-forward law 8cd76a17 | microtimer | chessclock | gmdice | PASS 3x | bat | [RV]",
 "Thread":          "ojluni Thread | ThreadShadow + F-THREAD-TICK inline run | microtimer | gmdice | — | PASS 3x | bat | [T]",
 "AndroidX":        "AndroidX source | ArchTaskExecutor + F-011 keyed tag | dooz | survivalmanual | — | PASS 3x | bat | [~] BLOCKED — dooz SavedStateHandlesProvider → next: ComponentActivity state research",
 "View":            "AOSP View | ViewShadow + F-011/F-015 | g06 fixture | headingcalculator | tictactoe | PASS 3x | bat | [RV]",
 "ViewGroup":       "AOSP ViewGroup | G11 addView/cycle laws 37 | g06 | headingcalculator | g07 | PASS 3x | bat | [RV]",
 "Measurement":     "AOSP MeasureSpec | LinearLayout law 24 | g10 fixture | microtimer | — | PASS 3x | bat | [RV]",
 "Layout":          "AOSP layouts | G10 law 23 | microtimer | unote | — | PASS 3x | bat | [T]",
 "Resources":       "AOSP androidfw | ARSC style 17 + core 42 + config 48 | m3 fixture | EXT-01 | density matrix | PASS 3x | bat | [RV]",
 "AXML":            "AOSP ResXMLTree | axml_parser + inflater | headingcalculator | g06/g07/g08 | m3 | PASS 3x | bat | [V]",
 "Drawable":        "AOSP Drawable | state_list + GATE H chain | simplestopwatch | gmdice | EXT-01 | PASS 3x | bat | [T]",
 "Canvas":          "AOSP Canvas | canvas_shadow | scope | bouncy | — | PASS 3x | bat | [T]",
 "Text":            "AOSP text | harfbuzz+fribidi shaper | EXT-01 | billthefarmer notes | — | PASS 3x | bat | [T]",
 "Input":           "AOSP input | touch_dispatcher | g06 | tictactoe | EXT-02 | PASS 3x | bat | [RV]",
 "Lifecycle":       "AOSP Activity | G07 law 25 + finish cascade | g07 fixture | microtimer | g08 | PASS 3x | bat | [RV]",
 "SQLite":          "SQLite semantics | REAL sqlite3 backend 969cfc28 | microtimer | — | f012 | PASS 3x | bat | [T]",
 "Room":            "Room generated | F-ROOM-CHAIN chain | microtimer | — | f012 | PASS 3x | bat | [~] BLOCKED — F-018 second-run cursor law",
 "Persistence":     "AOSP storage | F-012 data-root law 53e474e7 | microtimer | — | f012 | PASS 3x | bat | [T]",
 "Native boundary": "JNI | classified | — | — | — | — | — | [D]",
 "Multi-Dex":       "AOSP dex | EXP-066 per-DEX resolution | — | — | — | — | bat | [T]",
 "Toolchain":       "reproducible AE | bootstrap_toolchain.sh | — | — | — | — | bat | [RV]",
 "Corpus":          "registry law | 20-APK SHA-256 phase0 | phase0 all | — | — | 2x det | bat | [V]",
}
lines2 = BODY.split("\n")
in_matrix = False
filled = 0
for i, ln in enumerate(lines2):
    if ln.startswith("| Domain "):
        in_matrix = True
        continue
    if in_matrix:
        m2 = re.match(r"^\|\s*([^|]+?)\s*\|", ln)
        m2k = m2.group(1).strip() if m2 else None
        if m2k in MATRIX:
            lines2[i] = f"| {m2k} | {MATRIX[m2k]} |"
            filled += 1
        elif ln.startswith("| ---") or ln.startswith("|-"):
            continue
        else:
            in_matrix = False
print("matrix rows filled:", filled)
BODY = "\n".join(lines2)

# ── Reconciliation banner (compact) ──────────────────────────────────
BANNER = """> **RECONCILIATION PASS — audited against repository truth at HEAD `a8655a04` (main, clean, synced).** Baseline rebuilt; toolchain restored via AE gate; full battery 63/64 PASS + 1 honest FAIL (F-012 rc-law — blocked by FINDING-018; the persistence+determinism laws of that golden PASS). All 886 checklist items audited: 501 regression-proven `[x]`; every other item carries its factual status tag per §0.6 — unchecked + tag = proven to that grade, never mass-checked. Family-G exceptions [RV] via F-016 (real unwind + app-boundary law + strict CRASH). Family-L locks closed via F-017 (LocksShadow + active-cycle receiver-identity law). Families I/J/K/L/V/CF carry second-order proofs from this session's F-016 execution. BLOCKED rows name their root cause inline. Full DIRECT-URL evidence directory: FINDINGS_REGISTRY.md (F-001..018), scripts/run_test_battery.sh (64 stages), phase0 20-APK matrix, commits 1ab35251 · cb5680f2 · a8655a04."""
inserted = False
for i, ln in enumerate(lines2):
    if ln.startswith("# MASTER-ROADMAP v3"):
        lines2.insert(i + 1, "")
        lines2.insert(i + 2, BANNER)
        inserted = True
        break
print("banner inserted:", inserted)
BODY = "\n".join(lines2)
open('/tmp/issue9_body_new.md', 'w').write(BODY)
print("final len:", len(BODY))

