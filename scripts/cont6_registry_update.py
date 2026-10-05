#!/usr/bin/env python3
"""cont6_registry_update.py — CONT-6 registry wave: F-NEW-247/248/249 +
sudokusolver kotlinx-serialization open frontier. Syncs summary counts."""
import json

REG = 'root_registry.json'
reg = json.load(open(REG))
roots = reg['roots']
ids = {r.get('id') for r in roots}

new_roots = [
    {
        "id": "F-NEW-247",
        "title": "java.util.TreeSet pop-family SINGLE-STORE read-through (first/last/pollFirst/pollLast + contains/size/isEmpty/clear/remove coherence over BOTH the F-097 ts_* heap store and the ambient CollectionShadow store)",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "framework/collections-treeset",
        "root_cause": "TreeSet-family receivers were served by TWO disjoint stores: add/remove/isEmpty/size claimed by the ambient CollectionShadow (C013-HIER superclass walk Lnq2; -> java/util/TreeSet;) while first() fell through to the F-097 gate and read the ts_* heap fields (never populated for that receiver: ts_size=0 fields=0 at the gate). isNotEmpty()==true + first()==null -> DepthSortedSet.remove(NULL) -> the APK's real check(node.isAttached) ran on a NULL receiver -> the misleading ISE \"DepthSortedSet.remove called on an unattached node\" -> AndroidComposeView.dispatchDraw died at the app boundary -> APP_DRAW_OPS=0 (DEFAULT_BACKGROUND_ONLY) on Compose apps queuing measure/layout into MeasureAndLayoutDelegate. Same misleading-ISE shape as dooz R-NEW-330/F-097: the node was never unattached — the ARGUMENT was null. (Runtime proof: [ROOT-059] null-recv routed to shadow law: Lp71;.I; [DRAWWIN-ZRET] decl=Lp71;.I recv=0() ret=FALSE.)",
        "evidence": "run/cont6/sudoku_r330.log (pre-fix ISE + null-recv proof) vs run/cont6/sudoku_f247_r1..3.log (ISE count 0/3, measure/layout pop loop runs, R347-MEASURE + DEX-MEASURE ComposeView dispatch reached). Generic: keyed on receiver runtime TreeSet ancestry, never on package. Ordering stays the documented F-097 deterministic insertion-order approximation. Anchor drift: ZERO (5/5 x3 byte-identical post-fix).",
        "fix_law": "OpenJDK TreeSet.java: first()/last() = min/max; pollFirst/pollLast = remove-and-return (null when empty); first()/last() throw on empty (engine answers null per the F-097 honesty law). Read-through cascade (F-101 discipline): ts_* store first, then the ambient CollectionShadow store for the SAME receiver id; removals/clear keep both stores coherent.",
        "test": "sudokusolver com.galaxyrio.sudokusolver_8 x3 deterministic; anchors 5/5 x3 byte-identical; goldens 4/4; gate A 97/0/2; negatives 19/19",
        "three_run": "sudokusolver f247_r1..r3 byte-identical d602648e8e401895 (pre-existing white frame sha — frame unchanged, death chain advanced 2 roots)",
        "corpus_fanout": "every Compose app using MeasureAndLayoutDelegate/DepthSortedSet (all androidx.compose 1.6.x); every TreeSet first()/last()/poll* consumer",
        "remaining_blocker": "none for this law — sudokusolver advances to the kotlinx.serialization face (open frontier registered separately)"
    },
    {
        "id": "F-NEW-248",
        "title": "java.util.Map STRING-KEY CONTENT LAW (String-object keys normalize to __string_value__ content, not identity) in map_key_value_law",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "framework/collections-map-keys",
        "root_cause": "map_key_value_law unwrapped boxed Numbers (int:/long:) but NOT String heap objects: a key arriving as a String OBJECT (OBJECT_REF class java/lang/String) keyed as obj:<id> while a const-string get keyed by CONTENT — the two String materializations of the same text never met. OpenJDK law: java.util.Map key classification uses the key object's equals() — for String that is CONTENT equality, never identity. (Related-but-distinct face: sudokusolver's navigator registration ALSO needed F-NEW-249 — the raw F089-MAP rows showed the puts keyed correctly by name; the real registration blocker was token churn. The String-key law remains a standing OpenJDK-correct coherence requirement for every mixed String-object/const-string map consumer.)",
        "evidence": "F089-MAP/F-089 widened diag (bounded 40) + S24-COLL key dumps across run/cont6/sudoku_*.log; put-side and get-side now agree regardless of which String materialization the call site used.",
        "fix_law": "map_key_value_law: OBJECT arg whose heap class is Ljava/lang/String; unwraps __string_value__ to the CONTENT key (same normalization as the boxed-Number law); unreadable/unmaterialized receivers fall back to identity keying — no fabricated content.",
        "test": "anchors 5/5 x3 byte-identical (post-law); gate A 97/0/2; negatives 19/19; goldens 4/4",
        "three_run": "sudokusolver x3 byte-identical; zero drift on all recorded SHAs",
        "corpus_fanout": "every HashMap/LinkedHashMap consumer mixing String-heap-object keys with const-string lookups (NavigatorProvider-style registries, intent extras, serializer caches)",
        "remaining_blocker": "none"
    },
    {
        "id": "F-NEW-249",
        "title": "STABLE CLASS-TOKEN IDENTITY LAW (Object.getClass returns the SAME Class token per runtime class — F-069 const-class map reuse)",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "framework/reflection-class-identity",
        "root_cause": "const-class already minted STABLE per-descriptor Class tokens (F-069 class_token_ids_), but Object.getClass stamped ref_id = instruction_sequence_ — a DIFFERENT token per call site for the SAME class. ART ClassLinker mints ONE java.lang.Class instance per runtime class; identity is observable (==, HashSet<Class>, Class-keyed caches). Live face (sudokusolver): NavigatorProvider.addNavigator derives the navigator name via nameForNavigator(navigator.getClass()); androidx caches Class->Name in a STATIC LinkedHashMap keyed by the Class token. Token churn defeated the cache on every lookup AND the getAnnotation chain for navigators whose annotation the resolver then re-queried — all five addNavigator puts landed under the FIRST resolved name (\"navigation\") instead of navigation/activity/navigation/composable/dialog -> getNavigator(\"composable\") ISE \"Could not find Navigator with name\" -> NavGraphBuilder died -> zero NavHost destinations -> AndroidComposeView children=0 -> APP_DRAW_OPS=0.",
        "evidence": "Pre-fix F089-MAP: put key=\"navigation\" x5 (vals obj#3965/3968/3973/3974/3979 — five navigators ONE name) + F087 rows only for Lqp1; x2/Lmz; x1 (cache defeats). Post-fix F087: Lqp1;=navigation, Le3;=activity, Lkz;=navigation, Lmz;=composable, Ls90;=dialog (one query each — cache HITS) and F089-MAP puts: navigation/activity/navigation/composable/dialog EXACT. ISE count 0/3. run/cont6/sudoku_f249_r1..3.log.",
        "fix_law": "make_stable_class_token(desc): one heap object per descriptor (Ljava/lang/Class; with __referent_desc), allocated on first use and reused forever; getClass's four receiver branches (STRING_REF/CLASS_REF/OBJECT heap/OBJECT desc-fallback) all return it; const-class already shared the map. Type stays CLASS_REF with class_desc = referred descriptor (existing consumer contract preserved).",
        "test": "sudokusolver x3 deterministic; anchors 5/5 x3 byte-identical; goldens 4/4 REAL_APP_CONTENT; gate A 97/0/2; negatives 19/19; reinstall 8/8; multiapp ALL PASS; skill 13/13; NATX x3 == recorded sha",
        "three_run": "sudokusolver f249_r1..r3 byte-identical d602648e8e401895 (frame unchanged; death chain advanced: navigator ISE GONE, next face = kotlinx.serialization)",
        "corpus_fanout": "every Class-identity consumer: androidx NavigatorProvider name cache, HashSet<Class>/synchronized(Class), Class== comparisons, annotation caches keyed by Class, kotlinx reflective machinery",
        "remaining_blocker": "none for this law"
    },
]

added = []
for nr in new_roots:
    if nr['id'] not in ids:
        roots.append(nr)
        added.append(nr['id'])

# open_frontiers: add the sudokusolver kotlinx-serialization face
frontiers = reg['summary'].get('open_frontiers', [])
new_frontier = "F-NEW-250"
if new_frontier not in frontiers:
    frontiers.append(new_frontier)
    roots.append({
        "id": "F-NEW-250",
        "title": "kotlinx.serialization reflective serializer chain (serializerOrNull -> Companion/INSTANCE reflection -> @Serializable(with=) element dispatch -> KClass machinery) — sudokusolver Compose NavHost route arg serialization",
        "status": "CLASSIFIED",
        "priority": "P1",
        "layer": "framework/serialization-reflective",
        "root_cause": "After F-NEW-247/249 the sudokusolver NavHost graph builder reaches the route-arg serializer resolution. First divergence (named, not fixed this wave): Lal1;.s (kotlinx reflective resolver) asks Class.getDeclaredField(\"Companion\") on a Kotlin OBJECT class Lpw0; -> honest NoSuchFieldException (Lpw0; has INSTANCE, not Companion) -> app catch-all handles it -> INSTANCE path proceeds (Field.get INSTANCE ok, serializer() method found) -> @Serializable element dispatch: class_annotations_ for Lpw0; carries the annotation under its R8 type Lpj2; with ZERO elements (DEX default-value encoding — the parser drops/strips default elements; F087 diag ann{Lpj2;:}) while the app queries by Lto1; -> null -> downstream getClass-on-null (f141) uncaught at Lal1;.s pc=350 -> cascade -> APP BOUNDARY.",
        "evidence": "run/cont6/sudoku_f249_r1.log lines 2504-2521 (R500-REFLECT Companion miss CAUGHT, INSTANCE get OK, getMethods serializer() found, F087 ann{Lpj2;:} empty-element evidence, f141 pc=350 uncaught). Classification: category D (missing generic framework contract: annotation DEFAULT-VALUE element law + R8-renamed annotation-type resolution + KClass element dispatch).",
        "fix_law": "NEXT-WAVE PLAN (no blind implementation): (1) annotation DEFAULT element law — DEX annotations omit defaulted elements; the bridge must consult the annotation class's default-value table (annotations_directory default values) before answering null; (2) element-name/type resolution under R8 (the stored element name/type pairing); (3) the KClass with() element dispatch returning the Class token.",
        "test": "sudokusolver com.galaxyrio.sudokusolver_8 x3 deterministic (evidence banked); no fix applied this wave — honest CLASSIFIED",
        "three_run": "n/a (classified, not fixed)",
        "corpus_fanout": "every @Serializable Kotlin class consumed reflectively (Compose navigation route args, DataStore, Retrofit-Kotlinx)",
        "remaining_blocker": "open — P1; blocks Compose draw proof for sudokusolver (route args), NOT for Compose apps without @Serializable nav args"
    })

reg['summary']['total_roots'] = len(roots)
reg['summary']['open_frontiers'] = frontiers
reg['summary']['last_updated'] = ("CONT-6: F-NEW-247 ROOT-CAUSED-FIXED (TreeSet pop-family single-store read-through — "
                                  "DepthSortedSet.remove(null) misleading ISE closed, Compose measure/layout pop loop runs) + "
                                  "F-NEW-248 Map String-key content law + F-NEW-249 STABLE Class-token identity (Object.getClass "
                                  "reuse F-069 token map) — sudokusolver navigator registration repaired (navigation/activity/"
                                  "navigation/composable/dialog exact), getNavigator ISE GONE, Compose chain advances to the "
                                  "kotlinx.serialization face (F-NEW-250 CLASSIFIED). Regression at binary f19af76f4082f2f3: anchors "
                                  "5/5x3 byte-identical, goldens 4/4, gate A 97/0/2, negatives 19/19, reinstall 8/8, multiapp ALL "
                                  "PASS, uninstall ALL PASS, loading probe ALL PASS, skill 13/13, NATX x3 == recorded sha, "
                                  "fairymahjong 76e097244767d6c3 x3, raumballer a7a73cc61722497c x3 — zero drift.")

json.dump(reg, open(REG, 'w'), indent=1)
print("registry updated:", len(roots), "roots; added:", added, "+ F-NEW-250 frontier")
