#!/usr/bin/env python3
"""S40: register R-NEW-341/342/343 (FIXED) + R-NEW-344 (PARTIAL-FIX frontier)."""
import json, sys

path = '/home/z/my-project/root_registry.json'
reg = json.load(open(path))
roots = reg['roots'] if isinstance(reg, dict) and 'roots' in reg else reg
if isinstance(roots, dict):
    roots = roots

def next_id():
    return 'R-NEW-344'  # 341-343 registered below

entries = [
    {
        "id": "R-NEW-341",
        "title": "getApplicationContext served a plain Context singleton — Hilt Application resolution ISE killed dooz23 first composition",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1)",
        "observed": "ISE 'Could not find an Application in the given context: Context@7' thrown from Lk2;.b pc=776..880 (HiltViewModelFactory Application resolution: getApplicationContext() -> instanceof Application -> ContextWrapper.getBaseContext() walk -> throw). Escaped MainActivity.onCreate; composition died; white frame.",
        "root_cause": "Engine law gap: Context.getApplicationContext() returned get_or_create_singleton('Landroid/content/Context;') (plain object, class_desc Context) instead of THE Application instance. AOSP: ActivityThread.handleBindApplication creates ONE Application object (manifest android:name class) and getApplicationContext()/getApplication() serve THAT object. Hilt type-checks it (instanceof Application, Lxb0;.d() unwrap to the Dagger component).",
        "fix": "(1) bind_manifest_application() in dalvik_engine.cpp — runs INSIDE execute_apk_with_activity AFTER dex_report_ + secondary-DEX injection (the old runtime-side EXP093-APP trio ran with dex_report=NULL: [TRY-ENTRY] dex_report=NULL evidence, run r340 — App.onCreate's Dagger component build silently degraded, only 80 ins). Instantiates the manifest class (hint set_application_class_hint from both runtime paths + self-discovery fallback: single DEX class with superclass Landroid/app/Application;), runs <init>/attachBaseContext/onCreate via REAL DEX, records application_object_id_/application_class_desc_, stores ApplicationLoader.applicationContext, publishes identity to ActivityShadow. (2) P0.7 getApplicationContext serves application_object_id_ (fallback old behavior). (3) ActivityShadow.getApplicationContext serves application_heap_id_. (4) Manifest-activity path REUSES the bound object instead of allocating a second plain Application.",
        "evidence": "runs r341 (ISE gone, errors 6->2), r354 (0 errors, SUCCESS); [R341-APP] bound application obj#6 (Lio/github/yamin8000/dooz/ui/App;)",
        "discovered": "S40",
        "fixed_in": "S40"
    },
    {
        "id": "R-NEW-342",
        "title": "CopyOnWriteArraySet REC-MISS dropped the Hilt members-injector from the androidx lifecycle registry; iterator next() returned Ljava/lang/Object; (runtime class lost)",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1)",
        "observed": "MainActivity.<init> registers the injector Lae0;(this) into Leq;->a (CopyOnWriteArraySet); Ljm;.onCreate iterates the set and dispatches Lb11;->a(activity) (fast path Leq;->b != null skipped: b set only in Ljm;.onCreate). With add REC-MISS the set stayed empty -> injection never ran -> 'lateinit property settings has not been initialized' (Lxl; from Lqi0;.S, Le;.q @944 reads MainActivity.B) killed the resumed composition coroutine.",
        "root_cause": "(a) CollectionShadow.handles_class missed Ljava/util/concurrent/CopyOnWriteArraySet; (and the COWAL path lacked the concurrent/ segment). (b) CollectionShadow next() returned elements typed Ljava/lang/Object; — invoke-interface dispatch on the yielded observer could not find the DEX implementation.",
        "fix": "(1) handles_class += concurrent/CopyOnWriteArraySet + concurrent/CopyOnWriteArrayList. (2) add() set semantics for COW sets (addIfAbsent: contains check, return false when present). (3) HeapAllocator.get_object_class() (virtual, default false) + DalvikHeapAdapter override (heap get(id)->class_descriptor); next() returns the element's REAL runtime class. Evidence: [S24-COLL] add obj=165 elems 0->1->2, iterator/hasNext/next live, injectors dispatched (Lem;.a ran; Lae0;.a chain reached Lls;).",
        "evidence": "runs r344 (probe), r345 (real-class next), r347/r349/r351/r352 (FIELD-TRACE chain: A guard -> Lls;.a read -> B=<unset>)",
        "discovered": "S40",
        "fixed_in": "S40"
    },
    {
        "id": "R-NEW-343",
        "title": "java.lang.Class.cast(Object) unimplemented — Hilt component-holder unwrap Lpm;.B null-poisoned the whole DI chain",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1) — general: any DI framework",
        "observed": "Lpm;.B(obj, class): 'if (obj instanceof Lwb0;) return class.cast(obj); elif (obj instanceof Lxb0;) recurse obj.d(); else ISE'. With cast() unimplemented the OK path answered null -> Lns;.(null) -> Lls;.(null,null) -> Settings provider.get() null -> MainActivity.B injected <unset> -> lateinit ISE on the resumed compose coroutine (Le;.q @944). FIELD-TRACE r352: Lns;.a = <unset> despite Lps;.<init> having stored b=self=obj#14 (r351).",
        "root_cause": "No 'cast' handler anywhere in the engine (bridge_to_api/try_shadow_dispatch/shadows) for Ljava/lang/Class; receivers (CLASS_REF with referent_desc).",
        "fix": "R-NEW-343 law in the Class bridge (next to getName): cast(null)=null; castable (is_subclass_of incl. F-023 interface closure) -> return the SAME reference (identity law); else throw_deferred ClassCastException ('X cannot be cast to Y'). Evidence r354: [R343-CAST] Lps; as Ll2; obj#14 OK; run status SUCCESS with 0 errors (first dooz23 run ever with a clean report).",
        "evidence": "runs r350 (Lpc;.e=obj#14 memoized), r351 (Lps;.b=self), r352 (Lns;.a=<unset>), r353 (App.d reads f), r354 (casts OK, SUCCESS, 0 errors)",
        "discovered": "S40",
        "fixed_in": "S40"
    },
    {
        "id": "R-NEW-344",
        "title": "dooz23 first frame blank: Recomposer suspends on JobSupport.await (Lkp1;.Q, CancellableContinuation on job o1344) without re-posting a frame callback — await-resume machinery incomplete",
        "status": "OBSERVED-FAIL",
        "priority": "P0",
        "app": "io.github.yamin8000.dooz_23 (dooz, PRIORITY-1)",
        "observed": "Run r354 (after R-NEW-341/342/343): status SUCCESS, 0 errors, view tree real (Lho; ComposeView children=1, AndroidComposeView attached), pump fires cb=907 doFrame, runnable id=1348 (Lrx; resume) drains, Recomposer does real work (o1344 Lkp1; state machine: getKey/b/M/o/k/.Q), then suspends at Loj0;.Q(ZLkj0;)Ley; with CancellableContinuation o3048 (Lcj;) registered on job o1344 — quiescence pending_cb=0 queue_size=0 — no content nodes yet (Lt4; children=0) — screenshot 0 nonwhite. 36MB stderr (vs 11MB pre-fix) = massively deeper real execution.",
        "root_cause_hypothesis": "JobSupport.awaitOnComplete (.Q) registered the continuation on o1344's completion list; either (a) o1344 completed later in the same drain and the completion path did NOT resume registered continuations (engine gap in completeStateFinalization -> Lcj;.resumeWith dispatch), or (b) o1344 never completes and the awaiter is a long-lived loop job that must be driven by more pump ticks (bounded outer pump law, AOSP continuous vsync).",
        "next": "(1) Determine o1344's final state after the drain (heap field dump: Loj0;.e state). (2) If completed: verify the registered Lcj; continuation was resumed ([QUEUE] enqueue missing = resume gap -> fix the completion->resume path). (3) If not completed: implement the bounded outer pump (pump while progress: node-count/instruction deltas, bound 64) mirroring AOSP vsync. (4) Cross-check Lcj; (CancellableContinuationImpl) registration list identity ( Unsafe offsets from R-NEW-337).",
        "evidence": "run r354 tail: [CHOREO-DISPATCH] doFrame cb=907 -> runnable 1348 -> Lkp1; chain -> .Q with o3048(Lcj;) -> quiescence tick=1 pending_cb=0",
        "discovered": "S40"
    },
]

for e in entries:
    rid = e["id"]
    if isinstance(roots, dict):
        roots[rid] = e
    else:
        roots.append(e)
    print("registered", rid, e["status"])

json.dump(reg, open(path, 'w'), indent=1, ensure_ascii=False)
print("total roots:", len(roots) if hasattr(roots, '__len__') else '?')
