# S59 — R-NEW-379 closure (F-105) + R-NEW-380 discovery

HEAD at evidence time: working tree on top of b0271429 (S58 push state).
APK: apk_cache/io.github.yamin8000.dooz_23.apk (SHA-256 299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b — matches docs/upstream/dooz23_meta_inf_provenance.md).

## R-NEW-379 — Dooz ViewTreeLifecycleOwner frontier (P1, pinned S58) → ROOT-CAUSED-FIXED

FACE (pre-fix, miniandroid/run/s59_repro/): Compose init dies at
`ISE "ViewTreeLifecycleOwner not found from Lho;@1074"` (caller=Log0;.c pc=2,
depth 8, THROWABLE-MSG x4) uncaught at MainActivity.onCreate invoke_pc=317;
themed window painted (2,073,600 nb) before APP BOUNDARY unwind.

### DEX ground truth (scripts/s59_vtlo_forensic.py, s59_dump_vtlo.py, s59_dump2.py, s59_tagsites.py)

- The walk: `Lxd1;.g(View)Lvo0;` = lifecycle 2.8 ViewTreeLifecycleOwner.get —
  loop { `getTag(view, 2131230840)` → miss → `parent = Lrd1;.v(view)` →
  `instance-of parent, Landroid/view/View;` → if false abort }.
- 2131230840 = 0x7F080078 = **R.id.view_tree_lifecycle_owner** (aapt2 dump
  resources; aapt2-verified entry name). Companion keys verified:
  2131230844 = view_tree_view_model_store_owner, 2131230843 =
  view_tree_saved_state_registry_owner, 2131230802 = an unrelated Compose
  view-scope memo tag (Llo;.J), 2131230762/763 = ComposeView internal tags.
- DEX census (scripts/s59_setfind.py): **ZERO setTag sites for key
  2131230840 exist in the app DEX** — the owner install is androidx library
  machinery (the ComponentActivity contract), absent from the APK; the only
  DEX site storing that tag is the dialog-propagation Le81;.<init> (which
  GETs from an ancestor first).

### Runtime root-cause chain (MINIANDROID_INSTANCEOF_TRACE / M3-ANCESTRY diag)

1. **Abort face (D1)**: the walk's parent hop —
   `[INSTANCEOF-DIAG] Lxd1;.g pc=28 target=Landroid/view/View; obj=obj#20
   class=Landroid/view/View; heap=Lio/github/yamin8000/dooz/ui/MainActivity;
   is_instance=FALSE`. The ViewShadow node 20 is the F-023 ACTIVITY-AS-VIEW
   node (its id IS the activity's heap id BY DESIGN); heap#20 is the
   MainActivity, so the F-103 heap-authority classified the VIEW reference
   as the ACTIVITY → `parent as? View` FALSE → walk dead-ended at hop 1 →
   null → ISE. ART law violated: the reference means the entity its creator
   declared (getParent returned handled_object(20, "Landroid/view/View;")).
2. **Empty-set face (D2)**: nobody ever wrote the owner tag
   (getTag view=1074 key=2131230840 hit=0; no DEX install site — D2 above).

### FIX F-105 (three generic laws; no app-specific code)

- **F-105a (declaration↔heap reconciliation)** — `reconcile_class_decl()`
  shared by execute_instance_of + execute_check_cast:
  declaration empty/generic (`Ljava/lang/Object;`) → heap record wins
  (F-103 preserved); consistent pair (one assignable to the other) → the
  more specific wins; CONTRADICTION (neither assignable) → the
  creation-site declaration wins (the heap record at the shared integer
  belongs to a different entity). Rejected alternative: re-homing
  contradicted references onto heap proxies breaks the NEXT shadow hop
  (getTag/getParent key by the shadow node id — the entity id IS the
  shadow table key); documented in dalvik_engine.cpp.
- **F-105b (ComponentActivity view-tree owner law)** — ActivityShadow
  setContentView(View) handler, next to the F-023 parent-link: store the
  ACTIVITY object (it implements LifecycleOwner in the app DEX:
  Ljm; implements Lvo0;) under the app's OWN view_tree_lifecycle_owner
  resource id (name-resolved via arsc find_id — no hardcoded id) on the
  activity-as-view node (the F-023 decor counterpart, the walk's terminal
  hop), BEFORE the attach wave runs the ComposeView.onAttachedToWindow
  walk.
- **F-105c (instance-of on a Class token value)** — const-class (F-069/
  F-103) yields a CLASS_REF whose ref_id is the heap-backed
  Ljava/lang/Class; token and whose class_desc is the REFERENT. ART law:
  `X.class instanceof Y` classifies the TOKEN — the token's runtime class
  IS java.lang.Class. Pre-fix, ViewModelProvider's ViewModelStore key
  guard (Lwl0;.containsKey pc=0) rejected every CLASS_REF →
  IAE "Key must be a class" at depth 79 (post-105a/b intermediate face,
  miniandroid/run/s59_f105_post1/).

### Post-fix proof (miniandroid/run/s59_f105_post1/ with TAG-TRACE; clean rerun s59_f105_post2/)

- `[F105-OWNER] activity=20 installed as ViewTreeLifecycleOwner key=2131230840`
  (post1 stderr, TAG-TRACE on).
- Walk success: `getTag view=1074 key=2131230840 hit=0 parent=20` →
  `getTag view=20 key=2131230840 hit=1` → owner (the activity, obj#20)
  returned; the app's own dialog machinery (Le81;.<init>) then propagated
  it onto the decor (`setTag view=308 key=2131230840 kind=1 obj=20`) — the
  androidx contract cascade runs end-to-end in the app's own DEX.
- The R-NEW-379 ISE is GONE (0 occurrences in post1/post2; was x4).
  Execution advanced from depth 8 to depth 81.

## R-NEW-380 — NEW pinned face (post F-105), OBSERVED-FAIL, P1

Face (miniandroid/run/s59_f105_post2/stderr.log — clean rerun without
TAG-TRACE; key lines hashed in post2_keylines.log):
`RuntimeException "Cannot create an instance of " caller=Leo;.n pc=53
depth=81` — the ViewModelProvider create chain
(Lyd0;.b → Ltf1;.b → Lt32;.b → Lt32;.d → Leo;.n) reached the throwing
factory fallback while constructing the app's GameViewModel
(KClass.java round-trip → Lwl0;.containsKey guard now PASSES via F-105c →
factory selection → create → failure). The message's class-name portion is
EMPTY (`+ modelClass` → StringBuilder.append of a CLASS_REF renders
nothing) — the Class.toString/arg surface for CLASS_REF values is part of
the gap; the deeper gap is the create path itself (getDeclaredConstructor →
Constructor.newInstance → real <init> for the app's GameViewModel — the
[M3-REFLECT] surface exists but the chain does not complete for this path).
NEXT ranked: (1) trace Leo;.n's exact failure input (which factory step
failed: ctor discovery vs newInstance dispatch vs a stubbed dependency);
(2) Class.toString/getName for CLASS_REF args (referent name);
(3) Constructor.newInstance → try_recursive_invoke on GameViewModel.<init>.

## Regression gate

- semantic battery: 26/26 PASS (24 prior + f105_instanceof_classtoken_is_class
  + f105_instanceof_classtoken_not_referent); battery label updated
  "expect 24" → "expect 26".
- BATTERY GATE: ALL PASS (88 executed-or-cached stages, 0 FAIL, fresh state
  dir). Stage-count variance vs S58 (96) is environment-availability: 3
  corpus APKs could not be restored this session (Telegram/OpenLauncher —
  upstream re-build hash drift; TinyMusicPlayer — release 404). The EXT-01/
  02 external fixture was re-fetched SHA-verified
  (HelloWorldSelfAware-1.1.0-android.apk, SHA-256
  009b467109c4d48d4b00610b06f37f3a77eed75178fbaae344a111acc848cc41 per
  docs/evidence/EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md) and its stages
  PASS.
- Real-APK determinism (F-105 changes zero cross-app behavior):
  chessclock sha16 ecc001fd8e33519a (== S57/S58 record), notes sha16
  cf521b168a9b4ed2 (== record), unote sha16 7b30d52201bb22ac (== record).
- dooz v18: Choreographer doFrame loop alive, 0 THROWABLE-MSG, 0
  RECURSION-LIMIT (same healthy face as the S58 record; the S59 probe
  timeout cut the alive loop, rc=124 external).
