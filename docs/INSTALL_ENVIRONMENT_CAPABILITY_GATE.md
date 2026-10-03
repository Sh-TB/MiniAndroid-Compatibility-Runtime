# INSTALL-ENVIRONMENT CAPABILITY GATE (GATE A) — issue #370

> Status: **EXECUTED** at CURRENT HEAD `24326b44d2a5a1fd4ace6993578a0e9d477e56a8`
> (runtime binary sha16 `768085b1207ad55d`, built from the GATE-A wave tree).
> Companion machine-readable artifacts: `INSTALL_ENVIRONMENT_CAPABILITY_GATE.jsonl`,
> `INSTALL_ENVIRONMENT_API_MATRIX.jsonl`, `INSTALL_ENVIRONMENT_PROVENANCE_SCHEMA.jsonl`,
> `INSTALL_ENVIRONMENT_NEGATIVE_TESTS.jsonl`, `INSTALL_ENVIRONMENT_MULTI_APP_PROOF.jsonl`,
> `INSTALL_ENVIRONMENT_REINSTALL_MATRIX.jsonl`; gap inventory in
> `INSTALL_ENVIRONMENT_GAPS.md`; usage in `INSTALL_ENVIRONMENT_AGENT_GUIDE.md`.
>
> GATE A = installed-package **inspection** capability. GATE B (execution
> compatibility) and GATE C (visual/interactive compatibility) are separate
> gates and are NOT claimed here.

---

## 1. Mission compliance

APK → INSTALL → PACKAGE IDENTITY → SANDBOX → FILES / RESOURCES / ASSETS /
DEX / LIBS / DB / PREFS / MANIFEST / PROVIDERS → INSPECTION → PROVENANCE →
EVIDENCE. Every hop is exercised by a real APK with machine-readable
evidence, and the layer is usable **independently of whether the app
renders** (proven on a render-FAIL app, §6).

Laws read and obeyed: CONSTITUTION_V2 (§1 root-cause > symptom; §2
source-first; no fake success; evidence standard), `.agent/CODER_REQUEST_PROTOCOL.md`,
AOSP semantic laws cited per fix (ContextImpl / AssetManager2 / Runtime.loadLibrary0 /
ResourcesImpl / OpenJDK File). Generic only — zero package conditionals in
any fix.

## 2. What was already real vs what this wave added

Pre-existing (LOADING-CAMPAIGN 81134ac5 + F-NEW-231/234, re-verified — not
assumed): pkgstore install/record law, File read/write family, asset
open/list/openFd with ASSETS-WITHOUT-ARSC law, prefs atomic+escaped, real
SQLite WAL, one path law (`resolve_android_path`), FileIoTrace provenance.

**Added by this wave (all generic):**

| # | Fix | AOSP law | Evidence |
|---|-----|----------|----------|
| F1 | `pkginspect` agent CLI (13 sections, JSONL export) | issue §15 | `miniandroid pkginspect --help` |
| F2 | Context dir family returns **Android-logical** paths (`logical_android_path` reverse law) — host store paths are no longer app-visible | ContextImpl: apps never see host paths | probe DIR-01..12 all logical + physically backed |
| F3 | `getDataDir` / `getCodeCacheDir` / `getNoBackupFilesDir` / `getFileStreamPath` / `databaseList` / `getObbDir` (singular) laws (were REC-MISS → null) | ContextImpl | probe DIR-03/04/05/08/12, DB-02 |
| F4 | `PackageManager.getPackageInfo(GET_PROVIDERS)` providers array + **provider attachInfo(Context, ProviderInfo)** stage before onCreate | PackageParser / ActivityThread.installProvider | probe ID-04, PROV-01 (authority round-trip) |
| F5 | `getIdentifier` resolves **any type** through the ARSC (was: id-type only → 0) | ResourcesImpl.getIdentifier | probe RES-01 `0x7f030000` |
| F6 | `getString(unknown id)` throws **NotFoundException** (was silent `""`) | ResourcesImpl + R-3 fake-default removal | probe RES-04 |
| F7 | `openRawResource` serves real entry bytes via the `apk-entry:` byte law (was: unreadable stream → 0 bytes / silent null; missing → NotFoundException) | ResourcesImpl.openRawResource | probe RES-03 26/26 bytes |
| F8 | `System.loadLibrary/load` honest contract: request → ABI → installed entry → **UnsatisfiedLinkError** (was: silent void REC-MISS fake success) | Runtime.loadLibrary0 | probe NAT-01 + `[GATEA-NATIVE]` trace |
| F9 | `MODE_APPEND` bit law **0x8000** (was 0x0800 — appends truncated prior bytes) | Context.MODE_APPEND | probe IO-02 append preserves bytes |
| F10 | AFD `declaredLength` field + `getDeclaredLength` law | AssetFileDescriptor | probe FD-01 declaredLen=75 |
| F11 | PFD.open arg-convention-proof File resolution (real host fd / dup / close) | ParcelFileDescriptor | probe FD-04/05 |
| F12 | Manifest `<service>` / `<receiver>` components parsed (additive) | PackageParser | pkginspect manifest sections |
| F13 | ARSC `inventory()` whole-table accessor; ZIP central-directory reader; ELF reader (class/machine/SONAME/JNI dynsym) | — | pkginspect entries/libs (chess: 4 .so, aarch64, soname, 61 JNI exports) |

Probe-discovered divergences fixed **before any completion claim**: 11
(host-path exposure, provider field, obbdir, getIdentifier, NotFoundException,
loadLibrary, MODE_APPEND, declaredLength, raw-stream, PFD args, manifest
components) — the FAN-OUT discipline: probe → fail → law → generic fix →
re-run → regression.

## 3. The critical test (§1): install → hide source → run by identity

Executed for every app in the multi-app proof (`scripts/s41_gatea_multiapp.py`):
install → record source SHA-256 → verify `SHA(source) == SHA(installed
base.apk)` → **move the source APK away** → all further inspection and
execution by `--package` identity alone. 5/5 apps: source hidden, identity
holds, `pkginspect` completes. No source-APK fallback exists in any code
path (the store is the only code source after install; F-NEW-231).

## 4. Synthetic probe (§17)

`fixtures/gate_a_probe/` — real APK (aapt2 binary manifest + resources.arsc),
normal Android APIs only, per-op try/catch, machine-readable result lines
written through `openFileOutput` to `files/gate_a_results.jsonl` (physical
write proof) + rendered text view. Final verdicts: **69 PASS / 0 FAIL /
2 INFO** (the INFO rows are documented runtime determinism/AOSP-compressed
laws, not failures). Ops: identity ×4, provider ×1, dirs ×12, file ×11,
streams ×10, FD ×7, assets ×5, resources ×4, image ×3, prefs ×5, SQLite ×3,
native ×2, isolation ×4.

## 5. Multi-app proof (§18)

`docs/INSTALL_ENVIRONMENT_MULTI_APP_PROOF.jsonl` — 5 families, all green:
simple (gate_a_probe), storage-heavy (chess: db + prefs + 4 native libs),
game (bouncy: 4 libs, 25 assets), resource-heavy (memory: 5175 resource
entries), **render-FAIL (blockblast: Compose white app — inspection
completes identically: 633 classes, 109 resources, 3 libs inventoried)**.
GATE A independence from GATE B/C is thereby proven, not asserted.

## 6. Universal trace (§16)

`docs/INSTALL_ENVIRONMENT_PROVENANCE_SCHEMA.jsonl` — the canonical
INSTALL_REQUEST → … → FIRST_DIVERGENCE chain with 20 executed stages for the
probe app, plus the per-op runtime trace (`MINIANDROID_FILE_IO=<out>` —
op/path/result/subsystem/caller/package). Trace distinguishes
SUCCESS / FAILURE / MISSING(FNFE) / DENIED(namespace) / UNSUPPORTED(honest
ULE) — every negative case is a typed result, never a silent null.

## 7. Final regression (§23)

At HEAD `24326b44` after all fixes:
- user pixel goldens **4/4 REAL_APP_CONTENT** (2048: 535 colors; Snake
  Deluxe: 1203; MiniCraft: 2416; HelloWorld canonical) — `scripts/user_golden_gate.py`
- determinism anchors **5/5 ×3 byte-identical** (opencalc/chess/dooz/
  microtimer/unote) — `scripts/working_vs_failing_probe.sh` (chess/dooz
  remain determinism-only per the pixel-truth law)
- loading probe **23/23 ALL PASS**; uninstall **16/16 ALL PASS**
- gate-A harnesses: probe 69/0/2, negatives 17/17, reinstall matrix 8/8,
  multi-app 5/5.

## 8. Capability percentage (explicit denominator)

Denominator = the 60 verifiable capability rows of
`INSTALL_ENVIRONMENT_API_MATRIX.jsonl`. 59 rows TESTED/PASS, 1 row PARTIAL
(content:// query dispatch gap G-3 — recorded with its next action in
`INSTALL_ENVIRONMENT_GAPS.md`). **Capability = 59/60 ≈ 98%**, with the
remaining gap explicitly enumerated and severity-ranked; percentage alone
is NOT a completion claim — the ledger rows carry the per-item evidence.

## 9. Independent verification wave (#371, 2026-10-03) — G-5/G-6/G-7 closed

The #371 MASTER CONTINUATION required re-verification at the CURRENT HEAD
instead of trusting the completion comments. Clean rebuild from the synced
tree first reproduced the recorded Gate A binary byte-identically
(`768085b1207ad55d`), every gate was re-run green, and then the three
open GATE-A gaps were root-caused and CLOSED with generic engine laws:

| Gap | Disproven recorded suspicion | Real root cause (generic) | Fix | Evidence |
|-----|------------------------------|---------------------------|-----|----------|
| G-5 AFD stream equality | "0:0 spec serving compressed-vs-stored variant" | MISSING `java.util.Arrays.equals([B[B)Z` law — the static compare fell through the bridge and answered false for EQUAL arrays; hex diagnostic proved the two byte sources identical (PNG head `89504e47…` both, len 75 both) | Arrays.equals law (length + element-wise, null-aware, boxed forms) in the API bridge; FD-02 now ASSERTS equality | probe FD-02 `equal-to-direct=true` |
| G-6 list contains() | "trailing NUL from array materialization" | CollectionShadow.contains compared object ids over its own never-populated vector; asList-backed lists live in the canonical heap `array[i]` fields. Fixed: heap-first element-equality (string content + identity) in CollectionShadow + post-shadow bridge contains/containsAll law; IO-08 now ASSERTS contains | probe IO-08 `fileList has stream_io.bin=true` |
| G-7 File.getParent null | "relative-parent path capture" (ctor was already correct) | F-057 view-tree duality route routed EVERY getParent to ViewShadow; the node-less branch answered authoritative handled_null, starving the R-NEW-347 File law. Fixed with one structural scope law: node-less branch answers null only for view-family receivers (handles_class), otherwise not_handled | probe FILE-10 `parent=/data/data/com.probe.gatea/files` (assert) |

Post-fix regression (binary sha16 `75cb214df1374992`): battery **124/124 ALL
PASS**, user goldens **4/4 REAL_APP_CONTENT**, determinism anchors **5/5 ×3
byte-identical (zero drift)**, loading probe **23/23**, uninstall **16/16**,
Gate A probe **69 PASS / 0 FAIL / 2 INFO** (now with strengthened G-5/G-6/G-7
assertions), negatives **17/17**, reinstall **8/8**, multi-app **5/5**.
ROOT-B (memory) re-verified REAL_APP_CONTENT, ROOT-C (suntimes) provider
ISE stays gone, ROOT-A (spacevertex) stays past the recorded forName
divergence — no root fix regressed.

Battery tooling honesty: the cold-state battery run exposed a latent
tool-bug (10 unprotected run lines under `set -e` after the F-016 stages —
a cold run aborted instead of failing a stage). All 10 wrapped
`set +e`/`set -e`; no stage weakened, no golden touched. The EXT-01/02
external fixtures were re-fetched SHA-exact (`009b4671…` / `121d479c…`)
after the container reset.

## 10. FINAL COMPLETION wave (#371, 2026-10-03) — G-1/G-3/G-4/G-8 closed; fan-out proof

CURRENT HEAD `58f2dde2`; runtime binary sha16 `b2b8c18bb92dab6a`.

### Gap closures (generic only; probe-asserted)

| Gap | First missing semantic | Generic fix | Probe evidence |
|-----|------------------------|-------------|----------------|
| G-1/G-3 ContentResolver dispatch | no authority→provider map; no content:// routing; no Cursor transport | authority map populated at installContentProviders; query/insert/update/delete/getType/call/openFileDescriptor dispatch into the provider's DEX overrides with AOSP failure contracts (unknown-authority IAE; documented query null WITH trace row; FNFE for openFile without override); MatrixCursor row pool + Cursor interface; ContentValues typed map (box-unwrap); UriMatcher (#, *); ContentUris; Uri getAuthority/getQueryParameter/toString | probe PROV-02..09 (insert→Uri→state change; query rows; update count; delete→empty; PFD bytes == direct; getType; failure contracts) |
| G-4 ABI-scoped lib extraction | nativeLibraryDir phantom; no extraction | install extracts primary ABI (arm64-v8a > armeabi-v7a > x86_64 > x86) into codePath lib dir + native_libs.json; nativeLibraryDir seeds the real logical dir (phantom only as recorded fallback) | probe NAT-02/03; loadLibrary extracted-shape detail (size+sha16); multiapp lib inventories |
| G-8 device-protected storage | user_de paths DENIED (prefix-strip bug); no DE context | user_de prefix-strip fixed; DE fence gets its OWN backing (`data/user_de/0/<pkg>`); reverse law mapping added; createDeviceProtectedStorageContext + DE-aware dir family | probe DE-01 (spelling, 8-byte write, isolation from CE asserted) |
| G-2 native execution | no native execution layer (BY DESIGN) | pre-native path completed: 3-shape precise ULE (absent / not-extracted / extracted-with-identity incl. sha16); env-gated REAL host dlopen records the REAL dlerror — never a fake success | probe NAT-01/04/05 |

Fan-out-discovered generic engine laws (fixed in the same wave, no package
conditionals): `List.remove(int)` removed-element law (was a silent false —
probe PROV-05 exposed it), `FileInputStream(FileDescriptor)` reads the PFD's
backing file via the fd's host_path (probe PROV-06),
`ProviderInfo.grantUriPermissions` manifest law (androidx
FileProvider.attachInfo threw SecurityException("Provider must grant uri
permissions") — notes_secuso SplashActivity chain), Uri.toString law.

Probe extension: `fixtures/gate_a_probe` **69 → 95 PASS / 0 FAIL / 2 INFO**
(new op families: PROV-02..09, SVC-01..04, BCAST-01..04, DE-01,
CFG-01..05, NAT-03..05). CFG ops prove the AOSP ResTable_config best-match
law at the FROZEN device profile (-zh-rCN/-land/-night unreachable, density
best-match xhdpi@420dpi, font resource bytes) — UPP-004's frozen-profile
design verified by probe, device profile untouched.

### Services/broadcasts (UPP-006 core legs, probe-justified)

startService/startForegroundService/stopService/bindService/stopSelf
ActiveServices lifecycle (started-vs-bound distinction: unbind keeps a
started service alive), registerReceiver/unregisterReceiver/sendBroadcast
dispatch to dynamic + manifest receivers with the bound context.
Evidence: probe SVC-01..04, BCAST-01..04; SVC-*/BCAST-* trace rows.

### ST-10 provenance completion (UPP-007)

SQLITE-OPEN / SQLITE-EXEC / SQLITE-WAL and FONT-FACE rows now flow into the
same MINIANDROID_FILE_IO JSONL evidence model; the probe asserts both
families exist with real backing. First-divergence usefulness preserved
(pkginspect `--what diagnostics` reports the first MISSING/ERROR API call
or first FAILED file-IO row deterministically).

### Phase C — agent inspection surface complete

`pkginspect` now serves 15 sections: identity, manifest, entries, dex,
resources, assets, libs, media, data, external, dbs, prefs, provenance,
**runtime** (file-IO op counts + first failures + API status census bound
via `--file-io` / `--api-trace`), **diagnostics** (firstDivergence kind +
where, firstMissingSemantic, law chain, deterministic JSONL). Multi-package
inspections run against installed apps AND games (multiapp harness 5/5:
probe app, chess, bouncy, memory, blockblast).

### Phase D — REAL NEW SOFTWARE FAN-OUT (mandatory proof)

Protocol per target: install (real install path) → source APK hidden/moved
away → launch strictly by installed package identity (`run --package`) →
MINIANDROID_FILE_IO provenance → 40-frame time-driven capture → F-NEW-233
frame analysis → screenshot metrics + SHA → 3 cold runs.

| Target | Kind | Identity | Verdict (x3) | Pixels | Draw ops | Screenshot sha16 |
|--------|------|----------|--------------|--------|----------|------------------|
| flappycow (com.quchen.flappycow) | game | source==installed SHA ✓, source hidden ✓ | VERIFIED_REAL_APP_CONTENT ×3 (byte-identical) | REAL_APP_UI | 6 | `13cf47464d9787f4` |
| notes_secuso (org.secuso.privacyfriendlynotes) | app (provider/FileProvider, prefs, DB) | ✓ / ✓ | VERIFIED_REAL_APP_CONTENT ×3 (byte-identical) | REAL_APP_UI | 3 | `eb5ebd559cad1028` |

Neither target is among the four canonical pixel goldens (2048 / Snake
Deluxe / MiniCraft / HelloWorld) nor the chess/dooz determinism anchors.

### Phase E — causality (A/B against base binary 51f7e5f9, sha16 `c7f430427ebdcb75`)

- flappycow: VERIFIED_REAL_APP_CONTENT at BOTH binaries (identical
  screenshot sha) → the wave's contribution is the banked ×3 evidence +
  crash-log equivalence (18 exceptions both — the app-internal Google Play
  games-services chain, caught by the app; unchanged, never silenced).
- notes_secuso: REAL_APP_CONTENT at both at 40 frames, BUT the base run
  carries the FileProvider.attachInfo SecurityException escaping the app
  boundary (crash.log Total Errors: 1) while the current HEAD run is
  exception-free (Total Errors: 0). The grantUriPermissions law is thereby
  PROVEN to fix a real crash on real software (the visual verdict was
  already reachable via the deferred-UI frame capture; the crash was not).
- Explicit distinction recorded: no target flipped WHITE→CONTENT due to
  this wave; the wave's real-software yield is the crash elimination + the
  banked 3-run REAL_APP_CONTENT evidence + the provider call-chain proof.
- Explicit frontiers (unchanged, deterministic diagnostics): tripeaks /
  klondike (deferred-UI APP_DRAW_OPS frontier), tictactoedeluxe (libGDX GL
  backend — GdxRuntimeException at AndroidGraphics), suntimes (time4j
  PlainDate.<clinit> NPE — first divergence recorded with the full unwind
  chain), stopwatch (manifest declares NO launcher activity — the runtime
  correctly does not fabricate one).

### Phase F — regression at this HEAD

goldens 4/4 REAL_APP_CONTENT (2048/snakedeluxe/minicraft pixel-truth +
helloworld canonical); determinism 5/5 ×3 byte-identical (zero drift);
loading probe 23/23; Gate A probe 95/0/2; negatives 17/17; reinstall 8/8;
multiapp 5/5; uninstall 16/16; ROOT-A/B/C holds (spacevertex past forName,
memory REAL_APP_CONTENT, suntimes provider-ISE-free); random corpus sample
(seed 20261003) fishrings REAL_APP_CONTENT 44 draw ops (sha16
a341e3ad9092f640); full battery re-run logged to run/battery_371_v3.log.
