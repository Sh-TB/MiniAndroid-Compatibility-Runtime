# SOURCE_CHANGES.md — UNIFIED CODER campaign source-code changes

**Task ID:** UNIFIED-CAMPAIGN-2026-08-27
**Base commit (before changes):** `bbe0ce3` — EXP-098/CM-027: RLottieImageView → RLottieDecoder runtime wiring
**Change commit (after changes):** `86bd646` — UC-CM-001
**Note:** this document was written exactly per your request: every source change + reason + evidence, so that in the future you can update the main source based on it.

---

## Change list

| ID | File(s) | Type | Regression status |
|----|---------|------|-------------------|
| UC-CM-001 | `src/dex/dalvik_engine.cpp`, `src/dex/dalvik_engine.h` | generic fix (closing F012) | ✅ 3/3 SHA identical to baseline |

---

## UC-CM-001: Type-Aware return value in the API-bridge catch-all (closing open finding F012)

### Problem description (finding origin)
This problem was first recorded by **Coder 3** as a systemic "silent false-success" pattern:

```
unknown method → STUBBED + VOID → subsequently move-result / move-result-wide → silent zero
```

That is, every method that reached the bridge (`bridge_to_api`) without a dedicated handler always
returned `DalvikValue::make_void()` — even if the method's real signature in the DEX was
`Z` (boolean), `I` (int), `J` (long), or a reference. Result:

1. If the bytecode issues `move-result` after the call, a VOID value leaks into the
   register (an invalid type in the register).
2. `if-nez` / `if-eqz` make wrong decisions on such a value.
3. A "silent failure" state is created that is invisible in the trace because
   the status is correctly recorded (`STUBBED`) but the value is wrong.

The recommendation recorded in `CODER3_KNOWLEDGE.md` (F012 section):
> "The real fix: for unknown methods, check return type from proto
> descriptor and return appropriate default (0 for int, null for objects,
> false for boolean) instead of always returning void."

### Files and exact change location

#### 1) `miniandroid/src/dex/dalvik_engine.h` — the `bridge_to_api` signature
An optional `method_idx_hint` parameter was added (default = `0xFFFFFFFF`, meaning "no hint"):

```cpp
// before:
bool bridge_to_api(const std::string& class_name, const std::string& method,
                   const std::vector<DalvikValue>& args, DalvikValue& result,
                   ApiCallTrace::Status& status);

// after:
bool bridge_to_api(const std::string& class_name, const std::string& method,
                   const std::vector<DalvikValue>& args, DalvikValue& result,
                   ApiCallTrace::Status& status,
                   uint32_t method_idx_hint = 0xFFFFFFFFu);
```

**Compatibility:** because the parameter has a default, no old caller breaks.

#### 2) `miniandroid/src/dex/dalvik_engine.cpp` — the catch-all at the end of `bridge_to_api`
The final block (`// Default: stubbed but not crashing`) was replaced:

```cpp
// new (summary):
status = ApiCallTrace::Status::STUBBED;          // as before — honest
if (method_idx_hint != 0xFFFFFFFFu) {
    const std::string proto = resolve_method_proto_for_dex(method_idx_hint, current_dex_index_);
    const size_t rparen = proto.rfind(')');
    if (rparen != std::string::npos && rparen + 1 < proto.size()) {
        const std::string ret = proto.substr(rparen + 1);   // return descriptor
        // V→void(old) | Z→false | B/S/C/I→0 | J→0L | F/D→0.0 | L…/[…→null
        ... // map to DalvikValue::make_bool/make_int/make_long/make_null/...
        return true;
    }
}
result = DalvikValue::make_void();   // fallback: old behavior
return true;
```

**Key points:**
- Status remains `STUBBED` → the honesty of the bookkeeping is preserved
  (we do not fabricate success; we only return a "correctly-typed default value").
- `resolve_method_proto_for_dex` (present since EXP-088/F016) fetches the callee's real
  proto from the `proto_ids` of the same DEX; that function's own fallback is `()V`, which
  gives the same old behavior → no added risk.
- Reference types (`L...;` and arrays) → `make_null()` (equivalent to "no result"
  in ART for a missing method, without crashing).

#### 3) `miniandroid/src/dex/dalvik_engine.cpp` — 6 call sites updated
Every place that calls `bridge_to_api` now also passes `method_idx`:

| Line (approx) | Enclosing function | Change |
|---------------|--------------------|--------|
| 4817 | `execute_method_internal` | `..., status, method_idx)` |
| 7230 | `execute_invoke` (the main virtual/interface/static path) | `..., api_status, method_idx)` |
| 7398 | super-call path (`<super>`) | `..., api_status, method_idx)` |
| 7561 | `execute_invoke_direct` | `..., status, method_idx)` |
| 7875 | `execute_invoke_static` | `..., status, method_idx)` |
| 7969 | `execute_invoke_interface` | `..., status, method_idx)` |

### Why this change is safe (risk analysis)
1. **Without a hint** → exactly the previous behavior (void). Only invoke sites that have a
   method_idx (and all of them do) take the new path.
2. The new path only executes on methods that **were already failing**
   (no successful handler changes).
3. If the proto does not resolve → the resolver function's fallback returns `"()V"` →
   the same old void.
4. The new values (0/false/null) are what ART actually gets closest to at the register-semantic
   level for a "missing method"; CM-008 already fixed zero-truthiness for BOOLEAN/BYTE/SHORT/CHAR
   and this is consistent with it.

### EVIDENCE

#### Real APK — Telegram **12.10.1** (versionCode 70389, 5 DEX, 73MB)
- This version had **never been tested before** (the knowledge base had been built against 10.14.5)
  → the first forward-compatibility evidence.
- APK SHA256: `f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6`
- **Before the change:** 3 runs → all three `06fb40da16b1f473980cfea9...`, exit=0,
  41233 non-white pixels, 12582 trace events, 0 errors
- **After the change:** 3 runs → all three `06fb40da16b1f473980cfea9...` (identical to before),
  exit=0, same pixel count, same 12582 events, 0 errors
- Result: **zero regression** on the full-chain real execution (launch→login→SMS screen→render).

#### Build environment
- g++ 14.2.0 (Debian), `make -j4` → BUILD SUCCESS with no new errors
- rlottie was rebuilt from the Samsung/rlottie source (SHA `43075538`) via a static manual build
  (meson was not in the sandbox) — script: `scripts/build_rlottie.sh` (outside the repo)

### How to apply to the main source (for the future)
Two ways:
1. **patch file:** `0001-UC-CM-001-Type-aware-STUBBED-defaults-in-bridge_to_a.patch`
   → `git apply` or `git am` onto commit `bbe0ce3` or any later HEAD (as long as
   the `bridge_to_api` function and the final catch-all have not been rewritten).
2. **Manually:** the three sections above (header, catch-all, 6 call sites) — the whole diff is about 70 lines.

---

## Non-source changes (equipment/environment) — for reproduction

| Item | Description |
|------|-------------|
| rlottie rebuild | depth-1 clone of Samsung/rlottie + a hand-made `config.h` (`LOTTIE_THREAD_SUPPORT=1`, `LOTTIE_CACHE_SUPPORT=0`) + compiling 35 TU into `librlottie.a` |
| Telegram APK | downloaded from `telegram.org/dl/android/apk` → version 12.10.1; **HASH MISMATCH** vs the manifest (10.14.5) — version drift, real and usable |
| Persian test font | DejaVuSans.ttf (basic Arabic support) — for real production: Vazirmatn/Noto Naskh recommended |

## Toolchain findings (for transparency)
- The grep output for some files suffered a terminal artifact (`ESC[m`) because of the
  `ids[method_idx]` pattern — the file was healthy; verified by reading byte-by-byte in python.
  Lesson: before any grep-based change, verify the raw bytes (the same C2-F11 lesson).
