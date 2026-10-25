#!/usr/bin/env python3
"""CONT-32 registry update:
- F-NEW-522 ROOT-CAUSED-FIXED (Unsafe.allocateInstance law — the telegram
  play_billing chain killer)
- F-NEW-523 CLASSIFIED (the next telegram frontier: Dagger-provider ISE
  'Not all priorities have been configured' at Lra/a;.get — named with the
  full 12-frame chain; Firebase checkNotEmpty second face)
- F-NEW-381 evidence refresh (the CowStr register-representation lever
  landed: iget-object 1.9us -> 1.15us, zero semantic drift; stays CLASSIFIED)
Registry stays id-unique; mirror sync if mirror exists."""
import json, hashlib, shutil, os

BASE = "/home/z/my-project"
REG = f"{BASE}/canonical/root_cause_registry.json"
MIRROR = f"{BASE}/root_registry.json"

r = json.load(open(REG))
ids = {row["id"] for row in r}
print("registry rows:", len(r))

def append(row):
    if row["id"] in ids:
        print("SKIP (exists):", row["id"])
        return
    r.append(row)
    ids.add(row["id"])
    print("APPENDED:", row["id"], row["status"])

append({
    "id": "F-NEW-522",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "layer": "dalvik/unsafe-reflection (sun.misc.Unsafe.allocateInstance)",
    "date": "2026-10-25",
    "title": "sun.misc.Unsafe.allocateInstance(Class) had NO engine law (REC-MISS -> null) — the protobuf-lite default-instance bootstrap died: play_billing c3.g -> GeneratedMessageLite h(Class) returned a bare ISE, wrapped by the library into RuntimeException 'Unable to get message info for <cls>', killing BillingController.<init> -> ApplicationLoader.postInitApplication -> LaunchActivity.onCreate [APP-BOUNDARY] on every GMS-billing app (telegram face killer; exceptions 13 -> 2 families)",
    "root_cause": "Chain machine-pinned (run/cont32/tg/post.diag + dex decode scripts/cont9_dexdump.py): telegram BillingController.<init> pc=65 -> x4/b.<init> -> play_billing t1.zzb pc=50 (catch-wraps ANY Throwable into RuntimeException 'Unable to get message info for '+cls.getName()) -> v1.h pc=64 ISE 'Class initialization cannot fail.' OR the 0x00ec no-message ISE -> the missing link c3.g = sun/misc/Unsafe;.allocateInstance(Ljava/lang/Class;) — absent from the engine (0 grep hits), REC-MISS answered null -> the followup v1.d(6) NPE'd on the null (first face), and with the raw-path armed the arg arrived as a java.lang.Class TOKEN (class_desc=Ljava/lang/Class;, real class in __referent_desc per the F-069/F-103 convention) so a naive class_desc read allocated a bogus java.lang.Class shell (second face).",
    "evidence": {
        "wave": "CONT-32",
        "fix": "Unsafe dispatch block (dalvik_engine.cpp, the R337 getUnsafe/objectFieldOffset family): allocateInstance arm — (1) class-arg resolution honors BOTH token shapes (CLASS_REF class_desc != Ljava/lang/Class; reads directly; CLASS_REF bare-token and OBJECT_REF read the backing heap object's __referent_desc); (2) heap_.allocate(cls,0,0) = RAW zeroed shell with NO constructor (deliberately NOT materialize_init_default — skipping the ctor is the API's contract); (3) empty arg -> NPE, non-'L' shapes -> InstantiationException (libcore law). Runtime: '[R337-UNSAFE] allocateInstance Lcom/google/android/gms/internal/play_billing/p3; -> obj#5848 (zeroed, no ctor)' and the whole 'Unable to get message info' wrap is GONE (telegram post6.diag vs post2.diag).",
        "regression": "anchors 6/6 byte-identical at the final binary (dooz 851cc1761a1dfcdf x4, opencalc 63020bc7334048fe, chess 3f7e670759b7c6a8, microtimer bbd350b6c14fbd52, unote 7481e9b468eaa376, tower3d 11a38a5aeeff45a6); games 7/7 deterministic (6/7 exact-to-pin + snakeneon 2617c81c = the recorded R-NEW-467 A/B-neutral face); user goldens 4/4 PASS; negatives 19/19 PASS (after run/gatea/probe_store regeneration — the 9/19 was the stale-store artifact, same as the CONT-158 record); skill selftest 13/13.",
        "telegram_state": "face 774075b4 (re-based from 1671f5a3: the R-NEW-467/F-NEW-519/520 generic laws moved the face; honest re-base category = draw-path advance); exceptions 13 -> 2 families (Ll9/j; Firebase chain x2 + honest UnsatisfiedLinkError APP-BOUNDARY); telegram REQUIRES MINIANDROID_R350_LAW=1 for the 3-arg forName chain (the default-off gate root — microtimer Room retry — stays the named next-session root, R-NEW-350 gate comment)."
    },
    "verified_current": True,
})

append({
    "id": "F-NEW-523",
    "status": "CLASSIFIED",
    "priority": "P0",
    "layer": "telegram/dagger-provider-tree (post-F-NEW-522 frontier)",
    "date": "2026-10-25",
    "title": "Telegram Billing chain next link: IllegalStateException 'Not all priorities have been configured' at Lra/a;.get pc=121 — the Dagger/provider .get() tree inside BillingController.<init>'s x4/b build dies before the Play Billing client exists",
    "root_cause": "Full 12-frame chain machine-recorded (run/cont32/tg/post6/crash.log): LaunchActivity.onCreate <- ApplicationLoader.postInitApplication <- BillingController.getInstance <- BillingController.<init> <- x4/b.<init> <- kg/i.<init> (lambda) <- g5/s.a <- i5/a.get <- androidx/biometric/e.get <- a4/i.get <- jb/g.get <- ra/a.get pc=121 THROW. Second named face: FirebaseInitProvider.onCreate -> FirebaseApp(g9/g).<init> -> i6/l.f(String) checkNotEmpty threw (the FirebaseOptions API-key string answered empty — the metadata/resource read feeding it is the next engine law to decode). Third face: honest UnsatisfiedLinkError (ApplicationLoader.onCreate — arm64-only native libs on x86_64 host, APP-BOUNDARY stays honest per the UPP-001 family).",
    "evidence": {
        "wave": "CONT-32",
        "next": "dive Lra/a;.get pc=121 (the priority-config tree: what config read answers wrong), then the FirebaseOptions resource read. Ready-made tools: cont9_dexdump.py class decode + MINIANDROID_CL_TRACE."
    },
    "verified_current": False,
})

# F-NEW-381 evidence refresh
for row in r:
    if row["id"] == "F-NEW-381":
        ev = row.get("evidence") or {}
        if isinstance(ev, dict):
            ev["cont32_update"] = ("CONT-32 landed the named register-representation lever: DalvikValue "
                "dropped its two by-value std::string members (~112B/value) for out-of-band COW cells "
                "(CowStr, dalvik_engine.h): copy = 8B pointer + atomic inc ONLY when a cell exists; "
                "non-ref values (the majority of interpreter traffic) copy with ZERO atomics and zero "
                "string ctor/dtor churn. Measured on dooz 90s PERF-PHASES: iget-object per-call "
                "~1.9us -> ~1.15us (-39%), 3.83M iget-object calls in-window (recorded pre: 2.29M). "
                "ZERO semantic drift: anchors 6/6 byte-identical, games 7/7 det, goldens 4/4, "
                "negatives 19/19, skill 13/13. The wall itself remains (structural interpreter "
                "throughput) — next named lever: the heap field-map representation "
                "(HeapObject.fields = std::map<std::string,DalvikValue> string-keyed lookup per access).")
        print("F-NEW-381 evidence refreshed")

json.dump(r, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry rows after:", len(r))

if os.path.exists(MIRROR):
    try:
        shutil.copy(REG, MIRROR)
        h1 = hashlib.sha256(open(REG, "rb").read()).hexdigest()[:16]
        h2 = hashlib.sha256(open(MIRROR, "rb").read()).hexdigest()[:16]
        print("mirror synced:", h1 == h2, h1)
    except Exception as e:
        print("mirror sync failed:", e)
