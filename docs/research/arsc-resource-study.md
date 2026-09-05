# ARSC / Resource System Study

Sources (revisions in external-repositories.md):
- REAndroid/ARSCLib (Apache-2.0), auxten/libarsc (Apache-2.0) — canonical
  ARSC oracles locked from MiniAndroid records
- iBotPeaches/Apktool `baa603f` — BinaryResourceParser.java
- skylot/jadx `8f7ea4e` — core/xmlgen/ResTableBinaryParser.java
- AOSP frameworks/base Resources.java (see aosp-runtime-study.md AOSP-007/008)
- MiniAndroid's own ArscParser (`miniandroid/src/resources/arsc_parser.cpp`)
  as the implementation under audit.

## ARSC-001 — Table chunk constants (cross-implementation consensus)
Apktool `BinaryResourceParser` (verbatim constants):
- `NO_ENTRY = 0xFFFFFFFF`; `NO_ENTRY_OFFSET16 = 0xFFFF`
- `ResTable_typeSpec` flags: `SPEC_PUBLIC = 0x40000000`,
  `SPEC_FLAG_STAGED_API = 0x20000000`
- `ResTable_type` flags: `TYPE_FLAG_SPARSE = 0x01` (entries carry
  (entryId, offset) pairs, binary search; platforms ≥ Oreo),
  `TYPE_FLAG_OFFSET16 = 0x02` (16-bit offsets, real offset = offset*4,
  0xFFFF = NO_ENTRY)
jadx `ResTableBinaryParser` walks package chunks as
type / typespec / library (`RES_TABLE_LIBRARY_TYPE` = dynamic reference
table for shared-library package ids).
- MiniAndroid gap: our parser handles the classic table; the sparse and
  offset16 type-chunk encodings are the known gap (prior matrix row). The
  exact flag values above are the constants our decoder must check.
- Status: DISCOVERED (constants pinned); fixture work queued (differential
  fixture per resource category + sparse/offset16 unit fixtures).

## ARSC-002 — Chunk-walk discipline (jadx model)
`ResTableBinaryParser.parse()` pattern: verify `RES_TABLE_TYPE`; loop
`chunkStart = pos; chunkSize = readUInt32(); chunkEnd = start + size;`
dispatch on chunk type; `skipToPos(chunkEnd)` after EVERY chunk — a truncated
or lying chunk size can never corrupt the outer walk. Unknown chunk types
are logged and skipped (jadx logs "Null chunk type" and continues).
- MiniAndroid: our parser already walks chunks; adopt the explicit
  `skipTo(chunkEnd)` invariant as an assertion in debug builds.
- Status: REIMPLEMENT CONCEPT (hardening).

## ARSC-003 — ARSCLib's creation-side knowledge
ARSCLib README (read at prior session, structure re-verified this session):
programmatic package creation (`TableBlock.newPackage`), typed value encoding
(`ValueCoder.encode("#006400")` string→binary), config-qualified entries
(`-de`, `-ru-rRU`), JSON round-trips designed for OBFUSCATED resource trees.
- MiniAndroid applicability: (a) ValueCoder semantics = the missing encoder
  half of our fixture-APK tooling; (b) the JSON-round-trip idea = a cheap
  differential oracle: decode any corpus ARSC to JSON with ARSCLib, decode
  with ours, diff. Status: ADAPTABLE (queued as differential test).

## ARSC-004 — auxten/libarsc position
aapt-derived pure C++ ResTable reader, mutex-free. No code transfer needed
(our parser is complete for the classic format); value is as a struct-offset
cross-check reference. Status: NOT APPLICABLE (reference only).

## ARSC-005 — Resolution chain law (AOSP + corpus evidence)
The full chain MiniAndroid must honor: compiled resource in APK →
(resource id: package 0xPP | type 0xTT | entry 0xEE) → ARSC lookup
(package → type → entry with best config match) → typed value
(string pool / int / bool / color / dimension / fraction / reference) →
API surface (getString/getColor/getDimension/setText(resid)/setBackgroundColor)
→ View state → rendering → framebuffer pixels.
Real-Android nuances from AOSP: id 0 is INVALID (getIdentifier contract);
getString strips styling; format-args go through String.format with config
locale (AOSP-007/008).
- MiniAndroid: chain verified end-to-end for strings/colors on prior-HEAD
  fixtures (RESULT_016 family + `[ARSC-VALUES] strings=38 colors=8` chess
  clock evidence); differential fixtures per category (string/color/dimen/
  integer/boolean/drawable/raw/font/style/theme/layout/density/aliases) are
  the queued work item. Status: PARTIALLY VERIFIED.

## ARSC-006 — Obfuscation-resistance law
Resource names in real APKs are often stripped (aapt2 optimize) or
obfuscated; ARSCLib's JSON tooling and Apktool's staging both key on IDs and
typed values, not names. MiniAndroid's obfuscated-name fixture (Cycle D)
pinned the same law: never resolve by filename heuristics.
- Status: VERIFIED (fixture exists at prior HEAD; re-run queued).
