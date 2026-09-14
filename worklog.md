# Multi-Agent Shared Worklog — MiniAndroid-Compatibility-Runtime

NOTE: this shared log was wiped by the S38 mid-session container reset and is
recreated from the S38 record onward. Git-tracked session history lives in
`docs/maintenance/worklog.md` (authoritative); commit messages on origin/main
carry the per-session detail (S16..S37 at HEAD 73a84aad).

---
Task ID: S38-MAIN
Agent: Super Z (main)
Task: MASTER CAMPAIGN 3 continuation — publish old pushes; JPG evidence conversion
(user directive: JPG <=100KB, not PNG); Hello World archive expansion (advanced
fixtures); wave-4 reruns of S37 budget-timeouts; R-NEW-335 shift-law probe;
root audit.

Work Log:
- Published pushes: server main verified at 73a84aad; local main synced (0 unpushed).
- S38-A (done twice — container reset mid-session): all 31 ledger evidence images
  converted PNG->JPG (540x960, q72, hellocolor q60), every image <=100KB
  (max 89KB), total 287KB; ledger references updated, zero stale refs.
  Deterministic: second-run JPG SHAs byte-identical to first-run.
- CONTAINER RESET mid-session (tools/ + build/ + all untracked files + local
  refs rolled back to 7a172e7c): recovered via `git fetch + reset --hard
  origin/main` (server main = 73a84aad intact). Re-fetched toolchain (ecj
  3.36.0 Maven Central, r8 8.3.37 r8-releases, android-34 Sable, aapt2 Google
  Maven). All S38 untracked work re-created from session context.
- AUDIT FINDING: S36/S37 commit messages claimed "registry 321->322" but the
  registry file in git stayed at 303 roots until S37's actual committed state
  (recovered 73a84aad registry = 322 roots, last R-NEW-335 — verified true).
  Shared worklog text vs committed file discrepancy documented.
- hello_widgets (Advanced Hello World #3) + hello_smoke (Advanced #2) built
  aapt2-linked and executed (pre-reset evidence): both SUCCESS with real
  multi-widget renders; hello_widgets = most advanced View-world render in the
  archive (ImageView drawable + EditText + Button + TableLayout 3 rows +
  RelativeLayout layout_below, 35.5% non-background).
- R-NEW-336 registered (P1): post-click setText on a TextView under a
  ScrollView root renders empty (default text vanishes); identical chain under
  LinearLayout root renders (hello_smoke count=1). Isolated: not concat, not
  getText, not invalidate. Structural delta = ScrollView root.
- R-NEW-335 probe: s38_shift_law fixture (7 laws, 26 checks) replicating the
  exact androidx.collection ScatterMap long-arithmetic (writeRawMetadata/
  readRawMetadata/group() guard/hash MurmurHashC1 chain/convertMetadata/
  neg+shr63 guard), anti-constant-folded via non-final statics, hardcoded
  expected values from independent big-int computation, visual verdict bands.
  APK 1a82564691a248b8d2d0be363d5986c1e171ca886acd1e36656f2c1f3550a6f1.
  Run pending runtime binary rebuild (make -j2 in progress after reset).
- wave-4 script re-created: 4 S37 budget-timeouts re-queued at 900s + 2 hello
  fixtures + shift-law probe first.

Stage Summary:
- Registry 322->323 (R-NEW-336). Evidence images: 31 JPG <=100KB.
- Root audit delivered: 103 PARTIAL / 72 UNPROVEN / 4 OBSERVED-FAIL /
  16 RESEARCHED-NOT-IMPLEMENTED remaining; P0 frontier = R-NEW-335 (dooz AIOOBE)
  + R-NEW-301/303/242/246/256/259/261/279/281/285 compose/lifecycle family.
- Next: run shift-law probe verdict -> R-NEW-335 verdict (engine-vs-dual-store);
  wave-4 runs; ledger S38 section; push; report progress %.

---
Task ID: S39
Agent: Super Z (main)
Task: Continue MASTER CAMPAIGN from wave-4 launch — check wave-4 results, attack dooz23 render chain, close roots, push everything.

Work Log:
- wave-4 corpus runner had died silently (bg process policy kills process groups across tool calls; setsid also killed) — fixtures were already complete (hello_smoke/hello_widgets/scroll_min + hw_fixed diagnostics all in /tmp/s38_runs/wave4/).
- Verified S38 commit 4f205e72 already contained R-NEW-336 fix + ledger JPG rows; pushed (was marked ahead-2, actually up-to-date after fetch; remote main = 4f205e72 confirmed via ls-remote).
- dooz23 attack (vtree2 evidence): composition died on ISE "Job Lkp1;@828 is already complete or completing" (Loj0;.T = JobSupport.makeCompletingOnce) on the FIRST measure — registered R-NEW-337 (scripts/s39_register_r337.py, roots 323->324).
- Built R337-DUAL probe in THROWABLE-MSG site (heap field dump of job+proposed objects): state obj#505 class=Lh20; fields=.e=1 = Empty(Active) — state was ACTIVE, the check misfired.
- Disassembled Loj0;.T/.d0/.M + Lh20; + Ljd; via androguard (installed into venv): d0 pc=0 instance-of Lmf0; (Incomplete) on null -> ALREADY_COMPLETING sentinel; M() reads state via sun.misc.Unsafe.getObjectVolatile(this, offset) with offsets from statics Loj0;.e/.f — ALL REC-MISS: engine had ZERO sun.misc.Unsafe / java.lang.reflect.Field / getDeclaredField shadows.
- FIX R-NEW-337: full atomicfu-via-Unsafe contract in try_shadow_dispatch — Class.getDeclaredField(s), Field.getName/getType/getDeclaringClass/getModifiers/setAccessible/get/set, Modifier.isStatic, Class.isAssignableFrom, Unsafe singleton (theUnsafe via Field.get), objectFieldOffset (deterministic (class,field)<->offset registry, members unsafe_field_offsets_/unsafe_offset_to_field_/unsafe_next_offset_ in dalvik_engine.h), getObjectVolatile/getObject/putObjectVolatile/putOrderedObject/putObject, compareAndSwapObject/Int/Long (heap CAS by object identity), Int/Long volatile get/put variants, arrayBaseOffset/arrayIndexScale. Post-fix: 30 offsets registered, ZERO ISE.
- Frontier R-NEW-338: Lqi0;.Q (coroutines stack-trace sanitizer) NPE "null array in Arrays.copyOfRange" — getStackTrace dispatched with RUNTIME class (R8-obfuscated) and M3-19 guard demanded Throwable/Exception/Error in the name. FIX: guard widened to any class (Thread excluded), setStackTrace/getStackTrace stored-sanitized-trace round-trip. Post-fix: zero NPEs.
- Frontier R-NEW-339: ISE "Required value was null." in Lt4;.<init> (=AndroidComposeView) — caller-PC forensics (new THROWABLE-STACK-PC via CallStack::set_last_invoke_pc + push_frame capture) pinned engine pc=415 = first autofill checkNotNull; T4PROBE invoke-static trace in Lt4;.<init> pinned it to Lob;.b(View)->View.getAutofillId() -> null -> Lwd;.a null -> Ld1;.e null-branch. FIX: ViewShadow.getAutofillId law (memoized per-view AutofillId heap object, ViewNode.autofill_id_obj) + getSystemService(Class/string) registry mirrored into try_shadow_dispatch ([R339-SVC]). Post-fix: zero ISE, ComposeView gains AndroidComposeView child (C013-LEAFCHK children=1), placeholder no longer drawn.
- Frontier R-NEW-340: launch frame pump ran before onCreate posted the FrameCallback (log 242402 quiescence < 242620 postFrameCallback cb=757). FIX: post-lifecycle pump (16 ticks) in stage_capture_output. Post-fix: doFrame fired, resume machinery drained, Recomposer job machinery advanced to .Q await path — deepest Compose execution recorded for dooz23. Residual: recomposer suspends without re-posting a frame callback (NEXT in registry).
- Regression checks clean: hello_smoke renders, hello_widgets byte-identical (2059104 nonwhite).
- Commits: 4f205e72 (S38, verified+pushed), 472fc4d5 (S39 3-root fix chain), 997e23a1 (S39-FIX2 pump law). All on origin/main.
- Registry 323 -> 327 roots (R-NEW-337 FIXED, 338 FIXED, 339 FIXED, 340 PARTIAL-FIX).

Stage Summary:
- dooz23 (PRIORITY-1 app) advanced from "empty grey placeholder" to "real view tree + live Recomposer machinery 3 fixes deep".
- New reusable forensics: R337-DUAL heap dumps, THROWABLE-STACK-PC caller-pc frames, T4PROBE per-ctor invoke trace, INSTANCEOF-DIAG interface-closure dump.
- Scripts persisted: s39_register_r337.py, s39_disasm_r337.py, s39_register_fixes.py, s39_register_r340.py.
- Next: trace recomposer post-resume suspension (R-NEW-340 NEXT), corpus wave 4 APKs (budget-timeout retries still pending), ledger dooz23 S39 section, progress report to user.
