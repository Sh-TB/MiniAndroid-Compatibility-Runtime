# CONT-32 — Execution Ledger (دوز و تلگرام اولویت اصلی / ready-made-tools parallel wave)

Head: `7a1a9bee` (origin/main, CONT-29 W1) → CONT-32 wave. Binary: rebuilt from HEAD, sha16 `ead2663dfbae178d` (CowStr lever) → final (with F-NEW-522) built 19:24. Corpus: `upload/telegram_official.apk`, canonical dooz APK `299eab21ac8b3c61`.

## 0. Self-update from GitHub (user directive: «گیت هاب خیلی جلوتره، برری بکن و خودتو به روز کن»)

- Local container was STALE at the CONT-10-era snapshot `e99c2fbd`; `git fetch` showed origin/main **323 commits ahead** (`7a1a9bee`, the CONT-29 W1 resync consolidating CONT-11..CONT-28). Fast-forward reset, zero local divergence.
- Consumed: worklog (CONT-11..CONT-29 lineages merged), issue #387 ledger comments, registry 838→815-id rows (id-unique after dedup), dooz = `851cc176` REAL_APP_CONTENT@90-300s (chrome rendered, board frontier = F-NEW-381 throughput wall), telegram = `1671f5a3` (13 exceptions, UPP-001 honest native boundary).

## 1. Train A — F-NEW-381 structural lever: the register-representation change (60% core stream)

The wall (F-NEW-381 CLASSIFIED): `DalvikValue` carried TWO by-value `std::string` members (~112B per value); every register read/write copied both — the measured per-instruction value-copy constant (~60-90M copies per dooz run).

**Lever landed (dalvik_engine.h):**
- `CowStr` = intrusive-RC out-of-band string cell. Copy = 8B pointer + atomic inc ONLY when a cell exists; unset cells (non-ref values — the majority of interpreter traffic) are a null pointer with ZERO atomics and zero string ctor/dtor churn.
- `DalvikValue` 112B → ~40B. Value-identical by construction: reads return the same strings (operator const std::string& + the census-derived method surface: size/length/empty/c_str/data/back/at/operator[]/substr/find/rfind + the ADL free-operator set (+,==,!=,<<) + converting ctors for the 46 std::string-vs-CowStr ternary sites (fixer script `scripts/cont32_ternary_fix.py`, all READ shapes, assignment-LHS guarded).
- One deep-site fix: `String.charAt`'s `const std::string*` binding became a local copy (the pointer was only ever read through — behavior-identical).

**Measurement (dooz 90s, MINIANDROID_PERF_PHASES=1):**

| metric | recorded pre (CONT-29 W1) | post (CONT-32) |
|---|---|---|
| iget-object per-call cost | ~1.9 μs | **~1.15 μs (−39%)** |
| iget-object calls in 90s window | 2.29M | **3.83M** |
| #1 burn opcode | iget-object | iget-object (still — next lever named below) |

**Zero semantic drift (the full wall):**
- anchors ×6 **byte-identical**: dooz `851cc1761a1dfcdf` (×4 runs incl. ×3 gate), opencalc `63020bc7334048fe`, chess `3f7e670759b7c6a8`, microtimer `bbd350b6c14fbd52`, unote `7481e9b468eaa376`, tower3d `11a38a5aeeff45a6`
- games ×7 **deterministic** r1=r2=r3: 6/7 exact-to-pin + snakeneon `2617c81c` = the recorded R-NEW-467 A/B-neutral face
- user goldens **4/4 PASS** (2048/snakedeluxe/minicraft REAL_APP_UI pixel gates + helloworld canonical `83720c1028f832d0`)
- negatives **19/19 PASS** (after `run/gatea/probe_store` regeneration at the correct path — the 9/19 was the stale-store artifact, same as the CONT-158/CONT-29-W1 records)
- skill selftest **13/13 PASS**

F-NEW-381 stays CLASSIFIED (the wall remains; the constant shrank). Next named lever: **the heap field-map representation** (`HeapObject.fields` = `std::map<std::string, DalvikValue>` — the string-keyed map lookup is the remaining iget-object cost), plus the shadow→DEX compareTo bridge (PQ ordering) from the standing queue.

## 2. Train B — Telegram: F-NEW-522 ROOT-CAUSED-FIXED (the play_billing chain killer)

**Chain machine-pinned** (run/cont32/tg/post*.diag + dex decode via the ready-made `cont9_dexdump.py`):

```
LaunchActivity.onCreate [APP-BOUNDARY]
 ← ApplicationLoader.postInitApplication pc=0xfc
 ← BillingController.getInstance pc=8 / .<init> pc=65
 ← x4/b.<init> → kg/i.<init> → play_billing t1.zzb pc=50 (catch-wraps ANY Throwable
   into RuntimeException "Unable to get message info for <cls>")
 ← v1.h (GeneratedMessageLite h(Class)): map miss → forName → map miss →
   c3.g(cls) = sun/misc/Unsafe;.allocateInstance  ← NO ENGINE LAW (REC-MISS → null)
```

**Root (generic, zero app-specific code):** the engine had NO `Unsafe.allocateInstance` law (0 source hits). Two faces were killed and fixed in one arm:
1. missing law → null → `v1.d(6)` NPE → the library's own RuntimeException wrap;
2. the Class-TOKEN convention: the arg arrives as `class_desc=Ljava/lang/Class;` with the real class in `__referent_desc` (F-069/F-103 law) — a naive class_desc read allocated a bogus `java.lang.Class` shell (proven by the R337 trace `allocateInstance Ljava/lang/Class; -> obj#5848`).

**Fix** (the R337 Unsafe dispatch family, dalvik_engine.cpp): token-shape-aware class resolution (CLASS_REF direct / bare-token+OBJECT_REF via `__referent_desc`), `heap_.allocate(cls,0,0)` = RAW zeroed shell with NO constructor (deliberately NOT materialize_init_default — skipping the ctor is the API's contract), honest NPE/InstantiationException shapes. Runtime proof: `allocateInstance Lcom/google/android/gms/internal/play_billing/p3; -> obj#5848` and the entire "Unable to get message info" family is GONE (post6.diag vs post2.diag).

**Serves every protobuf-lite app** (play_billing/GMS-billing family, Firebase/MLKit components, DataStore proto chains — the same family R-NEW-350/F-NEW-495 were already serving).

**Telegram state after the fix** (60s wall, MINIANDROID_R350_LAW=1):
- exceptions **13 → 2 families**: the Billing RuntimeException ×N is DEAD; remaining = Firebase `Ll9/j;` ×2 + honest `UnsatisfiedLinkError` (arm64-only native libs — APP-BOUNDARY stays honest per UPP-001)
- face `1671f5a3` → `774075b4` (justified re-base: the R-NEW-467/F-NEW-519/520 generic laws moved the face; category = draw-path advance, same as the CONT-157 record)
- **F-NEW-523 CLASSIFIED** (the named next frontier): `Lra/a;.get pc=121` ISE "Not all priorities have been configured" (full 12-frame chain in the registry row) + the Firebase `checkNotEmpty(empty API key)` second face (the FirebaseOptions metadata read is the next law to decode).

## 3. Train C — batch-20 census (the parallel stuck-apps stream)

20-title census re-run at the CONT-32 binary (fresh stores, 90s window, same families A/B/C as cont13). Results: `evidence/cont32/batch20_census.json` (see the closing ledger comment for the crossing table).

## 4. Honest residuals

- dooz: chrome rendered (775 draw ops), the game BOARD still does not paint — the F-NEW-381 wall is the proven blocker; this wave shrank its per-instruction constant (−39% on the #1 opcode) and did NOT claim board pixels. No «دستاورد الکی».
- telegram: the Billing chain is cleared but LaunchActivity still does not reach the chat list — F-NEW-523 + the Firebase face + the honest native boundary stand.
- The R-NEW-350 default-off gate (microtimer Room retry) remains the named root blocking a default-ON 3-arg forName law; telegram runs in evidence mode with `MINIANDROID_R350_LAW=1`.
