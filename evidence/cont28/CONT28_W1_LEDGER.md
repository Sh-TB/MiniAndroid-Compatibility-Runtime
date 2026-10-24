# CONT-28 W1 — f141 null-contract battery (F-NEW-516 family root fix)

**Binary:** `bc855252d150815d` (base f7894c4e847627b6 + F516 L1–L4)
**Head:** CONT-11 W7 lineage `b8213493` + this wave
**Directive:** «الگو های تکراری باعث میشن چند ده برنانه به صورت هم زمان جلو برن — تقسیم کار بکن»
(recurring-pattern leverage + division of work). 60% core stream.

## Family shape (the repeated pattern)

R8 compiles its implicit null-check instrumentation as an **immediate
`X.getClass()` on factory results** — frequently inside `<clinit>`. A
framework factory that answers null therefore kills the whole class at
first touch, while on ART the same bytecode never sees null (these APIs
are never-null by contract: ART returns a real instance or throws).

Census DEX-decoded roots (cont26 disassembler, machine-verified pc matches):

| title | face | root cause |
|---|---|---|
| webstack | `Lru1;.<clinit> pc=47` getClass on null | `Logger.getLogger(name)` → **null** |
| audiobook | `Lox5;.<clinit> pc=14` getClass on null | `LocalTime.of(22,0)` → **null** |
| wocheneinkauf | `Lqm;.<clinit> pc=25` init on null | `TrustManagerFactory.getInstance("X509")` → **null** |
| wocheneinkauf | `Ly7;.a pc=34` setText on null | `BreakIterator.getLineInstance` → **null** |
| (pool) prism/aurora/goodtime/dmfs/surgeengine | same shape | named per-title, W2 first-dives |

## Laws landed (bridge_to_api, F516 battery)

- **L1** `java.util.logging.Logger` — OpenJDK demand-create-and-cache
  `getLogger`; getName; log/info/… void family; isLoggable true;
  getLevel **null is the OpenJDK contract** for an unset level (not a stub).
- **L2** `java.time.LocalTime` — of/ofSecondOfDay/ofNanoOfDay/now real
  value objects (nano-of-day payload), DateTimeException on out-of-range
  (never null); getHour/…/toNanoOfDay/isBefore/isAfter/compareTo/toString.
- **L3** `javax.net.ssl.TrustManagerFactory` — getDefaultAlgorithm="X509";
  getInstance non-null or NoSuchAlgorithmException; init void;
  getTrustManagers 1-element array; getAlgorithm recorded.
- **L4** `java.text.BreakIterator` — getInstance family non-null; setText
  stores; first/next boundaries with DONE contract.

## Verification

- Named faces DEAD: webstack `Lru1;.<clinit> result=OK`;
  audiobook `Lox5;.<clinit> result=OK`;
  wocheneinkauf `Lqm;.<clinit> result=OK` + BreakIterator face gone
  (`[F516-L4] BreakIterator.getLineInstance -> oid`).
- dooz advanced by its OWN family hit: `Logger.getLogger('o0')` (OkHttp
  clinit) now completes → dooz 90s anchor re-pins `31ddd4d5` → `851cc176`
  (the recorded CONT-12-era deeper state, reached within 90s). Root-caused,
  not drift.

## Regression wall (binary bc855252)

| gate | result |
|---|---|
| anchors ×6 | opencalc 63020bc7334048fe / chess 3f7e670759b7c6a8 / microtimer bbd350b6c14fbd52 / unote 7481e9b468eaa376 / tower3d 11a38a5aeeff45a6 **byte-identical**; dooz re-pin 851cc1761a1dfcdf (lawful, root-caused above) |
| games battery ×7 | rc=0 all, r1=r2=r3, SHAs byte-identical to pre-W1 (g2048 f43face0… tetris b818a6a7… snake_deluxe 5235683f… snakeneon b669ce89… ttt_deluxe db1d633d… minicraft e77a073f… gmdice 3891679d…) |
| user goldens | **4/4 PASS** (2048 / snakedeluxe / minicraft REAL_APP_UI pixel gates + helloworld canonical 83720c1028f832d0) |
| negatives | **19/19 PASS** |
| skill selftest | **13/13 PASS** |
| batch-20 census | verdict lines unchanged (honest): W1 killed the named faces; each title's NEXT face named below |

## Next faces (honest — the layer-2 family)

The remaining f141 faces per title are the **collections view/iterator
stub family** (GPG-107 kin): `Map.put` REC-MISS → stub, `entrySet`/
`iterator`/`hasNext`/`Entry.getKey` stubs (wocheneinkauf `Ll7;.b pc=13`
OkHttp logger list, `Ly7;.a pc=118`), audiobook fragment-controller
field chain (`Lhm;.n pc=30` f@22103 null), webstack `Lp21;.<init> pc=67`,
prism unifiedpush cursor producer, surgeengine Sensors static list,
goodtime `Lap2;.a`. The collections-view law is the next highest-leverage
recurring fix (affects every app iterating framework maps).
