# DEX Runtime Study — Dalvik semantics across ART, DaliVM, dexterpreter, DroidSaw, WineDroid

Purpose: consolidate every DEX-semantics fact gathered this campaign that
bears on MiniAndroid's interpreter (`miniandroid/src/dex/dalvik_engine.cpp`,
`dex_interpreter*.cpp`), and re-state the standing finding list that must be
re-validated on current HEAD (campaign law §26: previous agent claims are
hypotheses until re-proven).

## Sources studied
- ART: `libdexfile/dex/` (loader, verifier, code_item_accessors), official
  googlesource HEAD `6484611f` — see aosp-runtime-study.md AOSP-015/016.
- Dalvik spec material mirrored under `platform_dalvik` (historical docs).
- fatalSec/DaliVM (GPL-3.0, ORACLE ONLY — zero import): README publishes
  127+ opcode hex-range tables; targeted-method execution with limits;
  backward data-flow + forward lookup argument resolution; Android API mock
  tables; multi-DEX unified index; `<clinit>` tracking.
- vimalloc/dexterpreter: README single line, no license → differential
  reference only, low yield (unchanged from prior session).
- droidsaw `50eb045b` (BSD-3): DEX→Java with byte-exact round-trip
  preservation mode — 5,767 F-Droid DEX files recovered bit-identically;
  "the test fails loudly when the format model has a hole".
- WineDroid `a784c0b` (Apache-2.0): AOT lowering of a subset; see
  winedroid-study.md WINEDROID-004/005/006/007/011/012/013/014.

## DEX-001 — MUTF-8 decoding law (cross-project consensus)
Every correct implementation must: reject literal NUL inside data; accept
`0xC0 0x80` as NUL; handle surrogate pairs; verify the decoded UTF-16 unit
count against the ULEB128-declared `utf16_size` (WineDroid fails the string
on mismatch; ART's verifier cross-checks string data bounds; droidsaw's
round-trip mode catches it byte-wise).
- MiniAndroid: our string pool decodes MUTF-8; the declared-size cross-check
  is not asserted. Action: add cross-check + the three edge tests (NUL,
  surrogate pair, u32-max ULEB128) from WineDroid's unit tests as local
  fixtures. Status: IMPLEMENTATION CANDIDATE (diagnostics-grade).

## DEX-002 — Multi-dex resolution law
Discovery = `classes.dex` + `classesN.dex` with NUMERIC ordering
(`classes2` < `classes10`), rejecting non-numeric tails and nested paths
(WineDroid `is_dex_name`/`dex_number` with named unit tests). Method lookup
across dex files is a unified index (DaliVM) — the APP's class may live in
any file.
- MiniAndroid: multi-dex method resolution is a standing finding from the
  prior campaign; revalidation at current HEAD is queued (see audit).
  The numeric-ordering test vector is adoptable as-is. Status:
  REVALIDATE + adopt test vector.

## DEX-003 — invoke argument delivery (the ABI law)
Unified across WineDroid's generic ABI and Dalvik spec: incoming registers
occupy the TAIL of the frame (`incoming_start = registers_size - ins_size`);
`this` is the first incoming register for instance methods; wide args take
two cells; absent incoming registers are zero (WineDroid zero-fills;
the spec leaves un-set registers as method-local anyway).
- MiniAndroid: invoke-35c and invoke-range receiver handling are standing
  findings (RESULT families + "invoke-range receiver handling", "35c float
  arguments" in §26). Revalidation must include: receiver positioning,
  float bits passing through the 32-bit cell without int coercion, wide
  pairs, and >5-arg range calls. Status: REVALIDATE (existing fixtures +
  new zero-fill discriminator).

## DEX-004 — Arithmetic corner semantics
- Java int div/rem: `INT32_MIN / -1 == INT32_MIN`, `INT32_MIN % -1 == 0`,
  div-by-zero raises ArithmeticException (WineDroid exits 101 at its AOT
  layer; an interpreter must route to the exception path, not abort).
- long arithmetic (const-wide/32 decoding, cmp-long, shl/shr/ushr with
  masked shift counts) — the RESULT_001/009 finding families.
- NEG/NOT are bitwise ops with defined wrap behavior.
- MiniAndroid: all listed in §26 revalidation queue with existing fixtures;
  DaliVM's hex-range table is the opcode-coverage oracle for building the
  planned gap table. Status: REVALIDATE (fixtures exist at prior HEAD).

## DEX-005 — Switch payloads are data, not instructions
`packed-switch-payload`/`sparse-switch-payload` blocks (and fill-array-data)
must never be decoded as opcodes by a linear scanner; identification is by
ident (0x0100/0x0200/0x0300) not by position. WineDroid's outstanding
"0x00 opcode edge" bug is exactly a scanner that walked into payload data.
- MiniAndroid: implemented for both switch forms; the invariant deserves a
  dedicated fixture where a payload byte pattern equals a valid opcode.
  Status: VERIFIED (behavior) + ADD fixture for the invariant.

## DEX-006 — Exceptions: ordering and typed catch
Try/catch tables (try_item + encoded_catch_handler_list) drive handler
search by code address range and catch_type_index; ordering across the
industry is consistent: arithmetic/switches first, exceptions later
(WineDroid roadmap position 3; MiniAndroid already has typed catch 8/8 at
prior HEAD — ahead of WineDroid).
- Status: VERIFIED (prior HEAD) — re-run battery at current HEAD.

## DEX-007 — Reflection is the universal cliff
SukiSU's AOT run ends at `NoSuchMethodException` (WineDroid status 103);
DaliVM mocks `Class.getDeclaredMethod`/`Method.invoke`/`sun.misc.Unsafe`;
WineDroid roadmap item 4 is "minimal reflection". Real APKs reflect early
in Application/Activity init.
- MiniAndroid: our shadow registry handles the reflection-named APIs the
  corpus hits; the diagnostic lesson is that "ends at reflection" is a
  NORMAL healthy stop point, not a runtime bug — our probe reports should
  classify it as such. Status: DOCUMENTED (diagnostic taxonomy).

## DEX-008 — Opcode coverage matrix as a repo artifact
DaliVM publishes exact hex ranges per opcode family; WineDroid's
`instruction_width()` encodes instruction widths as data; ART's
`code_item_accessors` gives canonical access patterns. None of MiniAndroid's
audit artifacts enumerates implemented opcodes as data.
- Action (transferred methodology): generate `opcode coverage table` from
  `dalvik_engine.cpp` dispatch, diff against DaliVM's table + the Dalvik
  spec set, store as a repo artifact with PASS/FAIL per exercised opcode.
  Status: METHODOLOGY TRANSFERRED (tool queued; not built this session —
  recorded in knowledge-transfer-log.md as DEFERRED with reason).

## DEX-009 — Byte-exact round-trip as the format-model test (droidsaw)
droidsaw re-emits parsed DEX byte-for-byte; any parser hole (offset off by
one, missed alignment, forgotten padding) makes the re-emitted bytes
diverge and the test names the byte. This is the strongest known
parser-correctness test pattern and is directly applicable to BOTH our DEX
and ARSC parsers (parse → re-serialize → diff = the ARSC differential
fixture plan already queued in the reference matrix).
- Status: METHODOLOGY TRANSFERRED (queued as ARSC round-trip fixture).
