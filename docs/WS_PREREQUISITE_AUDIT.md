# WS PREREQUISITE AUDIT — are white/black cases environment-caused?

> HEAD `59c57519ea37` · binary sha16 `4c01757e8f11c8a0` · prerequisite layer in `pkginspect --what prerequisites` (this wave)

## Answer (WS-002)

- **Environment-caused (prerequisite mismatch): 0** — cases where the APK
  requires a capability the environment cannot provide (ARM-only native code without a
  bridge; Vulkan-native engine on a GLES2 software backend).

- **Dual-cause (environment + runtime frontier): 2** — Godot class: the arm64-only
  libgodot.so cannot execute AND the godot_fragment_container Fragment never materializes
  a child (the recorded ViewPager/Fragment frontier).

- **Ordinary runtime roots: 7** — white faces whose prerequisite check
  is CLEAN (no ABI/feature/API mismatch); first divergence sits in ViewTree/Compose/
  Fragment/WindowInsets/lifecycle chains. These are NOT environment failures.

## Per-case table

| Case | Face | Env-caused | First divergence | Classification |
|---|---|---|---|---|
| org.fossify.clock | white | False | authoritative WINDOW_ROOT absent at frame time after App.onCreate EventBus death + LayoutInflater.inflate null | B SAME_ROOT/NEW_EVIDENCE |
| com.sidhant.blockblast | white | False | ComposeView NOT in class index — content view never materialized (tree 1 node) | B SAME_ROOT/NEW_EVIDENCE |
| com.game.asteroids_revenge | white | DUAL | Arrays.toString REC-MISS → kotlin Intrinsics NPE → GodotActivity.onCreate died at pc=0x3a before native GodotV | C NEW_SUB_LAW for prereq face: APK declares android.hardware |
| fr.arnaudguyon.spacevertex | white | False | kotlin.internal implementations Class.forName NPE; re-dispatch androidx Fragment ISE (HomeFragment must be pub | B SAME_ROOT/NEW_EVIDENCE |
| com.sanskritbasics.memory | white | False | WindowInsets CONSUMED sget → NPE in androidx compat clinit during ActionBarOverlayLayout init (WebView content | B SAME_ROOT/NEW_EVIDENCE (fix landed post-#366; re-run shows |
| com.yepgoryo.EggReturnsHome (Godot) | background-only (windowBackground, 0 app draw ops) | DUAL | GodotActivity.onCreate → godot_fragment_container Fragment never materializes a child (FrameLayout children=0) | D NEW_ROOT for the environment face (CPU-translation boundar |
| sudoku plain-run | white | False | WINDOW_ROOT (verdict NO_ROOT) | A DUPLICATE (recorded) |
| whatsapp | white | False | window/content chain | A DUPLICATE (recorded) |
| telegram settings-face | partial (renders 2-face) | False | ACTIVITY_NAVIGATION (intro/auth chain) | A DUPLICATE (recorded) |

## Redroid-class proof (ARM-only install-then-fail)

com.yepgoryo.EggReturnsHome_1.apk: install rc=0 (redroid law: advertisement without
translator lets ARM-only APKs INSTALL), runtime stops at DEFAULT_BACKGROUND_ONLY with
0 app draw ops because the arm64-only libgodot.so cannot execute on the x86_64 host.
Evidence: run/closeout/env_egg_run1.log; prerequisite verdict ABI_MISMATCH_TRANSLATION_REQUIRED.

