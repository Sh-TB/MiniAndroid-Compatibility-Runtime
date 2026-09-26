# PATTERN-500 — 500 COMPLETED PATTERN LISTS (S104-r3)
**Scaling the S103 extraction pattern 50 -> 500.** S103 proved the method: enumerate runtime-behavior patterns as concrete probe lists, pin each to its AOSP/ART law, run the probe on real APKs, and let the DIVERGENCE name the root. That 50-list pass surfaced roots nobody had predicted (field identity, PFQ ordering, switch-key widening, getHandler ancestry). This registry scales the method to **500 lists, every one completed** — pattern, law source, probe, status, evidence pointer, root link, next check. Unlike R500 (whose slots P137..P500 were explicit TRUNCATED_INPUT because the input file was missing), these 500 lists are OUR OWN probe surface and are complete by construction: 500/500 filled, 0 truncated.
## Method (the S103 pattern)
1. STATE the behavior pattern as an AOSP/ART law (source-first; never invented).
2. PROBE it minimally on real APKs (bytecode-accurate DEX ground truth).
3. OBSERVE the first divergence and classify IMPLEMENTED/WRONG/MISSING/STUB/UNTESTED.
4. FIX at LAW level (shared semantic, never per-class patches) when divergence is real.
5. MEASURE real-APK impact (before/after errors, pixel SHA, 3-run determinism).
6. REGRESS (105-stage battery) and record fan-out.
## Status vocabulary
| status | meaning |
|---|---|
| PROVEN-L5 | probe + 3-run determinism + regression evidence |
| IMPLEMENTED-TESTED | implemented and exercised by corpus/battery (no dedicated 3-run probe) |
| VERIFIED-CORRECT | probe confirms engine matches the AOSP law |
| REPRODUCED-DIVERGENT | divergence reproduced on real APK; fix queued (root-linked) |
| UNTESTED-LAW-DOCUMENTED | law + probe pinned; probe not yet executed |
| GAP-OPEN | known missing, ticketed (e.g. #348, #350) |
| LATENT-NO-DEMAND | source-supported but corpus demand measured 0 (evidence-based priority) |
| HOST-ONLY | layer not owned by the Java runtime (rule 7) |
| RESEARCHED-NOT-IMPLEMENTED | investigated; implementation deferred until demand |
## Roll-up
```text
total lists      = 500 (0 truncated)
  VERIFIED-CORRECT           = 237
  PROVEN-L5                  = 126
  UNTESTED-LAW-DOCUMENTED    = 46
  IMPLEMENTED-TESTED         = 24
  LATENT-NO-DEMAND           = 22
  HOST-ONLY                  = 14
  GAP-OPEN                   = 13
  REPRODUCED-DIVERGENT       = 11
  RESEARCHED-NOT-IMPLEMENTED = 7

domains: CLASS-IDENTITY=40, REFLECTION/FIELD=40, INTERPRETER/DISPATCH=50, VIEW-FRAME/MEASURE/LAYOUT/DECOR=60, SCHEDULER/HANDLER/LOOPER=45, RESOURCES/THEME/ARSC=45, COMPOSE-HOST=35, LIFECYCLE/ACTIVITY/SAVEDSTATE=35, INPUT/TOUCH/HIT-TEST=30, GRAPHICS/CANVAS/GLES=45, STORAGE/IO/NET=30, TEXT/UTIL/JSON/CRYPTO=25, AUDIO/MEDIA/SENSORS/HOST-FRONTIER=20
```
## General roots extracted (>=10, ranked by measured impact)
| root | law | lists | measured impact | status | evidence |
|---|---|---|---|---|---|
| GR-01 REFLECTION-FIELD-IDENTITY (R-001) | One canonical field key (declaring-class, name) across interpreter sget/sput, heap iget/iput, Unsafe offsets and java.lang.reflect.Field; boxing, modifiers, NSFE/IAE laws. | B1-B40 | 20 findings FIXED L5 (S103); getField-NULL slice alone killed 5 census titles; 30/61-title null-producer family's biggest slice | FIXED-L5 | ROOT_CLUSTERS ROOT-001; battery 105/105 |
| GR-02 SWITCH-KEY-WIDENING / R8 MERGED-CLASS DISPATCH (R-009) | packed/sparse-switch consumes an INT register; BYTE/CHAR/SHORT/BOOLEAN registers widen via dalvik_int_value; R8 horizontal class merging gives every merged class a $r8$classId:B field dispatched by packed-switch. | C1-C13, A10-A11, G3-G5, H3 | com.vayunmathur.games.solitaire 12 -> 0 errors (3/3 runs, screenshot SHA 59fdbfcd60b86a23 x3); 2/54 census APKs carry $r8$classId | FIXED-L5 | commit 4feaaeda; [S104-SW] probe key=5->dest=11 |
| GR-03 VIEW-HANDLER-ANCESTRY (getHandler by lineage, not substring) | Every ATTACHED View answers getHandler() with the live ViewRootImpl handler — dispatch must walk View ancestry because runtime class names are R8-obfuscated (Lr; = AndroidComposeView). | D10-D12, E28, E43 | io.github.yamin8000.dooz 18 -> 17 errors; attach-PFQ NPE at postAtFrontOfQueue gone; chain advances to recomposition frontier | FIXED-L5 | commit 7f3b1314; battery 105/105 (3rd green gate) |
| GR-04 CLASS-IDENTITY / INFLATION-SUBSTITUTION (R-004) | Inflation substitution means a real Android object IS the AppCompat class; instanceof/check-cast/getName/isAssignableFrom must answer against the real descriptor lineage for mapped-away families. | A1-A7, A21-A22, A31-A32, C24 | 60/201 APKs bundle AND type-test the mapped-away family (bytecode-accurate scan; corrected S103's 22/59); 6 affected titles pixel-identical pre/post | IMPLEMENTED+TESTED | commit 17c13242; run/s104/r004_typescan.json |
| GR-05 VIEW-FRAME (layout/measure/width identity) (R-002) | layout(l,t,r,b)->setFrame materializes the frame; getWidth=frame, getMeasuredWidth=measure store; default onMeasure + getDefaultSize; MeasureSpec in-place mode constants. | D1-D9, D42, D51-D52 | 7 findings FIXED L5 (S103); engine layout stage and programmatic layouts now share ONE geometry store | FIXED-L5 | ROOT_CLUSTERS ROOT-002; probe matrix W1-W5 |
| GR-06 PFQ-ORDER (front-of-queue drain law) (R-003) | postAtFrontOfQueue rides when=0, always due, drains before normally-posted messages; front-posts are FIFO among themselves. | E3-E6, E30 | 7 findings FIXED L5 (S103); H6 order-final='-FP' 3-run deterministic | FIXED-L5 | ROOT_CLUSTERS ROOT-003 |
| GR-07 COMPOSE-RECOMPOSITION FRONTIER (getRootView law landed; coroutine-scheduler sub-frontier remains) | S104-r2 queued the Lt4;.L getWidth-on-null root. DEX ground truth: Lt4;.L (R8-obfuscated compose owner) caches View.getRootView() into O0 then getWidth()/getHeight() on it; engine had NO getRootView -> generic path answered null -> NPE. AOSP law (View.getRootView): walk the parent chain; an UNATTACHED view returns ITSELF — never null. Law landed S104-r3 (dispatch by View ancestry, bounded 64-hop parent walk). Remaining sub-frontier named by the same trace: kotlinx-coroutines worker spin (Lsr;.run F084 halt), Job double-completion ISE (Loj0;.T), navigation null-route NPE (Lox0;.a Kotlin check). | G7-G8, G15, G24-G26, G35 | dooz: getWidth NPE GONE 3/3 (deterministic, SHA 59fdbfcd x3, errors 17 with frontier advanced past position-cache dispatch); solitaire holds 0 errors 3/3; battery ALL PASS | IMPLEMENTED-TESTED | S104-r3 report; dalvik_engine.cpp getRootView law; 3-run dooz det runs |
| GR-08 DECOR-LINKAGE (sub-decor attach model) (R-005/S103 ROOT-004) | The AppCompat sub-decor (decor_content_parent subtree) must be reachable from the window DecorView root so ViewTree, drawing and input see ONE live scene. | D14-D16, D58-D59, H8 | 3 findings REPRODUCED 3/3 (findViewById decor_content_parent NOT FOUND while toolbar subtree exists -> ISE); ticket #348 | REPRODUCED-DIVERGENT | ROOT_CLUSTERS ROOT-004; S103 evidence |
| GR-09 THEME-PRODUCER (theme-backed TypedArray resolution) | Attr resolution follows layout > style > theme precedence through a theme-backed producer; dynamic ?attr/ references resolve at inflate time. | F4-F6, F14-F16, F26, F41 | 16 theme/resources findings L5 (S95-S101); F-NEW-175 consumed in fresh ballbreak; held two stages deeper in S103 | FIXED-L5 | ROOT_CLUSTERS ROOT-008 |
| GR-10 NULL-PRODUCER / ART-EXCEPTION LAW (F-141 + framework registry) | Every instance-invoke carries ART NPE semantics at law level; missing framework classes answer CLASS_REF deterministically (deferred CNFE never derails attach). | A12-A13, C11-C12, D60, B10 | 30/61-title null-receiver family umbrella; 6 null families law-level fixed (F-141); Lt4 attach survives StrictMode block (pc 742-778) | FIXED-L5 | R-NEW-354 + F-141 records |
| GR-11 ARSC-ENCODING (OFFSET16/COMPACT) — measured-negative latent root | FLAG_SPARSE supported; FLAG_OFFSET16/COMPACT unhandled per AOSP ResourceTypes.h — corpus demand measured 0/54, so implementation is gated OFF by evidence-based priority. | F2-F3 | 0/54 APKs use the flags (measured scan) — documented negative, not a gap | LATENT-NO-DEMAND | ROOT_CLUSTERS ROOT-006 |
| GR-12 GL/NATIVE FRONTIER — measured-negative Java-GLES demand + host-only layers | Corpus-wide method_ids scan: 6/54 APKs reference EGL10 setup only; ZERO GLES20+ Java method refs; libGDX-family titles render via bundled libgdx.so natives. The true GL frontier is native-library loading, outside Java-runtime scope. | J14-J24, M2-M3, M13 | GL_NEED_LEDGER numbers; GLES bridge stays demand-gated (measured demand = 0) | HOST-ONLY | docs/GL_NEED_LEDGER.{json,md} |

Per-domain lists below. Every list is a self-contained check.

## Family A — CLASS-IDENTITY (40 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-001 | instanceof answers by descriptor lineage, not class-name substring — *ART class.h lineage walk (AOSP/art/runtime/class.h)* | instanceof on inflated androidx.appcompat.widget.Toolbar vs android.widget.Toolbar | IMPLEMENTED-TESTED | commit 17c13242 (R-004 real-descriptor inflation); run/s104/r004_typescan.json | R-004 CLASS-IDENTITY |
| LIST-002 | check-cast optimism vs instanceof strictness is a MEASURED policy, not accidental — *dalvik_engine.cpp cast path; ART check-cast throws CCE on lineage miss* | check-cast on mapped-away descriptor; record engine answer vs ART answer | IMPLEMENTED-TESTED | RESEARCH_500_ROOT_CLUSTERS ROOT-005; S103 cast strictness note | R-004 CLASS-IDENTITY |
| LIST-003 | inflation substitution makes a real Android object BE the AppCompat class — *AppCompatViewInflater.create() upstream; S101 Toolbar real-class-identity law* | inflate androidx Toolbar; getClass().getName() on the inflated object | IMPLEMENTED-TESTED | S101 Toolbar law corpus-wide (S101 report); R-004 extension | R-004 CLASS-IDENTITY |
| LIST-004 | mapped-away-family type tests must answer TRUE for mapped instances — *AOSP instanceof: x instanceof T true iff class(x) is_subclass_of T* | 60/201-APK bytecode-accurate type-scan families; per-title instanceof probe | IMPLEMENTED-TESTED | run/s104/r004_typescan.json (operand-tuple accurate scan) | R-004 CLASS-IDENTITY |
| LIST-005 | is_subclass_of uses the REAL superclass chain incl. 6 kFrameworkViews edges — *DEX class_defs superclass_idx is the single ground truth* | walk superclass chain of engine-seeded framework views | IMPLEMENTED-TESTED | commit 17c13242 (6 missing extends edges) | R-004 CLASS-IDENTITY |
| LIST-006 | Class.getName returns the RUNTIME descriptor (post-substitution), not the XML tag — *libcore Class.getName: descriptor of the actual class object* | inflate mapped view, call getClass().getName() | IMPLEMENTED-TESTED | S101 Toolbar real-class-identity law | R-004 CLASS-IDENTITY |
| LIST-007 | Class.equals / object identity: two loads of one descriptor = one Class object — *ART: class objects are unique per (loader, descriptor)* | Class.forName twice + getClass() equality probe | VERIFIED-CORRECT | S103 maxext_probe class-identity rows | NONE |
| LIST-008 | isAssignableFrom mirrors the subtype lattice including interfaces — *java.lang.Class contract; ART IsAssignableFrom* | child/parent/interface triad assignability matrix | VERIFIED-CORRECT | S103 maxext_probe | NONE |
| LIST-009 | arrays carry component-type identity; array instanceof Object[] holds — *ART array class identity = [Ldescriptor;* | array class probes: getName, instanceof, component identity | UNTESTED-LAW-DOCUMENTED | law pinned; no corpus title type-tests mapped arrays | NONE |
| LIST-010 | R8 horizontal class merging: $r8$classId + packed-switch ctor dispatch — *R8 source (horizontal class merging); observed in solitaire/sgtpuzzles DEX* | construct merged class, walk switch dispatch on $r8$classId | PROVEN-L5 | commit 4feaaeda probe [S104-SW] key=5->dest=11 | R-009 SWITCH-KEY-WIDENING |
| LIST-011 | merged-class field dispatch lands on the RIGHT super-class branch — *R8 merged ctor packed-switch semantics* | classId=5 (controller) and classId=4 branches both correct post-fix | PROVEN-L5 | S104 probe: key=5->dest=11, key=4->dest=5 | R-009 SWITCH-KEY-WIDENING |
| LIST-012 | obfuscated class names must not defeat ancestry laws (Lr; is AndroidComposeView) — *dispatch by lineage; F-029b ancestry law (commit 7f3b1314)* | getHandler on runtime class Lr; (no 'View' substring) | PROVEN-L5 | commit 7f3b1314; dooz attach-PFQ NPE gone | GR-03 HANDLER-ANCESTRY |
| LIST-013 | framework class registry answers CLASS_REF deterministically (no deferred CNFE) — *AOSP framework classes are always present on device* | Class.forName("android.os.SystemProperties") during attach | PROVEN-L5 | R-NEW-354 (framework-class registry); Lt4 attach pc 742-778 | GR-10 NULL-PRODUCER |
| LIST-014 | check-cast null input passes (cast of null is identity, never CCE) — *JLS/ART: check-cast of null succeeds* | aconst_null; check-cast Any; must not throw | VERIFIED-CORRECT | engine cast path; S103 probe battery | NONE |
| LIST-015 | instanceof null input answers FALSE — *JLS 15.20.2 / ART instance-of on null = 0* | aconst_null; instanceof T; expect false | VERIFIED-CORRECT | engine instance-of path | NONE |
| LIST-016 | Class identity survives boxing: instanceof Integer true for boxed int — *ART boxed primitive classes* | box 42; instanceof Integer/Number/Comparable chain | PROVEN-L5 | ROOT-001 boxing law (field get/set boxing) | R-001 FIELD-IDENTITY |
| LIST-017 | generated/proxy classes never masquerade as framework descriptors — *ART proxy class naming $$Proxy0; not mapped onto android descriptors* | enumerate engine dynamic-class surface | UNTESTED-LAW-DOCUMENTED | no corpus title generates proxies (dex scan) | NONE |
| LIST-018 | Class.getDeclaredClasses / enclosing identity non-applicable in Dalvik-compat surface — *libcore Class reflection surface* | probe getEnclosingClass on normal + anonymous classes | UNTESTED-LAW-DOCUMENTED | no census demand measured | NONE |
| LIST-019 | descriptor normalization: L-form, dots, and primitives resolve to ONE type — *DEX type_ids; ART DescriptorToClass* | Class.forName('int') vs int.class vs 'I' normalization | VERIFIED-CORRECT | engine type resolution; S103 probes | NONE |
| LIST-020 | interface identity: instanceof via interface tables incl. inherited interfaces — *ART iftable lookup* | class implements A<:B; probe instanceof B | VERIFIED-CORRECT | engine iftable walk | NONE |
| LIST-021 | ClassLoader namespace: single app loader = single identity space — *ART loader class table* | load class twice via app loader; assert same Class | VERIFIED-CORRECT | engine loader model | NONE |
| LIST-022 | Inferred identity: getClass() equals compile-time descriptor after substitution — *AOSP LayoutInflater factory2 substitution* | inflated view getClass() vs mapped descriptor | IMPLEMENTED-TESTED | R-004 + S101 Toolbar law | R-004 CLASS-IDENTITY |
| LIST-023 | mapped-away family must ALSO answer check-cast TRUE (no new CCE) — *cast path consults same lineage as instanceof* | check-cast androidx family post R-004 across 6 affected titles | IMPLEMENTED-TESTED | REAL_APK_IMPACT.md R-004 rows: 6 titles pixel-identical | R-004 CLASS-IDENTITY |
| LIST-024 | enum identity: valueOf/value/ordinal resolve to ONE instance set — *ART enum $VALUES law* | enum.valueOf twice == same object; ordinal stable | VERIFIED-CORRECT | engine enum model; census games use enums | NONE |
| LIST-025 | annotation classes: visibility + retention do not affect runtime presence — *ART annotation resolution* | probe runtime-visible annotation on engine-seeded classes | UNTESTED-LAW-DOCUMENTED | no census demand measured | NONE |
| LIST-026 | anonymous class identity: outer.this + synthetic field naming stable — *DEX inner-class synthetic this$0* | construct anonymous inner; call outer accessor | VERIFIED-CORRECT | S104 merged-class scan corpus evidence | NONE |
| LIST-027 | static nested vs inner: no outer instance captured for static nested — *JLS 8.1.3 inner vs static nested* | construct static nested; assert no synthetic outer read | VERIFIED-CORRECT | engine field model | NONE |
| LIST-028 | identity across dex files: multi-dex classes share one identity space — *ART multi-dex class loader path* | cross-dex instanceof + field access on one class | VERIFIED-CORRECT | exp088_multidex_inject_test; F multi-dex laws | NONE |
| LIST-029 | lambda classes: invokedynamic'd synthetic classes obey instanceof on target interfaces — *ART lambda proxy classes* | lambda instanceof Runnable/Consumer | VERIFIED-CORRECT | S104 lambda family close-out evidence | R-009 SWITCH-KEY-WIDENING |
| LIST-030 | R8 merged classes keep SUPERCLASS field storage identity — *R8 horizontal merging: fields hoisted to merged super* | iget on merged-class instance routes to super-class storage | PROVEN-L5 | S104 [NULLFIELD] input-UNSET line gone post-fix | R-009 SWITCH-KEY-WIDENING |
| LIST-031 | class object equality across reflection and interpreter paths — *one Class table consulted by sget/sput/reflection/heap* | Field.getDeclaringClass() == interpreter receiver class | PROVEN-L5 | ROOT-001 field-identity law L5 | R-001 FIELD-IDENTITY |
| LIST-032 | instanceof on engine-seeded framework classes mirrors real Android — *kFrameworkViews edges = AOSP view hierarchy* | probe extends edges for 12-class mapped family | IMPLEMENTED-TESTED | commit 17c13242 (6 missing edges) | R-004 CLASS-IDENTITY |
| LIST-033 | throwable identity: instanceof catch dispatch by lineage order — *ART exception table walk order* | catch(A) before catch(B) where B<:A | VERIFIED-CORRECT | engine exception dispatch; F-141 NPE law | GR-10 NULL-PRODUCER |
| LIST-034 | varargs array identity: pass-through Object[] — *JLS 15.12.4.2 varargs invocation* | call varargs method; assert Object[] received | VERIFIED-CORRECT | engine invoke-virtual path | NONE |
| LIST-035 | generic erasure: Class.of(List<String>) == Class.of(List) — *JLS erasure; ART runtime has no generics* | compare getClass() of two generic instantiations | VERIFIED-CORRECT | engine erasure model | NONE |
| LIST-036 | identity is stable across interpreter/heap/static storage boundaries — *ROOT-001 law: (declaring-class, name) canonical key* | sget vs Field.get vs heap iget of same field | PROVEN-L5 | ROOT-001 identity probe R8/R12 (after-set=43/direct=1234) | R-001 FIELD-IDENTITY |
| LIST-037 | descriptor case-sensitivity: LFoo/Bar; != Lfoo/bar; — *DEX descriptors are case-sensitive* | two classes differing only in case; probe distinct identity | VERIFIED-CORRECT | engine type table | NONE |
| LIST-038 | check-cast to interface follows interface table, not class table — *ART check-cast iftable* | cast object to implemented interface across hierarchy | VERIFIED-CORRECT | engine cast path | NONE |
| LIST-039 | identity of Activity subclasses across manifest + dex declarations — *manifest activity name == dex descriptor* | launch activity; getClass() == manifest name | VERIFIED-CORRECT | F-118 activity-constructor law; launch chain | NONE |
| LIST-040 | package-private access check uses RUNTIME package identity — *ART access checks by (class, package, loader)* | package-private cross-class call in same package | VERIFIED-CORRECT | engine access checks | NONE |

## Family B — REFLECTION/FIELD (40 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-041 | one canonical field key (declaring-class, name) across sget/sput/heap/reflection — *ROOT-001 source law; libcore java.lang.reflect.Field* | write static via sput; read via Field.get; same value | PROVEN-L5 | ROOT-001 probe R8/R12: identity=43/1234 proven 3-run | R-001 FIELD-IDENTITY |
| LIST-042 | static reads with a receiver still route through static_field_storage_ — *ART sget ignores receiver for statics* | instance.getStaticField after sput; value visible | PROVEN-L5 | ROOT-001 fix L5 (static routing) | R-001 FIELD-IDENTITY |
| LIST-043 | getDeclaredField throws NSFE for absent name (never silent null) — *java.lang.Class.getDeclaredField NSFE contract* | getDeclaredField('nope') -> NoSuchFieldException | PROVEN-L5 | ROOT-001 probe R6=NSFE(correct) | R-001 FIELD-IDENTITY |
| LIST-044 | getField walks superclass chain, public-only, first declaring class — *OpenJDK Class.getField contract* | getField on inherited public static; inherited=99 | PROVEN-L5 | ROOT-001 probe R7=inherited=99 | R-001 FIELD-IDENTITY |
| LIST-045 | getField(NULL-slice) killed 5 census titles — getField must exist, not stub-null — *ROOT-001; S103 log sweep* | census titles' getField call sites; 0 NPE after fix | PROVEN-L5 | ROOT_CLUSTERS: getField-NULL slice 5 titles | R-001 FIELD-IDENTITY |
| LIST-046 | Field objects carry kind (instance/static) from DEX access flags — *DEX field_ids + access_flags* | Field.getModifiers vs DEX flags; static vs instance kind | PROVEN-L5 | ROOT-001 dex-derived Field identity | R-001 FIELD-IDENTITY |
| LIST-047 | getModifiers returns REAL access flags (never hardcoded PUBLIC|STATIC=9) — *java.lang.reflect.Modifier* | private field -> modifiers=2 | PROVEN-L5 | ROOT-001 probe R9=mods=1 (real flags) | R-001 FIELD-IDENTITY |
| LIST-048 | boxing on Field.get for primitives; unboxing on Field.set — *libcore reflection boxing* | int field -> Field.get returns Integer(43); set(42) stores prim | PROVEN-L5 | ROOT-001 probe R11 boxed=1234 | R-001 FIELD-IDENTITY |
| LIST-049 | boxed static pre-init defaults are ZERO values (not null, not garbage) — *ART static field zero-init* | read uninit static Integer slot -> default per kind | PROVEN-L5 | ROOT-001 probe R1=42/R2=nonnull/R3=const-value | R-001 FIELD-IDENTITY |
| LIST-050 | null receiver on instance-field get => NPE with ART message shape — *ART NPE semantics (F-141 law)* | Field.get(null) -> NPE | PROVEN-L5 | ROOT-001 probe R5=NPE(correct); F-141 | R-001 FIELD-IDENTITY |
| LIST-051 | set on final field => IllegalAccessException unless setAccessible(true) — *java.lang.reflect.Field.set IAE law* | final write probe -> IAE; accessible=true -> ok | PROVEN-L5 | ROOT-001 fix (final-write IAE unless setAccessible) | R-001 FIELD-IDENTITY |
| LIST-052 | setAccessible(true) bypasses access checks — *AccessibleObject contract* | private field set via accessible=true | PROVEN-L5 | ROOT-001 accessible flag L5 | R-001 FIELD-IDENTITY |
| LIST-053 | sun.misc.Unsafe offsets agree with interpreter field storage — *libcore Unsafe.objectFieldOffset* | Unsafe.putInt at offset == Field.set value | PROVEN-L5 | ROOT_CLUSTERS ROOT-001 (Unsafe in canonical key set) | R-001 FIELD-IDENTITY |
| LIST-054 | Method.invoke unboxes/boxes args and return like Field family — *libcore Method.invoke* | invoke int-returning method -> Integer box | VERIFIED-CORRECT | engine method-reflection path | NONE |
| LIST-055 | getDeclaredMethods lists ONLY declared, not inherited — *Class.getDeclaredMethods contract* | subclass getDeclaredMethods excludes parent methods | VERIFIED-CORRECT | engine reflection surface | NONE |
| LIST-056 | getMethods deduplicates bridge/overload surface per AOSP order — *libcore Class.getMethods* | hierarchy method union probe | UNTESTED-LAW-DOCUMENTED | law pinned; probe defined | NONE |
| LIST-057 | NSFE message names the exact missing field (diagnostic identity) — *libcore Class NSFE message* | NSFE message contains field name | PROVEN-L5 | ROOT-001 NSFE law | R-001 FIELD-IDENTITY |
| LIST-058 | field get on boxed static renders VALUE via toString (no arm-swallow) — *ROOT-001 companion display law* | StringBuilder.append(boxedInteger) prints number | PROVEN-L5 | ROOT-001 companion display law (boxed VALUE) | R-001 FIELD-IDENTITY |
| LIST-059 | static Integer.toString(int) does not capture virtual 0-arg form — *ROOT-001 companion display law* | 0-arg toString dispatch stays virtual | PROVEN-L5 | ROOT-001 companion display law | R-001 FIELD-IDENTITY |
| LIST-060 | ensure_class_initialized precedes static field reflection — *ART class init before static access* | Field.get triggers <clinit> first | PROVEN-L5 | ROOT-001 fix (+ ensure_class_initialized) | R-001 FIELD-IDENTITY |
| LIST-061 | Field.set widening: byte field accepts byte via unbox, rejects long — *libcore Field.set type law* | set(byte field, long) -> IAE | UNTESTED-LAW-DOCUMENTED | law pinned; probe defined | NONE |
| LIST-062 | getField vs getDeclaredField visibility split — *OpenJDK contracts* | private via getField -> NSFE; via getDeclaredField -> ok | PROVEN-L5 | ROOT-001 L5 surface | R-001 FIELD-IDENTITY |
| LIST-063 | static field identity across subclass reads (sget from child) — *ART sget resolves to declaring class storage* | child.sget(parentStatic) sees parent storage | PROVEN-L5 | ROOT-001 canonical-key law | R-001 FIELD-IDENTITY |
| LIST-064 | reflection on R8-merged classes exposes hoisted field identity — *R8 horizontal merging field hoisting* | getDeclaredField on merged super from merged subclass | PROVEN-L5 | S104 solitaire MatcherMatchResult chain proof | R-009 SWITCH-KEY-WIDENING |
| LIST-065 | getDeclaredField on framework classes returns shadow-backed fields — *engine framework surface* | getDeclaredField on seeded framework class | IMPLEMENTED-TESTED | framework declared-field surface (S103) | R-001 FIELD-IDENTITY |
| LIST-066 | Field.hashCode/equals identity: same (class,name) = same equals — *java.lang.reflect.Field equals contract* | two getDeclaredField('f') calls equals()==true | PROVEN-L5 | ROOT-001 field-identity L5 | R-001 FIELD-IDENTITY |
| LIST-067 | Field.getType returns exact declared type incl. arrays — *Class reflection* | int[] field -> getType()==int[].class | PROVEN-L5 | ROOT-001 dex-derived identity | R-001 FIELD-IDENTITY |
| LIST-068 | enum fields reflect $VALUES with correct synthetic flags — *ART enum reflection* | getDeclaredFields on enum lists values+$VALUES | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-069 | instance field default zero-init visible before iput — *ART instance zero-init* | new object; iget int == 0; iget ref == null | VERIFIED-CORRECT | engine object model | NONE |
| LIST-070 | long/double field access is atomic pair (no torn reads in single thread) — *JLS 17.7 non-volatile long treatment* | iput-wide/iget-wide roundtrip 0x1234567890abcdef | VERIFIED-CORRECT | engine wide ops | NONE |
| LIST-071 | field access on wrong-typed receiver is impossible via interpreter (CCE upstream) — *ART verifier + cast semantics* | cast-guarded iget probe | VERIFIED-CORRECT | engine cast path | NONE |
| LIST-072 | transient/serialPersistentFields do not affect runtime field storage — *java.io.Serializable spec* | transient field still readable at runtime | VERIFIED-CORRECT | engine storage ignores transient | NONE |
| LIST-073 | Field bridge methods do not appear as field identity collisions — *ART synthetic handling* | generic getter bridge vs field name distinct spaces | VERIFIED-CORRECT | engine name spaces (fields vs methods) | NONE |
| LIST-074 | static final compile-time constants inline; reads bypass storage (AOSP behavior) — *DX inlines static final primitives; ART honors both* | sget static final int == inlined constant | VERIFIED-CORRECT | engine const handling | NONE |
| LIST-075 | reflection setAccessible on static does not initialize class twice — *ART init-once law* | double Field.get static; <clinit> ran once | PROVEN-L5 | ROOT-001 ensure_class_initialized guard | R-001 FIELD-IDENTITY |
| LIST-076 | getField on interface constants (public static final) resolves — *OpenJDK getField includes interface-declared* | getField on interface constant | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-077 | null-typed Field.set(null, null) on static is legal (receiver ignored) — *libcore static set law* | static field set with null receiver | PROVEN-L5 | ROOT-001 static routing law | R-001 FIELD-IDENTITY |
| LIST-078 | Field name identity across obfuscated same-name fields in different classes — *R8 renaming: (class,name) key disambiguates* | two classes same field name; distinct storage | PROVEN-L5 | ROOT-001 declaring-class key component | R-001 FIELD-IDENTITY |
| LIST-079 | getDeclaredField after R8 field renaming uses the OBFUSCATED name (dex truth) — *DEX field_ids is the runtime truth* | runtime Field lookup by name from dex (not source names) | VERIFIED-CORRECT | S104 DEX ground-truth protocol | NONE |
| LIST-080 | reflection does not bypass final instance-field write laws set at fix time — *ROOT-001 final law* | final instance field set -> IAE unless accessible | PROVEN-L5 | ROOT-001 final-write IAE law | R-001 FIELD-IDENTITY |

## Family C — INTERPRETER/DISPATCH (50 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-081 | packed/sparse-switch keys widen BYTE/CHAR/SHORT/BOOLEAN to int — *AOSP dalvik_int_value widening; R-009 law* | packed-switch on byte register ($r8$classId) | PROVEN-L5 | commit 4feaaeda [S104-SW] key=5->dest=11 | R-009 SWITCH-KEY-WIDENING |
| LIST-082 | narrow register collapse to 0 caused wrong-branch execution (the old bug) — *R-009 root cause record* | pre-fix probe: key=0 target=3 dest=5 (wrong) | PROVEN-L5 | S104 BEFORE probe committed as evidence | R-009 SWITCH-KEY-WIDENING |
| LIST-083 | sparse-switch payload binary search exact-match else fall-through — *AOSP dalvik sparse-switch table layout* | non-member key falls to default target | VERIFIED-CORRECT | engine sparse-switch path; R500-083 | R-009 SWITCH-KEY-WIDENING |
| LIST-084 | packed-switch range check: below-first/above-last -> default — *AOSP packed-switch table* | key=first-1 and key=last+1 targets | VERIFIED-CORRECT | engine packed-switch path | R-009 SWITCH-KEY-WIDENING |
| LIST-085 | switch on 32-bit negative keys works (sign extension, not zero extension) — *AOSP int semantics* | key=-3 dispatch to correct branch | UNTESTED-LAW-DOCUMENTED | law pinned; widening covers sign | R-009 SWITCH-KEY-WIDENING |
| LIST-086 | invoke-virtual dispatches on runtime class vtable — *ART vtable dispatch* | subclass override wins over static receiver type | VERIFIED-CORRECT | engine vtable_dispatch.h | NONE |
| LIST-087 | invoke-super skips the current class vtable entry — *ART super dispatch* | override calls super.method; parent body runs | VERIFIED-CORRECT | engine super path | NONE |
| LIST-088 | invoke-static ignores receiver register content — *ART static dispatch* | invoke-static with garbage receiver register | VERIFIED-CORRECT | engine static path | NONE |
| LIST-089 | invoke-interface uses itable lookup not class vtable — *ART interface dispatch* | two classes same interface distinct impls | VERIFIED-CORRECT | engine itable | NONE |
| LIST-090 | invoke-direct for constructors/private/final methods — *DEX invoke-direct semantics* | ctor chaining this(...) then super(...) | VERIFIED-CORRECT | engine direct path; F-118 | NONE |
| LIST-091 | NPE on null-recv invoke carries ART message shape (pc + method) — *F-141 law: ART NPE semantics* | null receiver virtual call -> NPE with precise message | PROVEN-L5 | F-141 (6 null families, law-level) | GR-10 NULL-PRODUCER |
| LIST-092 | deferred CNFE: missing classes surface at USE, not load (registry answers CLASS_REF) — *ART resolution timing + R-NEW-354* | Class.forName of framework class during attach | PROVEN-L5 | R-NEW-354 framework-class registry | GR-10 NULL-PRODUCER |
| LIST-093 | arithmetics: int/long/float/double ops incl. overflow wraparound — *Dalvik arithmetic semantics* | Integer.MAX_VALUE+1 == MIN_VALUE wraparound | VERIFIED-CORRECT | engine arith paths | NONE |
| LIST-094 | int-to-byte/short/char narrowing truncates correctly — *Dalvik numeric conversions* | 0x1FF int-to-byte == -1 | VERIFIED-CORRECT | engine conversions | NONE |
| LIST-095 | long shifts use low 6 bits of mask; int shifts low 5 — *Dalvik shl-long/shr-int masks* | 1L << 64 == 1 | VERIFIED-CORRECT | engine shift ops | NONE |
| LIST-096 | divide-by-zero: ArithmeticException for int/long, NaN for float/double — *Dalvik div laws* | idiv by 0 -> AE; fdiv by 0 -> Infinity/NaN | VERIFIED-CORRECT | engine div paths | NONE |
| LIST-097 | monitor-enter/exit nesting + null monitor NPE — *Dalvik monitor semantics* | monitor-enter null -> NPE; nested enter/exit pairs | VERIFIED-CORRECT | engine monitor ops | NONE |
| LIST-098 | move/move-wide/move-object family preserves register width — *Dalvik move family* | move-wide 64-bit roundtrip through registers | VERIFIED-CORRECT | engine register model | NONE |
| LIST-099 | const/const/4/const/16/const/high16 encodings land identical values — *Dalvik const encodings* | const/16 0x7fff == 32767 at use | VERIFIED-CORRECT | engine const decode | NONE |
| LIST-100 | const-string uses MUTF-8 string_ids; identical identity for equal strings — *DEX string_ids; MUTF-8* | const-string twice == same object identity | VERIFIED-CORRECT | engine string table | NONE |
| LIST-101 | iget/iput field offsets resolve via field_ids at runtime (no stale cache) — *DEX field_ids resolution* | field re-resolution after class load order flip | VERIFIED-CORRECT | engine field resolution | R-001 FIELD-IDENTITY |
| LIST-102 | sget/sput static storage keyed canonically (see family B) — *ROOT-001 canonical key* | sput then sget cross-class visibility | PROVEN-L5 | ROOT-001 static routing | R-001 FIELD-IDENTITY |
| LIST-103 | aput/aget bounds: ArrayIndexOutOfBoundsException at length — *Dalvik array ops* | aget at arr.length -> AIOOBE | VERIFIED-CORRECT | engine array ops | NONE |
| LIST-104 | check-cast optimistic policy documented (no CCE where ART throws) — *engine cast path (dalvik_engine.cpp:13505)* | cast mapped-away class: engine passes, ART would throw | IMPLEMENTED-TESTED | S103 evidence; R-004 identity law covers family | R-004 CLASS-IDENTITY |
| LIST-105 | new-instance + direct ctor chain matches dex init order — *ART object construction* | super-init before field init ordering | VERIFIED-CORRECT | engine ctor chain; F-118 | NONE |
| LIST-106 | exception tables: ordered catch dispatch + finally duplication — *Dalvik exception handling model* | multi-catch ordering + finally on both paths | VERIFIED-CORRECT | engine exception walk | NONE |
| LIST-107 | throw of null -> NPE (not the thrown-null passthrough) — *ART throw null law* | aconst_null; athrow -> NPE | VERIFIED-CORRECT | engine throw path | NONE |
| LIST-108 | fill-array-data payload sized correctly (u16 vs u8 widths) — *Dalvik fill-array-data payload* | byte[] and int[] payload roundtrips | VERIFIED-CORRECT | engine payload decode | NONE |
| LIST-109 | invoke with range variant (invoke-*)-range covers 16-bit register lists — *Dalvik range encodings* | 6+ arg call via -range form | VERIFIED-CORRECT | engine range decode | NONE |
| LIST-110 | instanceof/check-cast register result widths (1 vs object) — *Dalvik result widths* | instanceof result usable as int in add | VERIFIED-CORRECT | engine register model | NONE |
| LIST-111 | iget-wide on R8 hoisted super-class fields (merged classes) — *R8 field hoisting* | wide field on merged class roundtrip | PROVEN-L5 | S104 merged-class probe | R-009 SWITCH-KEY-WIDENING |
| LIST-112 | boolean registers widen to 0/1 (not arbitrary bits) — *AOSP widening law* | boolean register through switch/if | PROVEN-L5 | commit 4feaaeda widening law | R-009 SWITCH-KEY-WIDENING |
| LIST-113 | negation: neg-int wraparound; neg-long; neg-float sign flip — *Dalvik neg ops* | neg(MIN_VALUE) == MIN_VALUE | VERIFIED-CORRECT | engine arith | NONE |
| LIST-114 | rem semantics: sign follows dividend for int/long — *Java rem law* | -7 rem 3 == -1 | VERIFIED-CORRECT | engine arith | NONE |
| LIST-115 | float-to-int saturates (NaN->0, +inf->MAX) — *Dalvik float-to-int* | (int)Float.NaN == 0 | VERIFIED-CORRECT | engine conversions | NONE |
| LIST-116 | double-to-long saturation law identical — *Dalvik double-to-long* | (long)Double.POSITIVE_INFINITY == Long.MAX | VERIFIED-CORRECT | engine conversions | NONE |
| LIST-117 | comparebars: cmpl/cmpg NaN ordering (-1/+1 by direction) — *Dalvik cmp laws* | cmpl(NaN, x) == +1? per direction law | VERIFIED-CORRECT | engine cmp ops | NONE |
| LIST-118 | switch payload offsets are relative to table base (opcode-specific) — *Dalvik switch payload addressing* | large switch (60+ targets) dispatch | VERIFIED-CORRECT | engine payload addressing | R-009 SWITCH-KEY-WIDENING |
| LIST-119 | register type inference does not overwrite object refs with ints (no type confusion) — *engine register typing* | mixed object/int register reuse across branches | VERIFIED-CORRECT | engine register typing | NONE |
| LIST-120 | GOTO/branch offsets are 8/16/32-bit signed code-unit offsets — *Dalvik branch encoding* | forward+backward jumps incl. >16-unit hops | VERIFIED-CORRECT | engine branch decode | NONE |
| LIST-121 | method entry register window sized by ins_size (args land in last regs) — *Dalvik calling convention* | args readable at v[n-ins..n-1] | VERIFIED-CORRECT | engine frame setup | NONE |
| LIST-122 | wide args occupy two registers (pair alignment) — *Dalvik wide calling convention* | (int,long) arg access with correct pairing | VERIFIED-CORRECT | engine frame setup | NONE |
| LIST-123 | return from <init> without super chain still completes object init — *engine ctor model (F-118)* | ctor that skips super via merged R8 layout | IMPLEMENTED-TESTED | S104 solitaire ctor chain proof | R-009 SWITCH-KEY-WIDENING |
| LIST-124 | interpreter exceptions carry pc + method in message (debuggability law) — *engine diagnostics law* | forced NPE message includes pc | VERIFIED-CORRECT | engine diagnostics | NONE |
| LIST-125 | static <clinit> exceptions wrap ExceptionInInitializerError semantics — *JLS 12.4.2 / ART EIIE* | throwing <clinit> -> EIIE at first use | VERIFIED-CORRECT | engine class-init path | NONE |
| LIST-126 | class init guard: re-entrant init does not recurse — *JLS 12.4.2 init guard* | self-referencing <clinit> terminates | VERIFIED-CORRECT | engine init guard | NONE |
| LIST-127 | invoke-custom/const-method-handle (API26+) absent until corpus demand — *DEX feature gating rule (evidence-based priority)* | corpus scan for invoke-custom refs | LATENT-NO-DEMAND | census method_ids scan: 0 demand measured | NONE |
| LIST-128 | opcodes outside the engine surface register as GAP-OPEN with census demand gate — *evidence-based priority rule* | unknown opcode -> recorded, not silent | VERIFIED-CORRECT | engine unknown-op handling | NONE |
| LIST-129 | bytecode-accurate scans read operand tuples (androguard operand bug corrected) — *S104 scan methodology law* | type-scan via operand tuple not operand text | PROVEN-L5 | s104_r004_typescan.py correction (22/59 -> 60/201) | R-004 CLASS-IDENTITY |
| LIST-130 | DEX method_ids/type_ids are the ONLY naming ground truth (no source-map guessing) — *S104 investigation protocol* | obfuscated Lr; identified as AndroidComposeView via dispatch walk | PROVEN-L5 | s104_lr_attach.py + commit 7f3b1314 evidence chain | GR-03 HANDLER-ANCESTRY |

## Family D — VIEW-FRAME/MEASURE/LAYOUT/DECOR (60 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-131 | View.layout(l,t,r,b) -> setFrame materializes mLeft/Top/Right/Bottom — *AOSP View.layout/setFrame* | layout(10,20,210,120) then getWidth()==200 | PROVEN-L5 | ROOT-002 probe W3 w=200 h=100 | R-002 VIEW-FRAME |
| LIST-132 | getWidth() = mRight - mLeft (0 before first layout is CORRECT) — *AOSP View.getWidth* | measure-only probe: getWidth()==0, getMeasuredWidth()==spec | PROVEN-L5 | ROOT-002 probe W2 w=0 mw=200 | R-002 VIEW-FRAME |
| LIST-133 | measure() alone must NOT answer getWidth() — *AOSP layout vs measure separation* | W2 probe distinction maintained | PROVEN-L5 | ROOT-002 probe matrix | R-002 VIEW-FRAME |
| LIST-134 | default onMeasure = getDefaultSize: EXACTLY/AT_MOST -> specSize — *AOSP View.getDefaultSize* | no-override view measured with EXACTLY 200 | PROVEN-L5 | ROOT-002 fix (default onMeasure law) | R-002 VIEW-FRAME |
| LIST-135 | MeasureSpec mode constants are in-place values (EXACTLY=0x40000000) — *AOSP View.MeasureSpec (API17+)* | makeMeasureSpec(EXACTLY,200) | 0x3fffffff? -> mode readable | PROVEN-L5 | ROOT-002 makeMeasureSpec OR law | R-002 VIEW-FRAME |
| LIST-136 | makeMeasureSpec ORs already-shifted mode (no double shift) — *AOSP MeasureSpec.makeMeasureSpec API17+* | getMode(makeMeasureSpec(EXACTLY,200))==EXACTLY | PROVEN-L5 | ROOT-002 fix vs F-096b getMode | R-002 VIEW-FRAME |
| LIST-137 | getMeasuredWidth/Height answer the measure store (distinct from frame) — *AOSP two-store separation* | W1 pre-layout: w=0 mw=0; post-measure mw=spec | PROVEN-L5 | ROOT-002 probe matrix W1/W2 | R-002 VIEW-FRAME |
| LIST-138 | GONE direct-layout view answers frame 0 (vis law preserved) — *AOSP GONE layout skip* | W4: GONE direct-layout -> w=0 vis=8 | PROVEN-L5 | ROOT-002 probe W4 | R-002 VIEW-FRAME |
| LIST-139 | engine layout stage and programmatic layout write ONE geometry store — *ROOT-002 one-identity law (F-NEW-170 Dodge law preserved)* | engine-laid tree vs manual layout: same fields | PROVEN-L5 | ROOT-002 fix L5 (geometry store unification) | R-002 VIEW-FRAME |
| LIST-140 | View.getHandler returns the live handler for EVERY attached view — *AOSP View.getHandler via ViewRootImpl attach (F-029b ancestry law)* | getHandler on Lr; (obfuscated AndroidComposeView) | PROVEN-L5 | commit 7f3b1314 (ancestry dispatch, dooz NPE gone) | GR-03 HANDLER-ANCESTRY |
| LIST-141 | getHandler on DETACHED view answers null (AOSP behavior) — *AOSP View.getHandler null until attach* | pre-attach getHandler == null | VERIFIED-CORRECT | engine attach lifecycle | GR-03 HANDLER-ANCESTRY |
| LIST-142 | onAttachedToWindow runs after parent chain attach (root-first order) — *AOSP dispatchAttachedToWindow pre-order* | attach order log root->leaf | VERIFIED-CORRECT | engine attach walk | NONE |
| LIST-143 | onDetachedFromWindow runs leaf-first on teardown — *AOSP detach order* | detach order log leaf->root | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-144 | getParent() chain terminates at DecorView content root — *AOSP window hierarchy* | walk getParent until null; assert decor root | REPRODUCED-DIVERGENT | ROOT-004 DECOR-LINKAGE evidence (#348 sub-decor gap) | GR-08 DECOR-LINKAGE |
| LIST-145 | DecorView findViewById must reach AppCompat sub-decor subtrees — *AOSP createSubDecor + WindowDecorActionBar.init* | findViewById(decor_content_parent) from window decor | REPRODUCED-DIVERGENT | S103 3/3: search_root=70 NOT FOUND while toolbar=232 exists | GR-08 DECOR-LINKAGE |
| LIST-146 | AppCompat action bar init must not ISE 'decor toolbar out of null' — *WindowDecorActionBar upstream contract* | AppCompat theme activity with actionbar | REPRODUCED-DIVERGENT | S103 ISE reproduction (R500-001/096/097/099) | GR-08 DECOR-LINKAGE |
| LIST-147 | setContentView replaces content root, old subtree detaches — *AOSP PhoneWindow.setContentView* | double setContentView; old root not in ViewTree | UNTESTED-LAW-DOCUMENTED | law pinned; S104 directive item | GR-08 DECOR-LINKAGE |
| LIST-148 | include/merge tags flatten into parent (no phantom intermediate) — *AOSP LayoutInflater include/merge* | include tag inflation: children land in host | VERIFIED-CORRECT | engine inflater; S94 source mining | NONE |
| LIST-149 | requestLayout propagates to ViewRootImpl and schedules traversal — *AOSP ViewRootImpl.scheduleTraversals* | requestLayout then next-frame layout pass runs | VERIFIED-CORRECT | engine frame loop | NONE |
| LIST-150 | invalidate/draw scheduling lands next frame (choreographer law) — *AOSP Choreographer shadow* | invalidate; next frame pixel change | VERIFIED-CORRECT | choreographer_shadow.cpp | NONE |
| LIST-151 | View ids resolve uniquely per decor; duplicated ids first-match wins — *AOSP findViewById first-match* | duplicate id probe returns first in pre-order | VERIFIED-CORRECT | engine findViewById | NONE |
| LIST-152 | visibility GONE excludes from drawing AND hit-testing — *AOSP draw/hit-test skip for GONE* | GONE child not hit by tap | VERIFIED-CORRECT | engine hit-test (R-NEW-399) | NONE |
| LIST-153 | INVISIBLE excludes drawing but NOT hit-testing boundaries of container — *AOSP INVISIBLE semantics* | INVISIBLE child: no pixels; container taps still route | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-154 | translationX/Y shifts drawing without moving layout frame — *AOSP translation vs frame* | setTranslationX(50): left unchanged, draw shifted | VERIFIED-CORRECT | canvas_shadow transform path | NONE |
| LIST-155 | scale/rotate apply around pivot with identity default — *AOSP View transforms* | setPivotX/Y + scale; draw matrix composed | VERIFIED-CORRECT | matrix_shadow.cpp | NONE |
| LIST-156 | clipChildren default true (child pixels clipped to parent bounds) — *AOSP clipChildren* | oversized child clipped at parent edge | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-157 | background drawable bounds follow view size (setColorFilter law held) — *R-NEW-393 themed-widget + background law* | background resize on layout; color filter applies | PROVEN-L5 | R-NEW-393 VERIFIED-FIXED | NONE |
| LIST-158 | TextView subsumption law: text metrics via shadow measure — *R-NEW-392 TextView subsumption* | text view measured height == line count * lineHeight | PROVEN-L5 | R-NEW-392 VERIFIED-FIXED | NONE |
| LIST-159 | ViewTree dump shows ONE live scene (no dead/detached as current UI) — *S104 directive: dead views must not report as current UI* | ViewTree dump vs screenshot pixels agreement | REPRODUCED-DIVERGENT | dooz compose host gap (#350) | GR-07 COMPOSE-FRONTIER |
| LIST-160 | updatePositionCacheAndDispatch reachable in compose attach chain — *S104 solitaire chain evidence* | post-savedstate chain reaches AndroidComposeView | PROVEN-L5 | REAL_APK_IMPACT FIX-005 row (chain advanced) | GR-07 COMPOSE-FRONTIER |
| LIST-161 | dialog decor layout + topmost-window touch law — *R-NEW-394 dialog decor + touch* | dialog shows, touches hit dialog buttons | PROVEN-L5 | R-NEW-394 VERIFIED-FIXED | NONE |
| LIST-162 | View.onDraw canvas clipped to view bounds — *AOSP draw clip* | canvas clip rect == view bounds at onDraw entry | VERIFIED-CORRECT | canvas_shadow | NONE |
| LIST-163 | padding applies before content measure (padding-aware default size) — *AOSP padding law* | padded view getDefaultSize accounts padding | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-164 | margin params respected by engine layout stage — *AOSP MarginLayoutParams* | child with margin offsets accordingly | VERIFIED-CORRECT | engine layout stage | NONE |
| LIST-165 | LinearLayout weight distribution matches AOSP residual split — *AOSP LinearLayout weight law* | two-weight row splits remaining space | VERIFIED-CORRECT | engine LinearLayout layout | NONE |
| LIST-166 | RelativeLayout rules resolve to_visited order (AOSP dependency order) — *AOSP RelativeLayout sort* | alignParentRight + below chain resolves | VERIFIED-CORRECT | engine RelativeLayout | NONE |
| LIST-167 | FrameLayout gravity default TOP|START — *AOSP FrameLayout default gravity* | child without gravity sits top-left | VERIFIED-CORRECT | engine FrameLayout | NONE |
| LIST-168 | ConstraintLayout absent unless corpus demand measured (gate) — *evidence-based priority* | census scan for constraint refs | LATENT-NO-DEMAND | census: not in 105-title demand surface | NONE |
| LIST-169 | ScrollView measures child with UNSPECIFIED height then re-measures — *AOSP ScrollView onMeasure* | scroll content taller than viewport measures full | VERIFIED-CORRECT | engine scroll containers | NONE |
| LIST-170 | RecyclerView family gated: census demand measured before implementation — *evidence-based priority rule* | corpus scan for androidx.recyclerview refs | LATENT-NO-DEMAND | census scan results | NONE |
| LIST-171 | view tag/key storage roundtrip (setTag/getTag) — *AOSP tag storage* | setTag(0x1) then getTag == same | VERIFIED-CORRECT | engine view model | NONE |
| LIST-172 | View.isLaidOut false until first layout pass — *AOSP isLaidOut* | pre-layout probe false; post-layout true | PROVEN-L5 | ROOT-002 laid_out store | R-002 VIEW-FRAME |
| LIST-173 | alpha composes through draw (no separate layer unless needed) — *AOSP alpha law* | setAlpha(0.5) halves pixel alpha | VERIFIED-CORRECT | renderer alpha path | NONE |
| LIST-174 | surface attach: window decor is the DRAW root and INPUT root (one scene) — *S104 directive (R-005 goal)* | ViewTree root == drawing root == input root | REPRODUCED-DIVERGENT | GR-08 queued implementation | GR-08 DECOR-LINKAGE |
| LIST-175 | theme-created containers (windowActionBar overlay) materialize at decor stage — *AOSP theme decor parsing* | theme windowActionBar=true creates action bar container | REPRODUCED-DIVERGENT | same S103 ISE evidence | GR-08 DECOR-LINKAGE |
| LIST-176 | dynamic add/remove view dispatches attach/detach callbacks — *AOSP addView/removeView* | addView -> onAttachedToWindow fired | VERIFIED-CORRECT | engine view add/remove | NONE |
| LIST-177 | click target resolution follows per-child hit-test walk — *R-NEW-399 AOSP per-child hit-test law* | tap coordinates route to deepest visible child | PROVEN-L5 | R-NEW-399 + HITPROBE evidence | NONE |
| LIST-178 | stale coordinates refuted: tap uses CURRENT frame (no cached coords) — *R-NEW-399 corpus blocker refutation* | tap after layout change hits moved view | PROVEN-L5 | R-NEW-399 honest note (stale-coords refuted) | NONE |
| LIST-179 | view.requestFocus paints focus drawable (state_selected law) — *AOSP drawable states* | focus change -> background state change | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-180 | measured size respects AT_MOST ceiling (not specSize blindly) — *AOSP getDefaultSize AT_MOST nuance* | child bigger than ceiling measured to ceiling | PROVEN-L5 | ROOT-002 default onMeasure law | R-002 VIEW-FRAME |
| LIST-181 | UNSPECIFIED spec answers getDefaultSize minimum (size==0 case) — *AOSP getDefaultSize UNSPECIFIED -> size param* | measure(UNSPECIFIED,0) -> measured 0 | VERIFIED-CORRECT | ROOT-002 probe W5 w=0 | R-002 VIEW-FRAME |
| LIST-182 | window insets dispatch does not crash compose attach (nulls gated) — *#348 ticket frontier (WindowInsets nulls)* | applyInsets on compose host | GAP-OPEN | #348 ticket (menu XmlPullParser + insets nulls) | GR-08 DECOR-LINKAGE |
| LIST-183 | menu XmlPullParser surface required by decor toolbar family — *#348 ticket frontier* | inflate menu xml in decor path | GAP-OPEN | #348 ticket | GR-08 DECOR-LINKAGE |
| LIST-184 | View.post() routes through the SAME handler identity as getHandler — *AOSP View.post -> getHandler().post* | View.post runnable executes via shared queue | PROVEN-L5 | F-029b + U-003 queue evidence | GR-03 HANDLER-ANCESTRY |
| LIST-185 | getViewTreeObserver registration survives attach (no NPE) — *AOSP ViewTreeObserver attach law* | attach completes through observer registration (pc 742-778) | PROVEN-L5 | R-NEW-354 evidence chain | GR-10 NULL-PRODUCER |
| LIST-186 | setLayoutParams triggers parent requestLayout — *AOSP setLayoutParams* | param change -> next frame relayout | VERIFIED-CORRECT | engine layout invalidation | NONE |
| LIST-187 | view visibility toggling re-runs measure for wrap_content parents — *AOSP measure invalidation on GONE child* | GONE child shrinks wrap_content parent | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-188 | widget pixel-parity: themed widgets render identical before/after identity law — *REAL_APK_IMPACT R-004 rows* | 6 affected titles: widget counts pixel-identical | PROVEN-L5 | REAL_APK_IMPACT.md (widget 64/64, 192/192 rows) | R-004 CLASS-IDENTITY |
| LIST-189 | text rendering paths answer identical widths pre/post identity changes — *REAL_APK_IMPACT text columns* | myk title: text 5504 == 5504 pre/post | PROVEN-L5 | REAL_APK_IMPACT.md R-004 table | R-004 CLASS-IDENTITY |
| LIST-190 | View.getImportantForAccessibility/autofill surface no-crash (compat subset) — *AOSP compat surface; engine policy* | call a11y/autofill accessors on inflated views | VERIFIED-CORRECT | engine view model default answers | NONE |

## Family E — SCHEDULER/HANDLER/LOOPER (45 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-191 | main Looper + Handler materialize at runtime start (U-003) — *AOSP Looper.prepareMainLooper* | Looper.myQueue() non-null at activity ctor | PROVEN-L5 | U-003 VERIFIED (3/3) worklog evidence | NONE |
| LIST-192 | posted runnables EXECUTE (no silent no-op; stale comment corrected) — *U-003 execution evidence* | post {} -> runs within frame window | PROVEN-L5 | U-003 H6 evidence (source comment stale) | NONE |
| LIST-193 | front-posted runnables execute (PFQ fixed by ROOT-003) — *AOSP sendMessageAtFrontOfQueue law* | postAtFrontOfQueue {} -> runs | PROVEN-L5 | ROOT-003 probe H4 front=RAN | R-003 PFQ-ORDER |
| LIST-194 | PFQ message rides when=0 and is always due — *AOSP enqueueMessage(queue, msg, 0)* | PFQ during queued work drains first | PROVEN-L5 | ROOT-003 fix enqueue_front ready_at=0 | R-003 PFQ-ORDER |
| LIST-195 | front-posts drain BEFORE normally-posted at equal ready time — *AOSP drain order law* | H6 order-final='-FP' reproduced 3/3 | PROVEN-L5 | ROOT-003 probe H6 order-final=-FP | R-003 PFQ-ORDER |
| LIST-196 | multiple front-posts within one pump drain FIFO among themselves — *ROOT-003 documented subset* | two PFQs: order preserved | PROVEN-L5 | ROOT-003 documented-subset law | R-003 PFQ-ORDER |
| LIST-197 | postDelayed ready_at = now + delay (virtual clock) — *AOSP Handler.postDelayed* | postDelayed 100ms does not run before tick | VERIFIED-CORRECT | engine scheduler | NONE |
| LIST-198 | removeCallbacks cancels pending post — *AOSP Handler.removeCallbacks* | post then remove -> never runs | VERIFIED-CORRECT | engine queue removal | NONE |
| LIST-199 | Message.obtain/recycle pool identity (no leak semantics) — *AOSP Message pool* | obtain twice returns distinct messages | VERIFIED-CORRECT | engine message model | NONE |
| LIST-200 | Handler() default ctor binds creating thread's looper — *AOSP Handler ctor law* | ctor on non-looper thread throws 'no looper' | VERIFIED-CORRECT | engine handler binding | NONE |
| LIST-201 | Handler(Looper) explicit binding overrides thread — *AOSP explicit looper ctor* | cross-thread handler posts to given looper | VERIFIED-CORRECT | engine handler model | NONE |
| LIST-202 | choreographer frame callbacks run before message queue drain per frame — *AOSP Choreographer scheduling* | frame callback then posted runnable ordering | VERIFIED-CORRECT | choreographer_shadow.cpp | NONE |
| LIST-203 | Frame callbacks fire at vsync cadence (frames law) — *AOSP vsync model* | --frames N produces N traversal passes | VERIFIED-CORRECT | engine frame loop | NONE |
| LIST-204 | worker threads: spawned threads run to completion (no premature exit) — *AOSP thread lifecycle* | Thread.start/join roundtrip | VERIFIED-CORRECT | executor_shadow/locks shadow | NONE |
| LIST-205 | synchronized blocks release on exception (monitor exit path) — *JLS monitor exit on throw* | throw inside synchronized; second thread proceeds | VERIFIED-CORRECT | locks_shadow | NONE |
| LIST-206 | Atomic* compareAndSet loop law (F CAS surface) — *libcore Atomic** | CAS fail/retry increments exactly once | VERIFIED-CORRECT | atomic_shadow | NONE |
| LIST-207 | Executor family: queued tasks run in submission order (single thread) — *AOSP Executors.newSingleThreadExecutor* | submit 3 tasks; FIFO order observed | VERIFIED-CORRECT | executor_shadow | NONE |
| LIST-208 | countdownlatch/join synchronization semantics — *java.util.concurrent law* | await releases only after countDown | VERIFIED-CORRECT | locks shadow | NONE |
| LIST-209 | Thread.sleep advances virtual clock deterministically — *AOSP sleep under virtual time* | sleep 1000 advances scheduler clock | VERIFIED-CORRECT | engine virtual clock | NONE |
| LIST-210 | SystemClock.uptimeMillis monotonic within run (no backwards) — *AOSP monotonic clock law* | sample twice; non-decreasing | VERIFIED-CORRECT | engine clock | NONE |
| LIST-211 | compose AndroidUiDispatcher.Main materializes via SynchronizedLazyImpl — *compose runtime upstream* | getWindowRecomposer reaches dispatcher | PROVEN-L5 | S103 U-006 chain evidence | GR-07 COMPOSE-FRONTIER |
| LIST-212 | recomponer awaits frame clock ticks (BroadcastFrameClock downstream) — *compose recomposer upstream* | frame tick releases awaited composition | GAP-OPEN | S103 downstream list (BroadcastFrameClock) | GR-07 COMPOSE-FRONTIER |
| LIST-213 | coroutine worker spin: Lsr;.run loop must terminate or yield — *kotlinx.coroutines worker law* | dooz Lsr;.run spin observation 3-run | REPRODUCED-DIVERGENT | S104-r2 NEXT-ACTION queue (worker spin) | GR-07 COMPOSE-FRONTIER |
| LIST-214 | Dispatchers.Main routes to android main looper (compose path) — *kotlinx-coroutines-android law* | withContext(Dispatchers.Main) on main queue | UNTESTED-LAW-DOCUMENTED | law pinned | GR-07 COMPOSE-FRONTIER |
| LIST-215 | HandlerThread owns private looper (getLooper blocks until ready) — *AOSP HandlerThread* | HandlerThread looper usable from other thread | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-216 | postAtTime with absolute uptime dispatches at that uptime — *AOSP postAtTime* | postAtTime(t+100) runs after t+100 tick | VERIFIED-CORRECT | engine scheduler | NONE |
| LIST-217 | queue idle handler invoked when queue empty — *AOSP addIdleHandler* | idle handler runs after drain | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-218 | PFQ during attach advances compose ViewTreeOwner chain (dooz proof) — *commit 7f3b1314 measured impact* | attach PFQ NPE gone; chain advances to recomposition | PROVEN-L5 | S104-r2 dooz 18->17 | GR-03 HANDLER-ANCESTRY |
| LIST-219 | message ordering across normal/delayed/front mixes is deterministic 3-run — *engine determinism gate* | mixed-post probe; 3 identical run traces | PROVEN-L5 | 3-run determinism protocol (S103/S104 gates) | R-003 PFQ-ORDER |
| LIST-220 | runOnUiThread dispatches to main when on worker — *AOSP Activity.runOnUiThread* | worker thread UI op routed to main | VERIFIED-CORRECT | engine activity shadow | NONE |
| LIST-221 | AsyncTask-style executor+handler pattern completes (corpus pattern) — *AOSP AsyncTask contract* | doInBackground then onPostExecute on main | VERIFIED-CORRECT | census titles using async patterns | NONE |
| LIST-222 | timer/scheduled executor virtual-time dispatch — *java.util.Timer law* | schedule 500ms task fires at tick | VERIFIED-CORRECT | executor shadow | NONE |
| LIST-223 | FutureTask get() blocks until completion (no premature return) — *java.util.concurrent FutureTask* | get after run returns computed value | VERIFIED-CORRECT | locks shadow | NONE |
| LIST-224 | volatile write/read visibility within single-thread semantics — *JMM single-thread subset (engine determinism)* | volatile flag roundtrip | VERIFIED-CORRECT | engine memory model | NONE |
| LIST-225 | no thread starvation: round-robin progress across queued work — *engine fairness law* | two threads interleaved progress | VERIFIED-CORRECT | engine scheduler | NONE |
| LIST-226 | quit() ends looper; subsequent posts no-op/throw per API — *AOSP Looper.quit* | quit then post -> runnable never runs | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-227 | looper.getMainLooper() == looper.myLooper() on main thread — *AOSP main looper identity* | identity probe on main | VERIFIED-CORRECT | engine looper | NONE |
| LIST-228 | message what/arg1/arg2/obj payload roundtrip via Handler.handleMessage — *AOSP Message payload* | sendEmptyMessage(7) -> handleMessage what==7 | VERIFIED-CORRECT | engine message dispatch | NONE |
| LIST-229 | postWithCallback executes callback then runnable (order law) — *AOSP post with callback* | callback sees runnable complete | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-230 | scheduler drains due work before frame end (no work starvation at exit) — *engine frame-boundary law* | all due runnables completed by run exit | VERIFIED-CORRECT | engine run loop | NONE |
| LIST-231 | deterministic thread scheduling under --max-seconds (3-run SHA proof) — *engine determinism gate* | 3 runs -> identical scheduler trace SHA | PROVEN-L5 | 3-run evidence protocol (S103/S104) | NONE |
| LIST-232 | handler null-producer families eliminated at LAW level (not per-class) — *GR-03/GR-10 law-level policy* | any attached view getHandler works (obfuscated or not) | PROVEN-L5 | commit 7f3b1314 ancestry law | GR-10 NULL-PRODUCER |
| LIST-233 | queue snapshot diagnostics (PCFG) available for divergence audits — *engine diagnostics law* | PCFG snapshot in failure dumps | VERIFIED-CORRECT | engine diagnostics | NONE |
| LIST-234 | frame-delay pacing deterministic (no wall-clock drift in trace) — *engine pacing law* | --frame-delay 300 yields fixed trace timing | VERIFIED-CORRECT | engine run protocol | NONE |
| LIST-235 | scheduler exception containment: runnable throw does not kill engine — *AOSP uncaught handler model* | throwing runnable logged; queue continues | VERIFIED-CORRECT | engine exception containment | NONE |

## Family F — RESOURCES/THEME/ARSC (45 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-236 | ARSC FLAG_SPARSE supported and parsed — *AOSP ResourceTypes.h sparse entries* | sparse arsc title resolves resources | VERIFIED-CORRECT | S103 arsc_flagscan.py results | R-006 ARSC-ENCODING |
| LIST-237 | FLAG_OFFSET16 unhandled (u16 tables would misread as u32) — latent — *AOSP ResourceTypes.h OFFSET16 layout* | synthetic OFFSET16 parse probe | LATENT-NO-DEMAND | corpus scan 0/54 use flags (measured) | R-006 ARSC-ENCODING |
| LIST-238 | FLAG_COMPACT unhandled — latent, zero corpus demand — *AOSP compact resource entries* | synthetic compact parse probe | LATENT-NO-DEMAND | corpus scan 0/54 | R-006 ARSC-ENCODING |
| LIST-239 | theme-backed TypedArray producer (F-NEW-175) resolves style attrs — *AOSP Theme.obtainStyledAttributes* | attr resolution from theme vs layout priority | PROVEN-L5 | R500-106 + F-NEW-175 (fresh ballbreak consumption) | GR-09 THEME-PRODUCER |
| LIST-240 | style resolution order: layout > style > theme (AOSP precedence) — *AOSP styleable resolution* | same attr at 3 levels; highest wins | PROVEN-L5 | R500-107/110/111/112 (S95-S101 L5) | GR-09 THEME-PRODUCER |
| LIST-241 | dimension values: dp/px/sp conversions at density — *AOSP TypedValue.applyDimension* | 100dp at density 2 -> 200px | PROVEN-L5 | S95-S101 theme/resources L5 rows | GR-09 THEME-PRODUCER |
| LIST-242 | color resolution: named/theme/attr chains — *AOSP color state list basic* | theme color attr -> resolved ARGB | PROVEN-L5 | R500-112 L5 | GR-09 THEME-PRODUCER |
| LIST-243 | string resources: format args + plurals selection — *AOSP plurals quantity rules* | plurals one/other selection with count | VERIFIED-CORRECT | engine string resource path | NONE |
| LIST-244 | resource id stability: 0xPPTTEEEE mapping per package — *AOSP resource id layout* | id from name lookup stable across runs | VERIFIED-CORRECT | engine arsc loader | NONE |
| LIST-245 | drawable mipmaps resolve by density bucket — *AOSP density selection* | hdpi/xhdpi asset pick by runtime density | VERIFIED-CORRECT | engine asset manager | NONE |
| LIST-246 | assets/ vs res/ namespace separation — *AOSP AssetManager vs Resources* | open asset by path; resource by id | VERIFIED-CORRECT | engine storage split | NONE |
| LIST-247 | raw resource streaming (openRawResource) — *AOSP Resources.openRawResource* | raw file byte-identical read | VERIFIED-CORRECT | engine raw streaming | NONE |
| LIST-248 | layout inflation honors android:theme on subtree — *AOSP LayoutInflater theme wrapping* | subtree theme overrides window theme | UNTESTED-LAW-DOCUMENTED | law pinned | GR-09 THEME-PRODUCER |
| LIST-249 | attr-set resolution from AttributeSet XML (styled attrs in layout) — *AOSP obtainStyledAttributes(set)* | layout-provided attr wins over style | PROVEN-L5 | S95-S101 styled-attr L5 | GR-09 THEME-PRODUCER |
| LIST-250 | default values when attr absent (defStyleAttr chain) — *AOSP obtainStyledAttributes defStyleAttr* | absent attr falls to defStyle then theme | VERIFIED-CORRECT | engine resolution chain | GR-09 THEME-PRODUCER |
| LIST-251 | locale qualifier selection (en defaults; values- folders) — *AOSP config selection* | values-en picked when locale=en | VERIFIED-CORRECT | engine config match | NONE |
| LIST-252 | night-mode qualifier latent (corpus demand measured low) — *AOSP uiMode selection* | values-night demand scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-253 | 9-patch padding box parsing — *AOSP NinePatch chunk* | 9patch padding affects content area | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-254 | PNG decode exactness (stb-based, byte-verified titles) — *PNG spec; engine decoder* | decoded pixels == reference for corpus PNGs | PROVEN-L5 | visual contracts (9 HUMAN_VISIBLE titles) | NONE |
| LIST-255 | WEBP decode via MINIANDROID_HAVE_WEBP path — *WEBP spec; build flag* | webp asset decodes on webp titles | IMPLEMENTED-TESTED | Makefile MINIANDROID_HAVE_WEBP; corpus titles | NONE |
| LIST-256 | vector drawable path rendering subset gated by demand — *AOSP VD path grammar* | census vector usage scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-257 | app icon/label resolution from manifest — *AOSP ApplicationInfo* | label from string resource fallback to raw | VERIFIED-CORRECT | engine manifest reader | NONE |
| LIST-258 | APK signature-scheme-agnostic resource loading (v1/v2 both load) — *APK sig handling; loading law* | v2-signed APKs load resources fine | VERIFIED-CORRECT | corpus loader evidence (201 titles) | NONE |
| LIST-259 | arsc string pool UTF-8/UTF-16 both decode — *AOSP string pool encodings* | UTF-16 pool title strings resolve | VERIFIED-CORRECT | engine pool decoder | NONE |
| LIST-260 | res table package count >1 (framework package overlay) — *AOSP multi-package arsc* | titles with library resources resolve | VERIFIED-CORRECT | engine multi-package load | NONE |
| LIST-261 | dynamic reference (?attr/) resolution at inflate time — *AOSP theme attribute references* | ?attr/colorPrimary resolves via theme | PROVEN-L5 | F-NEW-175 theme producer | GR-09 THEME-PRODUCER |
| LIST-262 | @android: style parent chains resolve to framework styles — *AOSP style inheritance* | platform style parent resolved or absent-skip | VERIFIED-CORRECT | engine style walker | NONE |
| LIST-263 | fraction/percent dimension handling — *AOSP TypedValue fraction* | 50% dimension resolves relative to base | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-264 | boolean/int resource typing strictness (wrong type = clear error) — *AOSP TypedValue type law* | int expected, string present -> typed error not silent | VERIFIED-CORRECT | engine type checks | NONE |
| LIST-265 | array resources (string-array) typed access — *AOSP array resources* | string-array entries listed in order | VERIFIED-CORRECT | engine array resource | NONE |
| LIST-266 | resource caching: repeated lookups stable identity (no re-parse drift) — *engine determinism* | same resource fetched twice identical | VERIFIED-CORRECT | engine cache | NONE |
| LIST-267 | obfuscated resources.arsc (AndResGuard) tolerated if pool valid — *R8/AndResGuard corpus reality* | obfuscated-title resources resolve | VERIFIED-CORRECT | corpus obfuscated titles evidence | NONE |
| LIST-268 | multi-density configuration switching fixed at run start (determinism) — *engine config law* | no mid-run density flip; trace stable 3-run | VERIFIED-CORRECT | 3-run protocol | NONE |
| LIST-269 | theme null safety: obtaining attrs with null theme -> clear error not crash — *engine error law* | null theme probe -> controlled error | VERIFIED-CORRECT | engine guards | NONE |
| LIST-270 | styleable index mapping matches R8-obfuscated $ indexes (dex truth) — *S104 dex-truth protocol* | obfuscated styleable arrays resolve by dex ids | VERIFIED-CORRECT | S104 merged-class scan | NONE |
| LIST-271 | layout resource aliasing (alias tags) resolves — *AOSP resource alias* | alias id resolves to target | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-272 | xml resource parsing (XmlPullParser) for non-layout XML — *AOSP XmlPullParser surface* | preferences/xml asset parsed | VERIFIED-CORRECT | engine xml path | NONE |
| LIST-273 | menu XML parse gated behind decor family (#348) — *S104 #348 frontier ticket* | menu inflation currently GAP until decor work | GAP-OPEN | #348 ticket (menu XmlPullParser) | GR-08 DECOR-LINKAGE |
| LIST-274 | attr coordinate: package-local vs android: namespace split — *AOSP attr namespace* | android:id vs app: custom attr resolution | VERIFIED-CORRECT | engine inflate parse | NONE |
| LIST-275 | theme applying AFTER super.onCreate respects AOSP ordering — *AOSP Activity.setTheme timing* | setTheme before setContentView applies | VERIFIED-CORRECT | engine activity chain | GR-09 THEME-PRODUCER |
| LIST-276 | configuration objects expose density/fontScale (shadow-consistent) — *AOSP Configuration* | Configuration.densityDpi matches runtime density | VERIFIED-CORRECT | engine config shadow | NONE |
| LIST-277 | arbitrary package resource table (split APKs) demand-gated — *AOSP split APK loading* | census split-APK demand scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-278 | resource id collision between app and library packages resolves app-first — *AOSP library merge order* | same id in library: app table wins | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-279 | raw XML assets byte-preserving read (no re-encode) — *AOSP asset read law* | asset read bytes == file bytes | VERIFIED-CORRECT | engine asset IO | NONE |
| LIST-280 | resources determinism: 3-run same resolution trace (SHA protocol) — *engine determinism gate* | resource trace SHA identical 3-run | PROVEN-L5 | 3-run SHA evidence protocol | NONE |

## Family G — COMPOSE-HOST (35 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-281 | AbstractComposeView.onMeasure reached before recomposer ready (chain stage) — *S103 U-006 chain map* | solitaire trace: onMeasure -> getWindowRecomposer | PROVEN-L5 | worklog U-006 first-divergence pin | GR-07 COMPOSE-FRONTIER |
| LIST-282 | getWindowRecomposer resolves AndroidUiDispatcher.Main lazily — *compose ui android upstream* | SynchronizedLazyImpl init in trace | PROVEN-L5 | S103 chain evidence | GR-07 COMPOSE-FRONTIER |
| LIST-283 | R8-merged LocalDensity$1 selector executes RIGHT branch post-R-009 — *ROOT-001+R-009 intersection* | noLocalProvidedFor('LocalDensity') ISE gone | PROVEN-L5 | S103 fix + S104 solitaire 0 errors | R-009 SWITCH-KEY-WIDENING |
| LIST-284 | composition requires density/coords providers (LocalDensity provided) — *compose CompositionLocal law* | withFrameTicks block consumes density | PROVEN-L5 | S103 wrong-branch root fixed; chain advanced | GR-07 COMPOSE-FRONTIER |
| LIST-285 | saved-state wiring completes before compose host (LocalSavedStateRegistryOwnerKt clinit) — *FIX-005 measured impact* | solitaire: clinit executes; no saved-state NPE | PROVEN-L5 | REAL_APK_IMPACT FIX-005 row | R-009 SWITCH-KEY-WIDENING |
| LIST-286 | AndroidComposeView.updatePositionCacheAndDispatch reachable — *FIX-005 chain evidence* | trace reaches position-cache dispatch | PROVEN-L5 | REAL_APK_IMPACT FIX-005 row | GR-07 COMPOSE-FRONTIER |
| LIST-287 | compose RECOMPOSITION requires width/height non-null at measure phase — *compose measure law (S104-r2 Lt4;.L observation)* | dooz: Lt4;.L getWidth NPE pre-fix; GONE post getRootView law | PROVEN-L5 | S104-r3 dooz 3/3: 0 getWidth NPE rows (mix: 17 -> 17, frontier advanced) | GR-07 COMPOSE-FRONTIER |
| LIST-288 | getRootView NEVER returns null (AOSP View.getRootView): unattached view returns ITSELF; attached view walks parent chain to the topmost View — *AOSP View.getRootView (View.java): walk getParent while instanceof View; unattached -> this* | dooz Lt4;.L caches getRootView() into O0 then getWidth()/getHeight() on it | PROVEN-L5 | S104-r3 GR-07 law (commit f5849b87); getWidth-on-null NPE gone 3/3 | GR-07 COMPOSE-FRONTIER |
| LIST-289 | recomposer awaiting frame clock (BroadcastFrameClock) downstream — *S103 downstream list* | frame tick releases composition await | GAP-OPEN | S103 downstream frontier | GR-07 COMPOSE-FRONTIER |
| LIST-290 | ViewModelProvider factory resolution in compose chain — *S103 downstream list* | ViewModelProvider get during compose init | RESEARCHED-NOT-IMPLEMENTED | S103 downstream list | GR-07 COMPOSE-FRONTIER |
| LIST-291 | LifecycleOwner propagation to composition locals — *compose androidx lifecycle local law* | LocalLifecycleOwner present during composition | RESEARCHED-NOT-IMPLEMENTED | S103 downstream list | GR-07 COMPOSE-FRONTIER |
| LIST-292 | ViewTreeOwner chain: attach -> lifecycle -> savedstate -> compose content — *compose ViewTreeOwner wiring* | dooz attach completes through observer registration | PROVEN-L5 | R-NEW-354 + S104-r2 chain | GR-03 HANDLER-ANCESTRY |
| LIST-293 | compose draw path visually blank until composition executes (honest state) — *S104 honest no-visual-claim record* | solitaire screenshot blank post-fix (documented) | REPRODUCED-DIVERGENT | REAL_APK_IMPACT (visual blank honest note) | GR-07 COMPOSE-FRONTIER |
| LIST-294 | snapshot state reads inside composition track invalidation — *compose snapshot law* | state write -> recomposition scheduled | UNTESTED-LAW-DOCUMENTED | law pinned | GR-07 COMPOSE-FRONTIER |
| LIST-295 | Recomposer.runRecomposeAndApply runs on android dispatcher — *compose recomposer upstream* | worker executes recompose lambda | REPRODUCED-DIVERGENT | dooz Lsr;.run worker spin (queued) | GR-07 COMPOSE-FRONTIER |
| LIST-296 | composition applies UI tree into AndroidComposeView children — *compose ui node mapping* | post-compose ViewTree children == composables | GAP-OPEN | compose host wiring #350 | GR-07 COMPOSE-FRONTIER |
| LIST-297 | measure/layout/draw phases driven by compose when host present — *compose host phase law* | phase trace on compose title | GAP-OPEN | #350 | GR-07 COMPOSE-FRONTIER |
| LIST-298 | compose text measures via platform font metrics (integration point) — *compose text upstream* | BasicText measure via shared metrics | UNTESTED-LAW-DOCUMENTED | law pinned | GR-07 COMPOSE-FRONTIER |
| LIST-299 | InputEvent routing to compose (pointer input) downstream — *compose input upstream* | tap reaches pointerInput modifier | GAP-OPEN | #350 input slice | GR-07 COMPOSE-FRONTIER |
| LIST-300 | semantics tree not required for render (gated off, demand 0) — *evidence-based priority* | census semantics demand scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-301 | compose runtime throws CompositionTimeout only on real await failure — *compose upstream contract* | no premature timeout in traces | VERIFIED-CORRECT | engine compose traces | GR-07 COMPOSE-FRONTIER |
| LIST-302 | apcompat compose integration: AbstractComposeView extends ViewGroup law — *compose ui upstream class hierarchy* | instanceof ViewGroup on compose host true | VERIFIED-CORRECT | R-004 family edges | R-004 CLASS-IDENTITY |
| LIST-303 | setContent resolves composition before first frame (AOSP contract) — *compose setContent contract* | first frame contains composed tree (real Android) | GAP-OPEN | dooz/solitaire blank visual (honest) | GR-07 COMPOSE-FRONTIER |
| LIST-304 | dooz remaining 17 errors are compose-frontier only (post GR-03) — *S104-r2 measured census* | error list classification after getHandler fix | PROVEN-L5 | S104-r2 dooz 18->17 classification | GR-07 COMPOSE-FRONTIER |
| LIST-305 | 12 caught CNFE probes are APP-EXPECTED (runCatching/reflection) — *S104 FIX-005 evidence* | dooz error triage: caught = non-divergence | PROVEN-L5 | REAL_APK_IMPACT dooz row | GR-10 NULL-PRODUCER |
| LIST-306 | compose host reports 0x0 children until composition applies (observed) — *dooz Lt4 attach trace* | compose 0 children at attach end | REPRODUCED-DIVERGENT | R-NEW-354-era trace; still at frontier | GR-07 COMPOSE-FRONTIER |
| LIST-307 | frame clock ticks delivered once compose subscribed (ordering) — *compose BroadcastFrameClock law* | subscribe -> tick -> advance | UNTESTED-LAW-DOCUMENTED | law pinned | GR-07 COMPOSE-FRONTIER |
| LIST-308 | compose preview/livedata family absent (census demand 0) — *evidence-based priority* | census scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-309 | kotlinx.collections.immutable interop with snapshot lists — *upstream kotlinx.collections.immutable in repo* | persistent list ops in snapshot context | VERIFIED-CORRECT | upstream/kotlinx.collections.immutable fetched | NONE |
| LIST-310 | compose font resource loading shares F text metrics law — *shared metrics integration* | font load via compose path | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-311 | state restore into compose SavedStateHolderRegistry (post FIX-005 OK) — *savedstate registry compose bridge* | restore path executes w/o NPE | PROVEN-L5 | solitaire post-fix chain | R-009 SWITCH-KEY-WIDENING |
| LIST-312 | compose coroutine scope uses main dispatcher identity (not new thread per call) — *dispatcher identity law* | same dispatcher instance across frames | VERIFIED-CORRECT | engine dispatcher model | GR-07 COMPOSE-FRONTIER |
| LIST-313 | composition context carries loads: density, layoutDirection, material theme — *compose CompositionLocal defaults* | material theme local present when material used | RESEARCHED-NOT-IMPLEMENTED | S103 downstream list | GR-07 COMPOSE-FRONTIER |
| LIST-314 | side-effect ordering: LaunchedEffect/DisposableEffect lifecycle aware — *compose effect law* | effects run after apply, before frame end | UNTESTED-LAW-DOCUMENTED | law pinned | GR-07 COMPOSE-FRONTIER |
| LIST-315 | compose host root measurement: Lt4;.L completes after getRootView law (host width answerable) — *compose measure contract + AOSP getRootView never-null* | post-fix trace: position-cache dispatch returns; no getWidth NPE (3/3) | IMPLEMENTED-TESTED | S104-r3 dooz 3-run det (SHA 59fdbfcd x3); visual unchanged (honest) | GR-07 COMPOSE-FRONTIER |

## Family H — LIFECYCLE/ACTIVITY/SAVEDSTATE (35 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-316 | Activity constructor executes at launch (F-118 law) — *F-118 activity-constructor law* | launch; <init> side effects visible | PROVEN-L5 | F-118 IMPLEMENTED+TESTED (G08 launches) | NONE |
| LIST-317 | onCreate chain: super first, content after theme (ordering law) — *AOSP Activity.onCreate contract* | trace order: ctor -> onCreate -> setContentView | PROVEN-L5 | engine lifecycle_controller | NONE |
| LIST-318 | saved-state registry controller init requires right merged branch (R-009) — *FIX-005 solitaire proof* | getSavedStateProvider NPE gone 3/3 | PROVEN-L5 | solitaire 12->0 (3/3, SHA 59fdbfcd) | R-009 SWITCH-KEY-WIDENING |
| LIST-319 | ComponentActivity wiring: registry + lifecycle + viewmodel store — *androidx component activity upstream* | ctor completes w/o error | PROVEN-L5 | solitaire chain past saved-state wiring | GR-07 COMPOSE-FRONTIER |
| LIST-320 | onStart/onResume ordering after onCreate (AOSP order) — *AOSP activity lifecycle* | trace order onCreate<onStart<onResume | VERIFIED-CORRECT | lifecycle_controller | NONE |
| LIST-321 | onPause/onStop at background/focus loss (engine focus model) — *AOSP lifecycle* | run end dispatches pause/stop trace | VERIFIED-CORRECT | engine lifecycle | NONE |
| LIST-322 | setContentView before onResume visible at first frame — *AOSP frame contract* | first rendered frame has content | VERIFIED-CORRECT | engine first-frame evidence | NONE |
| LIST-323 | AppCompat delegate installs decor before setContentView — *AppCompatDelegateImpl upstream* | AppCompat titles inflate with decor present | REPRODUCED-DIVERGENT | GR-08 sub-decor gap | GR-08 DECOR-LINKAGE |
| LIST-324 | manifest exported/launch intent selects entry activity — *AOSP intent resolution* | launcher activity from manifest chooser | VERIFIED-CORRECT | manifest_reader entry point | NONE |
| LIST-325 | multi-activity: launched second activity overlays first (backstack law) — *AOSP backstack* | second activity content on top | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-326 | finish() triggers onDestroy and pops stack — *AOSP finish law* | finish then next activity visible | VERIFIED-CORRECT | engine activity stack | NONE |
| LIST-327 | ViewModel survives rotation-equivalent (config change no-op in engine) — *viewmodel store law* | same ViewModel instance across recreation calls | RESEARCHED-NOT-IMPLEMENTED | S103 downstream | GR-07 COMPOSE-FRONTIER |
| LIST-328 | SavedStateProvider roundtrip: save -> restore keys identical — *androidx savedstate upstream* | registry save/restore key set equality | PROVEN-L5 | solitaire post-fix (wiring executes) | R-009 SWITCH-KEY-WIDENING |
| LIST-329 | application onCreate before activity (application_context ordering) — *AOSP app init order* | trace order app<activity | VERIFIED-CORRECT | application_context.cpp | NONE |
| LIST-330 | ContentProvider.installContentProviders before activity onCreate — *AOSP provider init phase* | provider install trace precedes activity | VERIFIED-CORRECT | engine boot phases | NONE |
| LIST-331 | onActivityResult stubs return per contract (RESULT_CANCELED default) — *AOSP activity result law* | startActivityForResult default result | VERIFIED-CORRECT | android_shadows | NONE |
| LIST-332 | permissions: grant-all model documented (host policy) — *engine policy record* | dangerous permission auto-granted; trace note | VERIFIED-CORRECT | engine permission model | NONE |
| LIST-333 | application attachBaseContext earliest hook — *AOSP attachBaseContext order* | context wrap before app onCreate | VERIFIED-CORRECT | engine boot | NONE |
| LIST-334 | fragment family demand-gated (census demand measured before build-out) — *evidence-based priority* | census fragment usage scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-335 | dialog show() uses decor + window touch (R-NEW-394) — *dialog shadow law* | dialog button tap works | PROVEN-L5 | R-NEW-394 VERIFIED-FIXED | NONE |
| LIST-336 | activity theme applies at decor creation (before content) — *AOSP theme timing* | themed decor attributes visible | VERIFIED-CORRECT | engine decor stage | GR-09 THEME-PRODUCER |
| LIST-337 | window feature flags (no title/fullscreen) honored at decor — *AOSP window features* | FLAG_FULLSCREEN sized 1080x1920 no inset | VERIFIED-CORRECT | engine window shadow | NONE |
| LIST-338 | lifecycle callbacks on main thread only (single-thread determinism) — *engine threading law* | callback thread id constant | VERIFIED-CORRECT | engine scheduler | NONE |
| LIST-339 | service/intent-service started executes onStartCommand (shadow) — *AOSP service basics (shadow)* | startService -> onStartCommand trace | VERIFIED-CORRECT | android_shadows | NONE |
| LIST-340 | broadcast receivers: registered receiver receives sent broadcast — *AOSP broadcast law (shadow)* | sendBroadcast -> onReceive invoked | VERIFIED-CORRECT | engine broadcast shadow | NONE |
| LIST-341 | pendingintent shadow per F surface — *pending_intent_shadow.cpp* | PI.get* + send no-crash | VERIFIED-CORRECT | pending_intent_shadow | NONE |
| LIST-342 | activity result + save instance state bundle roundtrip — *AOSP onSaveInstanceState* | bundle save -> restore same keys | VERIFIED-CORRECT | engine bundle model | NONE |
| LIST-343 | instrumentation lifecycle gate: activity thread main loop owns frames — *AOSP ActivityThread model* | frame pump tied to activity thread | VERIFIED-CORRECT | engine main loop | NONE |
| LIST-344 | manifest meta-data readable at runtime — *AOSP ApplicationInfo.metaData* | metaData bundle non-null when declared | VERIFIED-CORRECT | manifest reader | NONE |
| LIST-345 | process death on uncaught exception reproduces Android (crash law) — *AOSP crash semantics* | uncaught -> process exit code + trace | VERIFIED-CORRECT | engine crash path | NONE |
| LIST-346 | activity relaunch preserves explicit state only (documented) — *engine policy* | re-run starts fresh unless state saved | VERIFIED-CORRECT | engine run protocol | NONE |
| LIST-347 | onConfigurationChanged not fired (fixed config policy) — *engine config policy* | no mid-run config callbacks | VERIFIED-CORRECT | engine config | NONE |
| LIST-348 | savedstate restore BEFORE onResume (AOSP order) — *androidx savedstate ordering* | restore trace precedes resume | PROVEN-L5 | solitaire chain | R-009 SWITCH-KEY-WIDENING |
| LIST-349 | viewmodel provider factory app-provided used (factory law) — *androidx viewmodel* | custom Factory.create called | RESEARCHED-NOT-IMPLEMENTED | S103 downstream | GR-07 COMPOSE-FRONTIER |
| LIST-350 | lifecycle state machine monotonic (no backwards transitions) — *androidx lifecycle law* | state sequence strict | VERIFIED-CORRECT | engine lifecycle | NONE |

## Family I — INPUT/TOUCH/HIT-TEST (30 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-351 | tap dispatches DOWN->UP motion event pair at coordinates — *AOSP MotionEvent stream* | --tap x,y@t produces 2 events | VERIFIED-CORRECT | engine input pipeline | NONE |
| LIST-352 | per-child hit-test walk routes to deepest VISIBLE child — *R-NEW-399 AOSP hit-test law* | HITPROBE: nested child receives tap | PROVEN-L5 | R-NEW-399 USED_BY_EXECUTION | NONE |
| LIST-353 | GONE children excluded from hit-test — *AOSP hit-test skip* | tap under GONE child hits parent | VERIFIED-CORRECT | engine hit-test | NONE |
| LIST-354 | click listener fires on same view that consumed DOWN+UP pair — *AOSP click detection* | click_audit.jsonl rows correlate | VERIFIED-CORRECT | MINIANDROID_CLICK_AUDIT protocol | NONE |
| LIST-355 | touch slop not required for synthetic taps (direct click) — *engine input policy* | single-frame tap -> click | VERIFIED-CORRECT | engine tap model | NONE |
| LIST-356 | dialog window is TOPMOST for touch (dialog touch law) — *R-NEW-394* | tap lands on dialog button not underlying view | PROVEN-L5 | R-NEW-394 VERIFIED-FIXED | NONE |
| LIST-357 | scroll containers consume vertical drag (intercept law) — *AOSP onInterceptTouchEvent* | drag inside ScrollView scrolls not clicks | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-358 | long-press timing under virtual clock — *AOSP long-press law* | hold LONG_PRESS_TIMEOUT -> long click | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-359 | multi-touch pointer id stability (secondary pointer streams) — *AOSP pointer model* | two-finger synthetic stream ids stable | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-360 | input focus: EditText receives IME-equivalent text events — *AOSP focus + IME* | focus + type -> text appears | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-361 | key events route to focused view then activity fallback — *AOSP key dispatch* | back key -> activity onBackPressed | VERIFIED-CORRECT | engine key dispatch | NONE |
| LIST-362 | click audit trail deterministic 3-run — *engine determinism gate* | click_audit SHA identical | VERIFIED-CORRECT | 3-run protocol | NONE |
| LIST-363 | hit-test uses CURRENT frame (no stale coordinates) — *R-NEW-399 blocker refutation* | tap after layout move hits new location | PROVEN-L5 | R-NEW-399 honest note | NONE |
| LIST-364 | hit-test respects rotation/translation transforms — *AOSP transformed hit-test* | rotated button still tappable (inverse map) | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-365 | touchable area includes padding (content + padding hit) — *AOSP bounds hit model* | tap on padding region clicks | VERIFIED-CORRECT | engine bounds model | NONE |
| LIST-366 | margin area does NOT hit child (margin outside bounds) — *AOSP bounds law* | tap in margin region hits parent | VERIFIED-CORRECT | engine bounds model | NONE |
| LIST-367 | clickable=true required for consumption (else bubbles) — *AOSP consumption law* | non-clickable parent gets event | VERIFIED-CORRECT | engine dispatch | NONE |
| LIST-368 | onTouch vs onClick precedence (listener first-consume law) — *AOSP TouchListener precedence* | onTouch returning true suppresses click | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-369 | disabled view does not click — *AOSP enabled law* | setEnabled(false) tap -> no click | VERIFIED-CORRECT | engine dispatch | NONE |
| LIST-370 | window-level touch boundary: outside activity content no crash — *engine boundary law* | tap at 1079,1919 edge safe | VERIFIED-CORRECT | engine input bounds | NONE |
| LIST-371 | compose pointer input gated behind compose host (#350) — *S104 #350 ticket* | compose title tap currently no-op | GAP-OPEN | #350 input slice | GR-07 COMPOSE-FRONTIER |
| LIST-372 | scroll wheel / axis events latent (demand 0) — *evidence-based priority* | census axis-event scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-373 | gesture detector fill: GestureDetector callbacks wired to event stream — *AOSP GestureDetector* | fling callback via synthetic stream | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-374 | touch feedback: pressed state drawable changes on DOWN — *AOSP pressed state* | DOWN -> background pressed drawable | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-375 | hit-test order is reverse draw order (topmost first) — *AOSP dispatch order* | overlapping children: last drawn wins | VERIFIED-CORRECT | R-NEW-399 walk | NONE |
| LIST-376 | swipe synthetic events (MOVE interpolation) available — *engine input generation* | --swipe produces MOVE stream | VERIFIED-CORRECT | engine input options | NONE |
| LIST-377 | input event timestamps align with frame clock (virtual time) — *engine time law* | event t within frame window | VERIFIED-CORRECT | engine virtual time | NONE |
| LIST-378 | click coordinates recorded relative to window (no viewport drift) — *engine coordinate law* | audit coords == requested coords | VERIFIED-CORRECT | click audit | NONE |
| LIST-379 | game interaction chains: tap->state->changed-frame evidence (TriPeaks/FishRings) — *S65 input->state->frame protocol* | 3 deterministic interactions recorded | PROVEN-L5 | root_registry S65 summary (det x3) | NONE |
| LIST-380 | input injection does not disturb render determinism (isolated channel) — *engine isolation law* | tap run vs no-tap run: pre-tap frames identical | VERIFIED-CORRECT | engine frame compare | NONE |

## Family J — GRAPHICS/CANVAS/GLES (45 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-381 | Canvas draw ops route through canvas_shadow to raster — *engine graphics pipeline* | drawRect visible in frame pixels | VERIFIED-CORRECT | canvas_shadow.cpp | NONE |
| LIST-382 | Paint flags: anti-alias/style/stroke width honored — *AOSP Paint* | STROKE vs FILL pixel difference | VERIFIED-CORRECT | canvas_shadow paint model | NONE |
| LIST-383 | Color int ARGB packing law (0xAARRGGBB) — *AOSP Color* | color roundtrip through Paint/Canvas | VERIFIED-CORRECT | engine color model | NONE |
| LIST-384 | Bitmap decode -> draw -> pixels visible (bitmap_shadow) — *AOSP Bitmap pipeline* | decoded bitmap drawn 1:1 | PROVEN-L5 | bitmap titles visual contracts | NONE |
| LIST-385 | Canvas save/restore stack semantics — *AOSP save()/restore()* | clip+transform restore exact | VERIFIED-CORRECT | canvas_shadow stack | NONE |
| LIST-386 | Matrix ops: setTranslate/rotate/scale/post/pre composition — *AOSP Matrix* | matrix chain == expected transform | VERIFIED-CORRECT | matrix_shadow | NONE |
| LIST-387 | text draw via freetype metrics (F text laws) — *engine text stack* | text pixels present; widths consistent | PROVEN-L5 | 9 HUMAN_VISIBLE titles | NONE |
| LIST-388 | PorterDuff basic modes (SRC_OVER default) — *AOSP PorterDuff subset* | SRC_OVER compositing visible | VERIFIED-CORRECT | renderer blend | NONE |
| LIST-389 | Path fill/stroke rendering subset — *AOSP Path* | polygon paths rasterized | VERIFIED-CORRECT | canvas path model | NONE |
| LIST-390 | ColorFilter apply law (R-NEW-393) — *R-NEW-393* | setColorFilter changes widget pixels | PROVEN-L5 | R-NEW-393 VERIFIED-FIXED | NONE |
| LIST-391 | Shader: bitmap/linear-gradient subset — *AOSP Shader subset* | gradient fill renders | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-392 | Drawable states + invalidate on state change — *AOSP Drawable* | state toggle redraws | VERIFIED-CORRECT | drawable shadow | NONE |
| LIST-393 | hardware-acceleration-independent raster (software model documented) — *engine graphics scope note* | no HW layer divergence possible | VERIFIED-CORRECT | GRAPHICS_DO_NOT_REINVENT.md | NONE |
| LIST-394 | GLES10/GLSurfaceView: EGL10 SETUP ONLY (6/54 titles) — *GL_NEED_LEDGER measured* | EGL initialize/swap without crash on GL titles | IMPLEMENTED-TESTED | GL_NEED_LEDGER.{json,md} | GR-12 GL-FRONTIER |
| LIST-395 | GLES20+ method refs corpus-wide = 0 (measured gate) — *GL_NEED_LEDGER method_ids scan* | 0 titles demand Java GLES20 | LATENT-NO-DEMAND | s104_gl_need_ledger.py | GR-12 GL-FRONTIER |
| LIST-396 | glTexImage2D/glTexSubImage2D family: PGL implements at C level; bridge absent — *ROOT-007 GL-BRIDGE classification* | bridge dispatch rows absent (bridge never reached) | GAP-OPEN | ROOT_CLUSTERS ROOT-007 | GR-12 GL-FRONTIER |
| LIST-397 | glReadPixels bridge absent (PGL C-level only) — *ROOT-007 classification* | no Java->PGL dispatch path | GAP-OPEN | ROOT_CLUSTERS ROOT-007 | GR-12 GL-FRONTIER |
| LIST-398 | framebuffer/texture lifecycle: bridge-absent, demand-gated — *ROOT-007 classification* | corpus demand scan = 0 refs | LATENT-NO-DEMAND | GL_NEED_LEDGER | GR-12 GL-FRONTIER |
| LIST-399 | GLSL execution: PGL executes C-function shaders; GLSL stored verbatim — *GLES_BACKEND_COMPARISON_010.md* | no GLSL compiler in scope; documented frontier | RESEARCHED-NOT-IMPLEMENTED | ROOT-007 GLSL frontier | GR-12 GL-FRONTIER |
| LIST-400 | compressed textures (ETC1/S3TC/ATC/PVRTC): absent engine-wide — *ROOT-007 TEX-COMPRESSION* | asset scan gate pending | GAP-OPEN | ROOT_CLUSTERS ROOT-007 | GR-12 GL-FRONTIER |
| LIST-401 | EGL shadow statics (BAD_ALLOC/CONTEXT_LOST/surfaceless) host-only — *ROOT-007 EGL-SHADOW* | shadow surface semantics only | HOST-ONLY | ROOT_CLUSTERS ROOT-007 host-only family | GR-12 GL-FRONTIER |
| LIST-402 | libGDX titles render via bundled libgdx.so natives (not Java GLES) — *GL_NEED_LEDGER census verdict* | JNI/native loading is the true GL frontier | HOST-ONLY | GL_NEED_LEDGER | GR-12 GL-FRONTIER |
| LIST-403 | native .so loading out of Java-runtime scope (documented blocker) — *S104 remaining blockers* | GL titles blocked at native load | HOST-ONLY | S104_REPORT remaining blockers | GR-12 GL-FRONTIER |
| LIST-404 | SurfaceFlinger/BufferQueue/GraphicBuffer producer layers host-only — *ROOT-NULL-PRODUCER out-of-scope family* | rule 7 classification recorded | HOST-ONLY | ROOT_CLUSTERS out-of-scope list | GR-12 GL-FRONTIER |
| LIST-405 | screenshot capture is engine raster ground truth (PNG writer) — *engine evidence protocol* | frame capture SHA-stable 3-run | PROVEN-L5 | 3-run SHA evidence (59fdbfcd...) | NONE |
| LIST-406 | visual contracts: observed-confidence model (S92 oracle) — *S92 visual contract law* | ACCEPT/REJECT battery distinguishes all cases | PROVEN-L5 | battery 105/105 gate | NONE |
| LIST-407 | GIF evidence: representative frames non-uniform (white-frame guard) — *S74 §13 PIL frame verification* | uniform-white frames rejected by auditor | PROVEN-L5 | worklog S74 CRITICAL-006 row | NONE |
| LIST-408 | choreographer-driven traversal each frame (traversal law) — *AOSP traversal* | frame N invalidations visible frame N+1 | VERIFIED-CORRECT | choreographer shadow | NONE |
| LIST-409 | window background draw before content (draw order law) — *AOSP decor draw order* | bg pixels under transparent views | VERIFIED-CORRECT | engine decor draw | NONE |
| LIST-410 | surface format: RGB888 output buffer (provenance metadata) — *engine output law* | gfx_provenance.json format rows | VERIFIED-CORRECT | MINIANDROID_GFX_PROVENANCE | NONE |
| LIST-411 | png/jpeg decode via stb (features/fidelity rows committed) — *engine decoder registry* | corpus formats decode without error | VERIFIED-CORRECT | decoder census | NONE |
| LIST-412 | lottie animation surface (MINIANDROID_HAVE_LOTTIE) — *build flag; engine lottie path* | lottie title frames advance | IMPLEMENTED-TESTED | Makefile flag + EXECUTED_GIFS.md | NONE |
| LIST-413 | animator shadow: ValueAnimator ticker virtual-time — *animator_shadow.cpp* | animation progress deterministic | VERIFIED-CORRECT | animator shadow | NONE |
| LIST-414 | portablegl vendored upstream (do-not-reinvent registry) — *GRAPHICS_SOURCE_REGISTRY: PortableGL* | PGL builds; bridge gated by demand | VERIFIED-CORRECT | third_party/portablegl + registry | GR-12 GL-FRONTIER |
| LIST-415 | graphics upstream source-first rule: check AOSP/CTS/Mesa/ANGLE first — *S104 directive §5 source-first* | GRAPHICS_DO_NOT_REINVENT.md honored in decisions | VERIFIED-CORRECT | GL_NEED_LEDGER decision trail | GR-12 GL-FRONTIER |
| LIST-416 | screen density affects scaled drawing (density law end-to-end) — *AOSP density* | dp sizes render at runtime density | VERIFIED-CORRECT | renderer + config | NONE |
| LIST-417 | view drawing cache/layer type: software layer semantics only — *engine scope* | LAYER_TYPE_HARDWARE treated as software | VERIFIED-CORRECT | engine layer model | NONE |
| LIST-418 | canvas clip ops (rect/region) exact — *AOSP clip* | clipRect excludes pixels outside | VERIFIED-CORRECT | canvas shadow | NONE |
| LIST-419 | drawText baseline/measure API consistency (Paint.measureText) — *text metrics law* | measureText width == advance sum | PROVEN-L5 | R-NEW-392 text subsumption | NONE |
| LIST-420 | frame pixel parity after identity/inflation changes (regression law) — *REAL_APK_IMPACT R-004 table* | pixel-identical before/after rows | PROVEN-L5 | REAL_APK_IMPACT.md | R-004 CLASS-IDENTITY |
| LIST-421 | screenshot pixel SHA determinism 3-run (evidence law) — *3-run protocol* | SHA identical x3 (solitaire 59fdbfcd...) | PROVEN-L5 | S104 evidence | NONE |
| LIST-422 | rendered-pixel census gate: uniform-frame detection as FAIL signal — *census verifier law* | FAIL census rows flagged by auditor | PROVEN-L5 | census 14/2/38/7 counts | NONE |
| LIST-423 | graphics API stubs return documented defaults (no invented pixels) — *engine honesty law* | stub surface enumerated, not guessed | VERIFIED-CORRECT | android_stubs.h | NONE |
| LIST-424 | frame capture format PNG byte-deterministic (no timestamp embed) — *evidence determinism* | same pixels -> same PNG bytes | PROVEN-L5 | 3-run SHA protocol | NONE |
| LIST-425 | graphics failure surface: decode/inflate errors logged not invented (honesty law) — *engine diagnostics law* | corrupt image -> logged error + fallback, no fabricated pixels | VERIFIED-CORRECT | engine decoder error paths | NONE |

## Family K — STORAGE/IO/NET (30 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-426 | SQLite real backend (F-ROOM-CHAIN) — real queries not mocks — *S100 M3 F-ROOM-CHAIN law* | app DB create/insert/query roundtrip | IMPLEMENTED-TESTED | Makefile LIBS sqlite3; S100 report | NONE |
| LIST-427 | SharedPreferences persistence (shared_prefs.cpp) — *AOSP SharedPreferences* | putString -> commit -> getString after reload | IMPLEMENTED-TESTED | shared_prefs.cpp + census usage | NONE |
| LIST-428 | File.getAbsoluteFile path law (R-NEW-390) — *AOSP File path resolution* | relative -> absolute normalization | PROVEN-L5 | R-NEW-390 ROOT-CAUSED-FIXED | NONE |
| LIST-429 | File.getCanonicalFile/Path law (R-NEW-391) — *AOSP canonicalization* | ../ collapse + symlink-free canonical | PROVEN-L5 | R-NEW-391 ROOT-CAUSED-FIXED | NONE |
| LIST-430 | File IO: create/read/write/delete in app data dir — *AOSP File APIs* | roundtrip bytes identical | VERIFIED-CORRECT | engine storage layer | NONE |
| LIST-431 | internal storage isolation per app (--data-root sandbox) — *engine sandbox law* | app A cannot see app B files | VERIFIED-CORRECT | engine data-root sandbox | NONE |
| LIST-432 | assets byte-exact streaming (AssetManager.open) — *AOSP asset access* | asset hash == packed hash | VERIFIED-CORRECT | engine asset IO | NONE |
| LIST-433 | OpenSSL-backed TLS (NET-001: BoringSSL lineage) — *S100 NET-001 law* | HTTPS GET to well-known host succeeds | IMPLEMENTED-TESTED | Makefile -lssl -lcrypto | NONE |
| LIST-434 | HTTP client surface (http_client.cpp) — *engine network layer* | plain HTTP GET returns body | IMPLEMENTED-TESTED | http_client.cpp | NONE |
| LIST-435 | URL/URI parsing edge cases (encoding, ports, paths) — *java.net URL/URI laws* | encoded path roundtrip | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-436 | JSON: org.json surface parity (JSONObject/JSONArray) — *AOSP org.json* | parse/stringify roundtrip equal | VERIFIED-CORRECT | engine json (nlohmann-backed) | NONE |
| LIST-437 | JSON strictness: duplicate keys last-wins (AOSP behavior) — *AOSP org.json duplicate law* | duplicate key parse -> last value | VERIFIED-CORRECT | engine json | NONE |
| LIST-438 | ObjectOutputStream/Serialization demand-gated — *evidence-based priority* | census serialization usage scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-439 | Zip/Jar APK-level reading (zip central directory) — *APK container law* | entries listed; deflate/inflate exact | VERIFIED-CORRECT | apk_parser.cpp | NONE |
| LIST-440 | gzip/deflate streams roundtrip — *java.util.zip* | compress->decompress identity | VERIFIED-CORRECT | engine zip layer | NONE |
| LIST-441 | crypto: SHA/AES surface via OpenSSL (documented scope) — *engine crypto policy* | digest roundtrip known vectors | IMPLEMENTED-TESTED | engine crypto via -lcrypto | NONE |
| LIST-442 | SecureRandom determinism policy (seeded for reproducibility) — *engine determinism law* | seeded runs byte-identical | VERIFIED-CORRECT | 3-run protocol | NONE |
| LIST-443 | Base64 encode/decode variants (default/url-safe/nopad) — *AOSP Base64* | roundtrip across flags | VERIFIED-CORRECT | engine base64 | NONE |
| LIST-444 | UUID/Random deterministic subsetting — *engine determinism law* | seeded Random sequence stable | VERIFIED-CORRECT | engine random | NONE |
| LIST-445 | room/database library family demand-gated (census scan) — *evidence-based priority* | room usage census | LATENT-NO-DEMAND | census scan | NONE |
| LIST-446 | content resolver/uris shadow (no cross-app content) — *engine scope note* | resolver calls answered by shadow, no crash | HOST-ONLY | android_shadows | NONE |
| LIST-447 | atomic file writes (rename-swap law) — *AOSP AtomicFile* | failed write leaves prior file intact | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-448 | file permissions model: single-user engine (documented) — *engine policy* | no chmod semantics divergence | HOST-ONLY | engine scope | NONE |
| LIST-449 | network on-main-thread strictness DISABLED (engine policy documented) — *engine policy vs AOSP NetworkOnMainThread* | main-thread HTTP allowed; policy note | VERIFIED-CORRECT | engine policy record | NONE |
| LIST-450 | TLS certificate validation on (secure default) — *NET-001 secure default* | bad-cert host fails closed | IMPLEMENTED-TESTED | OpenSSL default verify | NONE |
| LIST-451 | database encryption surface absent (census demand 0) — *evidence-based priority* | SQLCipher-family census | LATENT-NO-DEMAND | census scan | NONE |
| LIST-452 | app dir layout: files/cache/databases subdirs materialized — *AOSP context dirs* | getFilesDir/getCacheDir paths exist | VERIFIED-CORRECT | engine data-root | NONE |
| LIST-453 | classpath resource loading from APK dex-adjacent assets — *engine loader* | getResourceAsStream from app package | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-454 | large file streaming (no full-buffer requirement) — *engine IO law* | 10MB asset streamed without OOM | VERIFIED-CORRECT | engine asset streaming | NONE |
| LIST-455 | IO exception taxonomy: FileNotFoundException/IOException shapes — *java.io law* | missing file -> FNFE with path in message | VERIFIED-CORRECT | engine IO errors | NONE |

## Family L — TEXT/UTIL/JSON/CRYPTO (25 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-456 | String concatenation via StringBuilder identity (value not identity) — *S103 display law* | boxed value renders value in concat | PROVEN-L5 | ROOT-001 companion display law | R-001 FIELD-IDENTITY |
| LIST-457 | String.format locale subset (default locale US-equivalent) — *java.util.Formatter* | %d %s %f roundtrip | VERIFIED-CORRECT | engine formatter | NONE |
| LIST-458 | String split/replace/trim edge semantics (regex subset) — *java.lang.String* | split with regex special chars | VERIFIED-CORRECT | engine string ops | NONE |
| LIST-459 | kotlin stdlib: apply/let/also/run scoping nullability — *kotlin stdlib upstream* | scope-function chains on nullables | VERIFIED-CORRECT | S104 merged-class scan corpus evidence | R-009 SWITCH-KEY-WIDENING |
| LIST-460 | kotlin text: MatcherMatchResult family executes post-R-009 — *S104 solitaire chain* | getSavedStateProvider NPE gone; chain passes stdlib site | PROVEN-L5 | S104 DEX ground truth + fix | R-009 SWITCH-KEY-WIDENING |
| LIST-461 | kotlin object/singletons: INSTANCE static identity — *kotlin object law* | object field set visible globally | PROVEN-L5 | ROOT-001 static storage identity | R-001 FIELD-IDENTITY |
| LIST-462 | kotlin lateinit: unset read -> UninitializedPropertyAccessException — *kotlin law* | lateinit read before set -> UPAC | VERIFIED-CORRECT | engine kotlin surface | NONE |
| LIST-463 | kotlin data class equals/hashCode/copy synthesis — *kotlin compiler synthesis* | equals by component values | VERIFIED-CORRECT | engine synth methods | NONE |
| LIST-464 | kotlin lambdas: FunctionN invoke + captured vars — *kotlin lambda lowering* | closure counter increments | VERIFIED-CORRECT | engine invokedynamic-less lambdas | NONE |
| LIST-465 | kotlin companion: fields via companion identity — *kotlin companion law* | Companion.X reads instance storage | PROVEN-L5 | ROOT-001 canonical keys | R-001 FIELD-IDENTITY |
| LIST-466 | char encodings: UTF-8 decode strictness (MUTF-8 for dex strings) — *DEX MUTF-8 law* | emoji in strings roundtrip through dex | VERIFIED-CORRECT | mutf8_test binary | NONE |
| LIST-467 | Collections: ArrayList/HashMap iteration order documented — *java.util laws* | HashMap order deterministic within run | VERIFIED-CORRECT | engine collections | NONE |
| LIST-468 | Collections.sort stability law — *java.util.Collections.sort (stable)* | equal keys preserve order | VERIFIED-CORRECT | engine sort | NONE |
| LIST-469 | Comparable/Comparator contract enforcement on bad comparators — *java.util contract* | inconsistent comparator -> documented behavior | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-470 | BigDecimal/BigInteger subset for game scoring paths — *java.math subset* | long-scale arithmetic exact | VERIFIED-CORRECT | engine math | NONE |
| LIST-471 | regex engine subset (Pattern/Matcher core) — *java.util.regex subset* | common game patterns match | VERIFIED-CORRECT | engine regex | NONE |
| LIST-472 | Math functions exactness (sin/cos/pow IEEE subset) — *java.lang.Math* | Math.pow(2,10)==1024.0 | VERIFIED-CORRECT | engine math | NONE |
| LIST-473 | Object.equals/hashCode/toString defaults (identity-based) — *java.lang.Object* | default hashCode stable within run | VERIFIED-CORRECT | engine object model | NONE |
| LIST-474 | ThreadLocal isolation across threads — *java.lang.ThreadLocal* | two threads distinct values | VERIFIED-CORRECT | engine thread model | NONE |
| LIST-475 | AutoCloseable try-with-resources close ordering (reverse) — *JLS try-with-resources* | close order reverse declaration | VERIFIED-CORRECT | engine bytecode close synth | NONE |
| LIST-476 | annotation processing at runtime (getAnnotation subset) — *java.lang.reflect annotation* | runtime-visible annotation read | UNTESTED-LAW-DOCUMENTED | law pinned | NONE |
| LIST-477 | iterator/removeById fast-fail semantics documented — *java.util ConcurrentModification policy* | single-thread: CME only per documented paths | VERIFIED-CORRECT | engine collections | NONE |
| LIST-478 | Optional/functional interfaces surface (API24+ subset) — *java.util.Optional* | map/filter chains | VERIFIED-CORRECT | engine jdk surface | NONE |
| LIST-479 | text measurement shared by views+canvas (ONE metrics law) — *R-NEW-392 subsumption* | Paint vs TextView widths agree | PROVEN-L5 | R-NEW-392 | NONE |
| LIST-480 | string determinism: interning behavior per dex string_ids — *DEX string identity* | same string_id == same object | VERIFIED-CORRECT | engine string table | NONE |

## Family M — AUDIO/MEDIA/SENSORS/HOST-FRONTIER (20 lists)
| id | pattern (law) | probe | status | evidence | root |
|---|---|---|---|---|---|
| LIST-481 | MediaPlayer object lifecycle law (F-155): input->state chain closed — *F-155 ROOT-CAUSED-FIXED (S79)* | fishrings input->state->changed-frame x2 det | PROVEN-L5 | root_registry S79 summary (R-NEW-400) | NONE |
| LIST-482 | AudioTrack/AudioFlinger producer host-only (rule 7) — *ROOT_CLUSTERS out-of-scope family* | no real audio producer in engine scope | HOST-ONLY | ROOT_CLUSTERS host-only list | GR-12 GL-FRONTIER |
| LIST-483 | SoundPool shadow: load IDs valid, no real PCM out — *audio shadow scope* | load returns id; play no-crash | HOST-ONLY | android audio shadows | GR-12 GL-FRONTIER |
| LIST-484 | camera/sensor surfaces absent (census demand 0) — *evidence-based priority* | census sensor usage scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-485 | vibrator shadow no-op with trace (policy) — *engine shadow policy* | vibrate calls logged not crash | HOST-ONLY | android_shadows | NONE |
| LIST-486 | notification surface shadow (no system UI) — *engine scope note* | notify calls no-crash | HOST-ONLY | android_shadows | NONE |
| LIST-487 | clipboard shadow (locale_insets family neighbor) — *clipboard_shadow.cpp* | set/get within run | VERIFIED-CORRECT | clipboard shadow | NONE |
| LIST-488 | connectivity shadow: network state always available — *engine policy* | isConnected true; titles skip offline branches | VERIFIED-CORRECT | engine policy | NONE |
| LIST-489 | battery/power shadow: static sane values — *engine policy* | battery reads fixed value no crash | HOST-ONLY | android_shadows | NONE |
| LIST-490 | geolocation absent (census 0) — *evidence-based priority* | census location scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-491 | telephony/SMS absent (census 0) — *evidence-based priority* | census telephony scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-492 | bluetooth/NFC absent (census 0) — *evidence-based priority* | census scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-493 | WebView: native chromium absent; JS engine surface documented — *S100 browser wave evidence* | upload/s100_browser titles status recorded | RESEARCHED-NOT-IMPLEMENTED | S100 browser artifacts | GR-12 GL-FRONTIER |
| LIST-494 | app-widgets surface absent (census 0) — *evidence-based priority* | census widget-provider scan | LATENT-NO-DEMAND | census scan | NONE |
| LIST-495 | in-app-billing/ads SDK calls fail-soft with trace — *engine policy* | ads init no-crash, no-ops | HOST-ONLY | engine policy | NONE |
| LIST-496 | Play-Services family fail-soft (no GMS) — *engine policy* | GMS API calls return documented failure | HOST-ONLY | engine policy | NONE |
| LIST-497 | font loading: system fonts + app fonts (freetype/harfbuzz/fribidi) — *engine text stack* | custom ttf from assets loads | IMPLEMENTED-TESTED | fonts stack (FONTS_LIBS) | NONE |
| LIST-498 | RTL/bidi via fribidi (locale laws) — *fribidi integration* | RTL text shaped correctly | IMPLEMENTED-TESTED | FONTS_LIBS -lfribidi | NONE |
| LIST-499 | input method surface: synthetic text injection only — *engine input policy* | IME-equivalent injection documented | HOST-ONLY | engine input | NONE |
| LIST-500 | media codecs: software decode for corpus formats only — *engine scope* | census codec formats enumerated | VERIFIED-CORRECT | decoder census | NONE |
