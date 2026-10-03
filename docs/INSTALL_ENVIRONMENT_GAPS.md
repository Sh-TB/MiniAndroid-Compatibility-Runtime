# INSTALL-ENVIRONMENT GAPS — honest remaining-gap inventory (issue #370)

> CURRENT HEAD `24326b44d2a5a1fd4ace6993578a0e9d477e56a8`, binary sha16
> `768085b1207ad55d`. Each gap: API/law → current implementation → expected
> AOSP behavior → evidence → affected families → severity → next action.
> GATE A scope only (installed-package inspection); app-render frontiers
> (Compose ROOT-D, native S-2 execution, WebView callbacks) belong to
> GATE B/C and are not listed as GATE-A gaps except where inspection is
> affected.

### G-1 getContext()/attachInfo beyond the install window — LOW
- API/law: ContentProvider.attachInfo binds mContext/mInfo once (AOSP).
- Current: attachInfo is invoked with a real ProviderInfo + app context at
  install; per-provider query/insert/update/delete/openFile dispatch has no
  ContentResolver routing.
- Expected AOSP: full content:// client model with authorities resolution.
- Evidence: probe PROV-01 PASS (identity); no content:// dispatch (honest,
  untried).
- Affected: androidx.startup family (works), app-owned providers that
  self-query.
- Severity: LOW for GATE A (identity + existence provable); MEDIUM for apps.
- Next action: ContentResolver authority→provider map + Cursor transport
  (issue §10 full row).

### G-2 native EXECUTION (dlopen/JNI) — BY-DESIGN FRONTIER (S-2)
- API/law: Runtime.loadLibrary0 → dlopen → JNI_OnLoad/RegisterNatives.
- Current: inventory is real (ELF/ABI/SONAME/JNI dynsym via pkginspect);
  loadLibrary answers a typed UnsatisfiedLinkError with request→ABI→entry
  trace; nothing fakes a load.
- Expected AOSP: actual native code execution.
- Evidence: probe NAT-01 (honest ULE); chess inventory (61 JNI exports).
- Affected: Godot/libgdx/native-heavy apps (GATE B/C frontiers already
  recorded).
- Severity: NONE for GATE A (inspection complete); P0 for GATE B (existing
  S-2 campaign).
- Next action: S-2 dlopen/JNI frontier (upstream plan UPP-001).

### G-3 content:// query/Cursor dispatch — MEDIUM
- API/law: ContentResolver.query/insert/update/delete/openFileDescriptor.
- Current: not implemented; failure is loud REC-MISS (never silent null).
- Evidence: N-12 row records the boundary explicitly.
- Affected: apps reading contacts/downloads/FileProvider content.
- Severity: MEDIUM.
- Next action: authority map + provider-method virtual dispatch.

### G-4 wrong-ABI library install trace — LOW
- API/law: PMS installs one ABI's lib/ tree into nativeLibraryDir.
- Current: nativeLibraryDir is a phantom identity (`/data/app/~~miniandroid/
  base/lib/arm64`) — recorded honestly; per-ABI extraction does not exist
  (no execution layer to feed).
- Evidence: probe NAT-02 (value recorded); pkginspect lib inventories all
  ABIs statically.
- Severity: LOW (inspection unaffected).
- Next action: fold into S-2 (extract ABI-scoped libs at install).

### G-5 AFD.createInputStream byte-equality vs direct open — MEDIUM (open)
- API/law: AFD stream bytes == entry bytes (probe §5 "descriptor bytes ==
  direct bytes").
- Current: FD-02 read exactly 75 bytes through the AFD stream but the byte
  comparison against `AssetManager.open` reported mismatch; both lengths
  correct, content difference not yet root-caused (apkfd key path serves
  entry bytes; suspicion: 0:0 spec serving compressed-vs-stored variant).
- Evidence: probe FD-02 FAIL→(recorded as PARTIAL in API matrix).
- Affected: media-from-fd, mmap-from-assets consumers.
- Severity: MEDIUM.
- Next action: single-entry byte-source dump (direct vs apkfd) → one-line
  key fix; probe op asserts equality.

### G-6 engine String arrays vs contains() — LOW (cosmetic-facing)
- API/law: String equality over array elements (fileList / AssetManager.list).
- Current: arrays render/print correctly (toString shows exact names) but
  app-side `contains()` equality mis-fires — element String objects carry
  an invisible suffix (suspected trailing NUL from array materialization).
- Evidence: probe ASSET-01 (nameLens recorded), IO-08.
- Affected: apps membership-testing engine-returned string arrays.
- Severity: LOW-MEDIUM.
- Next action: dump element byte lengths in the aget-object String
  materialization law; strip at the single materialization site.

### G-7 File(File,String) parent capture for RELATIVE parent objects — LOW
- API/law: File(File parent, String child) joins parent path.
- Current: parent capture works for absolute parent Files; a relative-path
  parent object yields child-only path (probe FILE-10 parent=null while
  name/abs laws answered correctly through the anchor law).
- Evidence: probe FILE-10.
- Severity: LOW.
- Next action: one branch in the File <init> capture (join before anchor).

### G-8 device-protected storage spellings — DOCUMENTED DEVIATION
- API/law: getDeviceProtected*Context dirs (/data/user_de/0/<pkg>).
- Current: REC-MISS loudly (no credential-encryption boundary exists to
  model); the resolve law maps user_de spellings to the same backing when
  addressed directly.
- Severity: LOW (no consumer in the corpus).
- Next action: none until a real consumer appears (honest incompleteness).

### Verification of the gaps
Reproduce any row: `bash scripts/loading_probe_runner.sh` (23/23 gate),
`python3 scripts/s41_gatea_negative.py`, `python3
scripts/s41_gatea_multiapp.py`, probe APK re-run with
`MINIANDROID_FILE_IO=` trace. Gaps G-5/G-6/G-7 have probe ops already
pointing at the exact law sites.
