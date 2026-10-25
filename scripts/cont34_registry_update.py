#!/usr/bin/env python3
"""CONT-34 registry update: F-NEW-525/526/527/528/529 + R-NEW-530 (id-unique)."""
import json
from pathlib import Path

REG = Path("root_registry.json")
r = json.loads(REG.read_text())
existing = {e.get("id") for e in r}
print("before:", len(r))

def e(id, status, priority, layer, title, root, fix, evidence, frontier):
    return {"id": id, "status": status, "priority": priority, "layer": layer,
            "date": "2026-10-26", "title": title, "root_cause": root,
            "fix": fix, "evidence": evidence, "remaining_frontier": frontier}

NEW = [
 e("F-NEW-525", "ROOT-CAUSED-FIXED", "P1",
   "framework/content-provider (ProviderInfo seeding; #371 GATE A family)",
   "ProviderInfo.exported + multiprocess never seeded from the manifest — ShizukuProvider.attachInfo ISE killed every shizuku-integrated app at install",
   "DEX truth (cont26 disasm, aurora): attachInfo @0x3 iget-boolean multiprocess @0x5 if-nez->0x15; @0x7 iget-boolean exported @0x9 if-eqz->0xf; @0xf const 'android:exported must be true' @0x11 invoke Lop0;.a = ISE — census crash pc EXACT. Engine ProviderInfo seed (3 sites) left both booleans unset (read 0) while manifest truth says ShizukuProvider android:exported=true (aurora manifest line 177).",
   "F-NEW-525 law mirroring the #371 grantUriPermissions law at all 3 ProviderInfo seed sites (attachInfo install, resolveContentProvider, getProviderInfo): exported = the real manifest value (manifest_reader already parsed it), multiprocess = FALSE (AOSP PackageParser default). manifest_provider_exported_ vector + setter (same shape as grants).",
   "Shizuku ISE layer DEAD on all 3 census titles (aurora/batterymonitor/shizuwall) — each advanced to its next per-title face (aurora compose sx0$c chain; batterymonitor FragmentManager.enqueueAction ISE; shizuwall xy0 init NPE). Anchors 6/6 byte-identical.",
   "per-title deeper faces (compose chains, FragmentManager) — the census stuck-list"),
 e("F-NEW-526", "ROOT-CAUSED-FIXED", "P1",
   "framework/hidden-api (android.os.ServiceManager; R-NEW-354 registry family)",
   "android.os.ServiceManager had ZERO engine presence — the reflective shizuku service-holder chain (py7 clinit forName -> getService Method -> invoke) died on a swallowed CNF leaving getService null -> NPE at Method.invoke",
   "stderr ground truth (aurora CONT-34): [CLASS_INIT] Lpy7;.<clinit> result=OK with [R350-FORNAME deferred CNF] android.os.ServiceManager INSIDE the clinit's own try/catch -> the getService static Method field NEVER assigned ([SGET-MISS] key=Lpy7;.getService obj_id=0) -> f141-null-recv NPE 'Method.invoke on a null object reference' @ Lpy7;.a pc=19 -> APP BOUNDARY. DEX: py7.<clinit> populates SYSTEM_SERVICE_CACHE but getService assignment is downstream of the caught forName.",
   "Two touch points: (1) R-NEW-354 kFrameworkClasses += android.os.ServiceManager (forName law; R-NEW-355 pc-advance inherited); (2) bridge_to_api Landroid/os/ServiceManager; getService/checkService(String) -> deterministic per-name non-null Binder token (class_desc Binder; — Binder->IBinder hierarchy row exists so py7.a check-cast IBinder passes; never-null family law, F-NEW-516 precedent; approximation RECORDED: every name answers present). [F526-SM] diagnostic.",
   "getService('activity') -> oid=31 fires; py7 clinit completes; ShizukuProvider.onCreate passes; aurora reaches the compose-chain frontier.",
   "ServiceManager.getService for genuinely-absent services still answers non-null (recorded approximation)"),
 e("F-NEW-527", "ROOT-CAUSED-FIXED", "P0",
   "framework/collections (keySet/values/entrySet view sizing; F-NEW-520 view family)",
   "CollectionShadow generic size()/isEmpty() never consulted view_elements — keySet views answered 0, so telegram's Firebase ra/a.get gate 'priorities.keySet().size() < enum.values().length' threw ISE 'Not all priorities have been configured' at APP BOUNDARY",
   "F527-HMAP box-identity trace: 3 puts + keySet ALL on recv_oid=5921 (same box); d5/c enum DEX truth: 3 consts (a=DEFAULT,b=VERY_LOW,c=HIGHEST) + $VALUES array length 3 — faithful arithmetic gives 3 < 3 = false, so the only sub-3 answer is the VIEW: the keySet law (~3163) pushes into dst->view_elements while the generic size law (2060) reads elements/is_map/array only. The iterator hasNext law (~2711) already counted view_elements — size/isEmpty disagreed with it.",
   "size()/isEmpty() is_view branch counting BOTH stores (elements + view_elements — the dual-store shape lines 782/833 already use; a view populates exactly one). Same law shape as the F-NEW-237b array fallback.",
   "telegram priorities ISE GONE (0 hits in the post-fix 40s run; was the CONT-32 F-NEW-523 named frontier) — the run advanced to 2.39M IMPLEMENTED API calls / 4 frames / GMS-face then deeper. Retention: batch-50 12/12 content rows byte-exact.",
   "entrySet iteration and values() views consumers — same dual-store shape audited at 2711/3003 only for iteration"),
 e("F-NEW-528", "ROOT-CAUSED-FIXED", "P1",
   "framework/package-meta (ApplicationInfo.metaData reference values; PackageParser law)",
   "REFERENCE-typed <meta-data android:value=@0x…> stored as the string '@0x7f0a000a' — Bundle.getInt answered 0 — GoogleApiAvailability threw GooglePlayServicesMissingManifestValueException 'A required meta-data tag ... does not exist' though the manifest DOES declare com.google.android.gms.version",
   "telegram CONT-34 face: Lf6/g;.b pc=153 ISE. Manifest truth (aapt2 xmltree): meta-data line 1100 name=com.google.android.gms.version value=@0x7f0a000a (AXML TYPE_REFERENCE). manifest_reader get_attribute_value answers '@0x'+hex for REFERENCE; the ApplicationInfo.metaData seeding (2 sites) stored the string; getInt -> 0 -> the play-services presence gate ISE.",
   "ArscParser::resolve_int (scalar twin of resolve_int_array: resolve -> best_for -> non-complex -> value.data; one reference hop dereferenced) + both seeding sites convert @0x… refs to the RESOLVED integer (AOSP Bundle.putInt law); honest fallback = the resource id itself (nonzero — the caller gates on presence/nonzero).",
   "post-fix telegram: meta-data ISE GONE — GooglePlayServicesUtil logs the benign 'requires the Google Play Store, but it is missing' WARN (AOSP non-fatal degrade path) and the run continues deeper (OOM-killed by the container at 40s — the deeper execution envelope is itself the evidence).",
   "meta-data android:resource XML refs keep the id-only law (371-CLOSEOUT) — unchanged"),
 e("F-NEW-529", "ROOT-CAUSED-FIXED", "P2",
   "framework/string-format (java_format_walk %s object conversion; EXP093 family)",
   "String.format('%s', <app-object>) rendered 'object@5999' — the charset-factory ISE message named garbage and the real encoding set rendered as one 'object@5991' — the factory gate killed the chain on a message-format artifact",
   "telegram face: Lg5/q;.a pc=39 IAE 'object@5999 is not supported byt this factory. Supported encodings are: object@5991.' with [EXP093-STRFMT] showing the format args are OBJECT_REFs. java_format_walk's arg stringify: OBJECT_REF without a 'value' field fell straight to 'object@'+oid.",
   "AOSP %s == String.valueOf(obj) == obj.toString(): before the object@ fallback, bridge-dispatch the object's toString (bounded depth 4; object@N stays the honest last resort for law-less classes).",
   "applied at the final binary; anchors 6/6 byte-identical; games 7/7 exact (the law only changes outputs for objects that HAVE a toString law — previously object@N).",
   "objects with toString laws answer real strings; law-less classes keep object@N (honest)"),
 e("R-NEW-530", "ROOT-CAUSED-FIXED", "P1",
   "dalvik/interpreter-throughput (subclass-reachability memo; R-NEW-467 epoch-law family; F-NEW-381 wall lever #3)",
   "is_subclass_of walked the DEX superclass chain per query — dooz 300s PERF: 4,626,192 walks burning ~28% of the interpreter's core budget (52.8T of 185.3T ticks) — the compose placement pass re-derives the SAME answers millions of times",
   "CONT-34 dooz 300s PERF-PHASES profile: is_subclass_of calls=4.63M ticks=52.79T vs fetch_decode_exec 185.34T. The walk is a PURE function of the class tables (DEX superclass chains + the static framework ancestry table); the only mutation is monotonic class-table growth.",
   "Memoized wrapper (is_subclass_of -> is_subclass_of_impl): thread-local unordered_map<key,bool> keyed normalized(derived)\\0normalized(base), epoch = class_to_superclass_.size() (the R-NEW-467 law — any growth invalidates once); negatives memoize too.",
   "MEASURED (dooz 90s at identical lineage): walks 1.4M(300s-basis) -> 3,143 post-memo (>=99.8% hit rate); per-instruction cost 20.98K -> 18.66K ticks (~11% cheaper); ~11% more instructions executed in the same 90s window; dooz anchor 851cc1761a1dfcdf BYTE-EXACT both at 90s and 300s; anchors 6/6; games 7/7 exact; batch-50 retention 12/12.",
   "next machinery lever per the profile: tri.resolve 15.64M calls (stateful cascade — needs a pure-core split before any memo), class_init 4.61M checks"),
]
added = 0
for e_item in NEW:
    if e_item["id"] not in existing:
        r.append(e_item); added += 1
json.dump(r, REG.open("w"), indent=1, ensure_ascii=False)
print("after:", len(r), "added:", added)
ids = [x["id"] for x in r]
assert len(ids) == len(set(ids)), "ID COLLISION"
print("id-unique OK")
