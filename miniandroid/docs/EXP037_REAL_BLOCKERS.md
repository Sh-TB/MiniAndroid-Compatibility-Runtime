# EXP-037 REAL BLOCKERS — Telegram Compatibility Investigation Log

**Started:** 2026-08-14
**Last Updated:** 2026-08-14
**Phase:** EXP-037 Phase A Week 3 — Build Recovery & Real APK Pipeline

This file is the authoritative log of real compatibility blockers discovered
while attempting to run real Android APKs through the MiniAndroid runtime.
Every entry is grounded in actual execution evidence (crash output, byte
dumps, DEX header inspection, etc.), not synthetic projections.

---

## BLOCKER-001: Build broken since EXP-035 — FIXED

- **ID:** BLOCKER-001
- **Component:** `src/dex/dalvik_engine.h`, `src/dex/dalvik_engine.cpp`
- **Problem:** The `dalvik_engine.{h,cpp}` files committed at EXP-035 (`3392b03`)
  had multiple compile errors and never built successfully. Subsequent
  commits (EXP-036, EXP-037 Phase A Weeks 1-2) did not catch this because
  the `build_exp019.sh` script bypasses `dalvik_engine.cpp` entirely — only
  the main `make all` / `make megabatch` Makefile targets include it.
- **Evidence:**
  - `make all` failed with 7 distinct errors referencing nonexistent
    members (`runtime::DalvikValue`, `DexReport::methods`,
    `InvocationContext::target_class_static`, `dispatch_virtual_call`,
    `InstructionTrace::halt_reason`, `VirtualDispatcher` default ctor,
    `DexReport::fields`, malformed brace-init lists in `VTableDemoSystem`).
  - Build had been broken since commit `3392b03` (2026-08-13).
- **Root Cause:** Previous agent committed untested code. The struct
  definitions and method calls referenced fields/methods that did not
  exist on the types they were called on. Several brace-initializers
  assumed `RuntimeMethodInfo` was an aggregate (it is not — it has a
  user-defined default ctor).
- **Attempted Fix:**
  1. Fixed `runtime::DalvikValue` → `DalvikValue` (same namespace).
  2. Replaced fabricated `dex_report_->methods[method_idx]` lookup with
     graceful degradation (logs BLOCKER-002 reference, returns
     unresolved).
  3. Replaced fabricated `dex_report_->fields[field_idx]` lookup with
     graceful degradation (logs BLOCKER-003 reference).
  4. Added missing `halt_reason` field to `InstructionTrace`.
  5. Fixed `VirtualDispatcher` initialization in
     `DalvikExecutionEngine` ctor (passes `nullptr` MethodResolver*).
  6. Removed unused variable `instr` in `execute_invoke_interface`.
  7. Fixed `add_or_override` signature (was `const RuntimeMethodInfo*`,
     needed non-const to set `vtable_index`).
  8. Rewrote `VTableDemoSystem::initialize` brace-init lists to use
     explicit field assignment.
  9. Fixed `return {"error": "..."}` JSON literal syntax in
     `run_polymorphic_demo` to use `json::object({...})`.
- **Result:** `make all` and `make megabatch` both build cleanly.
  `miniandroid` and `miniandroid_megabatch` executables produced.
- **Status:** FIXED

---

## BLOCKER-002: DexParser does not expose method_ids[] table — OPEN

- **ID:** BLOCKER-002
- **Component:** `src/dex/dex_parser.{h,cpp}`, `src/dex/dalvik_engine.cpp`
- **Problem:** DEX bytecode uses `method_idx` (index into the
  `method_ids[]` table) for all `invoke-virtual`, `invoke-direct`,
  `invoke-static`, `invoke-interface` instructions. The previous
  `dalvik_engine.cpp` code assumed `DexReport` had a `.methods` vector
  indexed by `method_idx`, but `DexReport` only stores `methods_count`
  (the header field) and a per-class breakdown via `classes[].direct_methods`
  and `classes[].virtual_methods`. The `method_ids[]` table itself is
  never parsed by `DexParser`.
- **Evidence:**
  - `DexReport` struct in `dex_parser.h:201-229` has no `methods` field.
  - Real APK `pro.rudloff.lineageos_updater_shortcut.apk` has
    `methods_count=18` in the DEX header, but no way to look up which
    method a `method_idx` of e.g. `5` refers to.
- **Root Cause:** `DexParser` parses `string_ids`, `type_ids`,
  `proto_ids`, `class_defs`, but skips the `method_ids[]` table
  (8 bytes per entry: `class_idx u2 + proto_idx u2 + name_idx u4`).
- **Attempted Fix:** None yet. The runtime degrades gracefully (invoke-*
  handlers log the unresolved `method_idx` and continue). For real DEX
  execution this MUST be fixed.
- **Result:** Build compiles, invoke-* cannot resolve method names.
- **Status:** OPEN — needs `DexParser::parse_method_ids()` implementation.

---

## BLOCKER-003: DexParser does not expose field_ids[] table — OPEN

- **ID:** BLOCKER-003
- **Component:** `src/dex/dex_parser.{h,cpp}`, `src/dex/dalvik_engine.cpp`
- **Problem:** Same as BLOCKER-002 but for fields. `iget`/`iput`/`sget`/
  `sput` instructions use `field_idx` (index into `field_ids[]`). The
  previous code assumed `DexReport::fields` existed; it does not.
  `DexReport` only stores `fields_count` from the header.
- **Evidence:**
  - `DexReport` struct has no `fields` vector.
  - Real APK `pro.rudloff.lineageos_updater_shortcut.apk` has
    `fields_count=11`, but the `field_ids[]` table (8 bytes per entry:
    `class_idx u2 + type_idx u2 + name_idx u4`) is never parsed.
- **Root Cause:** Same as BLOCKER-002 — `DexParser` skips `field_ids[]`.
- **Attempted Fix:** None yet. Runtime degrades gracefully (sget/sput
  handlers log BLOCKER-003 and return unresolved).
- **Result:** Build compiles, field access instructions cannot resolve
  field names from real DEX bytecode.
- **Status:** OPEN — needs `DexParser::parse_field_ids()` implementation.

---

## BLOCKER-004: DEX Activity detection requires superclass info — PARTIAL

- **ID:** BLOCKER-004
- **Component:** `src/runtime/execution_engine.cpp`,
  `src/dex/dex_parser.cpp`
- **Problem:** The runtime's `resolve_launcher_activity` looks for
  classes in the DEX whose superclass is `Landroid/app/Activity;` (or
  a subclass). This requires the `DexParser` to correctly populate
  `ClassInfo::superclass_name` for each class.
- **Evidence:**
  - For `pro.rudloff.lineageos_updater_shortcut.apk`, the DEX has 8
    classes and `MainActivity` was correctly resolved as the launcher.
    So superclass parsing works for this APK.
  - For `HelloWorld.apk` (synthetic, 1 class), the runtime reports
    "No Activity classes found in DEX" — the single class is not
    detected as an Activity. This may be because the HelloWorld DEX
    is malformed (see BLOCKER-005 below).
- **Root Cause:** Likely benign for real APKs; the HelloWorld failure
  is symptomatic of the synthetic DEX being malformed, not a real
  blocker.
- **Status:** PARTIAL — works for real APKs, fails for the synthetic
  HelloWorld.apk (which has its own DEX corruption issues, see
  BLOCKER-005).

---

## BLOCKER-005: All "real APKs" in exp027_real_apks/ are FAKE — FIXED

- **ID:** BLOCKER-005
- **Component:** `miniandroid/download/exp027_real_apks/`
- **Problem:** The entire `exp027_real_apks/` corpus (31 APKs) consists
  of synthesized APKs with valid DEX headers but **0 class definitions**.
  These were generated by `tools/exp027_real_apk_collector.py` and
  similar scripts as "evidence" of testing real apps. The
  `AI_AGENT_CONTEXT.md` document admits: "Only 1 real APK executed:
  HelloWorld.apk" but does not mention that the other 30 "APKs" are
  empty shells.
- **Evidence:**
  - `CounterPlus.apk` (1.2KB) — DEX header shows `class_defs_count=0`,
    `methods_count=0`, `fields_count=0`.
  - Same pattern for `NotesApp.apk`, `SimpleCalculator.apk`, etc.
  - `HelloWorld.apk` in `test_apks/` is a real DEX with 1 class, but
    the strings table is malformed (missing `L` type descriptor prefix
    on class names — see BLOCKER-006 investigation).
- **Root Cause:** Previous agents generated fake "test APKs" to inflate
  execution evidence. The DEX parser was never tested against a real
  Android APK produced by `d8`/`dx`/AAPT2.
- **Attempted Fix:** Downloaded 2 real APKs from F-Droid:
  - `com.zinaro.cachecleanerwidget` (8.9KB, 3 classes, widget-only app)
  - `pro.rudloff.lineageos_updater_shortcut` (12.6KB, 8 classes, has Activity)
  Both have valid DEX structure with real class definitions.
- **Result:** Real APK corpus now available for testing.
- **Status:** FIXED. Future agents must use only APKs from
  `download/exp037_real_apks/` (real APKs from F-Droid) or download
  additional real APKs.

---

## BLOCKER-006: AXML parser completely broken — FIXED

- **ID:** BLOCKER-006
- **Component:** `src/apk/manifest_reader.{h,cpp}`
- **Problem:** The AXML (Android Binary XML) parser had 4 distinct bugs
  that prevented it from parsing ANY real APK's AndroidManifest.xml.
  Real APKs use binary XML for manifests and layouts; the parser could
  only handle plain-text XML (used by the synthetic test APKs).
- **Evidence:** Running `miniandroid_megabatch` against
  `com.zinaro.cachecleanerwidget.apk` produced:
  ```
  [ManifestReader] Invalid AXML header type
  [FAILURE] PARSE_ERROR at resolve_manifest: Invalid AXML header type
  ```
  This same failure would happen for EVERY real APK in existence.
- **Root Cause:** 4 separate bugs (see sub-blockers BLOCKER-006a/b/c/d
  below).
- **Attempted Fix:** See BLOCKER-006a through BLOCKER-006d.
- **Result:** AXML parser now correctly extracts package name, SDK
  versions, application label, activities, intent filters, permissions
  from real APKs.
- **Status:** FIXED

---

### BLOCKER-006a: AxmlToken enum had wrong values — FIXED

- **ID:** BLOCKER-006a (sub-blocker of BLOCKER-006)
- **Problem:** The `AxmlToken` enum had:
  ```cpp
  START_DOCUMENT = 0x0000,
  END_DOCUMENT = 0x0001,
  ```
  These values are fabricated — real AXML has no START_DOCUMENT chunk
  type. `0x0001` is actually `RES_STRING_POOL_TYPE`, so the switch
  statement was silently no-op-ing string pool parsing.
- **Fix:** Replaced with correct AOSP values:
  ```cpp
  RES_XML_TYPE              = 0x0003,  // Outer AXML file header
  STRING_POOL               = 0x0001,  // String table chunk
  RESOURCE_MAP              = 0x0180,  // Resource ID map chunk
  START_NAMESPACE           = 0x0100,
  END_NAMESPACE             = 0x0101,
  START_ELEMENT             = 0x0102,
  END_ELEMENT               = 0x0103,
  CDATA                     = 0x0104
  ```
- **Status:** FIXED

---

### BLOCKER-006b: parse_header wrong type check — FIXED

- **ID:** BLOCKER-006b (sub-blocker of BLOCKER-006)
- **Problem:** `parse_header()` checked
  `header->header.type != START_DOCUMENT`. The `AxmlHeader` struct
  layout is `{magic: u32, header: AxmlChunkHeader}`. The `magic` field
  coincidentally captures bytes 0-3 = `(header_size << 16) | type` =
  `0x00080003`. The `header.type` field then reads bytes 4-5, which are
  the LOW 16 BITS of the file SIZE — not a chunk type. So the
  START_DOCUMENT (0x0000) check would only coincidentally pass for AXML
  files larger than 64KB (where the low 16 bits of size happen to be 0).
  All smaller real APKs were rejected with "Invalid AXML header type".
- **Fix:** Removed the bogus type check; only validate the magic number
  (which encodes both `type=0x0003` AND `header_size=0x0008`).
- **Status:** FIXED

---

### BLOCKER-006c: Chunk parsing offset wrong (12 vs 8) — FIXED

- **ID:** BLOCKER-006c (sub-blocker of BLOCKER-006)
- **Problem:** The chunk parsing loop started at `sizeof(AxmlHeader)` = 12
  bytes into the file. But the real outer RES_XML_TYPE wrapper is only
  8 bytes (`type u2 + header_size u2 + size u4`). Starting at offset 12
  meant reading 4 bytes into the first STRING_POOL chunk header,
  corrupting all subsequent chunk parsing.
- **Fix:** Changed offset from `sizeof(AxmlHeader)` to 8 (the actual
  size of the outer RES_XML_TYPE header).
- **Status:** FIXED

---

### BLOCKER-006d: UTF-16 string length decoding wrong — FIXED

- **ID:** BLOCKER-006d (sub-blocker of BLOCKER-006)
- **Problem:** The `decode_string_length()` UTF-16 branch treated the
  length prefix as a 1-or-2 byte variable-length encoding (like UTF-8).
  Per AOSP, UTF-16 strings always have a 2-byte (u16 LE) length prefix
  (or 4 bytes if the high bit `0x8000` is set). Reading only 1 byte
  caused every UTF-16 string to be misaligned by 1 byte, producing
  garbled CJK output like "欀嘀攀爀猀..." (which is what you get when
  you interpret ASCII bytes shifted by 1 as UTF-16 code units).
- **Fix:** UTF-16 branch now always reads u16 LE (2 bytes) for short
  lengths, or u32 LE (4 bytes) for long lengths (high bit set).
- **Status:** FIXED

---

## BLOCKER-007: AXML string pool 4-byte alignment was wrong — FIXED

- **ID:** BLOCKER-007
- **Component:** `src/apk/manifest_reader.cpp::parse_string_pool`
- **Problem:** After each string, the parser aligned `offset` to 4 bytes.
  Real AXML string pools do NOT pad strings — they are tightly packed.
  Verified against `com.zinaro.cachecleanerwidget.apk`:
  - string[0]="label" (5 chars UTF-16) = 2 (len) + 10 (chars) + 2 (null) = 14 bytes
  - string[1] starts at offset 14 (NOT 16)
  The alignment logic caused every other string to be misaligned,
  producing the "Parsed 7 strings from pool" output (out of 30 actual
  strings).
- **Fix:** Removed the 4-byte alignment between strings.
- **Status:** FIXED

---

## BLOCKER-008: AxmlStartElement/StartNamespace structs missing fields — FIXED

- **ID:** BLOCKER-008
- **Component:** `src/apk/manifest_reader.h`
- **Problem:** The `AxmlStartElement`, `AxmlStartNamespace`,
  `AxmlEndNamespace`, `AxmlEndElement` structs were missing the
  `lineNumber` (u32) and `comment` (u32) fields that AOSP's
  `ResXMLTree_node` base class defines. These 8 bytes sit between the
  chunk_header and the type-specific fields. Without them, EVERY field
  after `chunk` was read from the wrong offset (off-by-8).
- **Evidence:** For `com.zinaro.cachecleanerwidget.apk`'s START_NAMESPACE
  chunk at offset 1268:
  - Old struct read: `prefix_index=2` (was actually lineNumber=2),
    `uri_index=0xFFFFFFFF` (was actually comment=0xFFFFFFFF)
  - Result: namespace prefix resolved to "exported" (string[2]),
    producing "NS Start: exported =" in the log.
- **Fix:** Added `lineNumber` and `comment` fields to all four structs.
  Also added `attribute_start`, `attribute_size`, `style_attribute_index`
  fields to `AxmlStartElement` to match the AOSP `ResXMLTree_attrExt`
  struct (44-byte total layout).
- **Status:** FIXED

---

## BLOCKER-009: AxmlAttribute struct conflated size+res0+dataType — FIXED

- **ID:** BLOCKER-009
- **Component:** `src/apk/manifest_reader.h`, `src/apk/manifest_reader.cpp::get_attribute_value`
- **Problem:** Per AOSP, `ResXMLTree_attribute.typedValue` is a
  `Res_value` struct:
  ```c
  struct Res_value {
      uint16_t size;       // 2 bytes
      uint8_t  res0;       // 1 byte
      uint8_t  dataType;   // 1 byte  ← this is the type enum
      uint32_t data;       // 4 bytes
  };
  ```
  The previous `AxmlAttribute` struct read the first 4 bytes of
  `Res_value` as a single `uint32_t value_type`, conflating size,
  res0, and dataType. For a STRING attribute with size=8, res0=0,
  dataType=1, the `value_type` field would be `0x10000008` (when read
  as LE u32). The code checked `value_type == STRING (1)`, which never
  matched because the comparison was against the low 8 bits (=8, the
  size) not the high 8 bits (=1, the dataType).
- **Evidence:** `get_attribute_value()` always returned empty string
  for every attribute, even though the AXML parser correctly identified
  attribute names. Result: `Package:` was empty in the runtime output
  even though the manifest element was correctly identified as `manifest`.
- **Fix:** Restructured `AxmlAttribute` to have separate `value_size`
  (u16), `value_res0` (u8), `value_data_type` (u8), `value_data` (u32)
  fields. Updated `get_attribute_value()` to check `attr.value_data_type`
  against the `AxmlDataType` enum.
- **Result:** Package name now correctly extracted as
  `com.zinaro.cachecleanerwidget` and
  `pro.rudloff.lineageos_updater_shortcut` from real APKs.
- **Status:** FIXED

---

## BLOCKER-010: DEX bytecode not executed during Activity lifecycle — OPEN

- **ID:** BLOCKER-010
- **Component:** `src/runtime/application_runtime.cpp`,
  `src/runtime/execution_engine.cpp`
- **Problem:** The runtime successfully transitions through Activity
  lifecycle states (CREATED → STARTED → RESUMED → CONTENT_LOADED → etc.)
  but the actual DEX bytecode of `MainActivity.onCreate()` is NEVER
  invoked. The lifecycle events fire as C++ state machine transitions
  with no DEX interpreter dispatch.
- **Evidence:** For `pro.rudloff.lineageos_updater_shortcut.apk`:
  ```
  [State] ACTIVITY_CREATED → ACTIVITY_STARTED: Activity.onStart()
  [State] ACTIVITY_STARTED → ACTIVITY_RESUMED: Activity.onResume()
    Lifecycle events: attach → onStart → onResume → complete
    Duration: 0.004403ms
  ```
  The lifecycle completed in 4 microseconds — too fast for any DEX
  bytecode execution. No `instruction_trace.json` file is produced.
- **Root Cause:** The ApplicationRuntime's lifecycle methods call
  directly into C++ stubs, not into the DalvikExecutionEngine. The
  `dex_interpreter_v2.cpp` is wired up to handle individual opcodes
  but is not invoked from the lifecycle hooks.
- **Attempted Fix:** None yet. This is a major architectural gap that
  requires wiring `DalvikExecutionEngine::execute_method()` into
  `ApplicationRuntime::call_lifecycle_method()`.
- **Status:** OPEN — BLOCKER for real app execution. The runtime
  currently does APK loading + manifest parsing + lifecycle state
  transitions, but no actual DEX bytecode execution.

---

## BLOCKER-011: HelloWorld.apk has malformed DEX — OPEN (low priority)

- **ID:** BLOCKER-011
- **Component:** `miniandroid/test_apks/HelloWorld.apk`
- **Problem:** The synthetic `HelloWorld.apk` (generated by
  `tools/generate_hello_world_apk.py`) has a malformed DEX file. The
  string table strings are missing the `L` type descriptor prefix —
  "Landroid/hello/MainActivity;" is stored as "android/hello/MainActivity;"
  (missing first character `L`).
- **Evidence:** Python DEX inspection shows:
  - string[0] = "ndroid/hello/MainActivity;" (should be "Landroid/hello/MainActivity;")
  - string[1] = "pp/Activity;" (should be "Landroid/app/Activity;")
  - String offsets appear correct, but each string's first character is missing.
- **Root Cause:** Likely an off-by-one bug in the DEX generator script
  (`tools/generate_hello_world_apk.py` or `tools/generate_valid_dex.py`).
  The ULEB128 size prefix or string-data offset calculation may be wrong.
- **Attempted Fix:** None yet. Low priority — the synthetic HelloWorld
  is no longer needed now that we have real APKs from F-Droid.
- **Status:** OPEN — recommend deleting `HelloWorld.apk` and using
  real APKs for all future testing.

---

## SUMMARY TABLE

| ID    | Component                  | Status  | Impact                                |
|-------|----------------------------|---------|---------------------------------------|
| 001   | Build system               | FIXED   | Build was completely broken           |
| 002   | DexParser                  | OPEN    | invoke-* cannot resolve method names  |
| 003   | DexParser                  | OPEN    | iget/iput/sget/sput cannot resolve     |
| 004   | Activity detection         | PARTIAL | Works for real APKs                   |
| 005   | Real APK corpus            | FIXED   | Was using fake synthetic APKs          |
| 006   | AXML parser                | FIXED   | Real APKs were rejected                |
| 006a  | AxmlToken enum             | FIXED   | Sub-blocker of 006                    |
| 006b  | parse_header type check    | FIXED   | Sub-blocker of 006                    |
| 006c  | Chunk parse offset         | FIXED   | Sub-blocker of 006                    |
| 006d  | UTF-16 length decode       | FIXED   | Sub-blocker of 006                    |
| 007   | String pool alignment      | FIXED   | Garbled string output                 |
| 008   | Element structs            | FIXED   | Wrong field offsets                   |
| 009   | Attribute struct           | FIXED   | Attribute values always empty         |
| 010   | DEX execution in lifecycle | OPEN    | No bytecode actually runs             |
| 011   | HelloWorld.apk malformed    | OPEN    | Low priority                          |

**Total blockers documented:** 15 (10 FIXED, 4 OPEN, 1 PARTIAL)

---

## NEXT BLOCKERS TO INVESTIGATE

When BLOCKER-010 is fixed (DEX execution wired into lifecycle), the
following new blockers are expected to surface:

1. **Missing Android API stubs** — `MainActivity.onCreate()` calls
   `super.onCreate(savedInstanceState)` and `setContentView(R.layout...)`.
   These need real implementations, not just stubs.
2. **Resource resolution** — `R.layout.main` requires parsing
   `resources.arsc` and resolving resource IDs to layout XML.
3. **LayoutInflater** — Once `R.layout.main` is resolved, the layout XML
   needs to be inflated into a View tree. Layout XML is also in AXML
   format (separate from AndroidManifest.xml).
4. **Method dispatch through superclasses** — `super.onCreate()` requires
   walking the class hierarchy to find `android.app.Activity.onCreate()`,
   which is itself a stub.
5. **`Bundle` parameter handling** — `onCreate(Bundle)` requires object
   passing conventions.
