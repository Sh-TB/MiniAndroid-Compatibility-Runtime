# CONT-34 — BATCH-50 PARALLEL CENSUS + 5 ROOT-CAUSED LAWS + R-NEW-530 (dooz/telegram priority)

**Directive:** «۵۰ تاشو تست بکن به صورت موازی و ببین چرا اجرا نمیشن مشکلشون رو حل بکن تلگرام و دوز رو هم»

## 1. Batch-50 parallel census (the widest so far)

`scripts/cont34_batch50.py` — Pool(2) parallel workers, chunked-foreground resume,
20 known titles (retention = regression gate) + 30 NEW fdroid titles.
Evidence: `evidence/cont34/batch50_census.json`, stores `run/cont34_batch50/`.

**12/50 real-UI content rows** (≥1000 content px):

| title | px | colors | note |
|---|---|---|---|
| bouncy | 72,622 | 982 | retained |
| librecontacts | 85,219 | 4,030 | **NEW crossing** |
| peri | 41,915 | 2,530 | **NEW crossing** |
| balance | 41,263 | 2,261 | **NEW crossing** |
| netguard | 27,059 | 633 | retained |
| airlyrics | 15,390 | 511 | **NEW crossing** |
| fossify_math | 13,071 | 446 | retained |
| starlingmap | 11,628 | 1,179 | **NEW crossing** |
| fossify_calendar | 12,336 | 43 | retained |
| listai | 7,765 | 453 | **NEW crossing** |
| wocheneinkauf | 8,579 | 1,356 | retained |
| uturn | 2,266 | 292 | **NEW crossing** |

38 blanks clustered by deepest-unwind origin into 4 shared-root families:
Shizuku attachInfo ISE ×3 · Capacitor MalformedURLException ×4 ·
Application-lifecycle NPE/ISE ×~8 · APP_DRAW_OPS compose frontier ×6.

## 2. Root-caused laws landed (all machine-verified)

- **F-NEW-525** — ProviderInfo.exported/multiprocess never seeded → ShizukuProvider.attachInfo ISE "android:exported must be true" (crash pc 0x11 = DEX-exact). Fix mirrors the #371 grants law at all 3 seed sites. Shizuku layer dead on all 3 titles.
- **F-NEW-526** — android.os.ServiceManager had ZERO engine presence → the reflective shizuku holder chain died on a swallowed CNF (getService Method null → NPE @ py7.a pc19). Fix: R-NEW-354 registry + bridge getService law (never-null family, approximation recorded).
- **F-NEW-527** — the CONT-32-named telegram frontier: keySet views answered size 0 (the generic size/isEmpty laws never read view_elements) → Firebase `ra/a.get` ISE "Not all priorities have been configured". Box-identity trace: 3 puts + keySet all on oid 5921, enum has exactly 3 consts → the view was the only sub-3 answer. **Post-fix: priorities ISE GONE (0 hits).**
- **F-NEW-528** — REFERENCE-typed meta-data (`@0x7f0a000a`) stored as a string → `Bundle.getInt("com.google.android.gms.version")`=0 → play-services manifest ISE despite the manifest declaring it. Fix: `ArscParser::resolve_int` + both seeding sites resolve the reference (AOSP Bundle.putInt law). Post-fix: benign GooglePlayServicesUtil WARN (non-fatal degrade path).
- **F-NEW-529** — `String.format("%s", <object>)` rendered `object@N` → bridge-dispatch `toString()` (bounded depth) before the fallback.
- **R-NEW-530** — dooz 300s PERF named `is_subclass_of` = 4.63M walks ≈ 28% of core budget → memoized wrapper (R-NEW-467 epoch law). **Measured: walks →3,143 (≥99.8% hits), ~11% more instructions per 90s window, per-insn cost −11%.**

## 3. Telegram state (honest)

40s window at the final binary: the two named killers (F-NEW-523 priorities ISE,
F-NEW-523b Firebase manifest gate) are DEAD — the run now executes 2.39M
IMPLEMENTED API calls, renders 4 frames, and dies honestly on: the g5/q charset
factory law, Firebase components metadata, and the KNOWN native lib boundary
(`libtmessages.49.so` dlopen — libjnigraphics missing). Chat list NOT reached — no claim beyond the machine-verified rows.

## 4. Dooz state (honest)

851cc1761a1dfcdf byte-exact at 90s AND 300s at the final binary — the board
still does not paint (the F-NEW-381 wall is thinner: −28% core burn via
R-NEW-530). Next levers per the profile: tri.resolve pure-core split (15.64M
calls), class_init checks (4.61M).

## 5. Regression wall (final binary 5324674cb461fecb)

- anchors **6/6 byte-identical** (opencalc 63020bc7 / chess 3f7e6707 / dooz 851cc176 / microtimer bbd350b6 / unote 7481e9b4 / tower3d 11a38a5a)
- games **7/7 exact-to-pin, rc=0** (g2048 f43face0 / tetris b818a6a7 / snake_deluxe 5235683f / snakeneon 2617c81c / ttt_deluxe db1d633d / minicraft e77a073f / gmdice 3891679d)
- batch-50 retention **12/12 content rows byte-exact** through 4 laws + 1 memo
- registry 816→822 id-unique

## 6. Next wave (named)

1. Capacitor BridgeActivity MalformedURLException family (4 titles) — the biggest remaining shared root
2. Application-lifecycle NPE/ISE cluster (~8 titles) per-site decode
3. telegram: g5/q charset factory + Firebase components metadata
4. dooz: tri.resolve pure-core split → memo (the stateful cascade blocks a safe memo today)
