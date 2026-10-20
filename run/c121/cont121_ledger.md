# CONT-121 Ledger — «حل ۳۶۴ با این روش تمامشون رو حل بکن» train wave: 6 wagons, all terminal

- **Wave:** CONT-121 · **Base:** origin/main `e38c2135` (CONT-120; local unpushed worklog-only UUID commit `1af5530b` folded in) · **Final binary `1abe5c6a7abc6060`** (3 rebuild stages) · **9/9 anchors zero drift**

## Wagons

| # | Wagon | Verdict |
|---|-------|---------|
| W-00 | tool-bug capture (glow-worm) | تایید FIXED (dump_method_bytecode.get_string() sliced `data[end:end]` — zero-length — since the Sep-4 UUID commit: every string lookup returned '' so all type/method lookups silently failed on every dex; fixed to `[uleb_end:NUL)`; c3/n2/p3 found immediately) |
| W-01 | FIX-449 endgame | تایید LANDED — **F-NEW-449 ROOT-CAUSED-FIXED** (p3.d case-4 builds the correct Object[11]; n2.r walk fault pc=692cu=byte 0x568; ROOT = `String.length()` answered UTF-8 **byte** count (64) vs JVM UTF-16 **unit** count (40) — 12 Myanmar-block chars 3-bytes/1-unit → 24 phantom walk iterations → garbage descriptors → entries[11] AOOB. JVM unit law (`str_utf16_unit_count`/`str_char_at_unit`, supplementary = 2 unit slots high+low) at both charAt sites + both length sites. **VERIFIED: n2.r resolves ALL 11 p3 fields in p3.d's exact aput order; S36-AOOB ELIMINATED; telegram face `20ac8cbbbb` byte-identical anchor; 16 telegram PARTIAL unlocked)** |
| W-02 | bouncy Set-add | تایید LANDED — **F-NEW-467 ROOT-CAUSED-FIXED** (FIELD-TRACE pinned `iput requestedThumbnails value=<unset>` — the EXP-088+ CLASS-SCOPED CHM bypass force-bridged `newKeySet()` (real dex: `new KeySetView(new CHM(), TRUE)`) to a handlerless null → Set.add-on-null ×9. Method-scoped compute-family law (F-NEW-215 precedent) in BOTH swallow lists. VERIFIED: `value=obj#96`, f141 9→0) |
| W-02b | DesugarVarHandle CAS spin | تایید LANDED — **F-NEW-468 ROOT-CAUSED-FIXED** (casTabAt array-element offset hit F-NEW-217 UNSAFE-CAS-UNRESOLVED → CAS false forever → `.m` retry spin → F084 honest halt ×9. Array-element law: array box + `__array_length__` bounds → `array[i]`; field registry only for non-array targets; across get/put/CAS ×3 types. **VERIFIED: bouncy rc 1→0 FULL SUCCESS — first clean corpus run of bouncy; F084 0; F-NEW-217 0; face stable `8a6c24ac`**) |
| W-03 | F-NEW-374 MCM lever | تایید CLASSIFIED STANDS (opencalc under MCM+F368 on `1abe5c6a`: face `3e73a5ad` == recorded divergent face byte-for-byte — deterministic across binaries; OOB spec still declined; per-container DEX-measure trust stays the named lever — no false landing) |
| W-04 | B-cluster UNPROVEN re-scan | تایید NO-UPGRADE honest (72 roots × 15 fresh logs; 2 token hits REFUTED — provider-registration row + REC-MISS rows = inventory mentions, not behavioral evidence; 70 no hits; all stay UNPROVEN) |

## Battery (final binary `1abe5c6a`)

- **9/9 ANCHOR_MATCH zero drift**: dooz `d602648e`, opencalc `d5f3c7b5`, unote `90a67cc1`, microtimer `bbd350b6`, chess `a0319686`, tower3d `11a38a5a`, sudoku `be640e39`, klondike `31ddd4d5`, telegram `20ac8cbbbb`
- negatives PASS (rc=0) · selftest PASS (rc=0) · registry **783** id-unique, main==mirror status row-equal (F-NEW-449 upgraded; F-NEW-467/468 added — no inflation beyond 2 new roots)

## Honest discipline

- telegram keeps 5 honest uncaught (ll9/j ×2, UPP-001 ULE libjnigraphics, o6.k1/yc0.j theme-path NPEs) — independent open fronts, decoded, not suppressed.
- j$CHM get/put now execute real bytecode (no longer shielded) — telegram face held byte-identical; audit listed as next wagon.
- Signal BLOCKED stands (no artifact in corpus). F-NEW-374 CLASSIFIED stands.

## Next train

1. 16 telegram PARTIAL tasks re-adjudicated against the completed billing walk.
2. o6.k1/yc0.j theme-loading NPE decode (theme file path law).
3. j$CHM real-bytecode behavior audit under telegram.
4. F-NEW-374 per-container DEX-measure trust decode (R-NEW-441 family).

(issue #364 CONT-121, elephant batch, fixture-first, zero-drift wall)
