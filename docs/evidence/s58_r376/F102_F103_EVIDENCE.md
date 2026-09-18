# S58 — R-NEW-376 ctor-climb closure + R-NEW-378 cascade (F-102/F-103/F-104)

HEAD at evidence time: 5b89d654 (pre-session S58 work; fixes applied in working tree).
APKs: apk_cache/io.github.yamin8000.dooz_23.apk, io.github.yamin8000.dooz_18.apk (SHA-verified corpus fetch).

## R-NEW-376 — Dooz ctor-climb (P0-for-Dooz)

ROOT CAUSE (F-102, generic): the 3rc invoke path (invoke-*/range) in
DalvikExecutionEngine dropped the call site's method PROTO at the
try_recursive_invoke boundary (default ""). The F-023 exact-descriptor
overload law therefore could not fire; the arity heuristic (prefer LARGEST
bytecode body) re-selected the CALLING ctor overload itself ->
same-receiver self-recursion to the 2048-frame cap.

- DEX ground truth: scripts/s58_gz1_forensic.py (androguard disasm of
  Lgz1;/Lbp1; Kotlin default-args ladders — overload1(mask+I) ->
  overload2, argc identical across overloads, descriptor distinct).
- Pre-fix face: [RECURSION-LIMIT] frame dropped: Lgz1;.<init> depth=2048
  caller=Lgz1;.<init> (x3) + Lbp1;.<init> (x1) — miniandroid/run/
  s57_r344_proof2/stderr.log (S57 baseline).
- Post-fix (both versions): RECURSION-LIMIT count = 0 across v18 AND v23.
  v23: miniandroid/run/s58_r376_post4/stderr.log; v18:
  miniandroid/run/s58_r376_v18/stderr.log (rc=0, 310k+ instructions,
  Choreographer doFrame loop alive — Compose composing).
- Regression: semantic_long_cmp_conv_test f102_range_ctor_overload_exact_dispatch
  (discriminating: pre-fix heuristic picks the larger (I)V overload ->
  f==0; post-fix exact-descriptor -> f==127). 24/24 PASS in battery.

## R-NEW-378 — saved-state cascade (found past R-NEW-376, fixed by F-103)

Face: IAE "Can't put value with type null into saved state" from
Ljb1;.f (compose rememberSaveable ACCEPTABLE_CLASSES loop Lje;.<init>
pc=73..104) -> APP BOUNDARY unwind at MainActivity.onCreate invoke_pc=317.

ROOT CAUSE (F-103, generic):
1. Class.isInstance/isAssignableFrom had NO handler -> STUBBED typed-zero
   0 for all 29 ACCEPTABLE_CLASSES -> loop missed for a String value.
2. Class tokens minted from a private counter (class_token_counter_)
   collided with real heap object ids -> the §19 runtime-class dispatch
   sent Class-token receiver calls to UNRELATED early heap objects.
3. execute_instance_of consulted the register's cached class_desc and
   only fell back to the heap when it was EMPTY — a degraded
   "Ljava/lang/Object;" tag (CollectionShadow round-trip hardcode)
   defeated the heap lookup (ART runtime-type authority violated).

FIX (all generic): Class.isInstance/isAssignableFrom law over
class_to_superclass_/class_to_interfaces_ + HEAP-BACKED Class tokens
(const-class allocates a real Ljava/lang/Class; object with
__referent_desc; identity map keeps F-069) + instance-of heap-authority
law. Post-fix: saved-state IAE = 0; key-class IAE = 0 (Lwl0;.containsKey
"Key must be a class" — same family). Evidence:
miniandroid/run/s58_r376_post3(+post4)/stderr.log.
Regression: f103_class_isInstance_string_exact /
f103_class_isAssignableFrom_subclass / f103_instanceof_heap_subclass.

## R-NEW-352 — CLOSED (blocker pre-dated by R-NEW-355)

The recorded blocker (microtimer Room initDb 50k forName retry loop, S43
A/B) was the MISSING PC-ADVANCE CONTRACT, root-caused+fixed at S44
(R-NEW-355). S58 A/B re-proof at the fixed HEAD: microtimer law-ON
(MINIANDROID_R350_LAW=1) vs law-OFF are PIXEL-IDENTICAL — 1,041,437
non-white pixels both, rc=0, HALT-LOOP 0, exactly 2 forName resolutions.
(miniandroid/run/s58_r352_lawON vs s58_r352_lawOFF.) The R-NEW-350 forName
law is now DEFAULT-ON with MINIANDROID_R350_LAW=0 opt-out. Corpus
re-verified pixel-identical to S57 records: chessclock 2,040,736 nb,
notes 2,073,600 nb, unote 236,520 nb.

## F-104 — io/state law family (unlocked by the cascade; F-085 content path)

Real-app read chain made live end-to-end (Notes v139):
seeded sandbox doc (runtime data-root Notes/Notes.md) -> app's own
defaultFile/readNote/ReadTask -> ContentResolver.openInputStream (F-104
file-scheme law) -> BufferedInputStream->InputStreamReader->BufferedReader
(expanded EXP-071 propagation) -> readLine loop (real bytes: 10
[EXP071-READLINE] lines, EOF) -> StringBuilder -> setText (sb_value
extraction, 230 chars verified) -> markdownCheck (regex Matcher/Pattern
laws: appendTail preserved all 230 chars).
NEW LAWS: FileInputStream/FileReader sandbox ctor, Uri.fromFile + getPath/
getScheme/getLastPathSegment, ContentResolver.openInputStream,
AsyncTask.execute (doInBackground+onPostExecute dispatch), EnumSet.of,
java.util.regex Pattern.compile/Matcher.find/matches/group/appendReplacement/
appendTail (std::regex), requestPermissions -> onRequestPermissionsResult
callback dispatch (AOSP contract completion), [EXP093-FNA] trace env-gated
(F-074 hygiene).
REMAINING (honest): the commonmark Parser.parse->HtmlRenderer.render DEX
chain still yields an empty body (loadData bytes=251, text_chars=0) —
the document text is proven present up to loadMarkdownToView; the gap is
inside the library's own DEX execution. F-085 stays P1-open at that face.

## Regression gate

Battery at the fixed HEAD: BATTERY GATE: ALL PASS (96 stages), 0 FAIL,
0 cached (fresh state dir). 3-run determinism: dooz v23 screenshot
sha16 ef47a2d3cdc6929e x3; chessclock ecc001fd8e33519a x3 (== S57
record); unote 7b30d52201bb22ac x3 (== S57 record).
