# MINIANDROID FILE / RESOURCE / MEDIA LOADING COMPATIBILITY — full architectural diff

> Campaign: 2026-10-03. Companion: `docs/REAL_ANDROID_LOADING_ORACLE.md` (oracle),
> `docs/LOAD_COMPATIBILITY_MATRIX.jsonl` (machine-readable). Evidence = line-audit of
> the production tree at HEAD 3f05679f + live run proofs (§7). No app-specific findings.
> Status vocabulary: PROVEN (code+line cited) / INFERRED (flagged) / live-tested (§7).

---

## 1. SOURCE_FILE_CENSUS (ULTIMATE §1) — PROVEN

| Metric | Value |
|---|---|
| Source files (miniandroid/src) | **164** (78 .cpp / 86 .h) = **137,756 lines** |
| Compiled into `build/miniandroid` (Makefile is the real build graph) | **64 TUs** |
| Dead .cpp (not compiled) | **13 files / 8,164 lines** (`dex/api_dispatcher`, `exception_system`, `execution_guard`, `execution_observatory`, `exp002–006_*`, `renderer/view_renderer.cpp`, `resources/real_layout.cpp`) |
| Compiled-but-runtime-dead | `audio/audio_engine.cpp` (zero callers), `gles/gles20_bridge.cpp` (zero callers) |
| Stale build metadata | `CMakeLists.txt` references 6 nonexistent files; S68 build graph stale on audio/gles/megabatch; `docs/foundation/source_inventory.json` is actually an APK ledger |
| Largest TU | `src/dex/dalvik_engine.cpp` = **43,568 lines**; `bridge_to_api` ≈ lines 21609–43309 (~999 inline `method == "…"` branches) |

## 2. CANONICAL RUN PATH + SPLIT-BRAIN VERDICT (ULTIMATE §3/§116/§141) — PROVEN

```text
PRODUCTION (WORLD B — the only path that serves APKs):
main.cpp:827 main → :1136 cmd_run → :745-750 Storage::set_app_data_root
  → :751 runtime::ExecutionEngine engine → :765-776 ONE ShadowRegistry (33 shadows)
  → :790 run_on_art_sized_stack → ExecutionEngine::execute [BOOT-ORDER 7 stages
    execution_engine.cpp:153-195] → stage_execute_application_real_dalvik :581
    (Storage::set_context_package :630) → dalvik_engine_.execute_apk_with_activity :1222
  → DEX invoke → try_recursive_invoke (dalvik_engine.cpp:4688-8820, intercepts FIRST)
    else bridge_to_api (dalvik_engine.cpp:21609) / ShadowRegistry (first-handled wins)

WORLD A (test-only, unreachable by any APK code):
api/android_context.h Context/ContextWrapper/ApplicationContext + api/shared_prefs.h
  SharedPreferences + storage/file_sandbox.h FileSandbox
  — constructed ONLY by tests/test_android_context.cpp:675-845 (ContextFactory::create,
  application_context.cpp:597). Zero references from main/execution_engine/dalvik_engine.
  It implements MORE of the Context file API (openFileInput/Output, deleteFile,
  fileList, atomic pref writes) than the production engine — an unreachable richer twin.

SECOND UNIVERSE: ApplicationRuntime (runtime/application_runtime.cpp) — its own
ShadowRegistry + engine; constructed only by exp007_012_megabatch_main.cpp:469 (not in
`make all`). Legacy in-binary sim path: --execution-mode legacy (non-default).
```

**The APK-visible Context is a DEX-heap object** (`Landroid/content/Context;`,
dalvik_engine.cpp:9006/30878), never a C++ ApplicationContext. **Split-brain verdict:
CONFIRMED but asymmetric** — production is single-brained (WORLD B); the second brain
is dead weight that still gets compiled and still shadows the true API list.

**ResourceRuntime is a process-wide Meyer's singleton** (resource_runtime.cpp:14-17)
that re-inits **only when apk_path changes** (:20) — same-APK re-run reuses ARSC/ZIP/
theme/inflater caches; different-APK clear is partial (base theme + overlays only).

## 3. THE LOADING MATRIX (required §139 form; Layer | Real Android | MiniAndroid | Gap | Status)

Full per-layer rows are in `docs/LOAD_COMPATIBILITY_MATRIX.jsonl` (36 layers). Summary:

| Layer | Real Android | MiniAndroid (production) | Verdict |
|---|---|---|---|
| Package install | PMS commit → /data/app + identity | F-NEW-231 pkgstore (main.cpp:358-620) | ✅ TESTED |
| Package metadata | full PackageInfo/ApplicationInfo | versionCode/Name/sourceDir/publicSourceDir/phantom nativeLibraryDir; **dataDir/deviceProtected/credentialProtected/splitSourceDirs/processName/className = null** | ❌ GAP S-7 |
| Base APK | read in place, CRC, ZIP64 | ApkParser RAM cache 512MB cap, CRC32 ✓, **no ZIP64, uint16 entry count** | ⚠️ PARTIAL R-15 |
| Split APK | base+splits code/resource | **none** (splitSourceDirs never read) | ❌ MISSING S-11 |
| ClassLoader/DEX | BaseDexClassLoader, multidex | multi-DEX merge ✓, cross-DEX interface closure ✓, NCDFE clinit law ✓; **no DexClassLoader API, Class.getResourceAsStream missing** | ✅/⚠️ |
| Native libs | dlopen in nativeLibraryDir | **System.loadLibrary unhandled; nativeLibraryDir = phantom /data/app/~~miniandroid/base/lib/arm64; no .so extraction; JNI = Telegram-only stub registry; no JNI_OnLoad/RegisterNatives** | ❌ MISSING S-2 |
| Application | attachBaseContext→providers→onCreate | bind_manifest_application (dalvik_engine.cpp:4387-4526) real bytecode ✓ | ✅ (order ⚠️ S-1) |
| ContentProviders | installed BEFORE Application.onCreate | **NO provider stage anywhere (0 hits)** | ❌ MISSING S-1 |
| Activity/lifecycle | attach→onCreate→onStart→onResume | implemented w/ F-058 fan-outs | ✅ |
| Context | ContextImpl dir family | Storage::data_root F-NEW-234 law (files/cache/shared_prefs/databases/getDir/external) | ⚠️ PARTIAL (10 APIs missing, §4) |
| System services | real manager per constant | 21 names → bare singletons; **download/jobscheduler/usagestats/appops/phone/storage/wallpaper… → null marked IMPLEMENTED**; only layout_inflater/clipboard/alarm have behavior | ❌ HOLLOW S-8 |
| Resources (values) | best-match, NotFoundException | ARSC resolve_full (16-hop bound) + ThemeEngine attr chain ✓; **missing→""/black/24px/fake TypedArray; getIdentifier id-only; plurals/arrays absent** | ⚠️ FAKE-DEFAULT R-3/4/14 |
| Configuration | full qualifier law, night/land live | matcher AOSP-verbatim ✓ BUT device frozen 420dpi/1080x1920/portrait/NIGHT_NO/en-US; **-night/-land buckets unreachable; no-match → first-config fallback** | ❌ GAP R-8 |
| Assets | AssetManager2 open/openFd/list, FileNotFoundException | **open() fake-success (no existence check), 3 duplicate sites; list()→null; openFd/openNonAsset/openRawResourceFd/AssetFileDescriptor/ParcelFileDescriptor = 0 hits; assets read via popen(unzip), uncapped** | ❌ P0 R-1/R-2/R-5/R-7 |
| Streams | full java.io contract | read/readLine/available/close honest (K-34); **skip() unhandled; two divergent live readLine impls; >4MiB file: reads = fake EOF; FileOutputStream does not exist** | ❌ P0 ST-2/R-6 |
| File descriptors | PFD/AFD first-class | **zero support** | ❌ MISSING R-2 |
| Files | kernel semantics | exists/mkdir/create honest (R-NEW-346/347, F-NEW-223); **getAbsolutePath hijacked → constant /tmp/miniandroid/files (EXP-043 stub shadows the real law); isFile/delete/renameTo/list/listFiles/length/lastModified unhandled; no sandbox containment; no /data/user/0 alias; name-mutating clamps** | ❌ P0 ST-1/4/11/12 |
| Preferences | atomic XML, listeners, clear() | engine copy: **non-atomic ofstream, no XML escaping, commit() always true, remove/clear no-ops, no listeners** | ❌ GAP ST-6 |
| SQLite | real WAL/-journal lifecycle | real sqlite3 ✓; **WAL flag recorded-never-set (getter always false); databases_dir set by 3 parties order-dependent** | ⚠️ ST-7 |
| External storage | /storage/emulated/0 aliases | two spellings (virtual + backing); **stream laws + BitmapFactory.decodeFile translate neither** | ❌ GAP ST-5 |
| URI/ContentResolver | scheme dispatch + providers | Uri.parse/fromFile ✓; **ContentResolver=openInputStream(file://) only; content://, android.resource://, query/Cursor/PFD/FileProvider = none; Intent.getData() hardwired null** | ❌ MISSING S-4/5 |
| ContentProvider | component contract | **none** (no authority model at all) | ❌ MISSING S-1 |
| WebView | full API + callbacks | QuickJS engine real; file:///android_asset + https ✓; **no onPageFinished/shouldOverrideUrlLoading; addJavascriptInterface absent; localStorage kv_path never assigned (memory-only)** | ⚠️ S-10 |
| Fonts | per-request identity + fallback | DejaVu collapse (sans-serif*→DejaVuSans); **no Typeface.createFromAsset/createFromFile/getFont handlers; app assets fonts auto-registered silently (bold=filename heuristic); XML font-family unsupported; no requested≠resolved identity kept; monospace face missing at HEAD** | ⚠️ GAP R-12 |
| Images | all decoders via stream | decodeResource/File/ByteArray ✓ (PNG/JPEG/WebP/GIF/Vector/NinePatch); **decodeStream explicitly unsupported→null; Options absent (inSampleSize/inJustDecodeBounds); decodeResource ignores density (hardcoded 420 scale)** | ❌ GAP R-9/10 |
| Audio/Video | real pipelines | **MediaPlayer = object-state no-op (never reads source bytes); SoundPool synthetic ids; AudioTrack/VideoView/RingtoneManager absent; audio_engine compiled-dead** | ❌ STUB R-13 |
| Network | URL/OKHttp stacks | mininet http(s) ✓ (NET-001) | ✅ |
| Native file I/O | kernel under sandbox | **bitmap decodeFile raw; font fopen CWD-relative; absolute paths opened as-is; no .. / alias guard; popen(unzip) bypass** | ❌ GAP ST-4/5 |
| NDK assets | AAssetManager | **none** (no native layer at all) | ❌ N/A-today |
| Classpath resources | ClassLoader.getResource | getResources/getResource over APK entries ✓; ServiceLoader ✓; getResourceAsStream ✗ | ⚠️ |
| ZIP self-access | ZipFile over sourceDir | via apk-entry: law ✓ (tested Telegram) | ✅ |
| Asset packs | PAD model | none (honest: no consumer demand yet) | ⚠️ |
| Provenance | n/a (audit tool) | gfx byte_source 4-class + FileIoTrace 17 sites; **READ/LIST/DELETE/RENAME declared-never-emitted; byte reads untraced; fonts/audio/SQLite untraced** | ⚠️ ST-10 |

## 4. STRUCTURAL ROOTS (first divergences only — severity-ordered)

### TIER P0 — proven fake-success / capability-void on the production path

- **ST-1 `File.getAbsolutePath()` is hijacked by the dead EXP-043 stub** — dalvik_engine.cpp:38652-38656
  answers the constant `/tmp/miniandroid/files` for EVERY File and shadows the real
  R-NEW-347 law at 39908+ (its F-NEW-234 branch 39982 is unreachable). abs/canonical/path
  disagree per object; every absolute path an app trades is a foreign host path.
- **ST-2 `FileOutputStream` / `FileWriter` / `Context.openFileOutput` / `openFileInput` /
  `fileList` / `deleteFile` do not exist** — apps cannot persist any private file through
  java.io. (F-NEW-234 created the directories; the write API never landed.)
- **R-1 `AssetManager.open()` is fake-success** — 3 duplicate sites (5638-5677 live,
  39556-39576 divergent-duplicate, 42693 dead): no APK-entry existence check; a missing
  asset yields a stream whose first read is EOF ("open succeeded, read empty") instead of
  AOSP FileNotFoundException. Directly explains silent empty-config chains.
- **R-2 The entire FD family is absent** — openFd/openRawResourceFd/openNonAsset/
  AssetFileDescriptor/ParcelFileDescriptor: 0 hits. Media-from-fd, mmap-DB-from-assets,
  zip-over-fd resolve to tail null-stubs (43249-43293).
- **S-1 No ContentProvider installation stage** — androidx.startup/InitializationProvider,
  WorkManager/Firebase init never run (0 hits tree-wide). First blocker class for modern apps.

### TIER P1 — wrong answers where Android answers loudly

- **R-3 unresolved resource fake defaults**: getString→"" (33917), getColor→black (33958),
  getDimensionPixelSize→24px (33699), obtainTypedArray→fake len-1 zeros (22533),
  openRawResource→null-as-success (27421). AOSP throws NotFoundException.
- **R-4 `getIdentifier` resolves only type "id"** via the inflated tree (22692-22721);
  drawable/string/raw/font → always 0; programmatic resource binding dead.
- **R-5 asset bytes via `popen("unzip -p …")`** (4118-4125, 39652) — uncapped, host-tool
  dependent, quote-injection-prone; only `file:` reads are capped 4MiB (4084) so a >4MiB
  app-data file silently reads as EOF (fake).
- **R-6 two live `readLine` implementations with different byte-source laws** (5483 vs
  39632; dispatch depends on recursion-limit/dex_report_ state) — same app, different bytes.
- **R-7 `AssetManager.list()` unimplemented** → null (tail 43249).
- **S-4 ContentResolver = openInputStream(file://) only**; query/Cursor/getType/
  insert/update/delete/openFileDescriptor absent; content:// + android.resource:// dead.
- **S-5 `Intent.getData()` hardwired null** (android_shadows.cpp:2010) while the ctor
  records the Uri (:1982) — deep-links/ACTION_VIEW-with-data never receive data.
- **S-7 ApplicationInfo field starvation**: dataDir/deviceProtectedDataDir/
  credentialProtectedDataDir/splitSourceDirs/processName/className = null (34676-34691).
- **S-8 system services null-or-hollow, null marked IMPLEMENTED** (34298-34306):
  download/jobscheduler/usagestats/appops/phone/storage/wallpaper… → null; audio/
  notification/vibrator/sensor/location singletons have zero method handlers.
- **ST-4 no sandbox containment / no alias law**: absolute paths opened as-is (39849),
  `..` unguarded, no /data/user/0 ↔ /data/data equivalence (comments only, data_root.h:46);
  `File("/data/user/0/<pkg>/files/x")` from ApplicationInfo knowledge lands on the HOST.
- **ST-5 two external-storage spellings, streams know one**: getExternal* hand out BACKING
  paths (`<root>/storage/emulated/0/...`, data_root.cpp:95) while Environment hands out the
  VIRTUAL `/storage/emulated/0` (34473); translation exists only in metadata/creation laws —
  FileInputStream ctor (23496), openInputStream (23718), BitmapFactory.decodeFile
  (bitmap_shadow.cpp:167, fully raw) do not translate → exists()==true then open()==empty.

### TIER P2 — selection/correctness gaps

- **R-8 frozen device config**: 420dpi/1080x1920/portrait/NIGHT_NO/en-US (res_config.cpp:392-448);
  `-night`/`-land` buckets unreachable; no-match fallback = first-config-in-table
  (arsc_parser.cpp:556) instead of AOSP default-bucket rule; no runtime config switch.
- **R-9 density pipeline incomplete for bitmaps**: decodeResource ignores the selected
  density (bitmap_shadow.cpp:65-94); intrinsic scale hardcodes 420 (dalvik_engine.cpp:34147);
  BitmapFactory.Options (inSampleSize/inJustDecodeBounds/inScaled) absent.
- **R-10 `decodeStream` explicitly unsupported → null** (bitmap_shadow.cpp:189-196) — the
  canonical asset/network→bitmap path (SUPPLEMENT §49) is dead.
- **R-12 fonts**: no Typeface API handlers; assets fonts auto-registered with bold-by-
  filename heuristic (execution_engine.cpp:692-738); XML font-family/res/font unsupported;
  all sans-serif collapse to DejaVuSans; no synthetic bold; requested-vs-resolved identity
  not recorded (provenance law §28 violated).
- **S-2 native layer fictional**: System.loadLibrary unhandled (silent REC-MISS),
  nativeLibraryDir = phantom path, no .so extraction, no dlopen, JNI = Telegram stubs.
- **S-3/S-9/S-13**: broadcasts unmodeled (registerReceiver/sendBroadcast/onReceive = 0 hits);
  threading = serialized virtual-clock sim (FutureTask/CountDownLatch/wait unhandled,
  locks uncontended-by-construction); no Service lifecycle.
- **ST-6 engine SharedPreferences divergent**: non-atomic ofstream (32790), no XML escaping
  (32799 — a `<` or `&` value corrupts the file for its own line-parser), commit() always
  true (32816), remove/clear no-ops (32750), no listeners.
- **ST-7 DatabaseShadow root set by three parties in one init** (order-dependent guard,
  sqlite_shadow.cpp:18 + dalvik_engine.h:1303 + data_root.cpp:70); WAL getter always false
  (wal_enabled never assigned, :258 vs :352).
- **S-10 WebView**: no client callbacks fired; addJavascriptInterface absent; localStorage
  kv_path never assigned (webview_engine.cpp:118 — memory-only, comment claims file-backed).
- **S-11 split APKs unsupported** (code+resources; AAB apps NCDFE at first split-only class).
- **R-11 framework 0x01 = table + drawable/color file trees only** (no framework values
  beyond the generated attr table, no framework raw/fonts); getIdentifier never consults 0x01.

### TIER P3 — honest-incomplete / structural hygiene

- **R-13** audio/video object-state stubs; audio_engine.cpp compiled-dead. **R-14** plurals/
  getStringArray/getIntArray absent. **R-15** APK layer: whole-APK RAM (512MB cap), no ZIP64,
  uint16 entry cap. **R-16** provenance coverage image-centric; FileIoTrace declares
  READ/LIST/DELETE/RENAME that no code can emit (file_io_trace.h:7) and never traces actual
  byte reads (5487-5636), SQLite, fonts, popen extraction. **ST-8** FileSandbox second storage
  law, blind to --data-root, non-AOSP layout, linked-but-dead. **ST-9** virtual system image
  (fonts runtime/data/fonts, framework_res CWD fallbacks) shares the app-data namespace.
- **ST-11** ApplicationInfo.dataDir never seeded. **ST-12** name-mutating clamps (getDir →
  "default", 32882; getExternalFilesDir type → "default", 34354; FileSandbox erases `..`/dots)
  — silent renames violate the no-rewrite law. **ST-13** World-A dead weight (FileSandbox +
  ApplicationContext + api SharedPreferences compiled, unreachable) + 13 dead .cpp + stale
  CMakeLists + stale S68 graph. **ST-14** ResourceRuntime singleton partial reset between runs.

## 5. ROOT CLUSTERING (fan-out, not per-app) — the common roots that explain downstream symptoms

| ROOT FAMILY | Members | APIs | Symptom class in apps |
|---|---|---|---|
| FAKE-SUCCESS_RESOLUTION | R-1, R-3, R-4, R-7, S-8(null-as-IMPL), ST-1 | AssetManager.open/list, Resources getters, getIdentifier, getSystemService, File.getAbsolutePath | app continues silently on empty config/assets; wrong pixels/geometry; missing dynamic resources |
| FD_AND_STREAM_VOID | R-2, R-5, R-6, R-10, ST-2, S-4 | openFd family, PFD/AFD, decodeStream, FileOutputStream, openFileOutput, ContentResolver verbs | media/persist/export/image-from-stream features dead or empty |
| COMPONENT_CONTRACT_MISSING | S-1, S-3, S-13, S-11 | providers, receivers, services, splits | androidx.startup/WorkManager/Firebase init never runs; broadcast-driven and AAB apps blocked at init |
| PATH_LAW_INCOMPLETENESS | ST-1, ST-4, ST-5, ST-11, ST-12 | File family, alias law, external spellings | app-built Android paths hit host FS; exists/open asymmetry; /data/user/0 blind spot |
| NATIVE_FICTION | S-2, R-5 | loadLibrary, nativeLibraryDir, popen(unzip) | .so apps silently no-op; host-tool dependency |
| SELECTION_FROZEN | R-8, R-9, R-12, R-11 | config qualifiers, density, fonts, framework values | night/land variants never chosen; oversized bitmaps; font identity loss |
| STATE_LAYER_DIVERGENCE | ST-6, ST-7, ST-9, S-10(persistence) | prefs, SQLite WAL, fonts dir, localStorage | corrupt/lost persisted state across restarts |

## 6. "WE FORGOT THIS" — things previous campaigns had NOT registered

1. **ContentProvider installation stage missing entirely** (androidx.startup class).
2. **File.getAbsolutePath → constant /tmp/miniandroid/files** (dead stub shadowing the real law).
3. **FileOutputStream/openFileOutput family never existed** — the write side of app-private files.
4. **FD family (PFD/AFD/openFd/openRawResourceFd) is zero-hit** — a whole return-type class missing.
5. **AssetManager.open fake-success** (no FileNotFoundException contract).
6. **Two divergent live readLine / three open implementations** with dispatch-dependent behavior.
7. **`popen(unzip)`** as an asset byte source (host-tool dependency + injection surface).
8. **prefs XML unescaped + non-atomic + commit() always-true + clear() no-op.**
9. **WAL flag recorded-never-set; databases_dir set by 3 competing parties.**
10. **Intent.getData() hardwired null** despite ctor recording it.
11. **System services null-marked-IMPLEMENTED table** (honesty violation at the API-trace level).
12. **-night/-land buckets unreachable + first-config fallback** (wrong-bucket selection law).
13. **BitmapFactory.Options family absent; decodeResource density ignored (hardcoded 420).**
14. **Font identity never provenance-tagged** (requested≠resolved undetectable today).
15. **FileIoTrace declares READ/LIST/DELETE/RENAME that no code can emit.**
16. **External-storage double spelling breaks stream/FD round-trips.**
17. **ApplicationInfo.dataDir/splitSourceDirs/processName never seeded.**
18. **World-A dead object model compiled into the binary** (richer Context API unreachable).
19. **CMakeLists stale (6 nonexistent files) + S68 build graph stale** — build metadata lies.
20. **ResourceRuntime partial reset between same-path re-runs** (theme/ARSC cache law).

## 7. RUNTIME EVIDENCE (live proofs at HEAD 3f05679f — LOAD-AUDIT-2, 2026-10-03)

Build: HEAD source, `make -j1 CXXFLAGS=-O0 -g0`, 68 TUs, link OK (17.7MB). Suite:
`scripts/load_audit_proof.sh` + telegram probe; artifacts under `run/audit/`.

| Proof | Result |
|---|---|
| Install → identity (opencalc) | base.apk SHA == source SHA (2642613868a8a80f); store layout files/cache/code_cache/databases/shared_prefs/no_backup |
| Source-APK hiding ×3 targets | sources physically moved out during ALL runs; runs resolve from identity only; SHA verified on restore |
| 3-run determinism | opencalc e364b001ee7abd66 ×3 == registry golden; chess b5a7a35d5fe0564b ×3 == golden; telegram bbb6cd10a834963d == golden |
| Installed-provenance (P-3 live, telegram) | 7 asset OPENs, all `@ apk=<INSTALLED base.apk>` with real app DEX callers (o6;.p0, ih/a;.c/.a, ResLottieMeta, sg0); ALL 7 entries cross-checked == real APK entries → **no fake-success observed live** (R-1 stays code-proven: the existence check is absent; no target in this suite opened a missing asset) |
| files→APK asset fallback | files/bluebubbles.attheme EXISTS=FAILURE → OPEN assets/bluebubbles.attheme @ installed APK = SUCCESS (correct first-launch law) |
| **ST-4 live** | telegram opened **`/dev/urandom` as a raw host path** (OPEN SUCCESS) — absolute host paths are opened as-is, no sandbox containment (matches code law at 39849) |
| P-1 getAbsolutePath hijack | NOT-OBSERVED-THIS-CORPUS: opencalc/chess/telegram never feed getAbsolutePath into a traced op — remains line-proven (38652) only; needs a targeted probe APK |
| P-2 FileOutputStream void | NOT-OBSERVED-THIS-CORPUS: 1,517 traced API calls (chess) contain no FileOutputStream/openFileOutput call — remains code-proven (write path absent) |
| file-IO trace | 185 ops telegram r1 (93 MKDIR / 43 STAT / 31 WRITE / 9 OPEN / 7 EXISTS / 1 CREATE) — all app writes under data/data/<pkg>/ |

## 8. FINAL ANSWERS (the audit's required questions)

**Q44 (SUPPLEMENT):** *how does MiniAndroid know WHICH file an app means, WHERE it lives,
HOW to open it, and WHETHER the delivered bytes are the requested ones?*
- WHICH: resource ids via ARSC+config (correct for values/files); getIdentifier id-only
  (partial); asset paths verbatim (no existence contract); File paths as strings.
- WHERE: F-NEW-234 package sandbox for the Context family (correct); absolute Android
  paths NOT mapped (alias/`/data/user/0`/virtual-volume laws partial); system image
  (fonts/framework_res) CWD/exe-relative.
- HOW: real stdio for files, ARSC→APK-extract for resources, popen(unzip) for assets,
  NO fd layer at all.
- WHETHER: CRC32 on APK extraction ✓, gfx byte_source on decoded images ✓; asset
  streams/fonts/audio/SQLite UNPROVENANCED; requested-vs-resolved identity not recorded.

**WHAT IS PROVEN:** install identity, per-package sandbox, multi-DEX+clinit law, ARSC
best-match for values/drawables, theme/attr chain, inflate chain, WebView engine, network,
ZIP self-access, 3-run determinism culture.
**WHAT IS PARTIAL:** Context dir family (10 APIs), config selection (frozen device),
fonts, images (density/Options/decodeStream), SQLite (WAL), WebView (callbacks/persistence),
prefs, provenance coverage.
**WHAT IS BROKEN (P0):** ST-1, ST-2, R-1, R-2, S-1 (§4).
**WHAT IS UNKNOWN:** real-app fan-out per family until the corpus re-runs land; Persian
glyph coverage on host DejaVu; large-asset (>4MiB) behavior in real apps.
**COMMON ROOTS REMAINING:** the 7 families of §5 — fix order = fan-out rank: FD_AND_STREAM_VOID
and FAKE-SUCCESS_RESOLUTION first (they gate persistence, assets, media, decodeStream),
then COMPONENT_CONTRACT_MISSING (providers), then PATH_LAW_INCOMPLETENESS.

---

## 9. IMPLEMENTATION WAVE (LOADING-CAMPAIGN, 2026-10-03, HEAD = this commit)

The P0 class of §4 is now IMPLEMENTED + runtime-proven (no package-specific
code; every law cites AOSP):

| Root | Fix (generic) | Runtime proof |
|---|---|---|
| ST-1 abs-path hijack | EXP-043 stub DELETED; R-NEW-347 + F-NEW-234 branch now reachable | probe `abs-ok=true` (`/data/user/0/...` answers verbatim) |
| ST-2 write family void | FileOutputStream/FileWriter/BAOS ctor+write/flush/close; Context openFileOutput(MODE_APPEND honored)/openFileInput/fileList/deleteFile; File delete/renameTo/length(J)/isFile/list/listFiles | `write-length=14`; `probe.txt` 14B on store; `ren-dst-length=13`; `deleteFile-again=false` |
| ST-4 containment + alias | ONE `Storage::resolve_android_path` law (SANDBOX_DATA / INSTALLED_APK / VIRTUAL_EXTERNAL / SYSTEM_IMAGE / DEVICE_NODE / DENIED_HOST_PATH); `/data/user/0` ≡ `/data/data` | `host-deny=FNFE-HONEST`; `/etc` mkdirs=false; `/home` list=null; `alias-exists=true`; `/dev/urandom` ALLOWED (AOSP sepolicy-legal) |
| R-1 asset fake-success | APK-entry existence check at BOTH open sites → FileNotFoundException; provenance recorded | `asset-missing=FNFE-HONEST` |
| R-5 popen(unzip) + 4MiB fake-EOF | in-process ZIP extraction only; 256MiB honest refusal; char-device read law | no unzip subprocess in any trace; `urandom-read=OK` |
| R-7 AssetManager.list | real ZIP namespace; missing dir → null (AOSP quirk) | `asset-list-has-text=1`; nested len=1 |
| R-2 FD family void | openFd (stored-only law) → AssetFileDescriptor + REAL host fd; AFD getStartOffset/getLength (INT64)/createInputStream; ParcelFileDescriptor open/getFd/dup/close; openRawResourceFd | `openFd off=7417 len=75`; `afd-bytes=75`; magic `89 50` |
| R-10 decodeStream | engine-registered stream-bytes resolver drains open_assets_ sources → decoder | `decodeStream=8x8` |
| ST-5 decodeFile/spellings | decodeFile through the path law | `decodeFile=8x8` (75B png written via the write family) |
| ST-6 prefs | atomic tmp+rename, XML-escaped names+values (+unescape on read), commit() = real result, remove/clear real | `prefs-esc=a<b>&c"d'e` round-trip; `prefs-clear-killed-esc=1` |
| ST-7 SQLite authority+WAL | set_package_info setter REMOVED (one authority: set_context_package); real `PRAGMA journal_mode=WAL` on request | `-wal`/`-shm` files on microtimer store; `probe_db.sqlite` |
| S-1 provider stage | `install_content_providers()` at bind entry (BOTH default + custom app paths); manifest `<provider>` parse; real DEX `<init>`+onCreate | `provider-ran=1`; `[S1-PROVIDER] installed ... onCreate OK` |
| S-5 Intent.getData | returns the recorded Uri object | code law (android_shadows) |
| S-7/ST-11 ApplicationInfo | dataDir (logical `/data/data/<pkg>`), credentialProtected, deviceProtected (`/data/user_de/0`), processName, className seeded | seeded fields on the AI singleton |
| ST-2/ST-4 File metadata | length/lastModified `()J` INT64 register-pair law; isFile; delete/renameTo real; list/listFiles with null-when-not-dir | `ren-dst-length=13`; `ren-dst-isFile=true` |

### Probe-discovered NEW LAWS (registered; see docs/LOADING_FAILURE_DIAGNOSTICS.md)

1. `InputStream.read(byte[]) ≡ read(b,0,b.length)` fill law (the 2-arg
   overload must fill the caller's array — previously the single-byte law
   answered, leaving buffers unwritten → 0-byte sinks).
2. `java.io.ByteArrayOutputStream` family (ctor/write/toByteArray/size/reset).
3. `String(byte[])` ctors materialize onto the receiver object via the
   `__string_value__` convention (new-instance identity law).
4. `File.length()/lastModified()` + AFD `getStartOffset()/getLength()` are
   `()J` — INT64 register-pair law (INT32 answers read as 0).

## 10. PROBE + REGRESSION RESULTS (the wave's runtime evidence)

- **Synthetic probe gate: 23/23 ALL PASS** (`scripts/loading_probe_runner.sh`)
  — build → install → 3 runs on ONE store (restart law) → asserts on the
  rendered probe text + store tree + file-IO JSONL.
- **Restart persistence**: prefs counter 1→2→3 across restarts; probe.txt /
  img_copy.png (75B) / ren-dst.txt / probe_db.sqlite persisted in
  `<store>/data/data/com.probe.loading/`.
- **Real-package restart proof**: 3 gate runs on one store leave persisted
  state per package — opencalc `<pkg>_preferences.xml`, chess
  `chess_pgn.db`+`ChessPlayer.xml`, microtimer `app-data(-wal/-shm)`, unote
  `notes.db` (docs/INSTALL_TREE_PROOF.jsonl).
- **Regression (goldens byte-identical, zero drift)**: opencalc
  `e364b001ee7abd66` ×3, chess `b5a7a35d5fe0564b` ×3, dooz
  `d602648e8e401895` ×3, microtimer `da73010a37dd0189` ×3, unote
  `4f1a9e4e8f64fae8` ×3, telegram `bbb6cd10a834963d` ×1
  (`scripts/working_vs_failing_probe.sh`).

**Verdict**: the byte-loading architecture is no longer materially
incomplete at the P0 class — install identity (previous wave) + write/read
families + asset contract + FD layer + path law + provider stage now have
AOSP-shaped, runtime-proven implementations. Remaining frontiers (honest):
S-2 native/dlopen layer, S-4 content:// query/Cursor, S-11 split APKs,
S-3/S-13 broadcasts/services, SELECTION_FROZEN (config/density/fonts),
S-10 localStorage — each with a deterministic synthetic probe still to run
before any implementation claim.
