# WineDroid Study — Source-Level, File-by-File

- Repository: https://github.com/rickbergs/winedroid (exact URL per campaign law)
- Revision: `a784c0b956893733cc12ccd3bec7695b0791f978` (2026-07-14, "docs: rewrite project README")
- Identity: Rust 2024 workspace; "Compilação AOT de bytecode Android para executáveis Linux nativos" — APK → DEX → C → ELF64 PIE x86-64; author Richard Bergamaschi; **Apache-2.0**
- Method: all 21 `.rs` files (7,130 LOC) enumerated; core files read in full; every mechanism below cites file + function
- Prior-session reconciliation: the previous campaign resolved the name "Winedroid" to `winedroid.soham.sh` (Rust userspace Android translation layer, GPL-3.0, repo private). That is a DIFFERENT project. This campaign's mandated URL is `rickbergs/winedroid` and it is now confirmed public, Apache-2.0, and source-readable — the study below supersedes the site-docs-only evidence for the rickbergs project. Both entries remain in the reference matrix, distinct.

## What WineDroid actually is

WineDroid does NOT run Windows or Wine. It applies the *Wine approach*
(translate to host-native, no VM, no container) to Android *bytecode*: it
AOT-compiles a bounded graph of Dalvik methods into C, compiles that C with
Clang into an ELF64 PIE, and executes it directly on the Linux kernel with
unimplemented calls landing in generated stubs. MiniAndroid is a sibling in
intent (run APKs on the host without Android) but a sibling in OPPOSITE
execution model: MiniAndroid interprets DEX in-process; WineDroid lowers DEX
to native code ahead of time.

## Architecture (from source)

```
crates/winedroid-core/
  apk.rs      (251 LOC)  ZIP entry classification + inspection report
  axml.rs     (714 LOC)  Android Binary XML manifest parsing
  dex.rs      (949 LOC)  DEX header/index parsing (strings→classes)
  model.rs    (100 LOC)  ApkReport / DexInfo / ManifestInfo models
crates/winedroid-compiler/
  dex_method.rs (456)    method body extraction from APK (multi-dex aware)
  aot.rs        (863)    Dalvik→C lowering (root single method, no args)
  bootstrap.rs (1488)    objects backend: handles, fields, generic ABI
  linked.rs     (715)    lifecycle linking (4 root methods, one ELF)
  recursive.rs  (522)    BFS call-graph linker with per-method rejection
  main.rs / *_main.rs    CLI entry points (scan-apk / demo / compile-apk /
                         bootstrap-apk / winedroid-sukisu-*)
crates/winedroid-cli/
  main.rs      (202)     `winedroid inspect` / `winedroid doctor`
tests/                  6 integration test files = executable spec
dev/                    6 shell validation scripts
docs/                   8 technical notes (ARCHITECTURE, GENERIC_METHOD_ABI, ...)
```

## Mechanism catalog (research IDs)

### WINEDROID-001 — Single-pass APK inspection with entry classification
- Source: `crates/winedroid-core/src/apk.rs` — `inspect_apk()`, `classify_entry()`
- Mechanism: one walk over `ZipArchive` entries classifying each into
  `Manifest | Dex | NativeLibrary | ResourcesTable | SignatureV1 | Other`,
  capturing compressed/uncompressed size + compression method per entry.
  Manifest sampling is capped at 1 MiB (`MANIFEST_SAMPLE_LIMIT`), each DEX at
  256 MiB (`MAX_DEX_FILE_SIZE`). Unsafe/absolute ZIP paths are detected via
  `entry.enclosed_name()` and downgraded to warnings. Duplicate
  AndroidManifest.xml produces a warning instead of an error.
- Why it exists: APK = untrusted input; inspection must survive hostile
  archives and still report what it saw.
- MiniAndroid applicability: our `src/apk/` loader reports entries but does not
  (a) classify them into a typed enum, (b) warn on unsafe paths, (c) cap
  per-entry read sizes. REUSE DIRECTLY as a diagnostics hardening pass.
- Transfer decision: ADAPT ARCHITECTURE (pure diagnostics; no license issue).

### WINEDROID-002 — Defensive DEX header validation
- Source: `crates/winedroid-core/src/dex.rs` — `parse_header()`
- Mechanism: magic `dex\n` + ASCII-digit version + NUL check; `cdex`
  (Compact DEX) detected and explicitly rejected with a distinct message;
  endian tag must be `0x12345678` (reverse-endian rejected for indexing);
  `declared_file_size >= header_size` and `declared <= archive size` are
  enforced with a warning (not error) when they merely differ.
- MiniAndroid applicability: same checks exist in our DEX loader, but the
  *warning-vs-error split* (differ ≠ corrupt) is cleaner in WineDroid.
  REIMPLEMENT CONCEPT in diagnostics.

### WINEDROID-003 — Index-table pre-validation before any item read
- Source: `crates/winedroid-core/src/dex.rs` — `validate_table()`,
  `table_item_offset()`, `checked_slice()`
- Mechanism: every index table (string/type/proto/field/method/class_defs)
  is bounds-checked as `offset + count*item_size <= logical_size` and
  4-byte-aligned BEFORE parsing items; all offsets computed with
  `checked_add`/`checked_mul`; every out-of-range access names the table and
  the hex offsets in the error.
- MiniAndroid applicability: our `dalvik_engine` validates header offsets but
  not with per-table alignment checks. ADAPT ARCHITECTURE — this is cheap and
  converts corrupt-input crashes into named diagnostics.

### WINEDROID-004 — Complete MUTF-8 decoder with declared-size cross-check
- Source: `crates/winedroid-core/src/dex.rs` — `decode_mutf8()`, `continuation()`;
  test `decodes_modified_utf8_nul_and_surrogate_pair`
- Mechanism: decodes 1/2/3-byte MUTF-8; accepts the `0xC0 0x80` encoded NUL;
  rejects literal `0x00` inside the data; decodes UTF-16 surrogate pairs
  (`0xED 0xA0 0xBD 0xED 0xB8 0x80` → U+1F600) with continuation-byte
  validation; returns `(String, utf16_units)` and the caller FAILS if the
  decoded utf16 length ≠ the ULEB128-declared `utf16_size`.
- MiniAndroid applicability: our DEX string pool handles MUTF-8, but the
  *declared-vs-actual length cross-check* is a free corruption detector we
  lack. REIMPLEMENT CONCEPT (verify our decoder first; add the cross-check).

### WINEDROID-005 — ULEB128 hardening
- Source: `crates/winedroid-core/src/dex.rs` / `dex_method.rs` — `read_uleb128()`
- Mechanism: max 5 bytes; final byte at index 4 must be ≤ 0x0F or the value
  exceeds 32 bits → error; caller advances cursor with checked arithmetic.
- MiniAndroid applicability: parity check for our uleb reader; unit test
  `reads_maximum_u32_uleb128` (0xFF,0xFF,0xFF,0xFF,0x0F → u32::MAX, width 5)
  is directly portable to our test suite.

### WINEDROID-006 — Multi-dex discovery with numeric ordering
- Source: `crates/winedroid-compiler/src/dex_method.rs` — `is_dex_name()`,
  `dex_number()`; tests `recognizes_multidex_names`, `sorts_multidex_numerically`
- Mechanism: `classes.dex` plus `classesN.dex` for any N (regex-equivalent:
  strip `classes` prefix and `.dex` suffix, require non-empty all-digit tail);
  `assets/classes.dex` correctly rejected; sort key is the parsed number, so
  `classes2.dex` < `classes10.dex`.
- MiniAndroid applicability: direct cross-check for our multi-dex method
  resolution finding. Our loader scans entries but should assert the same
  ordering law. REUSE DIRECTLY (test vector).

### WINEDROID-007 — Generic Dalvik argument ABI (the invoke-argument law)
- Source: `crates/winedroid-compiler/src/bootstrap.rs` (frame setup),
  `docs/GENERIC_METHOD_ABI.md`
- Mechanism: every linked method has signature
  `wd_value method(uint32_t argc, const wd_value *args)` and the frame maps
  incoming registers as `incoming_start = registers_size - ins_size;
  v[incoming_start + i] = args[i]`. Missing arguments are zero-filled;
  `ins_size > registers_size` is rejected at link time. `wd_value` is
  `int64_t` — one unified register cell for int/float(ref bits)/handles,
  with wide values occupying two cells.
- Why it exists: the old ABI (`this` + one arg) could not express
  multi-arg/static/virtual/`<init>` calls; the generic ABI covers all.
- MiniAndroid applicability: **this is the same semantic law** we derived for
  invoke-35c/range receiver handling. WineDroid documents the edge cases in
  one table: this-register positioning, zero-fill of absent args, wide pairs.
  Cross-check our `dalvik_engine.cpp` invoke paths against it; the zero-fill
  rule for absent args is a testable discriminator we do not currently
  exercise. ADAPT ARCHITECTURE + add tests.

### WINEDROID-008 — Objects as int32 handles + shared field store
- Source: `crates/winedroid-compiler/src/bootstrap.rs` — `wd_new_object()`,
  `wd_iget()`, `wd_iput()`, `wd_ifield` struct, `wd_static_fields[]`
- Mechanism: objects are monotonically increasing int32 handles
  (`wd_next_object++`, allocation logged to stderr as
  `[WineDroid] new-instance #%d %s`); instance fields live in a shared store
  of `{object, field, value}` triples addressed by (handle, field_id);
  statics live in a global array indexed by field id.
- MiniAndroid applicability: our object model already uses handles; the
  diagnostic value here is the *allocation trace line* convention (see
  WINEDROID-015) and the simplicity of (object,field) addressing as a
  regression-dump format. REIMPLEMENT CONCEPT for trace output.

### WINEDROID-009 — Recursive linker with per-method rejection and reasons
- Source: `crates/winedroid-compiler/src/recursive.rs` — `collect_graph()`,
  `RecursiveLifecycleReport`
- Mechanism: BFS from root lifecycle methods (`<init>`/`onCreate` of the
  Application and launcher Activity); for each candidate: parse → analyze
  (collect referenced methods + unsupported opcodes) → reject or link.
  Rejection is PER-METHOD with a machine-readable reason (up to 8
  `pc=opcode` blockers listed), and never blocks expansion of other branches
  ("métodos incompatíveis são rejeitados individualmente"). Caps: depth 4,
  192-method graph ceiling, ≤1024 code units per non-root method,
  runtime recursion cap 128 (`wd_recursive_depth`). Roots are forced to
  link first in the emitted C (deterministic layout). A missing root method
  is a hard error with the collected rejection reason.
- MiniAndroid applicability: this is the most transferable *methodology* in
  the project. Our semantic fixtures run whole classes but we do not produce
  a per-method "link/reject + reason" graph report for an APK. A
  MiniAndroid equivalent would make "which methods of THIS APK are runnable"
  a first-class artifact (we already have `try_recursive_invoke`; it lacks
  the structured report). ADAPT ARCHITECTURE.

### WINEDROID-010 — External-namespace classification
- Source: `crates/winedroid-compiler/src/recursive.rs` — `is_known_external_namespace()`
- Mechanism: descriptors starting with `Landroid/`, `Landroidx/`, `Ljava/`,
  `Ljavax/`, `Lkotlin/`, `Lkotlinx/`, `Lorg/jetbrains/`, `Lorg/json/` are
  classified external (stub call sites) and never attempted for AOT.
- MiniAndroid applicability: we resolve framework classes through shadows;
  the classification *list* is a useful cross-check that our shadow registry
  covers the same namespaces (it does for android/java; kotlin/jetbrains/json
  stubs are exactly where real corpus apps spend unimplemented time).
  ORACLE for our shadow-registry coverage audit.

### WINEDROID-011 — packed-switch lowering with payload-as-data law
- Source: `crates/winedroid-compiler/src/aot.rs` (branch decoding) +
  `docs/GENERIC_METHOD_ABI.md` "Controle de fluxo"
- Mechanism: `packed-switch` (0x2b) reads `size`/`first_key` from its
  payload, resolves each relative target against the switch instruction,
  validates destinations, emits a C `switch`; DEX payloads are treated as
  DATA, never decoded as instructions (this is also why the instruction
  scanner is width-driven and the `0x00` payload edge is a known WineDroid
  bug to fix).
- MiniAndroid applicability: we already implement packed AND sparse-switch
  (25/25 switch-parse-neg fixtures pass at prior HEAD); WineDroid is behind
  us here (sparse-switch still blocks their methods). The transferable piece
  is the *payload-is-data invariant* as an explicit scanner test: our
  instruction scanner must never misinterpret switch payload bytes as
  opcodes — worth a dedicated fixture. TEST VECTOR.

### WINEDROID-012 — throw lowering without method-level poisoning
- Source: `crates/winedroid-compiler/src/bootstrap.rs` — `wd_throw()`;
  README "Exceções"
- Mechanism: `throw` (0x27) lowers to `wd_throw(handle)` executed only when
  the containing block is reached; an uncaught throw exits the ELF with
  status 103; full try/catch tables, handler search, and frame propagation
  are NOT implemented (honest limitation).
- MiniAndroid applicability: we are AHEAD (typed catch 8/8 at prior HEAD).
  WineDroid confirms our ordering choice (exceptions late, after arithmetic
  and switches) as the pragmatic build order for a from-scratch runtime.
  NO transfer needed; used as schedule-validation oracle.

### WINEDROID-013 — Java int division/rem semantics in the runtime
- Source: `crates/winedroid-compiler/src/aot.rs` — `wd_div()`, `wd_rem()`
- Mechanism: division by zero → message + exit(101);
  `INT32_MIN / -1 → INT32_MIN`; `INT32_MIN % -1 → 0` (both avoid x86 SIGFPE
  and match Java/Dalvik semantics exactly).
- MiniAndroid applicability: our interpreter must (and at prior HEAD does)
  implement the same two special cases; WineDroid's helper is a compact
  citation for the semantic test we already run. Verify at current HEAD.
  TEST VECTOR (already covered — keep).

### WINEDROID-014 — Static field opcode/type matching
- Source: `crates/winedroid-compiler/src/aot.rs` — `validate_static_opcode_type()`
- Mechanism: `sget/sput` opcode variant must match the declared field type
  (0x60/0x67→I, 0x63/0x6a→Z, 0x64/0x6b→B, 0x65/0x6c→C, 0x66/0x6d→S); a
  mismatch is a compile error naming the field descriptor; reads of
  sub-int types sign/zero-extend explicitly in the emitted C.
- MiniAndroid applicability: cross-check our sget/sput implementations for
  the same variant→type strictness (a lax parser would silently corrupt
  booleans/bytes). ADD TEST if absent.

### WINEDROID-015 — Diagnostics CLI + trace conventions
- Source: `crates/winedroid-cli/src/main.rs` (`inspect`, `doctor`);
  stderr conventions throughout (`[WineDroid] new-instance`,
  `[WineDroid] throw handle=`)
- Mechanism: `inspect` prints (or `--json`) archive stats, manifest format +
  package/version/SDK/components/permissions, per-DEX counts
  (strings/types/protos/fields/methods/classes) + sample descriptors, native
  libs grouped by ABI with sonames, `resources.arsc` presence, v1 signature
  entries, and accumulated warnings. `doctor` verifies the host toolchain.
- MiniAndroid applicability: our `--inspect`-style reporting is thinner;
  the per-DEX count block + warnings list is a template we can adopt
  cheaply and it directly serves our "font load diagnostics" / BLOCKED
  reporting laws. ADAPT ARCHITECTURE.

### WINEDROID-016 — Warning-accumulation discipline (inspection never hard-fails)
- Source: `crates/winedroid-core/src/apk.rs` + `axml.rs` (warnings fields on
  report models; chunk-walk breaks with warnings, not exceptions)
- Mechanism: parsing anomalies during *inspection* append to
  `report.warnings` and continue; hard errors are reserved for *execution*
  paths. The AXML parser bounds every chunk (`header_size`, `chunk_size`,
  overflow checks) and records `truncated manifest` etc. as warnings.
- MiniAndroid applicability: mirrors our "BLOCKED with exact reason" law but
  at parse level. REIMPLEMENT CONCEPT in our APK/ARSC diagnostics.

### WINEDROID-017 — Security posture for untrusted APKs
- Source: README "Segurança"; `apk.rs` size caps + path checks
- Mechanism: 256 MiB per-DEX cap; unsafe-path detection; explicit "never run
  as root", "APK is untrusted input", sandbox recommendation (namespaces,
  seccomp) — and an admission that the compiler/runtime are unaudited.
- MiniAndroid applicability: MiniAndroid runs real corpus APKs in-process
  today. We should adopt: per-entry size caps at load, and document our
  sandboxing posture (currently: none). ADAPT ARCHITECTURE (docs + caps).

### WINEDROID-018 — Inspectable emitted artifact
- Source: `crates/winedroid-compiler/src/aot.rs` — `compile(..., emit_c)`
- Mechanism: every AOT run can emit its intermediate C (`--emit-c`); C is
  compiled with `-Wall -Wextra -Werror` (only `-Wunused-label` relaxed, with
  a documented reason: preserved Dalvik labels may lose predecessors).
- MiniAndroid applicability: our equivalent is frame dumps / UI dumps /
  frame hashes. The principle "the intermediate representation is a
  first-class inspectable artifact" is already ours; WineDroid corroborates.
  VALIDATED (no change).

### WINEDROID-019 — Test suite as executable specification
- Source: `crates/winedroid-compiler/tests/{aot_smoke,bootstrap_smoke,
  generic_abi,linked_lifecycle,packed_switch,recursive_linker}.rs`; `dev/*.sh`
- Mechanism: integration tests assert on the EMITTED C (e.g.
  `generic_abi.rs` asserts `wd_linked_method_3(uint32_t argc,
  const wd_value *args)` and `args[3]` reachability) plus runtime checks in
  dev scripts; unit tests build a synthetic minimal DEX in code
  (`build_class_only_dex()` in dex.rs) instead of shipping binaries.
- MiniAndroid applicability: our fixture-APK builder plays the same role;
  the synthetic-DEX-in-code trick is handy for corruption-edge tests we
  currently do by hand. REIMPLEMENT CONCEPT (test tooling).

### WINEDROID-020 — Honest limitation ledger + roadmap ordering
- Source: README "Limitações atuais" (14 explicit non-goals/missing pieces),
  ROADMAP.md (10 ordered milestones: sparse-switch → 0x00 edge → try/catch
  → minimal reflection → virtual dispatch → java.lang/util/io →
  Context/Application/Activity → first Wayland window → JNI → ARM64)
- MiniAndroid applicability: direct precedent for our README "what is NOT
  implemented" section and for campaign ordering. VALIDATED (we already do
  this; cross-checked their order against our completed milestones).

## Reconciliation with MiniAndroid's current state

| WineDroid area | MiniAndroid current (at HEAD 8233432) | Delta |
|---|---|---|
| DEX parsing | our own parser + semantic battery (118/118 at prior audit) | WineDroid's declared-vs-actual MUTF-8 length cross-check is NEW for us (WINEDROID-004) |
| invoke args | invoke-35c/range fixed at prior HEAD | zero-fill-of-absent-args discriminator not exercised (WINEDROID-007) |
| packed/sparse-switch | both implemented | our payload-is-data scanner test is implicit (WINEDROID-011) |
| exceptions | typed catch implemented | we are ahead; their roadmap validates our order |
| objects | handle-based model | allocation-trace convention absent (WINEDROID-008/015) |
| graphics | we render real framebuffer frames | WineDroid has NONE yet (their #8 milestone is first Wayland window) |
| resources | ARSC-first parser + fixtures | WineDroid only reports `resources.arsc` presence |
| lifecycle | Application/Activity onCreate paths run real APKs | WineDroid links 4 lifecycle roots AOT (SukiSU report) — same root-set choice, different execution model |

## Verification pointer

Every claim above was re-checked against the clone at
`../research-clones/winedroid` during this session; file/function names are
verbatim. Re-run `ls crates` + `rg` on any future revision before citing.
