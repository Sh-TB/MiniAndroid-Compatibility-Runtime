# CONT-42 TRAIN 2 EXECUTION LEDGER — dooz board throughput wave

HEAD at wave start: 94a4d98f (origin/main = CONT-41 TRAIN 1)
Binary at wave end: 7af40aa291aaf039 (-g0 -O2 build of the fixed tree)
Dooz APK: upload/canonical_apks/io.github.yamin8000.dooz_23.apk
User directive: «ادامه از جایی که ناقص موندی ادامه بده» — resume where incomplete,
under the standing «چند ده قطار» (dozens of trains) directive.

## §0 — SELF-UPDATE (honest)

- This container session started from a STALE local main (e99c2fbd, the CONT-10/W6
  era) while origin/main was at 94a4d98f (CONT-41 TRAIN 1) — **~31 waves behind**.
  ADMITTED per the «گیت هاب خیلی جلوتره / یا اگر تو له روزی بگو» law, then
  fast-forwarded (local was a strict ancestor; merge --ff-only). All further work
  happened at the synced tree.
- A container-build mystery was root-caused en route: background processes only
  receive CPU while an interactive tool call is active — the first two `make`
  attempts appeared to "die" silently. Resolution: foreground build chunks with
  dependency-driven resume (make -MMD). Banked as an operational note.
- Build flags: the canonical `-g -O2` line OOM-killed on this 2-core/3-4GB sandbox
  during dalvik_engine.cpp twice; the wave builds with `-g0 -O2` (zero codegen
  effect; the wall is the byte-exactness contract, not binary identity — and the
  wall held at every gate below).

## §1 — THE INCOMPLETE POINT

CONT-41's dooz train prep named the frontier: the composition is THROUGHPUT-bound
(Case E) — 90s window = 32.3M insns, RSS 332MB stable, the compose slot-table
family burning, iget-object 1.9M ticks. The board draw block (Lz6;) is never
CONSTRUCTED (R-NEW-546) because the interpreter runs out of budget first. The
train's mission: raise interpreter throughput GENERICALLY (no app-specific law),
with byte-exact walls as the only acceptable proof of semantic preservation.

## §2 — MEASURE FIRST (evidence, not guesswork)

- gprof (-pg build; dooz 60s ≈ 14.3M insns): the interpreter core
  (fetch_decode_execute) is only 4.25% of wall. The budget went to machinery:
  1. **CallStack::pop_frame 12.69% self** (1,272,435 calls): the EXP-042
     completed-frames cap erased ONE element from the FRONT on every push at cap
     (vector::erase(begin) per METHOD EXIT — the exact shape the F-107b law
     banned for trace vectors in the S61 era) + the frame was copied TWICE
     (push_back(frame) + return frame) though the sole caller discards the return.
  2. **batched_cap_push<ApiCallTrace> 9.03%** (1,557,425 pushes): even batched
     (F-107b, BATCH=64), each batch memmoves cap×sizeof(ApiCallTrace) ≈ 750KB →
     ~18GB of memmove per dooz run.
  3. **std::map<string,int>::operator[] 6.41%** (4,434,794 calls): the M3-19
     re-entry gate bumps m3_call_counts + m3_key_active_depth per INVOKE with a
     long concatenated key; rb-tree string compares = pure overhead;
     active_invoke_keys_ (std::set) the same shape.
  4. **Ungated per-field-op temporaries**: every iget/iget-object/iput/sget call
     site built `(current_class_ + "." + current_method_)` BEFORE the env-gated
     field-trace check — a heap string allocation per field-op tick (iget-object
     1.9M) with tracing OFF in every normal run.
- FALSIFIED THEORY (the phase clock, MINIANDROID_PERF_PHASES=1): is_subclass_of
  is called only 2,973 times in 45s (39.5M ticks ≈ 13ms) — the 49M
  "R530Memo dtor" flat-profile entry is NOT memo churn. The phase-clock call
  counts redirected the wave from the speculative map/memo surgery to the four
  measured levers above.

## §3 — THE FIXES (all generic; zero app/package knowledge)

1. **pop_frame** (dalvik_engine.h): F-107b BATCHED erase (drop 64 in ONE erase;
   identical FIFO order, identical survivor set modulo the documented bounded
   BATCH lag) + `push_back(std::move(frame))` + signature StackFrame→void (the
   sole caller never consumed the copy).
2. **Trace ring** (dalvik_engine.cpp + DalvikExecutionResult): batched_cap_push
   gains a cursor ref: until cap → push_back; at cap → OVERWRITE slot
   [cursor++ % cap]. O(1), zero memmove, IDENTICAL survivor set (the last cap
   entries). `ring_normalize_chrono()` rotates to the exact chronological FIFO
   order ONCE at the end of execute_apk_with_activity + execute_method (single
   O(cap) std::rotate) — every downstream consumer (S135 missing/ERROR census +
   first-20 emission, S69 JSON dump, ApiCallRecord recording) keeps reading
   chronological order exactly as before. New result field:
   api_call_ring_cursor.
3. **M3 gate containers**: m3_call_counts + m3_key_active_depth
   std::map→std::unordered_map; active_invoke_keys_ std::set→std::unordered_set.
   Lookup/increment/erase-by-key only — no ordered iteration anywhere.
4. **field_trace_filter_set()** zero-cost pre-check added and wired at ALL 9
   field-trace call sites (semantics identical: the temporary was only ever
   consumed when MINIANDROID_FIELD_TRACE is set).

## §4 — THE PROOF (throughput + zero drift)

- **dooz 90s window: 32.9M → 45.9M instructions (+39.5%)** at the SAME wall
  clock; anchor sha 851cc1761a1dfcdf BYTE-EXACT before and after.
- **FULL WALL at the throughput binary**:
  - anchors 6/6 BYTE-EXACT: opencalc 63020bc7 / chess 3f7e6707 / microtimer
    bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a / dooz 851cc176
  - games 7/7 EXACT-TO-PIN: g2048 f43face0 / tetris b818a6a7 / snake_deluxe
    5235683f / snakeneon 2617c81c / ttt_deluxe db1d633d / minicraft e77a073f /
    gmdice 3891679d
  - negatives 19/19 (after run/gatea/probe_store regen at the new binary — the
    established stale-store artifact, CONT-32/33/158 precedent)
  - reinstall 8/8, skill selftest 13/13
  - batch-50 census: 50/50 rows, **14/14 content rows BYTE-EXACT RETAINED**
    (aat/airlyrics/balance/bouncy/concealmobile/fossify_calendar/fossify_math/
    librecontacts/listai/netguard/peri/starlingmap/uturn/wocheneinkauf); zero
    drift; no new crossing claimed this train.
- Post-fix re-profile: pop_frame and map<string,int>[] OUT of the top;
  batched_cap_push 9.03% → 1.82%. Interpreter core now 6.31% of a FASTER run.

## §5 — NEXT FRONTIER (banked for the next trains)

- The post-fix profile's #1 is a 68.4M-entry ICF-merged destructor symbol
  (unordered_map<string,bool> dtor code folded engine-wide by the linker) plus
  660M std::string operator== per 60s and _init at 9.9%: the next throughput
  train needs a **-fno-icf PROFILE build** for true attribution before touching
  anything.
- The planned pipeline stands: CONT-43 telegram SvgHelper parse loop; CONT-44
  XmlPullParser family (gecko/lumolight/sopadeletras); CONT-45 Fragment family;
  CONT-46 the 6 zero-unwind blanks; then back to the dooz board (the composition
  gets 39.5% more budget per window — the R-NEW-546 four allocation sites are
  the named target for the next dooz train).

## Artifacts

- evidence/cont42/{CONT42_EXECUTION_LEDGER.md, throughput_evidence.json,
  batch50_census.json}
- run/cont42/{dooz_baseline, wall, prof, phaseclock.log} (bounded)
- scripts/{cont42_baseline.sh, cont42_profile_build.sh, cont42_batch50.py,
  cont11_drawmap*.py (superseded by the self-update; kept for the record)}
- registry 843 → 844 (R-NEW-554 ROOT-CAUSED-FIXED)
