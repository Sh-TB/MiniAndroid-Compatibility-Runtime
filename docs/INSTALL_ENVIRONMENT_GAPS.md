# INSTALL-ENVIRONMENT GAPS — honest remaining-gap inventory (issue #370)

> CURRENT HEAD (this wave): see docs header stamp in the JSONL artifacts;
> fixed binary sha16 `75cb214df1374992` (clean-rebuild base 768085b1207ad55d + G-5/G-6/G-7 wave).
> Each gap: API/law → current implementation → expected AOSP behavior →
> evidence → affected families → severity → next action. GATE A scope only
> (installed-package inspection); app-render frontiers (Compose ROOT-D,
> native S-2 execution, WebView callbacks) belong to GATE B/C and are not
> listed as GATE-A gaps except where inspection is affected.
>
> **#371 verification wave (2026-10-03): G-5/G-6/G-7 CLOSED** with generic
> engine laws + strengthened probe assertions; G-1/G-2/G-3/G-4/G-8 remain
> honest open rows (ContentResolver dispatch, native execution, ABI install
> extraction, device-protected spellings).

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

### G-5 AFD.createInputStream byte-equality vs direct open — CLOSED
- API/law: AFD stream bytes == entry bytes (probe §5 "descriptor bytes ==
  direct bytes"); plus the actually-missing law `java.util.Arrays.equals
  ([B[B)Z` (OpenJDK: same length + element-wise equality).
- Resolution (2026-10-03, #371 verification wave): the recorded
  "compressed-vs-stored serving" suspicion was DISPROVEN — an env-gated
  stream hex diagnostic proved direct and apkfd sources byte-identical
  (PNG head 89504e47… both, len 75 both). The mismatch came from the
  MISSING Arrays.equals law: the static compare fell through the bridge
  and answered false for EQUAL arrays. Fixed generically:
  Arrays.equals law (length + element-wise equality, null-aware, boxed
  value forms) in the API bridge; FD-02 probe op now ASSERTS equality.
- Evidence: probe FD-02 `equal-to-direct=true` (assert); full regression
  green post-fix (battery 124/124, goldens 4/4, determinism 5/5×3 — zero
  drift).
- Severity: closed (was MEDIUM).

### G-6 engine String arrays vs contains() — CLOSED
- API/law: OpenJDK ArrayList.contains ≡ indexOf(o) ≥ 0 with
  element.equals(o) — never reference identity.
- Resolution (2026-10-03, #371 verification wave): the recorded
  "trailing-NUL materialization" suspicion was DISPROVEN — ASSET-01
  nameLens showed exact element lengths. Two real roots fixed:
  (1) CollectionShadow.contains compared object ids over its own
  (never-populated for asList lists) element vector — now consults the
  canonical heap "array[i]" fields first (string CONTENT + object
  identity), then the private vector with string-content equality;
  (2) the API-bridge ArrayList/List.contains+containsAll element-equality
  law added as the post-shadow net. IO-08 probe op now ASSERTS contains.
- Evidence: probe IO-08 `fileList has stream_io.bin=true` (assert);
  regression green post-fix (zero golden drift).
- Severity: closed (was LOW-MEDIUM).

### G-7 File.getParent starvation by the view-tree duality route — CLOSED
- API/law: AOSP View.getParent is null only for detached views; java.io.File
  getParent follows the R-NEW-347 name-component law (parent = path minus
  last separator).
- Resolution (2026-10-03, #371 verification wave): the ctor path-assembly
  law was already correct — the R-NEW-347 File law never ran. The F-057
  duality route in ShadowRegistry::dispatch routes EVERY getParent to
  ViewShadow first, whose node-less branch answered authoritative
  handled_null for ALL receivers — the File law starved. Fixed with one
  structural scope law: the node-less branch answers null only when the
  receiver class is view-family (handles_class); anything else is
  not_handled so the owning class law answers. FILE-10 probe op now
  ASSERTS a non-null parent.
- Evidence: probe FILE-10 `parent=/data/data/com.probe.gatea/files`
  (assert); regression green post-fix (memory ROOT-B still
  REAL_APP_CONTENT; dooz/chess determinism anchors byte-identical).
- Severity: closed (was LOW).

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
`MINIANDROID_FILE_IO=` trace (add `MINIANDROID_STREAM_HEX=1` for the
G-5 byte-source hex proof). Remaining open rows G-1/G-3 (ContentResolver
authority map + Cursor transport), G-2/G-4 (S-2 native frontier), G-8
(device-protected spellings) keep their next actions unchanged.
