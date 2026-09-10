# ROOT LAW GLOBAL AUDIT (MASTER-6 → MASTER CAMPAIGN 4 update)

**Campaign:** MASTER CAMPAIGN 4 — global root closure + impact audit +
GitHub/release synchronization
**Baseline HEAD:** `5a139afd` (verified; remote `8cb8851e` — the campaign
opened with the repo 1 artifacts-commit ahead; F-044/F-045 landed during
the campaign, commit pending at doc time)
**This document:** every root family from the MASTER-3/4 campaign briefs
and the forensic report, reconciled against the live tree, with status
vocabulary per §10 (`RESEARCHED … REJECTED_CLAIM`).

Evidence precedence: `LIVE EVIDENCE > LOCAL CODE > UPSTREAM SOURCE >
FORENSIC REPORT CLAIM`.

---

## Status ledger (this session)

| ID | ROOT | FAMILY | UPSTREAM SOURCE | CURRENT MINIANDROID STATUS | ALREADY FIXED? | LIVE EVIDENCE? | MICRO-PROOF? | REAL APK PROOF? | LOADING | DEX | RESOURCE | FRAMEWORK | UI | COMPOSE | REAL-APK COMPAT | COST | PRIORITY | CONFIDENCE | NEXT ACTION | COMMIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F-028 | untyped-register raw-bits reinterpretation (const/high16 float keys, conv/cmp/arith sites) | A/C | Dalvik bytecode spec (untyped registers); ART raw slots | REGRESSION-VERIFIED (M4) | YES (M4) | YES (dooz Material3 ISE gone) | YES (f028_float_law 7 bands) | YES (dooz past fontScale ISE) | 2 | 5 | 0 | 2 | 3 | 3 | 5 | M | P0 | 5 | keep protected | 8de5382b |
| F-028h | AtomicReferenceArray family (bounds, volatile access, identity CAS) | D | AOSP ojluni AtomicReferenceArray; OpenJDK VarHandle | REGRESSION-VERIFIED (M4) | YES (M4) | YES (dooz Segment livelock gone) | YES (f030 bands L1/L5/L6) | YES (dooz scheduler) | 1 | 3 | 0 | 2 | 2 | 4 | 4 | M | P0 | 5 | keep protected | 8de5382b |
| F-029 | reflection core (getDeclaredMethod/Method.invoke/Constructor.newInstance → real DEX) | H | AOSP libcore reflection | REGRESSION-VERIFIED (M4) | YES (M4) | YES (dooz HandlerCompat chain) | via battery (microtimer Room path guard) | YES | 1 | 2 | 0 | 4 | 3 | 4 | 4 | M | P0 | 5 | keep protected; hidden gaps listed below | 8de5382b |
| F-030 | zero-is-null-at-reference-USE (const/4 #0 → null for reference-typed params) | A/C | ART verifier Zero reg-type | REGRESSION-VERIFIED (M5) | YES (M5) | YES (dooz scheduler CAS spin gone) | YES (f030_zero_law 7 bands) | YES | 1 | 5 | 0 | 2 | 2 | 4 | 4 | M | P0 | 5 | keep protected | 3ed13292 |
| F-031 | View.mContext capture (dead <init> handler shadowed the live one) | I | AOSP View(Context) | REGRESSION-VERIFIED (M5) | YES (M5) | YES (dooz getContext chain) | via battery | YES | 1 | 1 | 0 | 4 | 3 | 3 | 4 | S | P1 | 5 | keep protected | 3ed13292 |
| F-032/F-033 | Context.getSystemService service registry + Class-based overload | J | AOSP Context/SystemServiceRegistry | REGRESSION-VERIFIED (M5) | YES (M5) | YES | via battery | YES | 1 | 0 | 0 | 5 | 3 | 4 | 4 | S | P1 | 5 | extend per demand (matrix below) | 3ed13292 |
| F-035/F-035b | 23x int-shift opcodes (shl/shr/ushr-int 23x missing → stale register); Integer.numberOfLeadingZeros destructive pre-loop | A/V | Dalvik 23x formats; OpenJDK Integer | REGRESSION-VERIFIED (M5) | YES (M5) | YES (dooz AIOOBE gone) | via battery goldens | YES | 1 | 5 | 0 | 1 | 1 | 3 | 4 | S | P0 | 5 | keep protected | b1cef9e6 |
| F-036/F-039 | Arrays.asList product + List iterator law; Collections singleton/empty/unmodifiable | G | OpenJDK Arrays/Collections; Kotlin collections | REGRESSION-VERIFIED (M5) | YES (M5) | YES (MainDispatcherLoader ISE gone) | via battery goldens | YES | 1 | 2 | 0 | 2 | 1 | 4 | 4 | M | P1 | 5 | keep protected | 6d88661a |
| **F-040** | **java.util.Arrays.fill family (all primitives + Object, 2-arg and 4-arg range)** | G/V | OpenJDK ojluni Arrays.java fill/rangeCheck | **IMPLEMENTED + REGRESSION-VERIFIED (M6)** | **YES (M6)** | **YES — the dooz Lh/u;.a scatter-map spin eliminated (rc 124→1)** | **YES — f040_arrays_fill 7 bands GREEN, 3-run byte-identical** | **YES (dooz dependency-table insert now commits)** | 1 | 3 | 0 | 1 | 1 | 5 | 4 | S | P0 | 5 | keep protected | (this session) |
| **F-041** | **encoded_catch_handler negative-size law: negative sleb size ⇒ \|size\| typed pairs + catch-all (was `-(size+1)`)** | X | DEX format spec encoded_catch_handler | **IMPLEMENTED + REGRESSION-VERIFIED (M6)** | **YES (M6)** | **YES — typed catch (IAE) now resolves to the real handler address** | **YES — f040 band L2 (rangeCheck IAE/AIOOBE caught correctly)** | **YES — every typed+catch-all handler entry in real R8/ECJ DEX** | 1 | 5 | 0 | 1 | 1 | 3 | 5 | S | P0 | 5 | keep protected | (this session) |
| **F-042** | **VALUE_LONG static-default law: encoded long defaults keep full 64 bits; materialize INT64 for `J` descriptors** | B/C | DEX encoded_value; AOSP ValueCoder | **IMPLEMENTED + REGRESSION-VERIFIED (M6)** | **YES (M6)** | **YES — dooz-shape EMPTY marker 0x8080808080808080 round-trips** | **YES — f040 bands L1/L7** | YES | 1 | 4 | 0 | 1 | 1 | 4 | 4 | S | P0 | 5 | keep protected | (this session) |
| **F-043** | **java.lang.Double/Float IEEE bit-conversion family (doubleTo(Raw)LongBits, longBitsToDouble, floatTo(Raw)IntBits, intBitsToFloat; NaN canonicalization)** | V | OpenJDK Double.java/Float.java | **IMPLEMENTED + REGRESSION-VERIFIED (M6)** | **YES (M6)** | YES | **YES — f040 band L6 (bits round-trip 0x4018000000000000)** | YES | 0 | 2 | 0 | 1 | 1 | 3 | 3 | S | P1 | 5 | keep protected | (this session) |
| **F-044** | **Per-frame return-descriptor law: `current_method_descriptor_` was set at frame entry but never saved/restored across recursive frames — a caller whose last callee returned boolean executed `return vAA` under the CALLEE's ")Z" descriptor and every int return collapsed to BOOLEAN(0/1)** | A/C/X | Dalvik return model (return opcode + method's own descriptor define interpretation); ART interpreted returns | **IMPLEMENTED + REGRESSION-VERIFIED (CAMPAIGN-4)** | **YES (C4)** | **YES — dooz version hash 6729 returned as BOOLEAN(1) (probe + register-file dump); post-fix rc 1→0, app-boundary NPE eliminated, onAttachedToWindow runs to its last instruction** | **YES — f044_return_descriptor_law 7 bands GREEN, 3-run byte-identical (32b8a456…)** | **YES (dooz 3-run deterministic at the fixed tree)** | 1 | 5 | 0 | 2 | 2 | 5 | 5 | S | P0 | 5 | keep protected | (C4 commit) |
| **F-045** | **System.identityHashCode(Object): was a silent REC-MISS → 0 for EVERY object; implemented per OpenJDK System.java (lifetime-stable identity hash, 0 for null; engine: Fibonacci-mixed heap id)** | V/D | OpenJDK ojluni System.java; identity (not equals) law | **IMPLEMENTED (CAMPAIGN-4)** | **YES (C4)** | YES (reached in the dooz version scan) | via f044 fixture arithmetic bands | YES (dooz) | 0 | 2 | 0 | 1 | 1 | 3 | 3 | S | P1 | 5 | add a dedicated fixture band on next battery pass | (C4 commit) |

---

## Family-by-family reconciliation

### ROOT FAMILY A — DEX / Dalvik semantic laws — `LOCAL_VERIFIED` (partial, see gaps)

Constant family (const/4 /16 /high16, const-wide family): implemented; F-028
covered the float-bit reinterpretation sites; F-042 now guarantees
VALUE_LONG static defaults keep 64 bits. Zero/polymorphic zero: F-030.
Move family (move/move-object/move-wide/move-result*): exercised by every
battery stage — `LOCAL_VERIFIED`. Invoke argument typing + proto-guided
conversion: F-030/CYCLE-E; `LOCAL_VERIFIED`. Arithmetic (int/long/float/
double), shifts incl. shift-distance masking, not-int/not-long, cmp family,
if-* typing, reference identity (if-eq/if-ne): exercised across battery
stages + this session's SWAR probe loop (ushr-long/2addr with overlapping
wide pairs, shl-long cross-chunk stitch, neg-long, mul-long broadcast,
cmp-long) — the dooz scatter-map scan executes these correctly post-M6.
Boxing/unboxing boundaries: exercised (Integer.valueOf CAS band f030 L5).

**Gaps (RESEARCHED, not yet runtime-reached):** rem-int/long (mod), div
overflow edge (Long.MIN_VALUE/-1), packed-switch/sparse-switch payload edge
shapes, double-to-long saturation at extremes beyond fixture coverage.
Classification: CONDITIONAL — implement when a real APK trace reaches them.

### ROOT FAMILY B — DEX loading / verifier / resolver — `LOCAL_VERIFIED` (partial)

class_def/class_data delta chains (direct+virtual lists with **per-list
index accumulators** — re-verified this session against the dooz class_data),
proto/shorty parsing, type descriptors, class/method/field resolution,
multi-dex enumeration: exercised by the 16-APK corpus. ULEB128/MUTF-8:
battery stages. Malformed-DEX bounds laws: parser-level hardening present
(§N security laws of the report are implemented as bound checks in
dex_parser.cpp).

**Gaps:** annotations beyond static-value arrays, default-interface methods
in resolution corners, circular class-init ordering beyond the cycle guard
(F-017b). CONDITIONAL.

### ROOT FAMILY C — Tagged-value / type-boundary semantics — `LOCAL_VERIFIED` (strong after M6)

The F-030/F-028/F-042 chain closed three boundary defects: produce-side
(const/4 zero), storage-side (VALUE_LONG defaults), convert-side (raw-bits
reinterpretation). This session's scatter-map investigation re-proved the
full chain: bits → tagged DalvikValue → register → invoke arg (wide pair) →
array element → comparison. Remaining boundary: **derive the semantic type
from the CONSUMING descriptor at every iget/iput/aget/aput site** — currently
descriptor-guided for invokes (F-030) and static defaults (F-042); array
element loads already carry tags from stores. P2.

### ROOT FAMILY D — Atomic / lock-free — `REGRESSION-VERIFIED`

AtomicReference/Integer/Long/ReferenceArray + Atomic*FieldUpdater (F-028d)
+ identity-CAS law preserved (F-030 band L5 guards the "do not weaken
identity" rule). Null identity, bounds exceptions: f030 bands. Volatile
visibility: single-threaded engine — publication ordering preserved within
the logical executor (report §K1 law). `NOT_RELEVANT` for weakCompareAndSet
spurious-failure semantics (single logical thread). Closed for current
corpus.

### ROOT FAMILY E — kotlinx.coroutines — `LOCAL_VERIFIED` (partial)

Segment/SegmentedQueue CAS (F-028h+F-030), LockFreeTaskQueue reserve/publish
(f030 L6), EventLoop/dispatcher machinery constructs (MainDispatcherLoader —
F-036/F-039), HandlerCompat.createAsync (F-029a), executor drain law
(F-025). **Open:** delayed-task dispatch through the AndroidUiDispatcher/
MonotonicFrameClock chain (the dooz withFrameNanos path) — this is the
scheduler-pump battle from M4, still `PENDING` and now behind the F-044
observation law below. LockSupport/virtual time: architecture choice,
documented, not an Android law (report §15 caveat honored).

### ROOT FAMILY F — Kotlin runtime / Intrinsics — `LOCAL_VERIFIED`

checkNotNull/areEqual (LM1/i — disassembled this session as ground truth),
parameter checks, Unit/Result. The Intrinsics-exception rule is honored:
every Intrinsics NPE is traced to its upstream null producer (this session:
both hits were upstream defects, not Intrinsics itself).

### ROOT FAMILY G — Collections — `REGRESSION-VERIFIED` (M5/M6)

Arrays.asList/iterator (F-036), singleton/empty/unmodifiable (F-039), and
now **Arrays.fill (F-040)**. HashMap identity handling present (EXP071
dispatch); MapBuilder-marker semantics: the dooz `Lh/u` scatter-map is APP
DEX executed by the interpreter — no engine-side map semantics needed once
F-040/F-042 made the metadata init work (the `Lh/r.c` insert commit path
executes correctly: tag byte written at slot + sentinel mirror, elements[]
store, hashes[] store). `Lh/r.c` dispatch question from the campaign brief:
RESOLVED — it dispatches; the spin was the missing EMPTY fill upstream.

### ROOT FAMILY H — Reflection — `REGRESSION-VERIFIED` (M4)

Core family implemented; Room/Constructor regression reconciled. Hidden
gaps (`RESEARCHED`): getDeclaredFields/inherited-member walk, generic
exception wrapping fidelity, synthetic/bridge method visibility. CONDITIONAL.

### ROOT FAMILY I — View object model — `REGRESSION-VERIFIED` (M5 core)

View(Context) chain (F-031), parent links (F-023 law set), view-tree tags
(this session: keyed tag store verified end-to-end — setTag(key,value) from
ComponentActivity.i, parent-walk getTag(key) hits with OBJECT identity
preserved). Measure/layout/draw pipeline: exercised by fixtures (G04/G06).

### ROOT FAMILY J — Context/service registry — `REGRESSION-VERIFIED` (M5) + `RESEARCHED` extensions

ACCESSIBILITY_SERVICE + Class-based overload landed. **Missing entries
(Radar, P2):** INPUT_METHOD_SERVICE, LAYOUT_INFLATER_SERVICE, WINDOW_SERVICE,
NOTIFICATION_SERVICE, CLIPBOARD_SERVICE, DISPLAY_SERVICE — implement
on-demand with the AOSP registry as source; no fabricated managers (§7).

### ROOT FAMILY K — Activity/lifecycle — `REGRESSION-VERIFIED`

G07 lifecycle golden: onCreate→onStart→onResume ordering, attach/content
linking (F-023), Intent extras via Bundle heap store (EXP093). The campaign
brief's warning honored: setContentView is NOT a lifecycle event — it is a
View-tree operation inside onCreate (verified in trace).

### ROOT FAMILY L — Intent/PackageManager — `LOCAL_VERIFIED` (partial)

Explicit intents + component identity + extras: corpus-proven. IntentFilter
matching (action/category/data/MIME): `RESEARCHED` — the report's warning
against a simplistic intersection is acknowledged; no live evidence yet.
P2.

### ROOT FAMILY M — Handler/Looper/Message — `REGRESSION-VERIFIED` (core)

createAsync (F-029a), main-Looper identity, virtual clock single-owner
(session 11 audit), postDelayed + virtual-time fast-forward (ChessClock
cross-APK proof). Delayed dispatch ordering: GATE-proven. removeCallbacks:
`RESEARCHED` P3.

### ROOT FAMILY N — PendingIntent/AlarmManager — `REGRESSION-VERIFIED` (F-018)

AMS IntentSenderRecord identity cache, cancel, setExact* boundaries,
canScheduleExactAlarms manifest law. No duplication in M6.

### ROOT FAMILY O — Resources/ARSC — `LOCAL_VERIFIED` (partial)

ARSC parser + canonical drawable resolver (density approximation) +
string pools. Qualifier/config selection beyond density: `RESEARCHED` P2.
aapt2-built fixtures remain the authority (no handwritten ARSC/AXML).

### ROOT FAMILY P — AXML/Manifest — `REGRESSION-VERIFIED` (core)

Manifest package/activities/permissions/exported parsing feeds
PackageManager + F-018. Typed values + resource references in AXML:
corpus-proven. Overlay/inheritance: `NOT_RELEVANT` yet.

### ROOT FAMILY Q — Layout/Measure — `LOCAL_VERIFIED` (partial)

MeasureSpec EXACTLY/AT_MOST/UNSPECIFIED + weight semantics: m3_style_weight
fixture + G04 density matrix. **Radar (campaign brief): weight/measure
edge semantics remain a known P2 radar item** — quantify when a real APK
with LinearLayout weights renders.

### ROOT FAMILY R — Canvas/rendering — `REGRESSION-VERIFIED` (core)

Software renderer + pixel goldens (7 fixtures) + 3-run determinism law.
PNG palette/alpha: libpng path. `RESEARCHED`: drawBitmap density, save/clip
corner cases. P2.

### ROOT FAMILY S — Text/fonts — `LOCAL_VERIFIED` (partial)

FreeType/HarfBuzz/FriBidi wired into the shaper; text measurement used by
TextView fixtures. Emoji fallback: `NOT_RELEVANT` (no corpus demand).
Line-breaking: `RESEARCHED` P3.

### ROOT FAMILY T — Compose — `LIVE_REPRODUCED` → `FRONTIER ADVANCED (CAMPAIGN-4)`

Campaign-4 resolution of the M6 "F-044 candidate": the DEX ground truth of
dooz's Compose proved the live blocker was NOT the observer-scope pairing
(the read observer and scope-entry calls all execute as DEX) — it was the
**per-frame return-descriptor law violation (F-044)**: the derived-state
version hash (LF/F$a.d, 6729) returned as BOOLEAN(1) because the stale
`current_method_descriptor_` let the CHAR-PROBE retyping fire under the
last callee's ")Z". The dependency-change compare therefore matched
forever, the derived record was permanently stale,
`getViewTreeOwners()` read the pre-write null, and the Intrinsics
checkNotNull NPE crossed the app boundary. F-044 (descriptor
save/restore) + F-045 (identityHashCode law) fixed the family generically:
dooz now runs `onAttachedToWindow` to its LAST DEX instruction, rc 1→0,
AndroidUiDispatcher + J$c runnables + frame-clock context chain execute,
3-run deterministic. **Remaining frontier (PENDING, next battle): the
first-frame pipeline — Recomposer frame → measure/layout/draw through the
AndroidUiDispatcher/MonotonicFrameClock delayed dispatch (the scheduler
pump, root-located per M4/M5 notes; the framebuffer is honestly still
blank — no visual claim).**

Report-claim reconciliation: the forensic report's "Snapshot readError
sequencing" frontier is `REJECTED_CLAIM` for the current tree — readError
was eliminated by M4/M5 fixes (fontScale/Zero/atomics), and the live
readError site no longer throws. The report's underlying knowledge
(snapshot IDs/records/visibility) remains valid radar for F-044.

### ROOT FAMILY U — SnapshotIdSet / bitset algorithms — `LOCAL_VERIFIED`

Long-window SWAR math (broadcast 0x0101..01, zero-byte detect, 0x80..80
mask, trailing-zero iteration, `w & (~w << 6) & 0x8080..80` EMPTY probe
test) — all executed correctly by the engine per this session's live
scatter-map trace after F-040/F-042. F-035's lesson (wrong shift corrupts
the algorithm) re-confirmed as a law.

### ROOT FAMILY V — Math/primitive library — `LOCAL_VERIFIED` (partial)

numberOfLeading/TrailingZeros (F-035b + the numberOfTrailingZeros long
call in the live probe loop), Math.min (dooz LF/F$b;.o), abs/max. F-043
adds the Double/Float bits family. floor/ceil/rotations: `NOT_RELEVANT`
(no live demand). Implement on trace evidence only.

### ROOT FAMILY W — Arrays/primitive arrays — `REGRESSION-VERIFIED` (core)

new-array/aget*/aput* (EXP-071 read-all-types law, OOB synthetic-exception
law), filled-new-array, array-length nibble law (DEMO-ARRLEN). F-040 adds
bulk fill. Evaluation-order folklore: honored (report §15 — DEX registers
already hold evaluated values).

### ROOT FAMILY X — Exceptions/control flow — `REGRESSION-VERIFIED` (M6)

throw/catch/catch-all/finally + F-016 honesty protocol. **F-041 fixed the
typed+catch-all handler-entry decode** — a defect class that hit EVERY
negative-size handler entry (the common R8 shape). The fixture's
from>to→IAE and to>len→AIOOBE now dispatch through the exact typed
handlers. monitor-enter/exit: single-threaded no-op + boundary logging.

### ROOT FAMILY Y — SQLite/Room/storage — `REGRESSION-VERIFIED` (M3/M5)

F-012 persistence protocol, F-017 locks shadow, F-026 rawQuery + contentEquals,
F-018 PendingIntent chain, hermetic data-root law. Room @Update/@Delete:
`DETECTED_NOT_EXERCISED` (unchanged).

### ROOT FAMILY Z — JNI/native/ELF — `RESEARCHED` (unchanged)

jni_bridge.h boundary classification stands. No corpus APK currently
demands ELF loading. Classification law preserved: missing native library
is NEVER reported as a Java API blocker. P2/P3.

---

## Forensic report claim reconciliation (§15 duty)

| Report claim | Verdict |
|---|---|
| "Current public main is 61fd7f1" | WAS TRUE for the remote at session start; 18 local commits were unpushed — **all pushed this session** (publish debt cleared) |
| "DOOZ current frontier = Compose SnapshotKt.readError" | **STALE** — eliminated by F-028/F-030 in M4/M5; live frontier at session start = `Lh/u;.a` scatter-map probe spin (now ALSO eliminated by F-040/F-042) |
| "Recommended next step: implement Compose Snapshot v0 micro-proof" | **REJECTED_CLAIM as stated** — the readError sequencing law was not the blocker; the report's snapshot knowledge remains radar for F-044 |
| AtomicReferenceArray acquire/release wording | Report's caution honored; identity-CAS law intact (F-030 L5) |
| "Java FP conversion is specified, not C-style" | Confirmed by F-028 (raw-bits reinterpretation, not numeric conversion) |
| IntentFilter ≠ simplistic intersection | Acknowledged; no live evidence yet (P2) |
| LockSupport/virtual time = architecture choice | Honored (Family E) |
| Intrinsics exception type per compiler version | Honored (Family F) |
| filled-new-array ≠ Java expression evaluation order | Honored (Family W) |

---

## Push/commit evidence

- Session start: remote main = `61fd7f1` (report's claim verified), local
  HEAD = `d358a0c9` → **18 unpushed commits pushed at session start**
  (`61fd7f17..d358a0c9 main -> main`, exit 0, `ls-remote` verified).
- M6 law commits: see the ledger above and the worklog (§ commit hashes).
