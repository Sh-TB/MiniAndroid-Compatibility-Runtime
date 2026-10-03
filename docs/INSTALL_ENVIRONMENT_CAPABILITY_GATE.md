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
`INSTALL_ENVIRONMENT_API_MATRIX.jsonl`. 57 rows TESTED/PASS, 3 rows PARTIAL
(fileList contains() gap G-6, AFD createInputStream byte-equality gap G-5,
content:// query dispatch gap G-3 — all recorded with next actions in
`INSTALL_ENVIRONMENT_GAPS.md`). **Capability = 57/60 ≈ 95%**, with the 3
gaps explicitly enumerated and severity-ranked; percentage alone is NOT a
completion claim — the ledger rows carry the per-item evidence.
