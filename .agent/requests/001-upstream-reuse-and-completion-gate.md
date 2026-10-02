# CODER REQUEST 001 — UPSTREAM REUSE + MASTER COMPLETION GATE

Status: OPEN
Owner: Coder
Rule: This file is both the executable request and its mandatory completion ledger.

## 0. NON-NEGOTIABLE OPERATING RULE

The Coder MUST read this entire file before doing work.

This is NOT a documentation task.

For every numbered requirement below, the Coder must:
1. inspect the current source;
2. perform the requested work;
3. test it when applicable;
4. record a one-line result in the completion table at the end;
5. mark it DONE only when evidence exists;
6. otherwise mark BLOCKED/PARTIAL and state the exact reason and next action.

A request is NOT COMPLETE merely because code was written, a commit exists, a test exits 0, or an issue was closed.

The Coder MUST NOT report "complete" while any required row is UNCHECKED.

If a requirement is impossible because of architecture/licensing/dependency constraints, it must still be investigated and receive an explicit verdict.

The Coder must continue through all rows instead of stopping after the first successful fix.

---

# 1. LAWS / CONTEXT TO READ FIRST

Read before implementation:

- CONSTITUTION_V2.md
- current worklog.md
- .agent/mission.md
- .agent/state.md
- .agent/master_campaign_state.md
- .agent/backlog.md
- current compatibility campaign documents
- docs/FINAL_COMPATIBILITY_CAMPAIGN.md if present
- current upstream/vendor/third-party documentation

Record in the worklog:

UPSTREAM_REUSE_LAWS_READ = YES

Also record any newly discovered law.

---

# 2. PRIMARY OBJECTIVE

Reduce MiniAndroid's custom maintenance surface.

Before writing or maintaining a custom implementation, search for an existing maintained implementation from:

1. AOSP / Android Open Source Project
2. AndroidX where semantically appropriate
3. maintained open-source GitHub projects
4. established parser/runtime libraries
5. existing code already present in MiniAndroid's upstream/ or other directories

Preferred order:

AOSP SOURCE
→ maintained compatible OSS
→ adapter/port
→ MiniAndroid-specific implementation only when necessary

Do NOT blindly copy code.

Check:
- semantics
- architecture
- language/runtime compatibility
- dependencies
- CPU/headless constraints
- license
- maintenance health
- tests
- update path

---

# 3. COMPLETE UPSTREAM INVENTORY

Search the entire repository and produce:

- docs/UPSTREAM_CODE_INVENTORY.md
- docs/UPSTREAM_CODE_INVENTORY.jsonl
- docs/UPSTREAM_AVAILABLE_NOT_USED.jsonl
- docs/UPSTREAM_REPLACEMENT_PLAN.jsonl
- docs/UPSTREAM_LICENSE_MATRIX.jsonl
- docs/UPSTREAM_RUNTIME_USAGE.jsonl
- docs/UPSTREAM_UPDATE_TRACKING.jsonl

For every major subsystem identify:

- current MiniAndroid implementation
- upstream implementation
- exact repository
- exact path
- branch/tag/commit
- license
- whether already used
- whether runtime reachable
- whether duplicated/shadowed
- direct reuse possible
- port/adaptation possible
- reason if not usable
- maintenance status
- final decision

Required classifications:

UPSTREAM_USED
UPSTREAM_ADAPTED
UPSTREAM_PORTED
REFERENCE_ONLY
AVAILABLE_NOT_USED
CUSTOM_REQUIRED
ARCHITECTURE_SPECIFIC
LICENSE_BLOCKED
INCOMPATIBLE
PENDING_RESEARCH

No major custom subsystem may remain unexplained.

---

# 4. SEARCH CURRENT CODE FOR DUPLICATES

Inspect all source, especially:

- upstream/
- miniandroid/
- tools/
- scripts/
- any vendor/external/third_party directories

Find:
- duplicated parsers
- duplicated resource logic
- duplicated file/storage logic
- duplicated Java/libcore behavior
- duplicated framework behavior
- dead upstream code
- shadowed implementations
- code that exists but is never compiled/reached

For every such case determine why.

Do NOT leave an upstream implementation unused without an explicit reason.

---

# 5. RESOURCE / APK LOADING

Compare current code against:

- AOSP AssetManager
- AOSP Resources / ResourcesImpl
- AOSP Configuration / DisplayMetrics
- AOSP resource selection
- AOSP BitmapFactory
- AXML/ARSC implementations

Also investigate maintained projects such as:

- androguard/axml
- androguard/axml-parser
- libarsc
- other maintained AXML/ARSC/APK implementations discovered during research

Determine what should be reused, ported, wrapped, or retained.

Actually implement high-confidence replacements.

Then test with real APKs.

---

# 6. FILE / STORAGE / STREAMS

Audit and implement against upstream semantics:

- File
- FileInputStream
- FileOutputStream
- Context.openFileInput
- Context.openFileOutput
- fileList
- deleteFile
- AssetManager.open
- AssetManager.list
- openFd
- openRawResourceFd
- InputStream / OutputStream
- FD
- ParcelFileDescriptor
- AssetFileDescriptor
- /data/data/<pkg>
- /data/user/0/<pkg>
- external app storage
- cache
- code_cache
- no_backup
- databases
- shared_prefs

Unify path mapping.

No host absolute-path escape.

A file existing on disk is NOT proof that the Android API contract is implemented.

---

# 7. RESOURCE / IMAGE SEMANTICS

Audit and implement:

- drawable
- mipmap
- raw
- layout
- XML
- font
- color
- dimen
- string
- style
- attr
- plurals
- arrays
- integer
- bool
- configuration
- qualifiers
- density

Image APIs:

- decodeResource
- decodeFile
- decodeStream
- decodeByteArray

Every important path needs runtime proof of:

REQUEST → RESOLUTION → OPEN → READ → DECODE → OBJECT → CONSUMER → VISIBLE EFFECT

No fake-success implementation.

---

# 8. FD / PROVIDER / URI

Audit:

- ParcelFileDescriptor
- AssetFileDescriptor
- FileDescriptor
- ContentResolver
- ContentProvider
- provider installation
- android.resource://
- file://
- content://
- provider authority resolution
- AndroidX Startup providers where required

Do not replace missing provider behavior with package-specific hacks.

---

# 9. SHARED PREFERENCES / SQLITE

Audit against Android semantics:

SharedPreferences:
- get
- put
- remove
- clear
- commit
- apply
- persistence
- restart
- package isolation

SQLite:
- database location
- open/reopen
- transactions
- WAL
- cursor behavior
- persistence
- package isolation

Use upstream implementation/reference where practical.

---

# 10. JAVA / LIBCORE / RUNTIME

Search AOSP libcore and other maintained implementations for:

- java.lang
- java.io
- java.util
- java.nio
- java.text
- relevant reflection/exceptions/threading behavior

Also compare DEX support with:

- ART/libdexfile
- Dalvik/libdex
- maintained DEX libraries

Separate format/parser infrastructure from MiniAndroid-specific interpreter semantics.

Do not replace the interpreter blindly.

---

# 11. GRAPHICS / TEXT

Audit:

- Canvas
- Paint
- Bitmap
- Drawable
- BitmapFactory
- Typeface
- StaticLayout
- text measurement
- View
- SurfaceView

Compare with AOSP and suitable maintained OSS.

Keep MiniAndroid-specific rendering architecture only where necessary.

Real APK rendering must be tested after changes.

---

# 12. POSITIVE PATH — WHY WORKING APPS WORK

This requirement was previously missing and is mandatory.

For working apps/games, determine exactly:

- APK identity
- installed APK path
- actual files/assets/resources used
- loading API
- caller DEX method
- logical Android path
- physical MiniAndroid path
- decoder/consumer
- visible effect
- upstream implementation involved
- which missing compatibility features are NOT exercised
- why the app succeeds despite remaining gaps

Minimum corpus:

- OpenCalc
- uNote
- Simple Stopwatch
- FishRings
- dooz
- MicroTimer
- Chess
- other current goldens

Produce:

docs/WORKING_APP_LOADING_EXPLANATIONS.md

---

# 13. NEGATIVE PATH — WHITE / BLANK / GREY / SPLASH

For every important failure trace:

REQUEST
→ API
→ CALLER
→ logical path/resource
→ resolution
→ physical backing
→ OPEN
→ READ
→ DECODE
→ OBJECT
→ CONSUMER
→ STATE CHANGE
→ FINAL FRAME

Identify the FIRST real divergence.

Do not assume every blank screen is a file/resource bug.

Produce/update:

- docs/WHITE_SCREEN_LOADING_ROOTS.md
- docs/LOADING_FAILURE_DIAGNOSTICS.md
- docs/WORKING_VS_FAILING_LOADING_MATRIX.jsonl

---

# 14. PREVIOUSLY IDENTIFIED BACKLOG — MUST NOT BE FORGOTTEN

The current .agent/backlog.md contains:

P0:
- forensic PC trace of LaunchActivity.onCreate PC 678-730
- determine why getFragmentStack() returns null
- smallest generic root fix
- reach getClientNotActivatedFragment()
- reach LoginActivity construction
- reach addFragmentToStack()

P1:
- cross-check R class values with androguard
- implement resources.arsc parser if needed

P2:
- typed catch handler / class hierarchy walk
- exception propagation across method boundaries

P3:
- minimal Fragment lifecycle
- INavigationLayout.addFragmentToStack dispatch

These are included in this request deliberately.

Do NOT assume they are obsolete.

For each one:
- verify current state from HEAD;
- if already fixed, provide commit/evidence;
- if partially fixed, continue;
- if obsolete, explain exactly why and what superseded it;
- if still open, execute the work.

---

# 15. PREVIOUS MASTER LOADING CAMPAIGN — MUST ALSO BE CHECKED

The previously requested loading campaign required:

- complete working-vs-failing loading comparison
- installed APK proof
- canonical package path mapping
- File APIs
- streams
- AssetManager
- resource families
- image decoding including decodeStream
- FD/PFD/AFD
- write/read/restart
- package isolation
- uninstall/reinstall
- SharedPreferences
- SQLite/WAL
- external storage
- URI/ContentProvider
- AndroidX Startup provider
- native library loading
- font/audio/media loading
- duplicate/dead/shadowed implementations
- synthetic probes
- white-screen first-missing diagnostics
- 3-run regression
- source-first AOSP verification

Audit each item against current HEAD and add its result to the completion ledger.

---

# 16. PREVIOUS UPSTREAM REQUEST — MUST ALSO BE CHECKED

The earlier upstream-reuse request required:

- complete source search
- AOSP comparison
- GitHub/open-source comparison
- inspect existing upstream/
- identify available-but-unused code
- identify custom duplicates
- license check
- maintenance check
- high-fan-out prioritization
- high-confidence replacement
- positive working-app explanation
- negative failing-app explanation
- runtime reachability
- synthetic probes
- real APK tests
- screenshots
- 3-run proof
- attribution
- update strategy
- custom-code justification

Do not silently skip these because this file supersedes them.

---

# 17. HIGH-FAN-OUT PRIORITY

Fix generic roots before package-specific symptoms.

Priority:

P0:
- resource/APK loading
- File/path semantics
- streams
- AssetManager
- FD/PFD/AFD
- Context storage APIs
- resource configuration/qualifiers
- BitmapFactory/decodeStream
- URI/provider
- SharedPreferences
- SQLite
- libcore semantics

P1:
- lifecycle
- Fragment
- component resolution
- PackageManager
- Intent
- graphics/text
- native loading

P2:
- media
- advanced WebView
- secondary APIs

Do not brute-force individual applications.

---

# 18. NO PACKAGE-SPECIFIC HACKS

Every implementation must be generic.

Forbidden:

- Telegram-only branch
- game-name branch
- package-name special case
- APK-specific resource substitution
- screenshot-specific rendering
- fake success only for one title

If an existing special case is found, document and remove/replace it where safe.

---

# 19. EVIDENCE STANDARD

A successful result requires appropriate evidence.

Weak evidence alone is insufficient:

- exit code 0
- APK loaded
- DEX parsed
- PNG exists
- PIL can decode PNG
- agent says "works"
- issue label
- commit exists

For runtime claims prefer:

- runtime trace
- ViewTree/provenance
- state change
- actual consumer
- screenshot metrics
- screenshot SHA
- 3-run reproducibility
- source/upstream correspondence

---

# 20. MANDATORY COMPLETION LEDGER

After executing the work, fill every row below.

Format:

| ID | Requirement | Status | Evidence | What was actually done / why not | Commit |
|---|---|---|---|---|---|
| 001 | Read laws | | | | |
| 002 | Upstream inventory | | | | |
| 003 | Available-but-unused search | | | | |
| 004 | Duplicate custom implementation audit | | | | |
| 005 | License audit | | | | |
| 006 | Maintenance audit | | | | |
| 007 | Resource/APK audit | | | | |
| 008 | File/storage audit | | | | |
| 009 | Streams audit | | | | |
| 010 | FD/PFD/AFD audit | | | | |
| 011 | URI/provider audit | | | | |
| 012 | SharedPreferences audit | | | | |
| 013 | SQLite audit | | | | |
| 014 | Java/libcore audit | | | | |
| 015 | DEX/runtime audit | | | | |
| 016 | Graphics/text audit | | | | |
| 017 | Working-app explanations | | | | |
| 018 | White/blank/grey failure tracing | | | | |
| 019 | Previous backlog P0 | | | | |
| 020 | Previous backlog P1 | | | | |
| 021 | Previous backlog P2 | | | | |
| 022 | Previous backlog P3 | | | | |
| 023 | Previous loading campaign coverage | | | | |
| 024 | Previous upstream campaign coverage | | | | |
| 025 | High-fan-out implementation | | | | |
| 026 | Synthetic probes | | | | |
| 027 | Real APK tests | | | | |
| 028 | 3-run reproducibility | | | | |
| 029 | Corpus regression | | | | |
| 030 | Attribution / licenses / notices | | | | |
| 031 | Update strategy | | | | |
| 032 | Custom-code justification | | | | |
| 033 | Final repository synchronization | | | | |

Allowed statuses:

IMPLEMENTED
TESTED
OBSERVED
PARTIAL
BLOCKED
PENDING
SUPERSEDED

Never use DONE without one of these evidence statuses.

---

# 21. ONE-LINE VERDICT RULE

For EVERY row, the Coder must write a concise explanation.

Example:

"IMPLEMENTED — replaced custom ARSC lookup with adapted upstream parser; gmdice + OpenCalc pass; commit abc123."

or:

"PARTIAL — AOSP behavior identified and adapter written, but decodeStream still lacks FD-backed source; synthetic probe fails at OPEN; next action X."

or:

"SUPERSEDED — old Fragment task was replaced by generic lifecycle implementation in commit abc123; runtime trace proves same required path."

or:

"BLOCKED — upstream library requires unavailable native dependency; retained custom implementation and documented semantic comparison."

The phrase "checked" alone is NOT acceptable.

---

# 22. FINAL REPORT

At the end provide:

## A. What was actually changed

List commits/files.

## B. What upstream code is now used

Exact repositories and paths.

## C. What upstream code exists but remains unused

With reasons.

## D. What custom code remains

With justification.

## E. What previous requests were still incomplete

Explicit list.

## F. What remains blocked

Exact blocker and next action.

## G. Runtime evidence

Apps, traces, screenshots, hashes, 3-run results.

## H. Regression result

State which working goldens remained stable.

---

# 23. FINAL COMPLETION RULE

The Coder MUST NOT say:

"All done"
"Complete"
"Fully implemented"
"Everything fixed"

unless EVERY mandatory requirement has a ledger row and EVERY row has a non-empty Status + Evidence + Explanation.

If any row is PARTIAL/BLOCKED/PENDING:

the overall campaign status MUST remain:

CAMPAIGN_STATUS: PARTIAL

and the Coder must continue with the highest-priority remaining item if it is actionable.

---

# 24. DELIVERY

At the end:

1. update this file's completion ledger;
2. update worklog.md;
3. update relevant .agent state files;
4. commit all changes;
5. push to origin/main;
6. verify remote HEAD;
7. record final commit SHA here;
8. report the exact result.

FINAL_COMMIT:
REMOTE_HEAD:
LEDGER_COMPLETE: YES/NO
OVERALL_STATUS:
REMAINING_ITEMS:

---

# 25. FUTURE REQUEST PROTOCOL

From now on, every major Coder request must be stored under:

.agent/requests/

Each request gets a unique numbered Markdown file:

001-...
002-...
003-...

The request file is the authoritative execution contract.

When the Coder finishes a request, it MUST return to that same file and append/fill its completion ledger.

This prevents:

- forgotten requirements
- partial execution
- "done" claims after only a few fixes
- losing old requests
- repeating already-completed work
- silently abandoning blocked requirements

A future request must first inspect previous request ledgers and carry unfinished items forward.

---

# CURRENT STATE

This request intentionally combines the new upstream-reuse objective with unresolved requirements from earlier campaigns.

The Coder must treat this as a continuity contract, not a fresh isolated task.

---

# COMPLETION LEDGER (filled 2026-10-03, forensic wave, HEAD 438f8e85+fixes)

| # | Requirement | STATUS | Evidence |
|---|---|---|---|
| 1 | Laws read | DONE | CONSTITUTION_V2 (headers + evidence laws), CAMPAIGN_STATE, worklog tail, .agent/* (state.md + master_campaign_state.md recorded STALE), CODER_REQUEST_PROTOCOL |
| 2 | Upstream inventory | DONE | docs/UPSTREAM_CODE_INVENTORY.md + .jsonl (11 rows, class+call-path per row) |
| 3 | Available-but-unused search | DONE | docs/UPSTREAM_AVAILABLE_NOT_USED.jsonl (10 verdict rows incl. nanoSVG/FFmpeg/SDL2/Yoga) |
| 4 | Duplicate/custom audit | DONE | UPSTREAM_RUNTIME_USAGE.jsonl marks WIRED_NOT_CONSUMED rows (PortableGL, audio) + ADAPTED rows |
| 5 | License/attribution audit | DONE | docs/UPSTREAM_LICENSE_MATRIX.jsonl (17 rows) |
| 6 | Maintenance/update path | DONE | docs/UPSTREAM_UPDATE_TRACKING.jsonl (5 rows) |
| 7-33 | Carry-over campaign rows | SUPERSEDED->ISSUE #364 | Owner folded this request into issue #364; the 33-row ledger is posted there (comment by forensic wave 2026-10-03) |

Honest verdict: request 001 is not silently closed; its upstream half is
delivered (rows 2-6) and its completion-gate half now lives in #364's ledger.
