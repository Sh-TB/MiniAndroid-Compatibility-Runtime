# P2/P3 — DexFile + dexHunter RESEARCH AUDIT (FIND-REUSE-DEX / FIND-REUSE-ART)

Campaign: GOLDEN-02 EXTERNAL INTERACTIVE VISUAL · Date: 2026-09-06
Priority rule honored: P0 GOLDEN-02 completed FIRST; these audits were
bounded and did not derail the gate.

Sources (commit-pinned):
- `vova7878/DexFile` @ `1616ed0c83773843931d308fbbeb68f530fe793a`
  (files: `src/main/java/com/v7878/dex/raw/DexReader.java`,
  `src/main/java/com/v7878/dex/io/ValueCoder.java`, `DexOffsets.java`,
  `DexVersion.java`)
- `zyq8709/dexHunter` @ `9d829a9f6f608ebad26923f29a294ae9c68d0441`
  (files: `art/runtime/mirror/class.h`, `art/runtime/class_linker.cc`,
  `art/runtime/dex_file_verifier.cc`)

Rule: GitHub projects are supporting engineering evidence, NOT
automatically authoritative Android law. Each finding states the
underlying AOSP/DEX-spec law the source demonstrates.

Status vocabulary: researched / implemented / tested / observed /
runtime-proven / verified. NOTHING here is marked `verified` from source
inspection alone — implemented findings carry hostile tests + the full
regression battery instead.

---

## FIND-REUSE-DEX-001 — encoded_value ARRAY/ANNOTATION variable-length walk
- Source: DexReader.readEncodedValue (DEX @1616ed0c) cases ARRAY/ANNOTATION
  → readEncodedArray/readEncodedAnnotation recursion.
- Law: encoded_array = ULEB128 count + count encoded_values;
  encoded_annotation = ULEB128 name_idx + ULEB128 count + count
  (ULEB128 name_idx + encoded_value) pairs. Payloads are VARIABLE length
  (DEX spec encoded_value encoding table).
- MiniAndroid (pre-audit): `parse_static_values` (dex_parser.cpp) treated
  EVERY unknown value as `p += value_arg+1`. For ARRAY/ANNOTATION this
  DESYNCHRONIZED the static-values stream: every later field default
  decoded from the middle of the array payload.
- Reproduction: hostile bytes `1c 02 <int> <byte> 17 07` — pre-fix decode
  of the trailing VALUE_STRING read from inside the array payload.
- Impact: MED-HIGH (wrong static defaults for any class whose
  encoded_array_item contains an array/annotation value).
- Transfer: generic walker `miniandroid::dex::read_encoded_value`
  (src/dex/encoded_value.h) with recursive element walk + ULEB completeness
  check (truncated uleb = malformed, not silent 0).
- Test: tests/encoded_value_law_test.cpp — array/annotation walks, nested
  array-in-annotation, truncation-at-every-prefix hostile sweep.
- Runtime evidence: full battery 23/23 stages (R-class constant path
  exercised by EXT-01 typography golden 9/9 + HelloWorld 26/26 unchanged).
- Integration status: **tested**

## FIND-REUSE-DEX-002 — signed encoded_value sign-extension law
- Source: ValueCoder.readSignedInt/readSignedLong (DEX @1616ed0c):
  load value_arg+1 bytes into the HIGH bits of the register, then
  ARITHMETIC shift right by (width_bytes-1)*8 — sign extension.
- Law: VALUE_BYTE/SHORT/INT/LONG payloads are sign-extended to their
  nominal width (art/libdexfile identical algorithm).
- MiniAndroid (pre-audit): little-endian assembly WITHOUT sign extension;
  a sub-width negative (1-byte 0xFF VALUE_SHORT) decoded as +255.
- Reproduction: hostile bytes `02 FF` → pre-fix 255, post-fix -1.
- Impact: MED (negative static-final short/int/long constants in
  sub-width encodings — d8 emits minimal widths).
- Transfer: sign_extend() in encoded_value.h; used for all four types.
- Test: encoded_value_law_test (SHORT/BYTE/INT/LONG sign cases; the
  full-width 0x7f030000 G17/G24 regression case stays fixed).
- Integration status: **tested**

## FIND-REUSE-DEX-003 — VALUE_CHAR unsigned + FLOAT/DOUBLE right-zero-extension
- Source: ValueCoder.readUnsignedInt(in, zwidth, fillOnRight) (DEX
  @1616ed0c); CHAR uses fillOnRight=false (zero-extended left), FLOAT and
  DOUBLE use fillOnRight=TRUE (bits in the HIGH positions of the 32/64-bit
  value, low bits zero).
- Law: DEX spec encoded_value encoding table (right-zero-extended format
  for floating point).
- MiniAndroid (pre-audit): CHAR dropped entirely (fell to the skip branch);
  FLOAT/DOUBLE skipped with correct payload skip but no default.
- Transfer: CHAR decoded (unsigned → default_int_value); FLOAT/DOUBLE
  walked correctly with raw bits captured in EncodedValue.float_bits.
- Impact: LOW-MED (CHAR static defaults now correct; FLOAT/DOUBLE default
  STORAGE still a recorded completeness gap → FIND-REUSE-DEX-004).
- Test: encoded_value_law_test (CHAR 0xFF → 255; FLOAT 0xC0 → 0xC0000000
  = -2.0f bits).
- Integration status: **tested** (CHAR + walk) / **researched** (float
  default storage)

## FIND-REUSE-DEX-004 — remaining default-value completeness (FLOAT/DOUBLE
   storage, TYPE/FIELD/METHOD/ENUM/METHOD_TYPE/METHOD_HANDLE indices)
- Source: DexReader.readEncodedValue (DEX @1616ed0c).
- Law: all of these are legal encoded_value types in encoded_static_values.
- MiniAndroid now: payload walked past CORRECTLY (no desync — the stream
  law holds), values surfaced in EncodedValue (float_bits / index_val),
  but FieldInfo has no float/index default storage.
- Impact: LOW (annotation-style defaults; no known MiniAndroid corpus APK
  exercises them).
- Proposed transfer: extend FieldInfo default union when a corpus APK
  demands it.
- Integration status: **researched**

## FIND-REUSE-DEX-005 — structural validation baseline (comparison)
- Source: DexOffsets.java / DexReader header checks (DEX @1616ed0c):
  magic/version gating (035..041, CompactDex 001, legacy 009/013),
  header size per version, ENDIAN_TAG, file-size vs buffer, map_list
  cross-checks in full verifiers.
- MiniAndroid: magic 035–039 accepted (dex_parser.cpp:133-138), endian
  tag checked (:157), file_size >= header_size (:163-170), checksum
  verified as WARNING (not fatal).
- Mismatch: none blocking — MiniAndroid's baseline covers classic APKs;
  040/041/CompactDex remain OUT OF SCOPE (recorded, not a gap for the
  current fixture set).
- Integration status: **observed**

---

## FIND-REUSE-ART-001 — class initialization on first ACTIVE use
- Source: dexHunter art/runtime/class_linker.cc EnsureInitialized /
  InitializeClass chain (@9d829a9f).
- Law: <clinit> runs on first ACTIVE USE (new-instance, sget/sput static,
  invoke-static), not at class-load; re-entrant initialization is a no-op;
  framework/stub classes may be pre-marked initialized.
- MiniAndroid: `ensure_class_initialized` (dalvik_engine.cpp:1666)
  implements EXACTLY this law (sget/sput + new-instance triggers,
  initialized-before-<clinit> re-entrancy guard, framework namespace skip,
  DEMO-CLINIT runtime evidence 2026-09-04).
- Impact: CONFIRMED alignment (no change needed).
- Integration status: **implemented** (pre-existing, law confirmed by
  this audit)

## FIND-REUSE-ART-002 — superclass-first class initialization (JLS 12.4.2)
- Source: class_linker.cc:3823-3830 (@9d829a9f): "Initialize super
  classes, must be done while initializing for the JLS" —
  InitializeClass resolves and initializes the superclass BEFORE the
  class's own <clinit> (CanWeInitializeClass walks the super chain).
- MiniAndroid: `ensure_class_initialized` marks the class initialized and
  runs its <clinit> WITHOUT first initializing the superclass chain.
- Mismatch: a subclass <clinit> reading inherited static state set by a
  superclass <clinit> would observe stale values.
- Impact: MED (rare pattern: static state in hierarchy roots consumed by
  subclass initializers).
- Proposed transfer: before running <clinit>, recursively ensure the
  superclass is initialized (bounded by the existing re-entrancy guard).
- Test suggestion: synthetic two-class DEX (super sets static, sub reads
  it in <clinit>).
- Integration status: **researched** (gap recorded; NOT yet fixed — no
  runtime evidence of breakage in the corpus, fix queued behind evidence)

## FIND-REUSE-ART-003 — class status state machine (lazy resolution)
- Source: mirror/class.h:83-120 (@9d829a9f): kStatusNotReady→Idx→Loaded
  (super/interfaces idx resolved LAZILY, cycle-tolerant — "Java allows
  circularities of the form where a super class has a field that is of
  the type of the sub class")→Resolved→Verified→Initializing→Initialized.
- Law: index-population and type resolution are DISTINCT stages;
  superclass/interface resolution must tolerate cycles.
- MiniAndroid: class injection resolves eagerly at load
  (inject_secondary_dex_classes etc.); no status machine.
- Relevance: LOW-MED for current corpus (single-DEX, acyclic app graphs
  so far); the cycle-tolerance law matters for self-referential class
  graphs — the interpreter's on-demand resolution already tolerates
  forward references in practice (EXT-01 Telegram-era evidence).
- Proposed transfer: none now; record the law for multi-DEX class-cycle
  debugging (FIND-REUSE-ART-003 stays a reference).
- Integration status: **researched**

## FIND-REUSE-ART-004 — DEX open invariants (checksum/signature leniency)
- Source: dex_file.cc / dex_file_verifier.cc chain (@9d829a9f): Open
  verifies magic + (for file-backed, verify mode) checksum & signature;
  verification failures degrade, not crash.
- MiniAndroid: checksum verified as WARNING (dex_parser.cpp:100-101) —
  matches the leniency law for the interpreter path.
- Impact: alignment confirmed; no change.
- Integration status: **observed**

---

## Remaining research (bounded, not derailing)
- FIND-REUSE-DEX-004 default-value storage extension (corpus-demand-gated).
- FIND-REUSE-ART-002 super-first init (fix + synthetic DEX test when a
  corpus APK exercises the pattern).
- CompactDex / DEX 040-041 container support: out of scope for the
  current fixture set.
