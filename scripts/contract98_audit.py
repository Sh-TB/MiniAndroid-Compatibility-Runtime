#!/usr/bin/env python3
"""#374 98-section foundation contract — execution status audit.

Produces docs/FOUNDATION_CONTRACT_98.jsonl + .md. Every section gets an
exact status and an evidence pointer. No placeholder counted as VERIFIED.
Statuses: VERIFIED / TESTED / IMPLEMENTED / PARTIAL / BLOCKED-EXTERNAL /
PENDING / NOT_APPLICABLE.
"""
import json
from pathlib import Path

BASE = Path("/home/z/my-project")

# id, title, status, evidence, remaining-gap ("" if none)
S = [(1,"PLATFORM / DEVICE CONTRACT","TESTED","docs/ENVIRONMENT_PROFILE.json ENV-001..010 (sha 56e6347116942bfc); density best-match probe CFG-01..05; locale/tz/12-24h laws in dalvik_engine",""),
 (2,"CPU / ABI / NATIVE FOUNDATION","TESTED","install ABI law main.cpp (SUPPORTED_ABIS x86_64-first); NATX 10/10x3 results sha 4d7761f7; arm-only APK refusal A/B (EggReturnsHome install-OK/launch-fail); ABI_MISMATCH_VERDICT in pkginspect prerequisites",""),
 (3,"PACKAGE MANAGER / INSTALLATION","TESTED","install creates package state (package.json/native_libs.json/data dirs); reinstall-identity src==inst==pkgaudit shas; pkginspect 15 sections; uninstall 16/16; splits = PARTIAL (S-11)"),
 (4,"APK STRUCTURAL PREFLIGHT","TESTED","pkginspect prerequisites APK-001..020 (sdk/components/abis/DT_NEEDED/features implied requirements REQUIRED/OPTIONAL/CONDITIONAL/IMPLIED); 30-APK matrix docs/ENV_PREREQUISITE_MATRIX.jsonl",""),
 (5,"PERMISSION FOUNDATION","TESTED","permission state machine normal/dangerous/signature/special + denial contracts; negatives 17/17 incl. N-perm rows; no universal grant",""),
 (6,"PACKAGE / USER / UID / SECURITY IDENTITY","TESTED","per-package isolation proofs (uninstall probe store-empty; cross-package DENIED rows N-xx); shared-UID model absent by profile (documented)"),
 (7,"FILESYSTEM / STORAGE","TESTED","path law categories SANDBOX_DATA/INSTALLED_APK/VIRTUAL_EXTERNAL/DEVICE_NODE/DENIED; CE/DE (user_de prefix-strip fix, DE-01); persistence 32/32; INSTALL_TREE_PROOF.jsonl",""),
 (8,"CONTEXT / CONTEXTIMPL","TESTED","Context dir family laws (getDataDir/getCodeCacheDir/...); createPackageContext/deviceProtectedStorageContext laws; provider-getContext receiver-identity gate R-NEW-462"),
 (9,"SYSTEM SERVICES","TESTED","SVC-01..04 ActiveServices started-vs-bound; BCAST-01..04 dynamic+manifest delivery; getSystemService inventory honest-absent for unimplemented (FALSE_ADVERTISED audit this wave)",""),
 (10,"BINDER / IPC","PARTIAL","in-process service/provider dispatch = real semantics for single-runtime profile; cross-process Binder driver is NOT implemented (declared profile boundary)","cross-process Binder transactions require a kernel-like Binder driver — profile boundary"),
 (11,"ACTIVITY / SERVICE / RECEIVER / PROVIDER / PROCESS","TESTED","lifecycle traces (lifecycle_trace.json); installContentProviders authority map; ActivityThread handleBindApplication laws; provider startup androidx.startup chain (memory app)"),
 (12,"INTENT / RESOLUTION","TESTED","IntentFilter engine state + resolution probes; resolveContentProvider installed-authority law; intent-filter manifest parse laws"),
 (13,"RESOURCES / CONFIGURATION","TESTED","multi-config probe CFG-01..05 (-night/-land/-zh-rCN unreachable-at-frozen-profile documented); density best-match xhdpi@420dpi; ARSC getIdentifier R-4"),
 (14,"MAIN THREAD / SCHEDULING","TESTED","Looper/Handler laws; frame pump probes; ThreadPoolExecutor real threads (fairymahjong async pipeline evidence)"),
 (15,"WINDOW / VIEW / INPUT FOUNDATION","TESTED","TouchDispatcher AOSP claim law (topmost-claimant-wins, tap pager->button proof); WindowInsets.CONSUMED seed R-NEW-461; view attach/measure/layout/draw traversal"),
 (16,"GRAPHICS / SURFACE / PRESENTATION","TESTED","FRAME_CAPTURE_TRUTH 12-item chain; 21-P0-6 pixel ownership; goldens 4/4 REAL_APP_CONTENT; app_owned_pixels + draw_ops metrics; GLSL recorded-not-executed (F-144 PARTIAL)"),
 (17,"INPUT / DEVICE FEATURES","TESTED","input dispatch probe rows; touch claim law; motion event routing to registered listeners (F117-TAP evidence)"),
 (18,"NETWORK","PARTIAL","S100 NET-001: real TLS via OpenSSL lineage (BoringSSL); HTTP(S) GET/parse proven; socket policies honest","netd/DNS service layering simulated; VPN absent (profile boundary)"),
 (19,"MEDIA / AUDIO","PARTIAL","real decode: mpg123 (MP3) + sndfile (WAV) + WebP/JPEG/PNG/GIF codecs; flappycow bitmap provenance 12 events APK-art-exact","MediaCodec API surface absent (decode is codec-lib direct); DRM absent"),
 (20,"HARDWARE / SENSOR CAPABILITIES","TESTED","honest absence: camera/GPS/BT/NFC/sensors return real 'not available' shapes; FALSE_ADVERTISED audit enforces zero fake hardware"),
 (21,"SYSTEM PROPERTIES / BUILD CONTRACT","TESTED","Build.* profile laws (device/fingerprint/SUPPORTED_ABIS honest); system property store; VERSION_CODES gates"),
 (22,"UNIFIED APK PRE-FLIGHT","TESTED","pkginspect prerequisites section (APK-001..020) + ENVIRONMENT_PROFILE compare + nativeAbiVerdict + missingCapabilities"),
 (23,"PRE-FLIGHT MUST PRECEDE LAUNCH","TESTED","Agent Skill op-1 intake runs prerequisites before install/run (skill_manifest.json op order; selftest 13/13)"),
 (24,"WHITE / BLACK / PARTIAL RECLASSIFICATION","TESTED","docs/WS_PREREQUISITE_AUDIT.md (5 runtime vs 2 env-caused vs 1 dup); DIFFERENTIAL_WORKING_VS_WHITE classification; env-vs-runtime split by evidence"),
 (25,"ROOT REGISTRY CROSS-MATCH","TESTED","docs/DEEP_ROOT_CROSSMATCH.jsonl 10 candidates A-F zero duplicates; registry 540 roots with crossmatch discipline"),
 (26,"NEGATIVE SECURITY TESTS","TESTED","negatives 17/17 (N-01..N-17); this wave extends to 19 (URI-grant, PendingIntent identity)"),
 (27,"REAL APK VALIDATION","TESTED","goldens 4/4 + anchors 5/5x3 + fan-out VERIFIED x3 + corpus 79 executed-with-evidence; new app/game each wave"),
 (28,"EVIDENCE","TESTED","STATUS-RESULT-EVIDENCE ledgers; run/ artifact dirs; docs/evidence/canonical; registry evidence fields; worklog append-only"),
 (29,"REQUIRED FINAL OUTPUT","IMPLEMENTED","ledger generators (this wave: FOUNDATION_CONTRACT_98, FALSE_ADVERTISED_MATRIX, BASE_COMPLETION_RECONCILIATION)"),
 (30,"DEFINITION OF DONE","IMPLEMENTED","#374 §98 gate checklist executed in the final report of this wave"),
 (31,"ANDROID RUNTIME / DEX EXECUTION CONTRACT","TESTED","law battery 124 stages (semantics/prefs/text/scroll/gif/canvas/drawables/layout); F-NEW-084 forward-progress law v3; register/verify laws"),
 (32,"JAVA/LIBCORE API FOUNDATION","TESTED","API matrix 59/60 TESTED (G-3 closed); EnumSet/framework-enum laws; Calendar/Date family; AtomicFile law; ArrayList/Collection laws"),
 (33,"JNI / NATIVE BRIDGE CONTRACT","TESTED","src/jni/dlopen_exec.cpp real dlopen + JNI_OnLoad + JNIEnv slot indices; native_thunk.S SysV ABI; NATX-01..10; honest ULE shapes"),
 (34,"PROCESS / ZYGOTE / APPLICATION STARTUP CONTRACT","TESTED","ActivityThread laws (bind app, installContentProviders, first-active-use clinit JVMS 5.5); process-death counting in A/Bs"),
 (35,"THREADING / MEMORY / PROCESS RESOURCE CONTRACT","TESTED","real pthread threads; MemoryPeak metric; ThreadPoolExecutor from real app; --max-instructions resource knob (semantic law separate)"),
 (36,"KERNEL / POSIX / LOW-LEVEL CONTRACT","TESTED","POSIX file/fd laws; character-device bounded-read (/dev/urandom); UnixFileSystem mapping; path reverse law"),
 (37,"HAL / HARDWARE ABSTRACTION BOUNDARY","NOT_APPLICABLE","no HAL drivers in container profile; all hardware surfaces honest-absent (profile documented in ENVIRONMENT_PROFILE)",""),
 (38,"BOOT / SYSTEM-SERVICE INITIALIZATION","TESTED","system-ready ordering for provider/ActivityThread chain; androidx.startup InitializationProvider sequencing evidence"),
 (39,"CLOCK / TIME / ALARM CONTRACT","TESTED","Calendar/Date family laws; time4j full chain closure (3 process deaths -> 0); AlarmManager honest-stub semantics"),
 (40,"POWER / BATTERY / DOZE-LIKE STATE","PARTIAL","battery/charging Build/property rows honest-static; doze semantics out of profile","doze/job idle modes require scheduler infrastructure — profile boundary"),
 (41,"NOTIFICATION / BROADCAST / ALARM / JOB CONTRACT","TESTED","NotificationManager core laws; broadcast delivery BCAST-01..04; JobScheduler honest-stub (registered not executed)"),
 (42,"URI / CONTENT / FILE PROVIDER SECURITY CONTRACT","TESTED","FileProvider.parsePathStrategy end-to-end (meta-data/getXml/loadXmlMetaData laws); PROV-02..09 ContentResolver/Cursor dispatch; grantUriPermissions manifest law"),
 (43,"DATABASE / SQLITE CONTRACT","TESTED","real sqlite3 backend; WAL provenance rows (SQLITE-OPEN/EXEC/WAL); restart persistence probe rows"),
 (44,"STORAGE / BACKUP / RESTORE / CLEAR-DATA SEMANTICS","TESTED","reinstall 8/8 (preserve semantics); clear-data + uninstall cleanup proofs; DE fence; backup/restore transport absent (profile)"),
 (45,"SIGNING / CERTIFICATE / PACKAGE TRUST","TESTED","pkginspect signature identity section; v1/v2 signer extraction; trust = install-time identity (no OTA/store trust chain in profile)"),
 (46,"PACKAGE UPDATE / SPLIT / INSTALLER CONTRACT","PARTIAL","install/update/uninstall real; split APK (.apks/base+config) loading = S-11 PENDING with recorded plan UPP-004","split-APK ClassLoader merge (S-11) — registered PENDING"),
 (47,"APP VISIBILITY / QUERIES / CROSS-APP DISCOVERY","TESTED","manifest <queries> parse law; package-visibility filtering in PackageManager query APIs; crossmatch via pkginspect"),
 (48,"COMPONENT SECURITY / PENDING INTENT","TESTED","exported/unexported + permission-guard laws in negatives; PendingIntent identity rows added this wave (N-18)"),
 (49,"APP DATA / CACHE / CODE LOADING TRUST BOUNDARY","PARTIAL","sandbox code-load trust enforced (installed-APK path laws); dynamic DexClassLoader from app-writable paths absent by profile","DexClassLoader dynamic loading — registered PENDING (S-family)"),
 (50,"GRAPHICS RESOURCE / FONT / TEXT STACK","TESTED","FreeType/HarfBuzz/FriBidi pipeline; font TTF bytes resource law; monospace law; StaticLayout/measure laws in battery"),
 (51,"ACCESSIBILITY / SEMANTIC UI CONTRACT","PARTIAL","ViewTree contentDescription semantics recorded; accessibility services absent (profile)","a11y service runtime — honest absent"),
 (52,"CONFIGURATION CHANGE / DEVICE STATE CONTRACT","TESTED","frozen-profile law (unreachable configs documented); density matrix 11/11; recreate/rotation semantics = frozen profile (documented)"),
 (53,"APP STOP / FORCE-STOP / BACKGROUND CONTRACT","TESTED","stopSelf/stopService laws (SVC); force-stop = process teardown in run contract; background policy minimal-honest"),
 (54,"EXCEPTION / ERROR / LOGGING CONTRACT","TESTED","crash.log + bounded logging law; exception propagation laws (caught-halt resume F-NEW-084); ANR watchdog absent (profile)"),
 (55,"OBSERVABILITY / FIRST-DIVERGENCE INFRASTRUCTURE","TESTED","first-divergence section in pkginspect; api_trace/lifecycle_trace/crash.log per run; MINIANDROID_FILE_IO/GFX provenance JSONLs"),
 (56,"FOUNDATION SELF-TEST SUITE","TESTED","battery 124 stages; gate A probe 95/0/2; loading probe 23/23; NATX 10/10; r464 probe 12/12; f084 probe 3/3"),
 (57,"FOUNDATION COVERAGE MATRIX","TESTED","docs/EXECUTION_LEVEL_MATRIX.jsonl (L0-L6, 15 L6); API matrix; ENV_PREREQUISITE_MATRIX 30 APKs; this wave adds FOUNDATION_CONTRACT_98"),
 (58,"UNKNOWN-APK GATE","TESTED","Agent Skill v2 selftest 13/13; pkginspect prerequisites -> verdict pipeline; 15-verdict vocabulary enforced (this wave audit)",""),
 (59,"BASE COMPLETION AUDIT","TESTED","docs/BASE_COMPLETION_RECONCILIATION.{md,jsonl} (this wave) + worklog reconciliation section"),
 (60,"FINAL COMPLETION RULE","IMPLEMENTED","final report #375 §19 with the §98 gate checklist"),
 (61,"PLATFORM BOOT / PARTITION / MODULE CONTRACT","NOT_APPLICABLE","no boot partitions in container; image/partition surfaces simulated by logical path laws only (documented)",""),
 (62,"APEX / MAINLINE / BOOTCLASSPATH / SYSTEM MODULE CONTRACT","NOT_APPLICABLE","single runtime image by design; bootclasspath = engine builtin (documented profile)",""),
 (63,"LINKER / ELF / NDK / C LIBRARY CONTRACT","TESTED","real dlopen/dlsym/DT_NEEDED closure; ELF class/machine checks; honest wrong-ELF refusal; musl/glibc host boundary documented"),
 (64,"COMPATIBILITY-CHANGE / TARGET-SDK CONTRACT","PARTIAL","target-SDK parsed + behavior gates where implemented (permissions model); compat-change IDs not individually enforced","compat framework change-ID matrix — registered PENDING"),
 (65,"API-LEVEL / SDK SURFACE MATRIX","TESTED","API matrix 59/60 TESTED; uses-sdk min/target from manifest; API-level gates in permission laws"),
 (66,"HIDDEN API / REFLECTION / LINKAGE CONTRACT","PARTIAL","reflection laws: Method.getModifiers R-NEW-464 (probe 12/12), getDeclaredMethods, annotation proxy access; hidden-API meta-enzyme not enforced (profile = public API + reflection used by real apps)","hidden-API greylist enforcement — declared out of profile"),
 (67,"SYSTEM SERVER / SERVICE DEPENDENCY GRAPH","PARTIAL","service inventory + start ordering implemented for used services; full system_server graph out of profile",""),
 (68,"INSTALld / VOLD / STORAGE-DAEMON CONTRACT","TESTED","install-time lib extraction + data dir creation semantics (installd-equivalent); vold = virtual external storage law; daemon processes themselves out of profile"),
 (69,"SCOPED STORAGE / SAF / MEDIASTORE CONTRACT","PARTIAL","app-specific external dirs + virtual external law implemented; SAF document provider + MediaStore provider absent","SAF/MediaStore — registered PENDING (S-4 extension)"),
 (70,"CRYPTO / TLS / CONSCRYPT / KEYSTORE CONTRACT","PARTIAL","TLS real (OpenSSL); MessageDigest/Cipher laws via OpenSSL; Android Keystore absent","Keystore hardware-backed semantics — external capability"),
 (71,"SELINUX / MAC / CAPABILITY CONTRACT","NOT_APPLICABLE","no SELinux in container; security model = package sandbox + permission machine (documented profile)",""),
 (72,"SIGNATURE / TRUST / IDENTITY CHAIN","TESTED","signer identity chain install-time; signature-permission denial negatives; cross-package identity isolation"),
 (73,"USERS / PROFILES / USER LIFECYCLE","PARTIAL","user 0 + user_de (DE) implemented with prefix law; multi-user/profile lifecycle absent","multi-profile — profile boundary"),
 (74,"APP STANDBY / ROLES / APP-OPS / USAGE STATE","PARTIAL","AppOps modeled in permission machine; standby buckets absent",""),
 (75,"NOTIFICATION / UI POLICY CONTRACT","PARTIAL","notification object/laws core; channels/UI policy surface minimal",""),
 (76,"WINDOWING / DISPLAY / IME / SYSTEM-UI CONTRACT","PARTIAL","single-window profile (documented); IME absent (honest); status bar chrome excluded from app pixels (21-P0-6)"),
 (77,"RENDERTHREAD / SKIA / TEXT / COMPOSITOR CONTRACT","TESTED","software renderer real draw ops; text shaping real; compositor = single-buffer present (documented); pixel-ownership gate"),
 (78,"INPUTFLINGER / EVENT ROUTING CONTRACT","TESTED","touch claim law + dispatch chain; key event path minimal-honest; inputflinger-equivalent = dispatcher module (documented)"),
 (79,"AUDIO / CAMERA / SENSOR / LOCATION PIPELINE CONTRACT","PARTIAL","audio output pipeline real (sndfile/mpg123 decode + sink); camera/sensor/location honest-absent",""),
 (80,"CONNECTIVITY / NETD / VPN / DNS CONTRACT","PARTIAL","TLS/HTTP real; DNS via host resolver; netd/VPN absent",""),
 (81,"MEDIA / CODEC / DRM CONTRACT","PARTIAL","codec-lib decode real for MP3/WAV/PNG/JPEG/WebP/GIF; MediaCodec surface API absent; DRM absent",""),
 (82,"CAMERA2 / IMAGE / SENSOR CONTRACT","BLOCKED_EXTERNAL_NO_CAMERA","no camera device exists in container — external hardware prerequisite, proven by environment","external hardware required"),
 (83,"ACCESSIBILITY / AUTOFILL / TEXT-SERVICE / IME CONTRACT","PENDING","a11y node semantics minimal; autofill/IME services absent",""),
 (84,"CLIPBOARD / DRAG-DROP / SHARE / CHOOSER CONTRACT","PARTIAL","ClipboardManager real; share/chooser intent routing minimal; drag-drop absent",""),
 (85,"SETTINGS / SYSTEM-CONFIGURATION CONTRACT","TESTED","Settings.Secure/Global reads wired to profile properties (12/24h, tz, fonts); writes honest-stub"),
 (86,"BACKUP / RESTORE / ACCOUNT / CREDENTIAL STATE","PARTIAL","clear-data/uninstall semantics real; backup transport + AccountManager absent",""),
 (87,"JOB / WORK / ALARM / FOREGROUND EXECUTION POLICY","PARTIAL","WorkManagerInitializer provider chain (memory app) + AlarmManager/JobScheduler registered-stub; foreground-service policy minimal",""),
 (88,"WIDGET / SHORTCUT / LAUNCHER / LIVE SURFACE CONTRACT","PARTIAL","ShortcutInfo.Builder law; app-widget host absent (no launcher surface in profile)",""),
 (89,"ERROR / CRASH / ANR / WATCHDOG CONTRACT","TESTED","crash.log contract + process-death counting + APP-BOUNDARY unwind classification; watchdog absent (single-threaded run contract)"),
 (90,"STRICTMODE / DEBUG / PROFILING OBSERVABILITY","PENDING","StrictMode/Traces APIs absent",""),
 (91,"TESTING CONTRACT — CTS-LIKE NEGATIVE/POSITIVE PAIRS","TESTED","negatives 17/17 (this wave 19); gate A positive/negative pairs; probe fixtures per law"),
 (92,"CORPUS-DERIVED FOUNDATION DISCOVERY","TESTED","corpus 79 executed-with-evidence; random-seed picks (fishrings seed 20261004); this wave new random picks"),
 (93,"API / SYMBOL / BEHAVIOR COVERAGE, NOT FILE COVERAGE","TESTED","API matrix asserts behavior (return values, exceptions), not file existence; NATX value-proofs cross-boundary"),
 (94,"REFERENCE-ORACLE DIFFERENTIAL TESTING","PARTIAL","A/B causal proofs per fix (S-2 0->10, time4j 3->0 deaths, fossifyclock REC-MISS 11->0); continuous oracle differential not built","oracle harness continuous mode — PENDING"),
 (95,"SUPPORTED-PLATFORM PROFILE","TESTED","docs/ENVIRONMENT_PROFILE.json + README CURRENT CAPABILITY STATE; claims outside profile = UNKNOWN by law"),
 (96,"FOUNDATION COMPLETENESS SCORE","TESTED","docs/BASE_COMPLETION_RECONCILIATION.md per-domain counts (this wave); no single percentage"),
 (97,"FINAL NOTHING-LEFT-HIDDEN REVIEW","TESTED","reconciliation matrix enumerates registry 540 + frontiers + 98 sections (this wave)"),
 (98,"FINAL GATE — BASE IS REALLY COMPLETE","IMPLEMENTED","final report executes the 16-point gate (this wave)"),
]

out = []
for row in S:
    num, title, st, ev = row[0], row[1], row[2], row[3]
    gap = row[4] if len(row) > 4 else ""
    item = {"num": num, "title": title, "status": st, "evidence": ev}
    if gap: item["gap"] = gap
    out.append(item)

with open(BASE / "docs/FOUNDATION_CONTRACT_98.jsonl", "w") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

from collections import Counter
c = Counter(r["status"] for r in out)
md = ["# #374 FOUNDATION CONTRACT — 98-SECTION EXECUTION AUDIT", "",
      "Every section classified with status + evidence pointer. No placeholder counted as VERIFIED.",
      "", "## Status totals", ""]
for k, v in c.most_common():
    md.append(f"- {k}: {v}")
md += ["", "| § | Section | Status | Evidence | Gap |", "|---|---------|--------|----------|-----|"]
for r in out:
    md.append(f"| {r['num']} | {r['title']} | {r['status']} | {r['evidence']} | {r.get('gap','')} |")
(BASE / "docs/FOUNDATION_CONTRACT_98.md").write_text("\n".join(md) + "\n")
print("sections:", len(out), dict(c))
