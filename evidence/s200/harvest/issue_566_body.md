## W17 — Coder-4 — ELEVEN base-layer laws + the S194-intake recovery (4APP campaign)

**Base**: `9bc2a115` (current main) · **Tip**: `006d24c7` (3 commits, fast-forward, zero conflicts)
**Patch**: `w17_laws.diff` — **1745 lines, sha16 `e663db810ce4d996`** — **attached IN FULL below (parts 1-4, in order)**; `git apply --check` verified on a clean worktree at the base (APPLIES CLEAN + FULL APPLY OK).
**Binary**: `cce85b8ef580f57c` (built `make -j1`, 107,222,448 bytes).
**Regression**: battery **11/11 CLEAN, zero tier drops**; goldens **ALL HOLD byte-exact** (bouncy `8a6c24ac`, unote `3b8dcb0a`, dooz `31ddd4d5`).

### The S194-intake recovery (why this wave starts with re-lands)

The S194 intake (`5119a933`) landed the W15 laws that applied clean but **dropped the hunks that conflicted**: F-C4-619 (`Class.getResourceAsStream` resolveName), F-C4-620 (`java.util.Properties` REAL load), F-C4-621 (`Collections.sort` natural order — the Tusky BOM root). All three re-landed here verbatim from `w15_laws.diff` (sha16 `16d989f25c60290f`): `4207d8a9` (621) + `d65c30f4` (619+620). **W16's `w16_laws.diff` was never attached to #564 at all** (the K-1 motivating failure of #565) — the nine W16 laws are re-implemented below from their live-root re-measurements on current main, SUPERSEDED by this wave where the main coder already landed equivalents (F-C4-623 → the landed F-C4-601; F-C4-624 → the new F-C4-629; F-C4-626 → already in main).

---

### F-C4-622 — `String.regionMatches` BOTH overloads (+ `contentEquals`, `compareToIgnoreCase`, + **622d heap-String receivers**)

**Root (live, Tusky 27.1, re-confirmed on `9bc2a115`)**: okhttp3 `HttpUrl` (R8 `Llk/w;.j`) validates the scheme with `regionMatches(true, 0, "https:", 0, 6)`; no bridge arm → typed-zero **false** → IAE `Expected URL scheme 'http' or 'https' but was 'https'` → uncaught → Koin `te/r.get` unwind → MainActivity content never inflated.
**Second root (622d)**: the receiver is a **heap String OBJECT** (`OBJECT_REF`) — the whole S100 String block typed `STRING_REF` skipped it. Law: resolve the receiver via the F-NEW-358 three-field convention (`__string_value__`/`value`/`sb_value`) and serve EVERY String law for both receiver forms. `ignoreCase` accepted as INT32 **or** BOOLEAN.
**Verify**: `[F-C4-622] regionMatches(ic=1, toff=0, other="https:", ooff=0, len=6) -> true`; `grep -c "Expected URL scheme"` = **0** (was 3). Tusky frontier now: Material `BottomSheetBehavior.from` IAE (`view.getLayoutParams()` must be a CoordinatorLayout.LayoutParams — the R8-decoded `D(View)` disassembly in the evidence) + a `String.length on null` family.

### F-C4-629 — `contains` DUAL-STORE COHERENCE + String content-equality (supersedes W16's F-C4-624)

**Root (live, ConnectBot 1.11.1, androguard-attributed)**: `NavDestinationBuilder.build` → `BundleKt.missingRequiredArguments(map, lambda)` → lambda `!deepLink.getArgumentsNames().contains(name)`; the `CollectionsKt.plus` product list is **dual-store** (shadow kind-2 string + engine-materialized `array[0]`); the OLD contains ran the heap-array branch FIRST, `get_object_array_string_element` only reads STRING_REF slots → element SKIPPED → false while toString printed `[hostId]` (hex `5b 68 6f 73 74 49 64 5d` verified) → IAE `Cannot set route "console/{hostId}" ... missing: [hostId]` ×16 → the whole NavHost composition died.
**Law**: shadow store answers FIRST when non-empty (the F-C4-602 render precedence); heap-array branch stays authoritative for asList products (empty shadow). Plus OpenJDK String.equals content-equality arms: STRING item vs kind-1 String-object elements (three-field content read); String-object item vs kind-2 inline strings; String-object vs String-object (both sides class-checked `Ljava/lang/String;`).
**Verify**: `grep -c "Cannot set route"` = **0** (was 16); CB uncaught 0; verdict `DEFAULT_BACKGROUND_ONLY / first_missing_stage=APP_DRAW_OPS / rf=COMPOSE` — composition completes (new frontier = the shared draw-dispatch chain, same as the maintainer W12 ts item 3).

### F-C4-625 / 625b — MediaStore + ContactsContract URI statics + `getContentUri` family

AOSP-faithful seeds (real heap Uri objects, `uri_raw`): Images/Video/Audio `INTERNAL_/EXTERNAL_CONTENT_URI`, `Audio.Media.CONTENT_URI`, Thumbnails, Downloads, `AUTHORITY` + the ContactsContract roots. `getContentUri(volume[, id])` on the 8 MediaStore tables → `content://media/<volume>/<table>[/{id}]`.
**Verify (NC)**: `getContentUri("external") -> content://media/external/file`; the `INTERNAL_CONTENT_URI must not be null` NPE family is gone.

### F-C4-627 — `java.time.Duration` factory + accessor family

OpenJDK law: `ofSeconds(s[, nano])` normalized, `ofMinutes/ofHours/ofDays/ofMillis/ofNanos`; objects carry `__dur_seconds__`/`__dur_nanos__` (I64); `toMillis/toNanos/getSeconds/getNano/toSeconds/toMinutes/toHours/toDays`.

### F-C4-628 — heap-String Throwable messages

`<init>(String)` args arriving as OBJECT_REFs (StringBuilder.toString products) were dropped → message-blind exceptions. Now captured via the three-field convention (TB's NoDefinitionFoundException no longer message-blind).

### F-C4-628b — Koin registry-key census (env-gated)

`MINIANDROID_KOIN_TRACE=1` → every `Class.getName` from Koin-family callers logs its dotted name (capped 400). **TB census captured**: 400 keys logged, registration healthy; the fatal `NoDefinitionFoundException` (6 hits) fires with no new key build — W18 probe target: the registry CHM dump at `Scope.resolveFromContext` (R8-specialized `resolveFromContext(Lcom/fsck/k9/mailstore/LocalStore$7;)`).

### F-C4-631 — manifest provider AUTHORITY resource-reference resolution

**Root (live, NC 3.50.x)**: 5 of 7 providers declare `android:authorities="@string/..."` (AXML REFERENCE, literal `@7F1300A7`); the literal was registered → the app's OWN query `content://org.nextcloud/...` threw IAE `Unknown authority: org.nextcloud` → uncaught → MainApp death. AOSP PackageParser resolves the reference through Resources at install.
**Law**: parse the `@0x<hex>` resid, resolve through the same ARSC the A7 label law uses; `;`-joined spellings resolve independently; unresolved stays literal (honest).
**Verify**: `[F-C4-631] @0x7f1300a7 -> "org.nextcloud" (FileContentProvider)` + 4 more; the `Unknown authority: org.nextcloud` IAE is gone.

### F-C4-632 — SYSTEM-PROVIDER shadow family

**Root**: with F-C4-625 handing apps real MediaStore Uris, apps QUERY them — `content://media/...` hit `Unknown authority: media` (no MediaProvider in a runtime sandbox). AOSP truth: system authorities are ALWAYS installed; a cold query answers a REAL empty Cursor, never an IAE.
**Law**: `media`/`com.android.contacts`/`settings`/`calllog` → query = real empty MatrixCursor (AOSP column shapes for the media tables); update/delete = 0; insert/getType/call = null.
**Verify**: `[F-C4-632] system-provider query content://media/external/images/media -> empty MatrixCursor` — the media folder scans proceed; NC MainApp now runs past insertConscrypt (`LOG/i/MainApp: Using Conscrypt/2.6.2 for TLS` — the REAL version from the app's own `conscrypt.properties`, loaded by the re-landed 619+620 through `Class.getResourceAsStream("conscrypt.properties")` package-relative resolution + Properties.load, 4 entries).

---

## Measured 4APP results (40-60s real-dalvik runs, `9bc2a115` baseline → W17)

| App | Before W17 | After W17 |
| --- | --- | --- |
| **ConnectBot** | fatal IAE `Cannot set route "console/{hostId}"` ×16, NavHost dead | **0 IAE, 0 uncaught; NavHost graph builds; Compose completes to APP_DRAW_OPS** |
| **Tusky** | okhttp IAE `Expected URL scheme` → content never inflates | **scheme wall DEAD (`regionMatches->true`)**; frontier: BottomSheetBehavior CoordinatorLayout-LayoutParams family |
| **Nextcloud** | MainApp death: Conscrypt `Version.major` NPE → lateinit cascade → ShowErrorActivity | **Conscrypt REAL (2.6.2 from APK properties), 5 provider authorities resolved from ARSC, media queries answer real cursors**; frontier: `getWork(...) must not be null` (caught; the W16-documented WorkContinuationImpl.mWork producer) + `Unknown uri id: content://org.nextcloud/capabilities` (the app's own UriMatcher path) |
| **Thunderbird** | message-blind Koin failure | **F-C4-628b census landed + heap-String messages captured**; W18: registry CHM dump probe at `Scope.resolveFromContext` |

## Evidence (sandbox layout `evidence/w17/`)

`baseline_4app.json` + `final_4app.json` + `{baseline,final}_<pkg>.console.log` (full 40s runs); `androguard_recon.json` (TB/TSK/CB DEX census); `w17_laws.diff` (the patch itself, sha16 `e663db810ce4d996`); battery `evidence/s188_w12/` rerun reports; goldens pins verified on `cce85b8ef580f57c`.

## K-7 checklist (per #565)

- [x] base commit stated and real (`9bc2a115`)
- [x] full cumulative diff attached, parts in order, 1745 lines, sha16 `e663db810ce4d996`
- [x] `git apply --check` verified on a clean worktree at the base
- [x] build command: `cd miniandroid && make -j1` (binary `cce85b8ef580f57c`)
- [x] per-app verify commands + expected + observed (above, per law)
- [x] regression battery 11/11 CLEAN + goldens ALL HOLD
- [x] every evidence path listed
- [x] every wave requirement has a status (all laws IMPLEMENTED+TESTED; TB deep-dive = W18)
- [x] English only; signed Coder 4

— Coder 4
