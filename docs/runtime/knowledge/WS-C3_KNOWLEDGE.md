# WS-C3 KNOWLEDGE — Android Framework / Resources / Streams / Components / Corpus

**Unified Coder campaign:** 2026-08-27 · Tested HEAD: `bbe0ce3` → `86bd646`
**Method:** source audit over `src/` (64k LOC), real APK execution, comparison with previous C3 baselines.

---

## UC3-001: Counting the current API bridge (FRAMEWORK FREQUENCY REMEASURE)

The current bridge level (`bridge_to_api` + shadows) was measured on HEAD:

- **95 classes** handled in `dalvik_engine.cpp` (plus 8 shadows in
  `framework/android_shadows.h`: ArchTaskExecutor, Thread, Looper, Handler,
  Intent, Activity, View, Collection)
- Categories: 30 widget/view, 12 androidx (appcompat+fragment), 10 manager
  (system services), base io/lang/util, 7 Telegram-specific classes
  (AndroidUtilities, TLRPC, LayoutHelper — only for the login chain)

### Priority-level gaps (compared to §7 charter)

| Level | Current status on HEAD | Charter status | Evidence |
|-----|------------------------|----------------|----------|
| InputStream family | only basic `InputStream`/`InputStreamReader`/`BufferedReader` (asset stream) | expand full | grep: no `BufferedInputStream`/`ByteArrayInputStream`/`FileInputStream` handlers |
| **Uri** | **ABSENT — no handler for `Landroid/net/Uri` exists** | 24/24 semantics | grep over the whole src: 0 results |
| LayoutInflater | PARTIAL (layout_cache.json path + Factory basic) | Factory2/style/theme/include/merge | OA_API_MAP: PARTIAL |
| Drawable family | only the resource→Bitmap path for ImageView; **no ColorDrawable/StateListDrawable/…** | 7 types | grep: 0 |
| Context methods | most basics IMPLEMENTED (getPackageName/getAssets/getFilesDir/…) | audit | bridged |
| Handler/Looper | Shadow + real MessageQueue (previous CM-018) | audit | 15 shadow references |
| Components (BR/Service/Provider) | **ABSENT** (IntentShadow only records information) | census | F010 still OPEN |
| Kotlin semantics | none (only class-init skip for `Lkotlin/*`) | audit | the F012 catch-all used to cause problems |
| SystemClock | **ABSENT** (F004: after the value-wide fix, the mechanism opened but the service itself is not there) | verify | grep: 0 → **F004 still OPEN** |
| Multi-DEX | WORKING (5 DEX of v12 loaded — new v12 witness) | expand | UC3-002 |
| JNI census | has tooling (`tools/exp042_jni_inventory.py` + docs/exp042/JNI_INVENTORY.md); runtime: JNI all stub | census | previous |
| Google census | NOT DONE in this campaign (needs corpus scan) | census only | §31 — census-only rule |

---

## UC3-002: Forward-version compat — Telegram 12.10.1 on HEAD (NEW PROOF)

- **PROVEN**: 12,544 classes/5 DEX loaded; 0 errors; deterministic (3/3 SHA).
  This is the biggest version jump tested (10.14.5 → 12.10.1, two years of versions).
- Architectural meaning: the generic paths (multi-DEX injection, `$r8$lambda` dispatch,
  AXML inflate, RLottie hook) are not version-dependent; only the **per-version mapping
  data** (resource_values.json) changes → solution: automatic generation of the
  mapping from ARSC (same as UC2-001a).

---

## UC3-003: UC-CM-001 — closing F012 (CATCH-ALL FALSE-SUCCESS)

- Implemented and merged: commit `86bd646` — full details in `SOURCE_CHANGES.md`.
- classification F012: **FIXED** (previously OPEN)
- classification F015 (superclass-bridge retry): **OPEN** (unchanged; next
  suggested path: on `try_recursive_invoke` failure, before the bridge, try the
  superclass chain once)

## UC3-004: Reconciliation of the remaining C3 findings

| ID | Title | Previous status | Current status on HEAD |
|----|-------|-----------------|------------------------|
| F002 | openFileOutput path divergence | PROVEN/KEEP | confirmed — sandbox is healthy, untouched |
| F004 | SystemClock absent/zero | PARTIAL | **OPEN** — still no handler (grep=0) |
| F005 | Application lifecycle | FIXED (b7dc97b) | confirmed — manifest android:name is read (v12 too) |
| F007 | getSystemService null | PARTIAL | PARTIAL — honest null; services absent |
| F010 | Components absent | OPEN | OPEN (unchanged) |
| F011 | PackageManager hardcode | NOT REPRODUCIBLE | confirmed — no hardcode exists |
| F012 | catch-all void | OPEN | **FIXED** (UC-CM-001, 86bd646) |
| F016 | proto resolution ()V fallback | IMPLEMENTED | confirmed + now also consumed by UC-CM-001 |
| F017/N9 | Makefile header deps (-MMD -MP) | OPEN | **ALREADY FIXED** on HEAD (Makefile line 5 has `-MMD -MP`) — closing |

---

## UC3-005: CORPUS — status and additions

- Current manifest: `tests/corpus/apks.json` — Telegram + gmdice + … (external
  entries, on-demand download).
- This campaign: Telegram **12.10.1** was introduced as a new entry (hash/version
  in `WS-C3_CORPUS.md`) — recorded per §18 as HASH-MISMATCH-vs-manifest
  but REAL and PASS.
- Total corpus count vs the "100+" claim: the repo only has a small manifest;
  **the 100+ claim was not verifiable from the clone** → per §18:
  recorded as UNKNOWN, not PASS. (Need: upload the full results registry)
- non-Telegram runs were not done in this campaign (time/network) — honestly recorded.

---

## STOP GATE status (§22) — WS-C3

| Item | Status |
|------|--------|
| framework frequency remeasured | ✅ (95 classes + 8 shadows counted) |
| InputStream expanded | ❌ OPEN (basics only) |
| Uri advanced | ❌ **ABSENT** — highest new priority |
| LayoutInflater assessed | PARTIAL (Cache path; Factory2/theme remain) |
| Drawable semantics assessed | ❌ ABSENT (Bitmap only) |
| resource qualifiers | PARTIAL (density/night in the previous ARSC parser) |
| Context audit | ✅ basics IMPLEMENTED |
| Handler/Looper audit | ✅ |
| components census | ❌ ABSENT (F010) |
| Kotlin audit | ❌ ABSENT |
| multi-DEX expansion | ✅ (v12 = new 5-DEX proof) |
| JNI census | PARTIAL (tooling exists; census not updated) |
| Google census | ❌ NOT DONE (census-only rule) |
| 125+ corpus progress | UNKNOWN (registry 100+ outside the clone) |
