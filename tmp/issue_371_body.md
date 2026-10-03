# MASTER CONTINUATION — VERIFY #364–#369 + EXECUTE #370

## Mission
Treat every prior Coder completion as a CLAIM until independently re-verified at the CURRENT remote HEAD.

Current remote tip observed before this request:
`820148c340f229854b124f4440eb96656c3c5654`

Do NOT assume older reported HEADs (`edecae3e`, `abb57444`, `428bc0bc`, `9c3dc4d1`) are current.

Authoritative scope:
- #364 Upstream Reuse + Complete Compatibility Campaign
- #365 Master Forensic Verification
- #366 Differential Execution
- #367 Closed Issue Forensic Batch 1/3
- #368 Closed Issue Forensic Batch 2/3
- #369 Closed Issue Forensic Batch 3/3
- #370 Install-Environment Capability Gate

## NON-NEGOTIABLE RULE
The word DONE in a previous comment is NOT evidence.
Use:
SOURCE → LAW → IMPLEMENTATION → TEST → CURRENT-HEAD RUNTIME EVIDENCE → ARTIFACT → REPEATABILITY.

Do not silently re-baseline failures. Do not weaken gates. Do not convert PARTIAL/BLOCKED/PENDING into VERIFIED merely because a document exists.

---

# PHASE 0 — CURRENT STATE FIRST

1. Read repository laws, .agent/CODER_REQUEST_PROTOCOL.md, worklog/CAMPAIGN_STATE, all seven Issue bodies/comments.
2. Determine the actual remote HEAD.
3. Reconcile all claims against the current HEAD.
4. Record the exact base commit used for every test.
5. If #367–#369 artifacts were produced against an older audit head, distinguish:
   - VERIFIED_CURRENT
   - HISTORICAL_ONLY
   - SUPERSEDED
   - PARTIAL
   - BLOCKED
   - UNVERIFIED_CLAIM
6. Never delete historical evidence.

---

# PHASE 1 — #364 CONTINUATION

Do not repeat already-proven rows unnecessarily. Verify the completion ledger and close only remaining real rows.

Current known open/pending families from its latest ledger include:
- UPP-001 dlopen/JNI/native
- UPP-002 ContentProvider Cursor/FileProvider
- UPP-003 split APK
- UPP-004 configuration/density/fonts
- UPP-005 Compose
- UPP-006 Broadcasts/Services
- UPP-007 SQLite/font provenance / trace extension
- remaining P1/P2/P3 rows
- release NOTICE/attribution if still open

For each remaining row:
- source/oracle
- semantic law
- current implementation
- runtime test
- evidence path
- exact status
- next action

Do not blindly import upstream code.

---

# PHASE 2 — #365 FORENSIC CONTINUATION

Re-check the forensic master against current HEAD.

Must preserve:
- all historical claims
- all missing-evidence classifications
- official Telegram BLOCKED-APK-ABSENT unless a real APK is acquired
- Safir/Black BLOCKED-BY-IDENTITY unless identities are actually established
- frozen 202-title corpus truth
- registry truth

Re-run only what is necessary to establish current truth and expose regressions.

---

# PHASE 3 — #366 DIFFERENTIAL CONTINUATION

Verify ROOT-A/B/C fixes still hold at CURRENT HEAD.

Then continue the honest open frontiers:
- ROOT-D Compose: do not collapse distinct failure modes
- ROOT-E native/Godot: continue S-2 dlopen/JNI/native surface
- ActivityResultLauncherCompat
- WorkManagerInitializer / provider metadata
- memory URI-null/WebView path
- chess RecyclerView binding if still open
- F-NEW-229/221/217/204..207/192 and any newly current first divergences

For every app:
installed identity → lifecycle → ViewTree/provenance → first missing capability → actual state change → screenshot metrics/SHA → 3-run where applicable.

---

# PHASE 4 — #367/#368/#369 CLOSED-ISSUE AUDIT

The previous wave claims all 108 issues were individually classified and canonical artifacts committed.

Do NOT simply redo 108 issues from scratch.

Instead:
1. Verify the frozen batch membership.
2. Verify every per-issue ledger has all required fields.
3. Verify the claimed artifact files exist at CURRENT HEAD.
4. Verify the audit-head vs current-HEAD distinction.
5. Re-run enough current-head gates to detect drift.
6. Any issue whose proof depends only on old HEAD must remain HISTORICAL-ONLY.
7. Any issue invalidated by later runtime changes must be marked SUPERSEDED/REGRESSED rather than silently retained.
8. Preserve the discovered generic ASSETS-WITHOUT-ARSC fix and verify it still passes.
9. Preserve pixel-truth rule: BYTE-STABLE != PIXEL-TRUTH.
10. User goldens remain exactly:
   - 2048
   - Snake Deluxe
   - MiniCraft
   - HelloWorld
   All must remain REAL_APP_CONTENT if claimed as visual goldens.
11. chess/dooz must not be promoted back to pixel goldens merely because deterministic.

---

# PHASE 5 — #370 FULL EXECUTION
## INSTALL-ENVIRONMENT CAPABILITY GATE

Execute the complete #370 contract, not a superficial APK-copy test.

Goal:
APK → INSTALL → PACKAGE IDENTITY → SANDBOX → FILES/RESOURCES/ASSETS/DEX/LIBS/DB/PREFS/MANIFEST/PROVIDERS → INSPECTION → PROVENANCE → EVIDENCE.

The gate must remain useful even when an app cannot render.

### A. Installation/package identity
Prove:
- source APK SHA
- installed base.apk SHA
- package metadata
- install/reinstall/uninstall
- per-package data roots
- code_cache/no_backup/cache/files/databases/shared_prefs/native libs/external roots
- source APK hidden after install
- run by installed package identity

### B. Context/package sandbox
Runtime-prove the semantics of:
getPackageName, getApplicationInfo, getPackageManager,
getFilesDir, getCacheDir, getCodeCacheDir, getNoBackupFilesDir,
getDataDir, getDatabasePath, getDir, getFileStreamPath,
getExternalFilesDir, getExternalCacheDir, getExternalMediaDirs,
getObbDir, openFileInput, openFileOutput, fileList, deleteFile,
databaseList and package isolation.

### C. File API
Prove positive and negative behavior for:
exists/isFile/isDirectory/canRead/canWrite/length/lastModified/list/listFiles/
mkdir/mkdirs/createNewFile/delete/renameTo/getAbsolutePath/getCanonicalPath/
getParent/getName/isAbsolute.

### D. Streams
Real byte-level proof for:
FileInputStream/InputStream
FileOutputStream/OutputStream
read/write/EOF/append/restart.

### E. FD/PFD/AFD
Real descriptors, not fake path objects:
FileDescriptor, ParcelFileDescriptor, AssetFileDescriptor,
getFileDescriptor, offsets, lengths, seekability, close,
openFd/openRawResourceFd.
Prove bytes equal the backing APK/data entry where applicable.

### F. APK assets
AssetManager:
list/open/openFd, nested assets, compressed/uncompressed, missing asset behavior.
Record provenance:
INSTALLED_APK / APP_DATA_FILE / EXTERNAL_APP_FILE / RESOURCE /
GENERATED_RUNTIME_FILE / DEVICE_NODE / OTHER.

### G. Resources
Inspect and test:
resources.arsc, IDs, package/type/name, qualifiers, density, locale,
drawable/mipmap/layout/values/string/color/dimen/style/theme/font/raw/XML/
arrays/plurals/aliases.
Test ID/name/getIdentifier/config selection/fallback/density/locale/not-found.

### H. Image/font/media inventory
Inventory real installed entries:
PNG/JPEG/WebP/GIF/XML/vector
TTF/OTF/XML fonts
audio/media.
For each: entry/path/id/backing/size/SHA/decoder/attempt/result.

### I. Persistence
SharedPreferences:
write → physical file → restart → read.
SQLite:
DB/WAL/SHM/journal, databases_dir, write → physical file → restart → read.

### J. URI/ContentProvider
Manifest providers, authority, class, exported, grants, attachInfo/context,
content URI, query/insert/update/delete/openFile/openAssetFile/Cursor.
No silent null.

### K. Native libraries
Inventory lib/*.so, ABI, ELF, SONAME, JNI symbols.
Trace System.load/loadLibrary/dlopen and actual caller/result.

### L. Manifest/components
Activities/services/receivers/providers/application,
permissions, intent filters, exported/enabled/process/launchMode/theme/
orientation/configChanges/metadata/authorities/task/affinity.

### M. DEX/multidex
Inspect classes.dex etc:
class/method/field/access flags/super/interfaces/annotations/native/framework refs,
with caller correlation where runtime access occurs.

### N. Provenance graph
Machine-readable chain:
source APK → install → base.apk → manifest/dex/resources/assets/libs →
data/prefs/db/external → runtime operation → physical backing → result/error.

### O. Agent inspection API/CLI
Provide machine-readable inspection for:
packages, manifest, APK entries, resources, assets, DEX, libs,
data/external, DB/prefs, provenance, runtime operations, first divergence.

### P. Universal trace
At minimum:
install request → identity → package install → metadata → data root →
manifest → DEX → resource table → asset/file/stream/FD/decode/db/prefs/
provider/native → physical backing → result/error → first divergence.

### Q. Synthetic probe APK
Real normal Android APIs, machine-readable:
identity, dirs, file I/O, byte arrays, FD/PFD/AFD, assets/resources/image decode,
prefs/SQLite/external/provider/native inventory, restart/isolation.

### R. Multi-app proof
At least:
- simple app
- storage-heavy app
- game
- resource/image-heavy app
- one app that currently fails to render

### S. Negative tests
Nonexistent package/file/asset/resource, invalid/closed FD,
invalid URI, cross-package private path, traversal, host absolute path,
malformed APK, missing lib/wrong ABI/missing provider/invalid DB/missing prefs.

### T. Restart/uninstall/reinstall
Record a machine-readable matrix.

### HARD FAILURE CONDITIONS
The gate is NOT complete if it only has:
- APK copy
- path strings
- fake directories
- asset listing without open/read proof
- resource names without actual resolution
- writes with wrong bytes/length
- fake FD/PFD/AFD
- prefs/SQLite path-only proof
- provider returning silent null
- incomplete native inventory
- source APK accidentally reopened
- cross-package private access
- no first-divergence trace
- prose-only evidence
- no machine-readable artifact.

---

# PHASE 6 — CURRENT-HEAD REGRESSION

After #370 changes:
- rebuild from clean state
- run the complete relevant battery
- 4/4 user pixel goldens must remain REAL_APP_CONTENT
- determinism anchors remain determinism-only
- probe/install/uninstall gates must remain green
- run at least 3 independent executions for critical claims
- record screenshot dimensions, non-background/app-pixel evidence, SHA and trace IDs
- if anything regresses, stop classification and root-cause it generically.

---

# PHASE 7 — REQUIRED #370 ARTIFACTS

Create/maintain exactly the requested canonical artifacts:
docs/INSTALL_ENVIRONMENT_CAPABILITY_GATE.md
docs/INSTALL_ENVIRONMENT_CAPABILITY_GATE.jsonl
docs/INSTALL_ENVIRONMENT_API_MATRIX.jsonl
docs/INSTALL_ENVIRONMENT_PROVENANCE_SCHEMA.jsonl
docs/INSTALL_ENVIRONMENT_NEGATIVE_TESTS.jsonl
docs/INSTALL_ENVIRONMENT_MULTI_APP_PROOF.jsonl
docs/INSTALL_ENVIRONMENT_REINSTALL_MATRIX.jsonl
docs/INSTALL_ENVIRONMENT_GAPS.md
docs/INSTALL_ENVIRONMENT_AGENT_GUIDE.md

Do not create a pile of redundant raw logs.

---

# PHASE 8 — COMPLETION LEDGER

Return to the relevant Issue(s) and post line-by-line:
STATUS | RESULT | EVIDENCE | CURRENT HEAD | TEST COUNT

Use only:
IMPLEMENTED / TESTED / OBSERVED / VERIFIED / PARTIAL / BLOCKED /
PENDING / SUPERSEDED / REGRESSED / UNVERIFIED_CLAIM / HISTORICAL_ONLY.

A completion claim without evidence does not close a row.

## Final question
At CURRENT HEAD, if an agent receives an APK, installs it, hides the source APK, and the app fails to render, can the agent still inspect essentially every important installed-package fact/file/resource/asset/DB/pref/native/component/code path and determine what exists, what was attempted, and the first missing capability without guessing?

If NO: enumerate every remaining gap with:
API/law → current implementation → evidence → affected app families → severity → next action.

Do not claim #364–#370 complete merely because the Issues have completion comments.
