# INSTALL-ENVIRONMENT GAPS — honest remaining-gap inventory (issue #370)

> CURRENT HEAD (this wave): commit 58f2dde2 (issue #371 FINAL COMPLETION
> CONTINUATION wave); runtime binary sha16 `b2b8c18bb92dab6a`.
> Each gap: API/law → current implementation → expected AOSP behavior →
> evidence → affected families → severity → next action. GATE A scope only
> (installed-package inspection); app-render frontiers (Compose ROOT-D,
> native S-2 execution, WebView callbacks) belong to GATE B/C and are not
> listed as GATE-A gaps except where inspection is affected.
>
> **#371 FINAL COMPLETION wave (2026-10-03): G-1/G-3/G-4/G-8 CLOSED.**
> G-2 stays an explicit BY-DESIGN frontier with a precision upgrade
> (3-shape failure contract + extraction identity + real dlopen/dlerror
> probe). The #371 verification wave had previously closed G-5/G-6/G-7.

### G-1 ContentResolver dispatch beyond the install window — CLOSED (#371)
- API/law: ContentResolver.acquireProvider resolves a content URI authority
  through the PMS provider map that ActivityThread.installContentProviders
  populates; provider methods run with the attachInfo-bound context
  (R-NEW-460 law).
- Resolution: the provider install stage now populates
  `authority → provider instance` (multiple ';'-joined authorities each map
  to the same instance). bridge_to_api dispatches
  query/insert/update/delete/getType/call/openFileDescriptor/
  openAssetFileDescriptor/acquire*ProviderClient into the provider's DEX
  overrides via try_recursive_invoke. AOSP failure contracts encoded:
  unknown authority → insert/update/delete throw
  IllegalArgumentException("Unknown authority") / query returns the
  documented null WITH a PROVIDER-* FileIoTrace row (no silent null);
  openFileDescriptor without an override → FileNotFoundException
  ("No files supported by the provider at …").
- Evidence: probe PROV-02 (insert→Uri, provider state change),
  PROV-03 (query→MatrixCursor rows), PROV-04 (update count + provider
  value), PROV-05 (delete count + table empty), PROV-06 (openFileDescriptor
  bytes == direct bytes), PROV-07 (getType + ContentUris.parseId),
  PROV-08/09 (failure contracts). Support laws: MatrixCursor row pool +
  Cursor interface (getCount/getColumnIndex/OrThrow/moveTo*/getX/isX/close),
  ContentValues typed map with box-unwrap, UriMatcher (addURI/match with
  '#'/'*'), ContentUris (withAppendedId/parseId), Uri
  getAuthority/getQueryParameter/toString.
- Fan-out law discovered by the probe: `List.remove(int)` answered false
  (element form) — removed-element law added in CollectionShadow.
- Severity: closed (was MEDIUM).

### G-2 native EXECUTION (dlopen/JNI) — BY-DESIGN FRONTIER (S-2), precision upgraded
- API/law: Runtime.loadLibrary0 → dlopen → JNI_OnLoad/RegisterNatives.
- Current: the PRE-NATIVE path is complete — request → ABI
  (arm64-v8a primary, Build.SUPPORTED_ABIS order) → extracted location →
  dlopen boundary. Install extracts ONE ABI's lib/ tree into the codePath
  lib dir (native_libs.json manifest). System.loadLibrary answers
  UnsatisfiedLinkError in THREE precise shapes: (1) absent from the APK
  ("not found"), (2) present but not extracted (pre-G-4 store), (3)
  extracted — with the real file identity (logical path, size, sha16).
  MINIANDROID_NATIVE_DLOPEN_PROBE=1 additionally attempts a REAL host
  dlopen and records the REAL dlerror string; even a dlopen success is
  never reported as a load success (JNI_OnLoad cannot run — no JNIEnv).
  Nothing fakes a load.
- Evidence: probe NAT-01 (absent shape), NAT-04 (extracted shape with
  identity), NAT-05 (not-found detail), NAT-02/03 (extraction-backed
  nativeLibraryDir), multiapp lib inventories.
- Affected: Godot/libgdx/native-heavy apps (GATE B/C frontiers already
  recorded — tictactoedeluxe GdxRuntimeException at AndroidGraphics is the
  GL backend face of the same frontier).
- Severity: NONE for GATE A (inspection + pre-path complete); P0 for GATE
  B (S-2 campaign unchanged).
- Next action: S-2 dlopen/JNI/native execution design (UPP-001) — UNCHANGED.

### G-3 content:// query/Cursor dispatch — CLOSED (#371)
- API/law: ContentResolver.query returns a Cursor over the provider's
  answer; insert/update/delete/openFileDescriptor follow the URI contract.
- Resolution: see G-1 (same wave; the authority map + provider-method
  virtual dispatch + Cursor transport + failure contracts).
- Evidence: PROV-02..09; API matrix ContentProvider/ContentResolver rows;
  multiapp/negative/reinstall gates green at the same HEAD.
- Severity: closed (was MEDIUM).

### G-4 wrong-ABI library install trace — CLOSED (#371)
- API/law: PMS installs ONE ABI's lib/ tree into nativeLibraryDir
  (preferred ABI present in the APK).
- Resolution: install command extracts the primary ABI (arm64-v8a >
  armeabi-v7a > x86_64 > x86) into `<store>/data/app/<pkg>/lib/<abi>/`,
  writes native_libs.json (entry/size manifest) and prints
  nativePrimaryAbi/nativeLibsExtracted. ApplicationInfo.nativeLibraryDir
  seeds the REAL logical dir when the extraction exists (phantom identity
  remains only as the honest fallback for pre-G-4 stores, recorded).
- Evidence: probe NAT-02/03; System.loadLibrary extracted-shape detail
  (size+sha16); multiapp install outputs.
- Severity: closed (was LOW).

### G-5 AFD.createInputStream byte-equality vs direct open — CLOSED (2026-10-03, #371 verification wave)
- API/law: AFD stream bytes == entry bytes; plus the actually-missing law
  `java.util.Arrays.equals([B[B)Z`.
- Resolution: "compressed-vs-stored serving" suspicion DISPROVEN by the
  env-gated stream hex diagnostic (sources byte-identical); root cause was
  the MISSING Arrays.equals law (static compare fell through and answered
  false for EQUAL arrays). Arrays.equals law added; FD-02 probe op asserts
  equal-to-direct=true.
- Severity: closed (was MEDIUM).

### G-6 engine String arrays vs contains() — CLOSED (2026-10-03, #371 verification wave)
- API/law: OpenJDK ArrayList.contains ≡ indexOf(o) ≥ 0 with element.equals.
- Resolution: "trailing-NUL materialization" suspicion DISPROVEN; roots:
  CollectionShadow.contains identity-only compare over its own
  never-populated vector + no bridge contains/containsAll law. Heap-first
  element-equality fixed; IO-08 probe op asserts contains.
- Severity: closed (was LOW-MEDIUM).

### G-7 File.getParent starvation by the view-tree duality route — CLOSED (2026-10-03, #371 verification wave)
- API/law: AOSP View.getParent null only for detached views; java.io.File
  getParent follows the R-NEW-347 name-component law.
- Resolution: F-057 duality route scoped to view-family receivers — the
  node-less branch answers null only for view-family receivers;
  FILE-10 probe op asserts a non-null parent.
- Severity: closed (was LOW).

### G-8 device-protected storage spellings — CLOSED (#371)
- API/law: ContextImpl.createDeviceProtectedStorageContext returns a
  context whose dir family resolves under /data/user_de/0/<pkg> — a
  DISTINCT fence from the credential-protected /data/data tree
  (StorageManager.isCeStorageUnlocked law).
- Resolution: two real defects fixed. (1) The forward path law's
  prefix-strip ternary tested "/data/user/" FIRST, so every /data/user_de/
  path read its pkg as "0" and was DENIED — user_de is now stripped with
  its OWN prefix and maps to its OWN backing
  `<store>/data/user_de/0/<pkg>` (the old same-backing claim was wrong —
  device-protected storage is distinct in AOSP). (2) The reverse
  (logical_android_path) law gained the user_de mapping.
  createDeviceProtectedStorageContext() returns a device-protected context
  (deviceProtected=1 identity flag) whose getFilesDir/getDataDir/
  getCodeCacheDir/getNoBackupFilesDir resolve the DE fence.
- Evidence: probe DE-01 (DE files dir spelling, 8-byte write, isolation
  from the CE files dir asserted); DE-CONTEXT trace rows.
- Severity: closed (was LOW, documented deviation).

### Verification of the gaps
Reproduce any row: `bash scripts/loading_probe_runner.sh` (23/23 gate),
`python3 scripts/s41_gatea_negative.py` (17/17),
`python3 scripts/s41_gatea_multiapp.py` (5/5),
`python3 scripts/s41_gatea_reinstall.py` (8/8),
probe APK re-run with `MINIANDROID_FILE_IO=` trace (add
`MINIANDROID_NATIVE_DLOPEN_PROBE=1` for the G-2 dlopen boundary proof,
`MINIANDROID_STREAM_HEX=1` for the G-5 byte-source hex proof).
Remaining frontier: G-2 native execution (S-2, explicit GATE B/C design
frontier — pre-native path complete, failure contract precise).
