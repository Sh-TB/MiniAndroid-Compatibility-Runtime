# MiniAndroid Compatibility Reference Matrix

Session: Cycle E / full compatibility audit (2026-09-05, HEAD b7fb5a67 lineage).

Method note (§20/§31/§42): every row below records what was ACTUALLY studied
this session — fetched source/README at the commit SHA or branch named — vs.
what is merely KNOWN. Claims are classified
`FETCHED_README` (source/README pulled and read this session),
`PARTIAL` (repo located, content not fetched),
`NOT_LOCATED` (search performed, no matching project found),
`DERIVED` (knowledge from MiniAndroid's own prior verified work / AOSP
specifications, not from a fresh fetch).
No claim from any reference is treated as proof of MiniAndroid compatibility;
references are engineering oracles only. Licenses were checked before any
adaptation decision; MiniAndroid is MIT and imports NO GPL code.

## Matrix

| PROJECT | SUBSYSTEM | OBSERVATION (what was studied) | MINIANDROID GAP | POSSIBLE ADAPTATION | LICENSE | IMPLEMENTED? | TEST | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|
| REAndroid/ARSCLib (branch main, README) | resources.arsc + binary XML | AOSP `androidfw/ResourceTypes.h`-derived Java library replacing aapt/aapt2; read/write/modify arsc + binary XML; JSON conversion explicitly designed for OBFUSCATED resources | MiniAndroid's ArscParser is read-only, default-config-first, and has no writer; obfuscated trees handled value-first (FIX-013-04) but sparse type chunks only partially covered | Differential oracle: run ARSCLib-decoded entry tables vs. `ArscParser::resolve/list_type` on the same APKs (gmdice, chessclock, Telegram) and diff name/value maps; adapt SPARSE type-chunk decoding | Apache-2.0 (per repo README) — adaptable with attribution | Partial (Cycle D ARSC parser; sparse-chunk path not differential-tested) | candidate: ARSC differential test (blocked: Java runner not in CI sandbox) | fetched README 200; MiniAndroid ARSC evidence: `[ARSC-VALUES] strings=38 colors=8` on chessclock | ADAPTABLE (differential test first) |
| auxten/libarsc (branch master, README) | resources.arsc (C++) | Pure C++ parser "transplanted from aapt", mutexes removed, single-binary use | MiniAndroid already has a zero-dependency C++ ARSC parser (UNIFIED_007/Cycle D) | Reference only — validate our struct offsets/decoding laws against its aapt-derived field names; no code import needed (duplicate dependency) | Apache-2.0 (aapt-derived) | No (superseded by our own parser) | n/a | fetched README 200 | NOT APPLICABLE (reference only) |
| v3l0c1r4pt0r/libarsc (branch master) | resources.arsc (Python) | Located via search; README fetch returned 404 this session | same as above | same | unverified (not fetched) | No | n/a | search hit only | PARTIAL (not studied) |
| fatalSec/DaliVM (branch main, README) | Dalvik emulation | Python Dalvik VM emulator for static analysis/string decryption; advertises 127+ opcodes incl. arithmetic/control-flow/arrays; targeted-method execution with `--limit`; primitive TYPE-descriptor table (`Integer.TYPE` …) | MiniAndroid opcode coverage is corpus-driven; no opcode GAP TABLE exists as a repo artifact | Build the §23 opcode gap table: enumerate MiniAndroid's implemented opcodes from `dalvik_engine.cpp` dispatch, diff against the Dalvik spec set, and generate a matrix doc + fixture list; DaliVM's targeted-method-with-limit pattern is adaptable to MiniAndroid's `try_recursive_invoke` harness | license field not present in fetched README — treat as REFERENCE ONLY (no import without verification) | No (gap table not yet generated) | candidate: opcode coverage matrix generator | fetched README 200 (127+ opcode claim is the AUTHOR'S claim, not verified line-by-line this session) | ADAPTABLE (methodology) |
| vimalloc/dexterpreter (branch master, README) | Dalvik opcode semantics | "A Dalvik bytecode (.dex) interpreter" — differential opcode reference for §27 | unknown opcodes fall through MiniAndroid's dispatch with only some emitting diagnostics | Per-opcode differential: for each corpus-exercised opcode, compare MiniAndroid register outcome vs dexterpreter's on synthetic bytecode | license not in fetched README — REFERENCE ONLY | No | folded into the opcode gap table above | fetched README 200 | ADAPTABLE (differential reference) |
| skylot/jadx (branch master, README) | Reverse-engineering oracle | Decompiles APK → Java; resolves classes/methods/resources/strings/refs; the §25 oracle for independent expectations | MiniAndroid has no independent expectation generator for real-APK behavior | Use jadx output to generate EXPECTED view trees/strings/resources for selected corpus apps, then diff against runtime ViewNode dumps. LICENSE BAR: jadx is GPL-3.0 — ZERO code import; oracle use only (run as external tool, compare outputs) | GPL-3.0 — ORACLE ONLY, no import | No (used ad-hoc this session: manual DEX decode of gmdice DSADiceSet) | candidate: jadx-vs-runtime ViewTree diff for gmdice/unote | fetched README 200; manual decode performed for the gmdice dialog finding | ORACLE (never import) |
| ryo100794/skydnir (branch main, README) | Runtime methodology | "Zero-kernel userspace runtime for mobile devices"; explicitly NOT a Docker product; exposes Docker-Engine-API-shaped workflows (`skydnird`), Compose/Dockerfile controls, "no-PRoot Android direct executor" | MiniAndroid's test gates are ad-hoc scripts; release gates exist (release-content gate) but no unified "reproducible test gate" doc | Adopt the METHODOLOGY pattern (§26): explicit compatibility boundaries per subsystem + machine-readable gate results; do NOT import Docker functionality (no corpus evidence justifying it) | license not confirmed from fetched head — reference only | Partial (validate_cycle_e.sh + validate_demo_proof.sh follow the gate pattern) | validate_cycle_e.sh (ALL PASS), demo VALIDATION_PASS | fetched README 200 | ARCHITECTURALLY INSPIRING (methodology only) |
| mirzachi/android-rro (branch main, README) | Runtime Resource Overlay internals | Diagrams/resources explaining the RRO mechanism | MiniAndroid has NO overlay concept; single-package ARSC resolution only | Future: overlay resolution precedence (idmap) if corpus evidence demands (none yet) | unverified (docs repo) | No | none | fetched README 200 | NOT APPLICABLE YET (no corpus demand) |
| MartinStyk/Android-RRO (branch master, README) | RRO sample | Sample app + runtime resource overlay for Android 31: standard app's resources changed by a separate elevated RRO APK | same | same | unverified | No | none | fetched README 200 | NOT APPLICABLE YET |
| Winedroid (owner-required §20 study) | Android-on-Windows runtime | REQUIRED deep study. GitHub search performed this session: candidates found (`aleste/winedroid` "Phonegap app test", `Terwine9090/Winedroid`, `Winedroid/Winedroid`) do NOT match the described architecture (APK loading + Android API interception on Wine). No matching repository located from this sandbox | unknown — cannot classify without source | NONE until located. RE-REQUEST from owner: exact repository URL (or mirror) so the §20 study can be executed honestly | unknown | No | none | searches logged 2026-09-05 | BLOCKED (source not located — no fabrication) |
| WinDroid | ambiguous | Multiple unrelated projects share the name; none verified against the intended one | unknown | none | unknown | No | none | not verified | BLOCKED (identity unconfirmed) |
| Droid-VM/DroidVM | VM on Android | Located by search ("Run virtual machine on Android Phones"); README not fetched (branch unknown this session) | likely orthogonal (VM-on-device, not Android-compat-on-host) | none until studied | unknown | No | none | search hit only | PARTIAL (located, not studied) |
| AndroidCSOfficial/android-code-studio | IDE for Android | Located by search ("IDE for Android to develop…"); README not fetched this session | likely orthogonal (IDE, not runtime compat) | none until studied | unknown | No | none | search hit only | PARTIAL (located, not studied) |
| AOSP Dalvik specification (dalvik-bytecode) | DEX semantics | DERIVED from MiniAndroid's own verified fixtures: 14/14 long-cmp-conv, 55/55 pass3 bridge, 25/25 switch-parse-neg, 5/5 filled-new-array, 8/8 typed-catch, 6/6 aput-bounds, 5/5 fill-array, return-wide — re-run at this session's HEAD | the §44 RESULT_001/009/010/012/013/016 families re-verified VERIFIED_FIXED this session (see worklog Task 6) | keep fixtures as the regression law | Apache-2.0 (AOSP docs/spec) | Yes (fixtures committed) | tests/semantic_*_test.cpp battery | this session's run log (all green) | DIRECTLY REUSABLE (already the law) |
| aapt/aapt2 (AOSP) | resource compilation | DERIVED: MiniAndroid fixtures use plain-text manifests + no resource compilation by design; real APKs ship binary AXML+ARSC which our parsers read | no aapt replacement needed | n/a | Apache-2.0 | n/a | fixture builds | build_fixture_apk.sh | NOT APPLICABLE |

## Session-adapted outcomes (what this study actually changed in MiniAndroid)

1. `scripts/build_fixture_apk.sh` jar-based class collection (D8 8.3.37
   rejects directories) — engineering lesson analogous to ARSCLib's
   "know the container format" discipline; discovered empirically, not
   copied.
2. Zero-skip gate pattern (`validate_cycle_e.sh` — DISCOVERED/EXECUTED/
   PASSED/FAILED/SKIPPED accounting, §39) — Skydnir-methodology-inspired.
3. ARSC-first resource values (§10 fix) — aligned with the libarsc/ARSCLib
   observation that `resources.arsc` is the single source of truth; our own
   parser, our own code (no import).
4. gmdice `DSADiceSet` decode was performed with an INDEPENDENT Python DEX
   parser written for this session (JADX-oracle methodology, no GPL code) —
   located the hardcoded 3/20 preset in the app's own `<init>`; tracked as
   a finding, not a fix.

## Re-validation queue (next sessions)

- Obtain Winedroid's real repository URL from the owner → execute the §20
  deep study honestly (architecture/APK loading/API interception/event
  handling classification: DIRECTLY REUSABLE / ADAPTABLE /
  ARCHITECTURALLY INSPIRING / NOT APPLICABLE).
- Generate the §23 opcode gap table from `dalvik_engine.cpp` dispatch vs.
  the Dalvik spec; diff-exercise corpus opcodes against dexterpreter/DaliVM
  behavior on synthetic bytecode.
- ARSC differential test: MiniAndroid ArscParser vs ARSCLib (Apache-2.0,
  adaptable) on the restored corpus (gmdice/chessclock/notes/heading).
- Telegram re-acquisition: registry pins 193ad551… (82 MB); this sandbox
  only receives a 1.2 MB stub from `telegram.org/dl/android` (hash
  mismatch — fetch tool reported and rejected it). BLOCKED on a reachable
  mirror; the v0.0.2 baseline evidence remains pinned and valid.
