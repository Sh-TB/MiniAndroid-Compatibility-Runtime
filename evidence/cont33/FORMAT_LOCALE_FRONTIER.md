# CONT-33 — Format-Locale + Saveable-Whitelist Frontiers: F-NEW-291/292
# Root-Cause, Fix, Probe, and the FIRST PAINTED CONTENT for composeStopwatch

Wave: CONT-33 (user directive: ادامه). Predecessor: evidence/cont32
(DIALOG_WINDOW_FRONTIER.md, §11 pinned this wave's targets). This wave:
(1) decoded and root-caused the Lwv;.p STR-BRIDGE SIOOBE to the EXP093
String.format Locale-overload gap (F-NEW-291), (2) root-caused and fixed the
rememberSaveable canBeSaved whitelist rejection of UUID and enum values to the
libcore interface-hierarchy gap (F-NEW-292, two table rows + per-hop consult),
(3) probe-proven both roots ×3 in BOTH directions, (4) the target app moved
FAILURE → PARTIAL SUCCESS and painted its FIRST content (a rendered dialog
window), (5) full zero-drift regression gate, (6) the mangled DataStore path
root-caused (decode-only, fix deferred).

## 0. RESUMABLE STATE BLOCK

| item | value |
|---|---|
| HEAD at wave start | 758c98e3 (tmp-artifacts auto-commit) over pushed 8dcb5285 (CONT-32) |
| pre-wave binary | c280b243f880e7e6 (byte-stable == CONT-32 record) |
| post-F-NEW-291 binary | fa7dd04c99364cad |
| post-F-NEW-292 binary | **859557953a3b144c** |
| target APK | tmp/cont31_apks/composeStopwatch_1009011.apk (sha256 dbf937ebbe7c0b3d…) |
| probe | fixtures/fnew291_probe, fixtures/fnew292_probe (real aapt2/ECJ/D8, w4 script) |
| regression | run/cont33/regression + scripts/cont33_regression.sh (anchors/probes/control parts) |

## 1. THE FACE (pre-fix, binary c280b243f880e7e6, cont32 runs)

composeStopwatch post-F-NEW-290: ISE "Dialog has no window" 0 (fixed), frame
UNCHANGED 5c4a0172628849ba (DEFAULT_BACKGROUND_ONLY, Lh4; onDraw ops=0), and
the deferred faces named by CONT-32 §8:

- `[SYNTH-EXC] STR-BRIDGE (deferred): StringIndexOutOfBoundsException
  (length=0; begin=0; end=2) method=Lwv;.p pc=26 → uncaught` — propagating
  through catch-alls (Lx30;.n ×3, Lel;.j ×4, Lad0;.m, Ld91;.c ×3, Lcj0;.j0,
  Lmc0;.Y) each pass — the composition text pass churning.
- Immediately upstream in the log: `[LOCALE-CONST] synthesized Locale.US`,
  `[EXP093-STRFMT] String.format("", n=2) → ""`, `[STR] concat("", ".")`.

The app only reached this code AFTER F-NEW-290 opened the dialog path — the
CONT-31/32 pre-fix runs died earlier, which is why this face is new.

## 2. DECODE (androguard, scripts/cont33_disasm.py)

`Lwv;.p(J)Ljava/lang/String;` — regs 5, ins 2:

```
 0 sget-object Locale.US
 1-2  rem-long  v3, v3, 1000        (millis % 1000)
 3-9  Long.valueOf + filled-new-array + Arrays.copyOf(1)
10  const-string "%02d"
11  invoke-static String.format(Locale, String, Object[])   ← 3-arg overload
15  invoke-virtual substring(0, 2)                          ← SIOOBE site
```

DEX string census: `%02d`, `%02d:%02d`, `%d:%02d`, `%d:%02d:%02d` all present
(the stopwatch time-format family). `Lwv;.p` is called from `Lwv;.v(J)` and
`Lpt;.d` — the time-display pipeline.

## 3. ROOT CAUSE — F-NEW-291 (String.format Locale overload)

The EXP093 bridge (dalvik_engine.cpp:53280) read `args[0]` as the format
string unconditionally. For the DEX 3-arg Locale overload
`format(Locale, String, Object...)`:

- args[0] = Locale OBJECT_REF → not STRING_REF → `fmt = ""`
- args[1] (the real `"%02d"`) and args[2] (the array) fell into the defensive
  non-array loop → `fargs = ["%02d", array]` → the log's `n=2`
- `java_format_walk("", …)` = `""` → substring(0,2) → SIOOBE length=0

ART law: `String.format(Locale l, String format, Object... args)` formats
with args[1] as the format string and args[2] as the varargs array. The two
DEX overloads are discriminated by ARG SHAPE (the 2-arg form is
(String, Object[]) — args[1] can never be a String there), no name checks.

**Fix**: shape discriminator in EXP093 — `fmt_idx/varargs_idx` shift to
(1, 2) when `args.size() >= 3 && args[0].type != STRING_REF &&
args[1].type == STRING_REF`; the defensive loop starts at varargs_idx.
`java_format_walk` untouched — it already formats `%02d` with a boxed Long
(OBJECT_REF "value" field INT64).

## 4. PROBE F-NEW-291 — fixtures/fnew291_probe

Rows: FMT-LOC-D2 (the law: `format(Locale.US,"%02d",7L)=="07"`),
FMT-LOC-SUB (the EXACT Lwv;.p consumer shape — pre-fix this throws the
SIOOBE), FMT-LOC-2ARG, FMT-LOC-S, FMT-LOC-DINT, and the 2-arg regression arm
FMT-NOLOC-D2/ARR.

| run | binary | result |
|---|---|---|
| PRE ×3 | c280b243f880e7e6 | SUMMARY **FAIL 2 pass 5 fail** — FMT-LOC-* all FAIL (got="" / threw SIOOBE length=0), NOLOC arm PASS |
| POST ×3 | fa7dd04c99364cad | SUMMARY **PASS 7/0** — "07", "50", "01:02", "x!", "42" |

Target after F-NEW-291 ×3: SIOOBE **1→0**/run, `EXP093-STRFMT`
`format("%d", n=1) → "0"`, `format("%02d", n=1) → "00"` (was `format("",
n=2) → ""`), frame UNCHANGED 5c4a0172628849ba — divergence moved onward.

## 5. THE NEXT FACE — rememberSaveable canBeSaved (F-NEW-292)

After the format fix the run's fatal face became:

```
IAE "Ljava/util/UUID;@7220 cannot be saved using the current
SaveableStateRegistry. The default implementation only supports types which
can be stored inside the Bundle. Please consider implementing a custom Saver
for this class and pass it to rememberSaveable()." ×51/run, thrown at
Laj0;.n, caught by Lh4;.onMeasure catch-all → measure aborted → ops=0.
```

**Upstream decode** (ui-android-1.11.4 AAR extracted from
upstream/cont12_maven/raw; scripts/cont33_jvm_disasm.py — a compact JVM
bytecode walker written for this wave because androguard 4.x dropped its JVM
module): `DisposableSaveableStateRegistry_androidKt.canBeSavedToBundle` =
NOT(value is SnapshotMutableState with a rejected policy) ∧
NOT(value is kotlin.Function ∧ value is Serializable) ∧
`Class[] {Serializable, Parcelable, String, SparseArray, Binder, Size,
SizeF}.isInstance(value)` (the `<clinit>` array, decoded instruction-level).

ART truth: **java.util.UUID implements Serializable, Comparable** (libcore
luni UUID.java header) → the Serializable arm accepts it. The engine's
`dalvik_class_assignable("Ljava/util/UUID;", "Ljava/io/Serializable;")`
answered FALSE: no DEX tables (platform class), and the F-NEW-253 framework
closure had **no UUID row**.

**The enum member of the same family**: after the UUID row, the IAE
returned for `Ll71;@10174` (×26/run) — androguard: `Ll71;` is an app enum
(`extends Ljava/lang/Enum;`, no declared interfaces). The Serializable edge
lives on the PLATFORM hop `java.lang.Enum implements Comparable, Serializable`
— and the superclass walk in dalvik_class_assignable checked
`class_to_interfaces_` (DEX-only tables) at each hop, never the framework
tables, so the platform hop's edges were invisible.

## 6. FIX F-NEW-292 — minimal, generic, receiver-identity keyed

1. `framework_class_interfaces()` (view_ancestry.h): **UUID row**
   `{"Ljava/util/UUID;", {Serializable, Comparable}}` + **Enum row**
   `{"Ljava/lang/Enum;", {Serializable, Comparable}}` — libcore source law,
   the same table pattern as F-NEW-253's parcel family.
2. `dalvik_class_assignable()` superclass walk (dalvik_engine.cpp:24682):
   per-hop platform consult `framework::framework_implements(walk, to_desc)`
   after the DEX-table check — intermediate platform hops see the same
   boot-classpath truth the F-NEW-253 tail already gives to `from_desc`.

No name dispatch, no app-specific branches, no exception suppression.

## 7. PROBE F-NEW-292 — fixtures/fnew292_probe

Rows: UUID-SER (THE law), UUID-INSTOF (DEX instanceof path), UUID-CMP,
ENUM-SER + ENUM-INSTOF (Tick enum = the Ll71; shape), and the
over-acceptance guards NEG-PARCEL / NEG-STR / NEG-CHARSEQ / NEG-ENUMSTR.

| run | binary | result |
|---|---|---|
| PRE (UUID face) ×3 | fa7dd04c99364cad | SUMMARY **FAIL 3/3** — Serializable.isInstance(uuid)=false (all three edges), negatives honestly false |
| PRE (enum face) ×1 | c577629024f2a33b (UUID row only) | ENUM-SER/ENUM-INSTOF **FAIL**, UUID rows PASS — per-face isolation |
| POST ×3 | 859557953a3b144c | SUMMARY **PASS 9/0** — UUID+enum edges true, all four negatives honestly false |

## 8. TARGET AFTER BOTH FIXES — FIRST PAINTED CONTENT

composeStopwatch ×3 on 859557953a3b144c:

| run | rc | screenshot | IAE canBeSaved | SIOOBE | verdict |
|---|---|---|---|---|---|
| csw_post292b_r1 | 1 | **9afb2bd2606f303e** | **0** (was 51) | 0 | PARTIAL SUCCESS |
| csw_post292b_r2 | 1 | **9afb2bd2606f303e** | 0 | 0 | PARTIAL SUCCESS |
| csw_post292b_r3 | 1 | **9afb2bd2606f303e** | 0 | 0 | PARTIAL SUCCESS |

- Status **FAILURE → PARTIAL SUCCESS**; the log records
  `[DIALOG-RENDER] window obj=0 frame=(80,936 920x48) painted` and
  `2029440 non-white pixels` — **the app paints a rendered dialog window on
  the dark background: the first content beyond DEFAULT_BACKGROUND_ONLY in
  its entire campaign history** (byte-stable ×3, a NEW deterministic frame).
- Honest bounds: `Lh4;` (the Compose stopwatch view) still dispatches onDraw
  with **ops=0**; the dialog body is empty (items=0); no content-pixel claims
  beyond the painted window chrome. The remaining uncaught traffic is
  **F084 wall-clock budget halts** (33/34/37 per run, count varies with
  scheduling) — the app is now ALIVE enough that the 15 s harness clock cuts
  it mid-churn, plus one f141-null-recv at Lk6;.<init> pc=409 (next-wave
  candidate) and the deferred S102/R350/STREAM faces (faithful/deferred).
- The frame change is a REAL divergence movement — recorded as MOVED, with
  the new deterministic frame sha as the anchor.

## 9. DATASTORE MANGLED PATH — ROOT-CAUSED (PENDING-FIX, deferred)

`STREAM-OPEN FileNotFound: runtime/data/data/data/<pkg>/runtime/data/runtime/
data/runtime/data/data/data/<pkg>/files/datastore/preference.preferences_pb`
— the double/triple prefix mechanism decoded:

1. `Context.getFilesDir` (dalvik_engine.cpp:41856) answers
   `Storage::context_dir("files").string()` = the **HOST path**
   `<root>/runtime/data/data/data/<pkg>/files` — the host prefix leaks into
   the app-visible logical path (AOSP: the app must see
   `/data/user/0/<pkg>/files`).
2. DataStore builds `File(filesDir, "datastore/…")` → the logical path now
   carries `runtime/data/…` → `resolve_android_path` sees a relative path →
   RELATIVE_APP_DATA anchors it under `package_data_dir()` → **double
   prefix**; a second round-trip triples it.
3. The ENOENT is deferred/handled (the app tolerates it) so no fatal today.

The fix (answering virtual AOSP paths from the dir getters, or making the
resolver recognize already-virtualized paths) touches EVERY directory getter
and every app's file dispatch — a dedicated wave with its own probe:
**CONT-34 candidate**, recorded with the precise locations. NOT patched this
wave (no speculative fixes without a reproducing-probe contract).

## 10. REGRESSION GATE — ZERO DRIFT at 859557953a3b144c

scripts/cont33_regression.sh (anchors / probes / control parts):

| gate | result |
|---|---|
| anchors ×3 ×8 apps | dooz d602648e8e401895, microtimer da73010a37dd0189, unote 4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow 13cf47464d9787f4, g2048 59ca1526611c4622 — **24/24 BYTE-IDENTICAL MATCH** |
| probe battery | fcol 140/0, f259 49/0, f259g 84/7 (known-honest F259-L row), f266 42/0, f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, fnew252 56/0, fnew290 56/0 — **== CONT-28..32 records EXACTLY** |
| new probes | fnew291 **56/0**, fnew292 **70/0** |
| Track B control | Simple Calculator ×3 rc=0 `7960bce447ac6d8f` — FULL SUCCESS retained |

## 11. STATUS WORDS

- F-NEW-291: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe PRE/POST ×3
  both directions + target SIOOBE elimination ×3).
- F-NEW-292: **ROOT_CAUSED_FIXED / TESTED / OBSERVED** (probe PRE/POST ×3
  both directions + target IAE elimination ×3 + first painted content ×3 +
  zero-drift regression).
- composeStopwatch: **PARTIAL SUCCESS — first content painted**; next
  frontier: Lh4; ops=0 face, the empty dialog body, f141-null-recv at
  Lk6;.<init>, and the F084 budget-halt churn (app-alive signal).
- DataStore mangled path: **ROOT_CAUSED / PENDING-FIX** (CONT-34 candidate).
- Registry: 599 → **601** (F-NEW-291, F-NEW-292; dedup-checked).

## 12. NEXT RESUMABLE CHECKPOINT

1. The DataStore path-join law (§9) — the virtual-AOSP dir-getter contract,
   with a filesDir round-trip probe (write→resolve→same-file) BEFORE any
   engine change.
2. composeStopwatch next faces: f141-null-recv at Lk6;.<init> pc=409; the
   Lh4; ops=0 face; the empty dialog body (items=0).
3. Standing: F-NEW-288 (TextUnit value-class spin, Track A P0) and Simple
   Calculator input-pump (Track B).
