#!/usr/bin/env python3
"""cont116_registry_update.py — CONT-116 registry refresh (id-unique preserved):
F-NEW-465: two ctor-dispatch laws ROOT-CAUSED-FIXED at binary 3ecd381c
  (a) BOTH Constructor.newInstance shims now unbox the varargs and dispatch
      the arity+primitive-shape-matched <init> via its EXACT descriptor
      (F-023 authority path) — the no-descriptor heuristic could bind the
      wrong same-arity overload (Array(I) vs Array(Array)).
  (b) materialize_init_default's F-NEW-464 dispatch condition was INVERTED
      (`!class_has_no_arg_ctor`): the ()V body ran only for classes that
      have NO ()V ctor. Fixed to run exactly when it exists.
  Bracket: tower3d ARR-LEN-NULL death (obj#393 bare-shell) ELIMINATED
  (IGET-MISS keys:<none> 2 -> 0); death advanced one layer to the attribute
  copy-ctor getClass-null chain (NEW evidence, next-wave fixture named).
  Regression: wall 4 MATCH + chess/tower3d/solitaire byte-identical, c448
  6/6, c449 4/4, goldens 4/4, negatives 19/19 (store regenerated per
  CONT-111 remedy), reinstall 8/8, MG-310 7/7, MG-150 3/3, selftest 13/13.
F-NEW-449: decode advanced (runtime forensics, no fix — stays OPEN):
  OOB array = o5042 Object[11] built by exactly 11 STRING_REF stores
  (EXP093-APUT idx 0..10, no FNA, no copyOf) ; n2.r walk consumed ALL 11
  p3 instance fields (10 real zze/zzg/zzh/zzi/zzf/zzj/zzk/zzl/zzm/zzn +
  aux zzd read 10x between them — 20 R337-UNSAFE rows) then read
  entries[11] as the post-field terminator entry; the engine's s2.b
  parse demands one more entry than the built array carries. Fixture
  (MessageInfo-shape probe: two count sources over the same class) is the
  named next lever per the CONT-107 plan.
"""
import json, datetime

MAIN = "canonical/root_cause_registry.json"

d = json.load(open(MAIN))
roots = d if isinstance(d, list) else d["roots"]

def find(rid):
    for r in roots:
        if r["id"] == rid:
            return r
    return None

today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

r465 = find("F-NEW-465")
r465["status"] = "ROOT-CAUSED-FIXED"
r465["title"] = ("Bare-shell ctor-skip face (R-NEW-414/Constructor.newInstance): two dispatch laws fixed — "
                 "CONT-116: (a) both Constructor.newInstance shims forward the varargs Object[] and dispatch the "
                 "arity+primitive-shape-matched <init> via its exact descriptor (F-023 authority path; the old "
                 "no-descriptor heuristic could cross-bind same-arity overloads Array(I) vs Array(Array)); "
                 "(b) materialize_init_default's F-NEW-464 condition was INVERTED — the ()V body ran only for "
                 "classes WITHOUT one; fixed to run exactly when it exists. Bracket: tower3d ARR-LEN-NULL death "
                 "(obj#393 zero-field Array) eliminated, IGET-MISS keys:<none> 2->0; face stays 11a38a5a "
                 "(draw-op frontier); next layer = attribute copy-ctor getClass-null chain (registered as the "
                 "continuation fixture target).")
r465["evidence"] = ("run/c116/t465c{1,2,3}.log (ARR-LEN-NULL absent, keys:<none> 0) vs run/c116/t_diag.log "
                    "(pre-fix death chain: R414-INIT-DEFAULT -> Array.add pc=4 ARR-LEN-NULL); "
                    "run/c116/t_diag2.log + run/c116/t_fields2.log (FIELD-TRACE items puts prove ctor now runs); "
                    "battery: wall 4 MATCH, c448/c449, goldens 4/4, negatives 19/19, reinstall 8/8, "
                    "MG-310 7/7, MG-150 3/3, selftest 13/13 at binary 3ecd381cda214dcd")
r465["registered_wave"] = "CONT-114 (open) -> CONT-116 (fixed)"
r465["date"] = today
r465["verified_current"] = True

r449 = find("F-NEW-449")
r449["root_cause"] = (
    "CONT-116 runtime decode (deepened, still OPEN): the OOB array is o5042 [Ljava/lang/Object; len=11 "
    "built by EXACTLY 11 STRING_REF aput stores idx 0..10 (EXP093-APUT trace; no filled-new-array — 98 FNA "
    "rows all [I and later; no copyOf in window). The n2.r walk consumed ALL 11 p3 instance fields "
    "(Unsafe objectFieldOffset rows: 10 real fields zze/zzg/zzh/zzi/zzf/zzj/zzk/zzl/zzm/zzn + aux zzd read "
    "10x interleaved = 20 R337 rows) and THEN read entries[11] as the post-field terminator entry — the "
    "parse of s2.b demands one more entry than the constructed array carries. p3 has exactly 11 instance "
    "fields; the c106b reflection-count law stays GREEN (negative control). Residual decode fork (needs the "
    "complete disassembly of n2.r or an ART reference run): which 12th store ART executes (unrolled+loop "
    "construction shows 11 stores at idx 0..10 in-engine), or whether the walk's terminator demand is "
    "string-derived and the string differs. Fixture per CONT-107 plan: MessageInfo-shape probe asserting "
    "two count sources agree over the same class.")
r449["evidence"] = ("run/c116_tg_s36.log [S36-AOOB] arr=o5042 len=11 idx=11; run/c116_tg_aput.log (11 stores "
                    "idx0..10 + v24 write-back row); run/c116_tg_fna.log (FNA exclusion + 20 R337 walk rows); "
                    "run/c115/telegram.log (signature rows at CONT-115)")

json.dump(d, open(MAIN, "w"), indent=1)
print("registry updated: F-NEW-465 -> ROOT-CAUSED-FIXED, F-NEW-449 decode deepened; roots:", len(roots))
