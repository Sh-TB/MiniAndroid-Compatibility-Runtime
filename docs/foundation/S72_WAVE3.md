# S72 WAVE 3 — F-141 ART NULL-RECEIVER INVOKE LAW + NULL-PRODUCER CLOSURE

Session: S72-W3 · HEAD base: c1150507 · Binary: build/miniandroid (patched)
Constitution: CONSTITUTION_V2.md (binding law; §-references below)

## 1. Root executed (single loop, RULE 19)

F-141 (P0, S72-W1): `invoke-virtual/range` on a null receiver executed the
callee DEX body silently with `this=NULL` — corruption compounded (dooz
PersistentHashMapBuilder.putAll trie walk) and crashed at the WRONG site
(`arraycopy(null)` NPE), hiding the first divergence (§030/§171).

## 2. The law fix (F-141a)

ART law (AOSP `DoInvoke` → `ThrowNullPointerExceptionFromInterpreter`): an
instance invoke whose receiver is null throws NPE from the CALLER frame at
the invoke site, BEFORE any callee body executes.

Patch: `f141_is_null_receiver()` (NULL_REF, or OBJECT_REF with object_id 0 —
the engine-wide null convention) + `throw_deferred` NPE at the invoke site in
ALL FIVE instance-invoke paths: 35c virtual (dalvik_engine.cpp ~14292), 35c
super (~14658), 35c direct (~14852), 35c interface (~15700), 3rc range
(~10187). Convention: `pc_ += 3`, `return true` — the catch-handler redirect
(exc_redirect_pending_) or frame-unwind propagation (UNIFIED_011.3, line
7711) does the rest. Covers §039 (no invented null receiver) and §177
(silent wrongness is worse than a crash).

## 3. What the law surfaced — and the null producers closed

Each run on the patched binary exposed the next TRUE divergence (§171);
each producer closed with an upstream-law fix (§013/§014):

| # | Divergence surfaced | Null producer | Law closed |
|---|---------------------|---------------|------------|
| 1 | `xr1.<clinit>` pc=4 `Runtime.availableProcessors` on null | `Runtime.getRuntime()` unimplemented → null | **F-141b** RuntimeShadow: OpenJDK Runtime.java singleton + availableProcessors (fixed device profile 4, MINIANDROID_CORES probe override) |
| 2 | `xu.<clinit>` pc=24 `Long.longValue` on null | `Long.getLong(key, def)` stubbed → null | **F-141c** boxed-reader family over the F-080 property table: Long.getLong/Integer.getInteger/Boolean.getBoolean (never null with primitive default; decode law) |
| 3 | `mc1.b` pc=25 `FragmentManager.findFragmentByTag` on null | `Activity.getFragmentManager()` legacy stub → null | **F-141d** getFragmentManager non-null (ActivityShadow) + FragmentManagerShadow: findFragmentByTag registry-empty null (install-on-miss contract), beginTransaction new transaction, fluent add/replace…, commit→int, executePendingTransactions→true |
| 4 | `we.run` pc=42 `Object.getClass` on null | `View.getResources()` STUBBED → null | **F-141e** P0.2 extended to View receivers (Resources singleton) |
| 5 | `g8.a` pc=569 `getClass` on null (chain) | F088 getClass declined STRING_REF receivers → null | **F-088 ext** string receivers answer String.class |
| 6 | `NoteMain.onCreate` pc=43 `Theme.resolveAttribute` on null (unote — law-surfaced regression) | `getTheme()` unimplemented → null | **F-141f** getTheme non-null + resolveAttribute over the F-093 theme chain authority (TypedValue type/data/resourceId/string fill) |

Note #6: the F-141 law CORRECTLY broke unote (its W2 "success" leaned on
silent null-theming, §177); F-141f both fixed unote and gave it REAL theme
resolution. Honest delta: 236520 (W2, garbage-backed) → 23472 (law, crashed)
→ 231120 (fixed, real theme values). Per §28: expected semantic change.

## 4. Remaining dooz first divergences (surfaced, NOT yet fixed)

- **F-146 (P1)**: `Lur;->e(J)Z` on null receiver at `g8.a` pc=569
  (F141-DIAG: recv v4:t8/o0; escapes onCreate 0xc1) — coroutine state
  machine path; producer upstream of the call.
- **F-147 (P1)**: `ViewGroup.getChildAt(I)` on null receiver at
  `MainActivity.onCreate` pc=228 (method_idx 1592; recv v10 NULL_REF; second
  boundary escape at 0xb4) — likely findViewById/content-view resolution.

Both are precise, machine-evidenced first divergences — next wave's queue
(the f141 law turned "dooz crashes somewhere" into two named, located roots).

## 5. Real-app proof (§165/§169)

- **dooz** (RULE-1 APK #1): frame_008 nonwhite **197 → 23472** (first real
  painted content on the surface; still splash-surface behind F-145).
  Determinism ×3: **BYTE-IDENTICAL** sha `eb16ab5c68fa9b6cd22ab1e067163464ec219989b59ade6e6887d2920552caf3` ×3.
- **unote**: regression RECOVERED — 23472 (law-exposed crash) → **231120**
  (real UI, real theme resolution).
- **gmdice** 182095→182628, **microtimer** 1041073→1041437, **fishrings**
  2072819→2073360, **tripeaks** 205273→205638 (UP deltas classified §28:
  new law coverage painting additional real content); gmdice ×3
  **BYTE-IDENTICAL** (1 unique sha).
- bouncy / stopwatch / opmt / tictactoe: pixel-SAME.

## 6. Regression (RULE 117/120/121)

- **Corpus (10 canonical APKs, canonical recipe)**: 4 SAME, 5 UP, unote
  recovered (§3) — ZERO unexplained deltas. rc is not a KPI (§135).
- **Foundation fixtures (25 pinned APKs, run on patched binary)**:
  **25/25 pixel-SAME** vs stored baselines, rc=0 ×25, ZERO f141 throws —
  the law broke no existing semantic.
- Determinism: dooz ×3 + gmdice ×3 byte-identical.

## 7. Instrumentation discipline (§111-116)

F141-DIAG probe: env-gated (`MINIANDROID_F141_DIAG`), bounded (24-register
window, 12 code units), renders nothing, answers ONE question (which
register carried the null receiver). Kept env-gated per W1 precedent;
documented for removal after F-146/F-147 closure.

## 8. FOUNDATION STATUS

**NOT COMPLETE** (§32) — frontier moved materially:
- P0 F-141 closed with real-app proof + zero regressions.
- Two new P1 roots (F-146/F-147) precisely localized on the dooz path.
- F-145 (screenshot capture surface) still open — dashboard honesty depends
  on it.

## 9. Registry delta

386 (W2) → 393: F-141 ROOT-CAUSED-FIXED (7 sub-fixes), F-146, F-147
registered; F-142 ROOT-CAUSED-FIXED (W2), F-143/F-144/F-145 unchanged.
