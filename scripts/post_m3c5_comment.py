#!/usr/bin/env python3
"""Post M3-C5 (F-ROOM-CHAIN) evidence comment to Issue #8."""
import json, urllib.request, pathlib

tok = pathlib.Path("/home/z/.gh_token").read_text().strip()
body = """**MASTER-3 · cluster 5 — F-ROOM-CHAIN (PHASE 1 P0) closure record**

START HEAD `9f831abb` → FINAL HEAD `969cfc28` (pushed, origin/main synced). Battery: **59/59 ALL PASS** at final HEAD.

## Forensics (real DEX + runtime evidence)
`La/e;->h` decoded = R8-inlined Kotlin Intrinsics null-check: walks `Thread.getStackTrace()[2..]`, skips `className=="La.e"` frames, builds *"Parameter specified as non-null is null: method X.Y parameter N"*. Runtime frame dump (new `MINIANDROID_TRACE_FRAMES` diag) proved the walk consumed the whole array → **AIOOBE at `La/e;.h pc=34`** → swallowed by the UNIFIED_011.3 uncaught-tail policy → **Room init silently died** → no tick ever scheduled.

## Root causes (5, all fixed at the semantic boundary — zero package-specific code)
1. **`SQLiteOpenHelper` had NO shadow** → `getWritableDatabase()` = null → `Lh/f.s` `"sqLiteDatabase"` null-check threw.
2. **`Collections.synchronizedMap` / `newSetFromMap` returned null** → `Database;.<init>` (`"synchronizedMap(mutableMapOf())"`) and `Le/o;.<init>` (`"newSetFromMap(IdentityHashMap())"`) checks threw.
3. **`Locale.US` static = null** → `Le/o;.<init>` `"(this as java.lang.String).toLowerCase(locale)"` check (`"US must not be null"`).
4. **`Thread.start()` / `Executor.execute` were silent void stubs** → Room transaction-executor runnables never ran → no INSERT, no tick.
5. **R8 interface dispatch by NAME missed** (`Lg/f;.h(IJ)V` implemented as `Le/x;.h(IJ)V`) → `EntityInsertionAdapter.bind` parameters silently dropped → INSERT bound all NULLs → `NOT NULL constraint failed: alarm.duration_dec6`.

## Fixes (commit 969cfc28)
- **FIX-M3-012** `storage/sqlite_shadow.{h,cpp}` — `DatabaseShadow` (14th canonical shadow): REAL **sqlite3** backend at `runtime/data/<pkg>/databases/<name>`; SQLiteOpenHelper/SQLiteDatabase/SQLiteStatement/SQLiteProgram/Cursor; **onCreate/onUpgrade fire as REAL DEX callbacks** (engine drains pending flags after the open dispatch — ART helper-delegate law).
- **FIX-M3-013** `Collections` static factories (single-thread law: `synchronizedMap`→backing map; `newSetFromMap`; `singletonList`; `singleton`; `emptyList`).
- **FIX-M3-014** `Locale.*` constant synthesis (22 constants, identity-cached).
- **FIX-M3-015** deterministic virtual-thread law: Thread target recording; `start()/run()` inline drain; `execute` with proto `(Ljava/lang/Runnable;)V` runs the REAL DEX `run()` to completion inline.
- **FIX-M3-016** invoke-interface **signature dispatch** walking the runtime class + superclass chain (renaming preserves descriptors = the stable identity).

## Runtime proof (microtimer v8 `79c6f730…`, fresh sandbox)
```
[SQLITE-SHADOW] helper<init> name="app-data" version=1
[SQLITE-SHADOW] opened db user_version=0 target=1 [onCreate pending]
[SQLITE-LIFECYCLE] onCreate -> REAL DEX callback executed on Lh/f;
[SQLITE-SHADOW] rawQuery rows=1 "SELECT count(*) FROM sqlite_master …"
[SQLITE-SHADOW] rawQuery rows=0 cols=4 sql="select * from alarm"
[INTERFACE-SIG] Le/x;.h(IJ)V (interface Lg/f;.h) → REAL DEX dispatched
[SQLITE-BIND] idx=1 long=1   (duration_dec6)
[SQLITE-BIND] idx=2 long=1   (remaining_dec6)
[SQLITE-BIND] idx=3 NULL     (id → AUTOINCREMENT)
[SQLITE-BIND] idx=4 long=1000001170  (expires_ms = VIRTUAL clock + duration — NON-zero)
```
INSERT **SUCCEEDED** (was: NOT NULL rejection). `EXC-PROPAGATE` NPEs in the run: **3 → 0**. The "Alarm.expiresMs collapses to zero" symptom is **closed at its root** (virtual G07 clock + real persistence).

## Regression
Battery **59/59 ALL PASS** (semantic 14/25/57+14, resources 48/42/18, layout 24/23/37, G04/G06/G07/G08 goldens + 3-run determinism, §6 shadow invariant 24 checks, EXT-01/02 typographic+interaction goldens 9+12, density matrix, M3 ARSC law 17, live corpus simplestopwatch/gmdice/microtimer SUCCESS). Harness delta: `-lsqlite3` on all test link lines; §6 canonical count 13→14; EXT-01 fixtures re-frozen from documented URLs (**SHA-256 009b4671… verified**).

## Honest status
- **F-ROOM-CHAIN root causes 1–5: closed, runtime-proven.**
- **REMAINING (next step):** after a successful insert, the ▶-press branch does not yet reach `Handler.postDelayed` tick scheduling (the `Ll/e` Handler wrapper) and the new timer row is not re-bound into rendered frames → visual tick loop pending. No fake timer, no fixture code — the loop will be closed on the same laws.
"""
req = urllib.request.Request(
    "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/8/comments",
    data=json.dumps({"body": body}).encode(),
    headers={"Authorization": f"token {tok}", "Content-Type": "application/json",
             "User-Agent": "miniandroid-m3"},
    method="POST")
r = json.load(urllib.request.urlopen(req))
print("COMMENT URL:", r["html_url"])
urls = json.loads(pathlib.Path("/home/z/my-project/scripts/comment_urls.json").read_text())
urls["M3 session-5 F-ROOM-CHAIN closure"] = r["html_url"]
pathlib.Path("/home/z/my-project/scripts/comment_urls.json").write_text(json.dumps(urls, indent=1))
print("recorded")
