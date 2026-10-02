# REAL ANDROID LOADING ORACLE — AOSP semantic laws for every byte source

> Campaign: INSTALLED-APP FILESYSTEM + FULL FILE/RESOURCE/MEDIA LOADING AUDIT (2026-10-03).
> Purpose: the authoritative REAL_ANDROID_LOADING_MATRIX. Every law here is cited from
> AOSP sources (frameworks/base) and is the comparison oracle for
> `docs/FILE_RESOURCE_LOADING_COMPATIBILITY.md`. Unknown remains unknown (CONSTITUTION §7).
> Companion machine-readable matrix: `docs/LOAD_COMPATIBILITY_MATRIX.jsonl`.

---

## 0. THE COMPLETE LOAD ARCHITECTURE (AOSP, android-13/14 era)

```text
INSTALL (PackageManagerService)
  → /data/app/~~random~~/<pkg>-<rand>/base.apk  (+ split_N.apk siblings)
  → PackageInfo / ApplicationInfo committed to PackageManager
  → /data/app/.../lib/<abi>/*.so extracted; nativeLibraryDir set
  → /data/user/0/<pkg>/{files,cache,code_cache,shared_prefs,databases,no_backup,app_*}
  → /data/user_de/0/<pkg>  (device-protected)
  → /storage/emulated/0/Android/{data,media,obb}/<pkg>/   (external, on first access)

PACKAGE IDENTITY
  → ApplicationInfo: sourceDir, publicSourceDir, splitSourceDirs[], dataDir,
    deviceProtectedDataDir, credentialProtectedDataDir, nativeLibraryDir,
    secondaryNativeLibraryDir, resourceDirs, sharedLibraryFiles
  → every field is a REAL path; /data/data/<pkg> == /data/user/0/<pkg> (same inode,
    user-0 alias) — apps use both spellings interchangeably

PROCESS START (ActivityThread)
  → zygote fork → ActivityThread.main → Looper.prepareMainLooper
  → attach(): IActivityManager.attachApplication
  → handleBindApplication:
      1. LoadedApk constructed (classloader = BaseDexClassLoader over
         sourceDir + splitSourceDirs; librarySearchPath = nativeLibraryDir)
      2. ContextImpl created (appContext) — the ONLY authoritative dir family:
         getFilesDir=/data/user/0/<pkg>/files, getCacheDir=.../cache,
         getCodeCacheDir=.../code_cache, getNoBackupFilesDir=.../no_backup,
         getSharedPreferencesPath=.../shared_prefs/<name>.xml,
         getDatabasePath=.../databases/<name>, getDir(name)=.../app_<name>
      3. Instrumentation created (AppComponentFactory.instantiateApplication)
      4. Application class loaded via the LoadedApk classloader
      5. app.attachBaseContext(base=ContextImpl-wrapping ContextWrapper)
      6. installContentProviders(): every <provider> in the manifest is
         instantiated + onCreate() called — BEFORE Application.onCreate.
         androidx.startup.InitializationProvider runs here: WorkManager,
         ProcessLifecycleOwner, Emoji2, etc. initialize in this window.
      7. Application.onCreate()
      8. (later) Activity creation: classloader → AppComponentFactory.instantiateActivity
         → Activity.attach(baseContext, ...) → onCreate → onStart → onResume
  → any <clinit> touched during 4–8 runs at first active use (JVMS 5.5);
    a throwing <clinit> = NoClassDefFoundError at every later use

REQUEST RESOLUTION (who answers "give me bytes")
  Context.getAssets()      → ResourcesManager → AssetManager (AssetManager2 native)
  Context.getResources()   → Resources → ResourcesImpl → AssetManager2
  Context.getContentResolver() → ContentResolver → provider IPC (content://)
  new File(path) / FileInputStream / FileOutputStream → kernel, raw paths
  ClassLoader.getResource  → DexPathList (APK-as-jar entries only)
  Class.getResourceAsStream → same, delegates to classloader
  System.loadLibrary(name) → Runtime.loadLibrary0 → linker(dlopen) in nativeLibraryDir
  Uri parsing → scheme dispatch: file://=kernel, content://=ACPM+binder, 
                android.resource://=Resources.openRawResourceFd, android_asset / 
                android_res = AssetManager / Resources internal, http(s)=network
```

## 1. PER-SUBSYSTEM SEMANTIC LAWS

### 1.1 AssetManager (frameworks/base/core/java/android/content/res/AssetManager.java + AssetManager2.cpp)
1. `open(String fileName)` = `open(fileName, ACCESS_STREAMING)`; resolves `fileName`
   against the merged table of ALL added asset paths (base.apk assets/ + split APKs +
   shared libraries), **in addAssetPath order** (base first, then splits).
2. Missing asset → **throws FileNotFoundException** — never returns null, never
   returns an empty stream. (Apps rely on catching it.)
3. Returned `AssetInputStream` is a real stream over the (possibly compressed) ZIP
   entry; `available()`/`read()`/`skip()`/`markSupported()` behave per InputStream
   contract; no size cap.
4. `openFd(fileName)` → `AssetFileDescriptor` **only for STORED (uncompressed)
   entries**; compressed entry → `FileNotFoundException("not a nested file")`.
   Returns offset+length for mmap/random access.
5. `list(String dir)` → String[] of the directory namespace across all asset paths
   (merged, deduplicated); missing dir → **null** (documented quirk), never throws.
6. `openNonAsset` resolves OUTSIDE assets/ (res/ + root entries) by cookie.
7. Asset identity stays INSIDE the APK: assets are not materialized to disk by the
   framework; a returned stream reads from the APK file itself (or its compressed
   inflate window).

### 1.2 Resources / ResourcesImpl (android/content/res/Resources.java)
1. `getIdentifier(String name, String defType, String defPackage)` → full lookup by
   (name,type,package) in the resource tables; returns 0 ONLY when truly absent.
   Works for drawable/string/raw/font/layout/… — any type.
2. Value getters (`getString/getColor/getDimension...`) on missing ID →
   **throws Resources.NotFoundException**; never silently "".
3. Configuration selection (ResourceTypes + ConfigDescription): best-match over ALL
   candidate buckets, AOSP priority order (mcc/mnc → locale → layoutdir → smallest
   width → available width/height → screen size → aspect → round → wide-color →
   orientation → uiMode **night** → night→density → touchscreen → keyboard → …).
   `isBetterThan` compares candidates pairwise; density never *filters*, it ranks.
   If NO bucket matches the device config, the **default (unqualified) bucket wins**;
   if there is no default, resource lookup fails (NotFoundException).
4. Density scaling: bitmap resources are decoded at native density; Views scale by
   `inDensity/inTargetDensity`; `BitmapFactory.Options.inSampleSize` reduces decode
   memory; `inJustDecodeBounds` reads only the header.
5. `openRawResource(id)` → InputStream (compressed OK); `openRawResourceFd(id)` →
   AssetFileDescriptor (uncompressed only). Missing → NotFoundException.
6. Resource references are resolved transitively: @string→@color→literal chains,
   theme attrs (?attr/name), style parents — unbounded depth, cycle-safe by contract.
7. Framework resources live in package 0x01 (framework-res.apk); app resources in
   0x7f; shared libraries get their own package ids. `android.R.*` resolves via 0x01.

### 1.3 Fonts (graphics/java/android/graphics/Typeface.java)
1. `Typeface.createFromAsset(mgr, path)` → AssetManager.open → parse (TTF/OTF);
   missing asset → RuntimeException (not silent fallback).
2. `Typeface.createFromFile` / `Resources.getFont(R.font.x)` (res/font + XML
   font-family with weight variants) — identity per (family, weight, style).
3. System families: sans-serif{,-light,-condensed,-thin,-medium,-black}, monospace,
   serif + per-locale fallback chain (Noto families); synthetic bold/italic when the
   exact face is absent.
4. Canvas text uses the resolved face; a request for family X must not silently
   render family Y (provenance: requested != resolved is a failure).

### 1.4 BitmapFactory / images
1. `decodeStream(InputStream)` — the canonical path for assets/network/ContentResolver
   bytes; works with ANY InputStream; returns null ONLY when the stream is not an
   image (or OOM), never for "stream type unsupported".
2. `decodeFile/decodeResource` are wrappers over the same decoders (PNG/JPEG/GIF/
   WebP/BMP/HEIF + VectorDrawable XML + NinePatch).
3. Decoded bitmap reaches the screen only after View→Canvas→SurfaceFlinger; bitmap
   object existence ≠ pixels on screen (pixel-ownership law 21-P0-6).

### 1.5 Audio/Video
1. `MediaPlayer.setDataSource(fd/uri/path)` → stagefright pipeline; prepared state
   only after real demux; `SoundPool.load(resid/path)` returns a REAL sampleId and
   decodes eagerly; missing source → onError/exception, never a fake playing state.
2. AudioTrack streams PCM; playback state is observable.

### 1.6 Files (java.io + ContextImpl)
1. `File` is a pure path object; all I/O hits the kernel. `exists()` true ⇔ kernel
   says so. There is NO path rewriting, NO sanitization, NO rename — a requested
   name is used verbatim (case-sensitive on ext4).
2. Relative `File` paths resolve against CWD; Android apps use absolute paths from
   Context. `getAbsolutePath` returns the constructed path; `getCanonicalPath`
   resolves symlinks/`..` via realpath.
3. `FileOutputStream` truncates/creates; `openFileOutput(mode)` =
   `/data/user/0/<pkg>/files/<name>` with MODE_PRIVATE/MODE_APPEND.
4. `/data/data/<pkg>` and `/data/user/0/<pkg>` are THE SAME directory (user-0 alias);
   both spellings must open the same files.
5. External storage: `Environment.getExternalStorageDirectory()` =
   `/storage/emulated/0`; `getExternalFilesDir` = `/storage/emulated/0/Android/data/
   <pkg>/files`; FUSE presents it to apps; kernel path differs but semantics are
   POSIX-consistent.
6. Streams: read/skip/available/mark/reset/close per InputStream contract; EOF = -1;
   a stream that opens must be readable unless the fd died.

### 1.7 Databases (SQLiteOpenHelper / SQLiteDatabase)
1. `getDatabasePath(name)` = `/data/user/0/<pkg>/databases/<name>`; opening creates
   `<name>`, `<name>-journal` (rollback) or `<name>-wal`+`<name>-shm` (WAL mode).
2. WAL enabled ⇒ getter `isWriteAheadLoggingEnabled()==true` and the -wal file
   visibly exists while connections are open.
3. Multiple connections on one db file share the page cache via file locks.

### 1.8 SharedPreferences (app/SharedPreferencesImpl.java)
1. Path: `/data/user/0/<pkg>/shared_prefs/<name>.xml`; created on first commit.
2. `commit()` = synchronous write with **atomic rename** (tmp→final); returns false
   on failure. `apply()` = async, in-memory immediately.
3. Values are XML-escaped; `remove`/`clear` take effect on next write; listeners
   fire (onSharedPreferenceChanged) on change; values survive process restart.
4. First read parses the whole XML; malformed XML → preloaded empty + disk error log
   (never crash by default).

### 1.9 Native libraries
1. `System.loadLibrary("foo")` → `dlopen("libfoo.so")` searched in
   `applicationInfo.nativeLibraryDir` (= extracted lib/<abi>/ from install).
2. `JNI_OnLoad` runs on load; `RegisterNatives` binds natives; failure →
   UnsatisfiedLinkError (loud).

### 1.10 URI / ContentResolver
1. Schemes: `file://` → kernel path; `content://` → ContentProvider via
   openFile/openAssetFileDescriptor/query (ACPM); `android.resource://<pkg>/<resid>`
   → Resources.openRawResourceFd; `file:///android_asset/x` and
   `file:///android_res/x` → AssetManager/Resources (WebView legacy prefixes);
   http(s) → network stack; `data:`/`blob:` inside WebView.
2. `ContentResolver.openInputStream(content://)` → provider.openFile →
   ParcelFileDescriptor (auto-close) → stream; provider missing →
   FileNotFoundException (loud).
3. `Intent.getData()` returns the Uri the Activity was started with — never null
   when started with data.

### 1.11 System services
1. `getSystemService(name)` returns a REAL manager for every documented constant;
   null is returned only for non-standard names. Managers are functional (each
   method has defined behavior) — a bare object with no methods does not exist.

### 1.12 Providers / receivers / services (the component contract)
1. Providers install BEFORE Application.onCreate (law above) — androidx.startup
   depends on it; missing provider install = permanently uninitialized libraries.
2. `registerReceiver`+`sendBroadcast` dispatch synchronously/queued to
   BroadcastReceiver.onReceive; BOOT_COMPLETED etc. delivered by the system.
3. `startService`/`bindService` create the Service component and call
   onStartCommand/onBind.

### 1.13 Split APKs / overlays
1. Resources and code resolve across base.apk + splitSourceDirs + overlays +
   shared libraries in a defined precedence; a resource present only in a split is
   reachable. FEATURE_NOT_INSTALLED is distinguishable from FILE_NOT_FOUND.

### 1.14 Threads / deferred work
1. Real preemptive threads; Handler/Looper queues per looper thread; Choreographer
   vsync; blocking primitives (wait/notify/CountDownLatch/FutureTask) work per
   java.util.concurrent semantics. Deferred work (postDelayed) fires in real time —
   a frame rendered before it is provisional, not final.

## 2. THE 12 UNIVERSAL QUESTIONS (SUPPLEMENT §1) — answered generically

| # | Question | AOSP answer (generic) |
|---|---|---|
| 1 | logical identifier provided by app | resource id/name, asset path, file path, Uri, fd, classpath name |
| 2 | who resolves it | AssetManager2 / ResourcesImpl / kernel / provider / classloader / linker |
| 3 | physical source selected | APK zip entry, /data/user/0 tree, external FUSE, framework-res, provider, network |
| 4 | configuration rules | AOSP best-match config law (§1.2-3), locale/density/night/… |
| 5 | permissions/path rules | per-uid sandbox; kernel enforces; no path rewriting |
| 6 | object returned | stream / fd / typed value / bitmap / cursor / manager |
| 7 | source missing | **typed exception** (FileNotFoundException/NotFoundException/UnsatisfiedLinkError) |
| 8 | exists but unreadable | IOException (EACCES) |
| 9 | decode fails | null bitmap / MediaCodec error / parse exception — observable |
| 10 | first source exists, next missing | downstream typed exception with the NEXT identifier (first-divergence) |
| 11 | source namespace | APK / app data / external / framework / other package / provider / Uri / native lib |
| 12 | copied at install or read in place | APK entries read IN PLACE (not copied); native libs + no code ARE extracted/installed |
| 13 | return type | host-real path, fd, stream, buffer, AssetFileDescriptor, PFD |

## 3. REQUIRED MINIANDROID-EXPOSED PATHS (the mapping contract)

| Android path | semantic owner |
|---|---|
| /data/app/.../base.apk (+splits) | install commit; sourceDir; resources+code read in place |
| /data/data/<pkg> == /data/user/0/<pkg> | Context family root (alias MUST hold) |
| .../files, cache, code_cache, no_backup, databases, shared_prefs, app_* | ContextImpl dir law |
| /data/user_de/0/<pkg> | device-protected storage |
| /storage/emulated/0/Android/{data,media,obb}/<pkg> | external per-app dirs |
| /system/fonts/*, /system/framework/framework-res.apk | system image |
| nativeLibraryDir | extracted lib/<abi> |
| content://, android.resource://, file:///android_asset(_res) | Uri resolvers |
