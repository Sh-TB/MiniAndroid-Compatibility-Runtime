# S45 SESSION RECORD — GAME PLAYABILITY FINAL ATTACK (R-NEW-359/360 landed, R-NEW-361 registered)

Date: 2026-09-15 · Base: origin/main 397eda3e (S44) · Binary: rebuilt from S44 sources + S45 laws

## 0. Environment recovery (container restart had wiped everything volatile)
- ALL APKs gone (zero-APK law kept — repo is hash-pinned only). Re-downloaded from pinned F-Droid URLs, **all SHA-256 EXACT match** → the downloaded Dooz/game models are byte-identical to every prior test: `dooz v18 d81292cd…`, `dooz v23 299eab21…`, `chessclock 5ca6f2c5…`, `gmdice 1621eda1…`, `microtimer 79c6f730…`, `unote be91103f…`.
- Toolchain re-bootstrapped at pinned versions: aapt2 8.13.2-14304508 (Google Maven), ECJ 3.33.0 (Central), r8 8.13.23 (Google Maven), android-34 stubs platform-34-ext7_r03.
- Engine rebuilt: 40 objects, build/miniandroid 76,135,200 B.

## 1. GitHub sync (user directive: publish all pushes)
- Local checkout found on the STALE GPG-evidence line (2 unpushed commits) while origin/main carried S35→S44 (38 commits, incl. "reconcile: adopt S43 engine line as authoritative; preserve GPG-092..095-session evidence").
- Verified `git ls-tree` superset law: **local HEAD had 0 files origin lacks; worklog byte-identical** → adopted origin/main S44 as local main (397eda3e). PAT used only as push credential, never stored in repo artifacts.
- Push verified: `origin/main = 397eda3e = local HEAD` ("Everything up-to-date" + ls-remote proof). All old pushes published.

## 2. R-NEW-359 — View.post / runOnUiThread main-queue law (VERIFIED-FIXED)
- **Attack site**: dooz23 blank frame — `[C013-LEAFCHK] Lt4; children=0 own_content=0 0x0` (AndroidComposeView empty).
- **Root cause (probe-proven)**: the deferred compose request `Ls7;.i` (Looper-identity check fails → View.post(Lk5;)) was dispatched into `ViewShadow::dispatch` → `m == "post" → handled_void` — **the runnable was silently dropped**. The runtime queue trace proves it: only ids 1200/1073/2816 ever enqueued; the compose request never appeared.
- **Law** (android_shadows.cpp ViewShadow + ActivityShadow): AOSP View.java `post(action) = attachInfo.mHandler.post(action)`; `postDelayed(action, delay)`; `removeCallbacks(action)`; `Activity.runOnUiThread` → enqueue on the SAME HandlerShadow queue (one MessageQueue ordering law, virtual clock). Returns handled_bool(true) per AOSP.
- **Effect**: `[R359-VPOST] View.post runnable=2770` enqueued + executed; ComposeView `Lho; children=1` (the AndroidComposeView child attaches). Deferred composition request EXECUTES for the first time.

## 3. R-NEW-360 — ArrayList(Collection) copy element-store cascade (VERIFIED-FIXED)
- **Attack site** (next layer, same run): `NoSuchElementException("List is empty.")` from `Ljk;.Q` (kotlin `last()`) at `Lcx0;.r` (NavController.popBackStack family) — uncaught through `MainActivity.onCreate` → ART process-death law → rc=1.
- **Root cause (DEX ground truth)**: kotlin lowers `arrayListOf(*array)` → `new ArrayList(Arrays$ArrayList(array))`. The R8-renamed wrapper `Lzc;` (= java.util.Arrays$ArrayList) has `size()` but **NO get(I)** (AbstractList inheritance pruned) → the engine's F-101 copy-ctor copied ZERO elements → empty ArrayList → `last()` threw. Second wrapper found: `Lad;` = kotlin ArrayDeque — a **circular buffer** (`g`=size, `e`=head, `f`=elements): raw `array[i]` probing yields capacity (10) not logical size (2) and rotationally-wrong elements.
- **Law**: F-101 cascade (engine site dalvik_engine.cpp + CollectionShadow copy-ctor + new typed HeapAllocator APIs `get_object_field_names` / `get_object_ref_field` / `get_object_array_ref_element` in shadow_registry.h + heap_adapter.h):
  1. `__array_length__` + `array[i]` raw array (Arrays.asList product)
  2. `size()` + `get(I)` real-DEX (RandomAccess contract)
  3. **iterator contract** — `iterator()`/`hasNext()`/`next()` via try_recursive_invoke (Collection contract proper; handles circular indexing through the deque's own iterator arithmetic)
  4. backing-array field probe (last resort, density assumed)
  - Contract-mismatch restart guard: size-promised ≠ elements-delivered → restart via iterator (no partial copies).
- **Effect**: `[R360-COPY] ArrayList(Collection) src=4488 (Lzc;) via ITERATOR elems=1` — NoSuchElementException GONE; NavController back-stack machinery now executes (2.6M+ instructions, `[R360-COPY] src=4032 (Lad;) backing field="f" arr=4479 elems=10` handled by the guard+iterator path).

## 4. R-NEW-361 (OBSERVED-FAIL) — R-NEW-335 refined; both dooz variants converge
- dooz23: after R360, `HALT-LOOP` in `Lbw0;.d` (androidx.collection MutableScatterMap probe, 671 units, 2.4M instrs) → force-exit → `aput-oob length=15 index=-733270216` in `Lbw0;.a` (set(key)) → process-death.
- dooz v18: first time PAST 400k instructions into Compose flow machinery (b2/u, F/l, P/b super-dispatch chains) → `HALT-LOOP` in `Lh/r;.b` → `AIOOBE length=2 index=-76748249` in `LP/v$a;.a` / compose ui node `i.h` → process-death.
- **Forensics run tonight** (narrowing): metadata `Arrays.fill` VERIFIED CORRECT (`[F040-DIAG] fill([J,0,2,0x8080808080808080)` ×N — the 0x80…80 EMPTY pattern lands); wide `ushr/shr` 2addr/lit8 laws verified correct (uint64/uint32 casts present). Both corrupt indices are NEGATIVE 32-bit values with high bits set → prime suspect: `key.hashCode()` of DEX-defined objects feeding the murmur h2/slot math (identity-hash law), or the boundary-slice `neg-long/shr-long/and-long` chain on slot reads.
- NEXT (registered in R-NEW-361): (1) [S44-R351]-style register dump at `Lbw0;.a pc=8` when the AIOB synthesizes; (2) verify `int-to-long`/`neg-long`/`shr-long/2addr` slice math against androidx.collection sources (already fetched); (3) ScatterMap micro-fixture via the exp052 fixture toolchain.

## 5. Regression gate (laws touch GENERIC paths — strict gate)
- TicTacToe §29 golden: **ALL PASS** (8 checks; deterministic replay 613cfccc0f27…).
- Full battery: **90/92 PASS — only the 2 pre-existing EXT-01/EXT-02 external-fixture-missing gaps (identical to pre-S45 record). ZERO regressions.**
- ChessClock re-run: screenshot SHA `e4a2d7c90cd2fd26…` **byte-identical to the committed golden**.
- gmdice `22f3730f452b562c…`, microtimer `c51269309cd14594…`, unote `7b30d52201bb22ac…` — all SHA-match their recorded frames (s33/s34 records).

## 6. Honest verdict
- The final attack landed TWO generic spec-level laws (R-NEW-359 View.post queue law, R-NEW-360 collection-copy cascade) and advanced BOTH Dooz models deeper than any prior session (v23: navigation machinery; v18: first deep Compose flow execution).
- The game-board pixel frontier is now exactly ONE registered root away (R-NEW-361 = refined R-NEW-335) — a focused session with the registered micro-fixture plan is the next move.
- TicTacToe golden remains ALL-PASS and TicTacToe Classic (palahsu) remains the fully-playable evidence line from S44 (its APK was lost with the legacy cache; SHA + evidence pinned in the ledger).
