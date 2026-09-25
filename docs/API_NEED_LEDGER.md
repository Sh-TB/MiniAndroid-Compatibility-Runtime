# API-NEED LEDGER (S101 RECALL SWEEP)

Engine head: `9c640c0a` — census: {'INTERACTIVE-EVIDENCE': 13, 'RENDERED-L2+': 2, 'PARTIAL': 39, 'FAIL': 7}

Every PARTIAL/FAIL title with the classes/APIs it needs, extracted from
crash forensics logs (evidence-first: each need carries its log line).
Families ranked by distinct-title fan-out — the next fix batch attacks
the top of this table first.

## Families by fan-out

| # | family | titles needing it | example titles |
|---|--------|------------------:|----------------|
| 1 | `compose-runtime` | 46 | app.halma, ch.logixisland.anuto, com.ahorcado |
| 2 | `unclassified` | 23 | app.halma, ch.logixisland.anuto, com.ahorcado |
| 3 | `savedstate-registry` | 19 | com.eightsines.firestrike.opensource, com.helddertierwelt.mentalmath, com.serwylo.babydots |
| 4 | `lifecycle-adapter` | 15 | com.helddertierwelt.mentalmath, com.serwylo.babydots, com.vayunmathur.games.solitaire |
| 5 | `coordinatorlayout` | 14 | com.kaeruct.raumballer, com.serwylo.babydots, com.vovagorodok.blidraughts |
| 6 | `constraint-layout` | 10 | com.serwylo.babydots, crypto.o0o0o0o0o.games.blackjack, eu.veldsoft.no.thanks |
| 7 | `appcompat-decor-toolbar` | 6 | com.sanskritbasics.memory, com.willie.mancala, de.georgsieber.ballbreak |
| 8 | `theme-gate` | 6 | com.eightsines.firestrike.opensource, com.serwylo.babydots, de.georgsieber.ballbreak |
| 9 | `gl-native` | 3 | com.emmanuelmess.tictactoe, com.rocket9labs.boxcars, dev.lonami.klooni |
| 10 | `libgdx-glsurfaceview` | 3 | app.halma, com.emmanuelmess.tictactoe, dev.lonami.klooni |
| 11 | `capacitor-bridge` | 1 | com.vovagorodok.blidraughts |
| 12 | `material-speeddial` | 1 | com.serwylo.babydots |
| 13 | `multidex-family` | 1 | org.secuso.privacyfriendlysudoku |
| 14 | `typedarray-null` | 1 | ch.logixisland.anuto |

## Per-title needs (PARTIAL/FAIL only)

### com.emmanuelmess.tictactoe — FAIL (L0)
- exceptions:
  - `RuntimeException|` x4
  - `RuntimeException|unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.init` x2
  - `RuntimeException|unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.initializeForView` x2
  - `RuntimeException|at Lcom/emmanuelmess/tictactoe/AndroidLauncher;.onCreate` x2
- families: compose-runtime, gl-native, libgdx-glsurfaceview, unclassified

### com.kaeruct.raumballer — FAIL (L0)
- exceptions:
  - `NullPointerException|at Ljgame/platform/JGActivity;.onCreate` x2
- families: compose-runtime, coordinatorlayout, unclassified

### com.serwylo.babydots — FAIL (L0)
- missing classes:
  - `ClassNotFoundException` x1: `ClassNotFoundException`
  - `Lkotlin/jvm/internal/Reflection;` x1: `ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflection;.<cli`
- exceptions:
  - `RuntimeException|unwound Lkotlin/jvm/internal/Intrinsics;.checkNotNull` x2
  - `RuntimeException|unwound Lcom/serwylo/babydots/AnimatedDots;.setSpeed` x2
  - `RuntimeException|at Lcom/serwylo/babydots/MainActivity;.onCreate` x2
  - `NullPointerException|` x10
  - `NullPointerException|unwound Lcom/leinardi/android/speeddial/SpeedDialActionItem;.createFabWithLabelView` x10
  - `NullPointerException|unwound Lcom/leinardi/android/speeddial/SpeedDialView;.addActionItem` x30
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, material-speeddial, savedstate-registry, theme-gate, unclassified

### crypto.o0o0o0o0o.games.blackjack — FAIL (L0)
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry

### eu.veldsoft.free.klondike — FAIL (L0)
- families: compose-runtime, savedstate-registry

### eu.veldsoft.tri.peaks — FAIL (L0)
- families: compose-runtime

### io.github.ebraminio.bouncy — FAIL (L0)
- families: compose-runtime

### app.halma — PARTIAL (L1)
- exceptions:
  - `RuntimeException|unwound Lcom/badlogic/gdx/utils/SharedLibraryLoader;.loadFile` x2
  - `RuntimeException|unwound Lcom/badlogic/gdx/backends/android/AndroidApplicationConfiguration$1;.load` x2
  - `RuntimeException|unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.init` x2
  - `RuntimeException|unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.initialize` x2
  - `RuntimeException|at Lapp/halma/AndroidLauncher;.onCreate` x2
- families: compose-runtime, libgdx-glsurfaceview, unclassified

### ch.logixisland.anuto — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Lch/logixisland/anuto/engine/theme/ThemeManager;.setTheme` x2
  - `NullPointerException|unwound Lch/logixisland/anuto/engine/theme/ThemeManager;.updateTheme` x2
  - `NullPointerException|` x10
  - `NullPointerException|unwound Lch/logixisland/anuto/GameFactory;.initializeEngine` x2
  - `NullPointerException|unwound Lch/logixisland/anuto/AnutoApplication;.onCreate` x2
- families: compose-runtime, typedarray-null, unclassified

### com.ahorcado — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Lio/flutter/embedding/engine/g/c;.a` x4
  - `NullPointerException|unwound Lio/flutter/app/FlutterApplication;.onCreate` x2
  - `NullPointerException|` x2
- families: compose-runtime, unclassified

### com.eightsines.firestrike.opensource — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Landroidx/preference/j;.m` x2
  - `NullPointerException|unwound Landroidx/preference/j;.o` x2
  - `NullPointerException|unwound Landroidx/preference/j;.n` x2
  - `NullPointerException|unwound Lzame/game/App;.onCreate` x2
  - `NullPointerException|` x2
- families: compose-runtime, savedstate-registry, theme-gate, unclassified

### com.helddertierwelt.mentalmath — PARTIAL (L1)
- missing classes:
  - `ClassNotFoundException` x2: `ClassNotFoundException`
  - `Landroidx/lifecycle/Lifecycling;` x2: `ClassNotFoundException; (androidx.activity.ComponentActivity$$ExternalSyntheticLambda6_LifecycleAdapter) method=Landroid`
  - `ClassNotFoundException?` x2: `ClassNotFoundException;`
- exceptions:
  - `IllegalStateException|unwound Lcom/helddertierwelt/mentalmath/DaggerMentalMath_HiltComponents_SingletonC$Builder;.build` x2
  - `IllegalStateException|unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath$1;.get` x2
  - `IllegalStateException|unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath;.generatedComponent` x2
  - `IllegalStateException|unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath;.hiltInternalInject` x2
  - `IllegalStateException|unwound Lcom/helddertierwelt/mentalmath/Hilt_MentalMath;.onCreate` x2
  - `IllegalStateException|` x2
- families: compose-runtime, lifecycle-adapter, savedstate-registry, unclassified

### com.jeffliu.balancetheball — PARTIAL (L1)
- families: compose-runtime

### com.rocket9labs.boxcars — PARTIAL (L1)
- families: compose-runtime, gl-native

### com.sanskritbasics.memory — PARTIAL (L1)
- missing classes:
  - `ClassNotFoundException` x1: `ClassNotFoundException`
  - `Lw0/l;` x1: `ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lw0/l;.<clinit> pc=3 → deferred handl`
- exceptions:
  - `NullPointerException|unwound Landroidx/core/view/s0;.v` x2
  - `NullPointerException|unwound Landroidx/core/view/s0;.u` x2
  - `NullPointerException|` x8
  - `NullPointerException|unwound Landroidx/appcompat/app/h;.c0` x6
  - `NullPointerException|unwound Landroidx/appcompat/widget/Toolbar;.z` x2
  - `IllegalStateException|unwound Lf/a;.b` x2
- families: appcompat-decor-toolbar, compose-runtime, unclassified

### com.sidhant.bubbleshooter — PARTIAL (L1)
- families: compose-runtime

### com.sidhant.puzzle — PARTIAL (L1)
- families: compose-runtime

### com.sidhant.queens — PARTIAL (L1)
- families: compose-runtime

### com.trianguloy.adnihilation — PARTIAL (L2)
- exceptions:
  - `NullPointerException|at Lcom/trianguloy/adnihilation/MainActivity;.onCreate` x4
- families: compose-runtime, unclassified

### com.vayunmathur.games.solitaire — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Landroidx/savedstate/internal/SavedStateRegistryImpl;.performAttach` x4
  - `NullPointerException|` x6
  - `NullPointerException|unwound Lkotlin/text/MatcherMatchResult;.performRestore` x2
  - `NullPointerException|unwound Landroidx/activity/ComponentActivity;.onCreate` x2
  - `NullPointerException|at Lcom/vayunmathur/games/solitaire/MainActivity;.onCreate` x4
  - `NullPointerException|unwound Landroidx/compose/foundation/BorderKt$$ExternalSyntheticLambda1;.invoke` x2
- families: compose-runtime, lifecycle-adapter, savedstate-registry, unclassified

### com.vovagorodok.blidraughts — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Landroidx/coordinatorlayout/widget/CoordinatorLayout;.onMeasure` x2
- families: capacitor-bridge, compose-runtime, coordinatorlayout, lifecycle-adapter, savedstate-registry

### com.willie.mancala — PARTIAL (L1)
- exceptions:
  - `NullPointerException|` x10
  - `NullPointerException|unwound Le/b0;.w` x10
  - `NullPointerException|unwound Landroidx/appcompat/widget/Toolbar;.m` x4
  - `IllegalStateException|unwound La2/d;.H` x4
  - `IllegalStateException|unwound Landroidx/fragment/app/f;.p` x4
  - `IllegalStateException|unwound Landroidx/appcompat/widget/Toolbar;.getWrapper` x4
- families: appcompat-decor-toolbar, compose-runtime, savedstate-registry, unclassified

### de.georgsieber.ballbreak — PARTIAL (L1)
- families: appcompat-decor-toolbar, compose-runtime, coordinatorlayout, lifecycle-adapter, savedstate-registry, theme-gate

### de.tobiasbielefeld.solitaire — PARTIAL (L1)
- exceptions:
  - `NullPointerException|` x20
  - `NullPointerException|unwound Landroid/support/v7/app/g;.a` x8
  - `NullPointerException|unwound Landroid/support/v7/app/e;.onCreate` x2
  - `NullPointerException|unwound Lde/tobiasbielefeld/solitaire/classes/c;.onCreate` x2
  - `NullPointerException|at Lde/tobiasbielefeld/solitaire/ui/GameSelector;.onCreate` x4
  - `NullPointerException|unwound Landroid/support/v7/app/e;.findViewById` x2
- families: compose-runtime, unclassified

### dev.lonami.klooni — PARTIAL (L1)
- exceptions:
  - `RuntimeException|` x4
  - `RuntimeException|unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.init` x2
  - `RuntimeException|unwound Lcom/badlogic/gdx/backends/android/AndroidApplication;.initialize` x2
  - `RuntimeException|at Ldev/lonami/klooni/AndroidLauncher;.onCreate` x2
- families: compose-runtime, gl-native, libgdx-glsurfaceview, unclassified

### eu.quelltext.counting — PARTIAL (L1)
- families: compose-runtime

### eu.quelltext.memory — PARTIAL (L1)
- families: compose-runtime

### eu.veldsoft.no.thanks — PARTIAL (L1)
- missing classes:
  - `ClassNotFoundException` x1: `ClassNotFoundException`
  - `Landroidx/lifecycle/Lifecycling;` x1: `ClassNotFoundException; (androidx.savedstate.Recreator_LifecycleAdapter) method=Landroidx/lifecycle/Lifecycling;.generat`
  - `ClassNotFoundException?` x1: `ClassNotFoundException;`
- exceptions:
  - `RuntimeException|unwound Lkotlin/jvm/internal/Intrinsics;.checkNotNull` x2
  - `RuntimeException|unwound Landroidx/lifecycle/Lifecycling;.resolveObserverCallbackType` x2
  - `RuntimeException|unwound Landroidx/lifecycle/Lifecycling;.getObserverConstructorType` x2
  - `RuntimeException|unwound Landroidx/lifecycle/Lifecycling;.lifecycleEventObserver` x2
  - `RuntimeException|` x12
  - `RuntimeException|unwound Landroidx/lifecycle/LifecycleRegistry;.addObserver` x2
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry, unclassified

### io.github.hathibelagal.mykanji — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Landroidx/core/view/WindowInsetsCompat$Impl28;.consumeDisplayCutout` x2
  - `NullPointerException|unwound Landroidx/core/view/WindowInsetsCompat;.consumeDisplayCutout` x2
  - `NullPointerException|` x18
  - `NullPointerException|unwound Landroidx/appcompat/widget/ActionBarOverlayLayout;.init` x2
  - `NullPointerException|unwound Landroidx/appcompat/app/AppCompatDelegateImpl;.createSubDecor` x8
  - `NullPointerException|unwound Landroidx/appcompat/widget/Toolbar;.inflateMenu` x2
- families: appcompat-decor-toolbar, compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry, theme-gate, unclassified

### io.github.johnathan.minesweeper — PARTIAL (L1)
- exceptions:
  - `IllegalStateException|unwound Lyp0;.f` x2
  - `IllegalStateException|unwound Lqd0;.setValue` x2
  - `IllegalStateException|unwound Lbg;.setContent` x2
  - `IllegalStateException|at Lcom/minesweeper/MainActivity;.onCreate` x2
  - `NullPointerException|` x18
  - `NullPointerException|unwound Lop;.iterator` x6
- families: compose-runtime, unclassified

### io.github.yamin8000.dooz — PARTIAL (L1)
- missing classes:
  - `ClassNotFoundException` x11: `ClassNotFoundException`
  - `Lub1;` x1: `ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lub1;.<clinit> pc=3 → deferred handle`
  - `Las0;` x1: `ClassNotFoundException; (androidx.datastore.preferences.protobuf.DescriptorMessageInfoFactory) method=Las0;.<init> pc=13`
  - `Ls30;` x1: `ClassNotFoundException; (androidx.datastore.preferences.protobuf.ExtensionRegistry) method=Ls30;.<clinit> pc=2 → deferre`
  - `Lqg1;` x2: `ClassNotFoundException; (androidx.datastore.preferences.protobuf.GeneratedMessage) method=Lqg1;.<clinit> pc=5 → deferred`
  - `Lq3;` x2: `ClassNotFoundException; (libcore.io.Memory) method=Lq3;.<clinit> pc=3 → deferred handler @0x0x8 type=<catch-all>`
  - `Lez0;` x1: `ClassNotFoundException; (androidx.datastore.preferences.protobuf.NewInstanceSchemaFull) method=Lez0;.<clinit> pc=5 → def`
  - `Lxp0;` x1: `ClassNotFoundException; (androidx.datastore.preferences.protobuf.ListFieldSchemaFull) method=Lxp0;.<clinit> pc=5 → defer`
- exceptions:
  - `IllegalStateException|unwound Ls;.g` x2
  - `IllegalStateException|unwound Lxz1;.Y` x2
  - `IllegalStateException|unwound Lg;.q` x2
  - `IllegalStateException|unwound Lg;.h` x2
  - `IllegalStateException|unwound Lat;.a` x2
  - `IllegalStateException|unwound Llo;.B` x2
- families: compose-runtime, unclassified

### jwtc.android.chess — PARTIAL (L1)
- exceptions:
  - `IllegalStateException|unwound Lg/c0;.z` x2
  - `IllegalStateException|unwound Lg/c0;.d` x2
  - `IllegalStateException|unwound Lg/j;.a` x2
  - `IllegalStateException|unwound Landroidx/activity/ComponentActivity;.onCreate` x2
  - `IllegalStateException|unwound Landroidx/fragment/app/j;.onCreate` x2
  - `IllegalStateException|unwound Ljwtc/android/chess/start;.Z` x2
- families: compose-runtime, savedstate-registry, unclassified

### name.boyle.chris.sgtpuzzles — PARTIAL (L1)
- families: compose-runtime

### net.sourceforge.solitaire_cg — PARTIAL (L1)
- families: compose-runtime

### org.andstatus.game2048 — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Lr3;.a` x2
  - `NullPointerException|unwound Lr30;.o` x2
  - `NullPointerException|` x18
  - `NullPointerException|unwound Lgc;.L` x2
  - `NullPointerException|unwound Lz40;.a` x2
  - `NullPointerException|unwound Ldu;.a` x2
- families: compose-runtime, unclassified

### org.asafonov.accelerace — PARTIAL (L1)
- families: compose-runtime

### org.mattvchandler.a2050 — PARTIAL (L1)
- exceptions:
  - `NullPointerException|unwound Landroidx/activity/q;.a` x2
  - `NullPointerException|unwound Landroidx/fragment/app/l0;.b` x2
  - `NullPointerException|unwound Landroidx/fragment/app/t;.a` x2
  - `NullPointerException|unwound Landroidx/activity/j;.onCreate` x2
  - `NullPointerException|unwound Landroidx/fragment/app/v;.onCreate` x2
  - `NullPointerException|unwound Lq2/i;.onCreate` x2
- families: compose-runtime, savedstate-registry, unclassified

### org.secuso.privacyfriendly2048 — PARTIAL (L1)
- missing classes:
  - `ClassNotFoundException` x1: `ClassNotFoundException`
  - `Lcom/bumptech/glide/Glide;` x1: `ClassNotFoundException; (com.bumptech.glide.GeneratedAppGlideModuleImpl) method=Lcom/bumptech/glide/Glide;.getAnnotation`
  - `ClassNotFoundException?` x1: `ClassNotFoundException;`
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry, unclassified

### org.secuso.privacyfriendlybattleship — PARTIAL (L1)
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry

### org.secuso.privacyfriendlydame — PARTIAL (L1)
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry

### org.secuso.privacyfriendlymemory — PARTIAL (L2)
- families: appcompat-decor-toolbar, compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry, theme-gate

### org.secuso.privacyfriendlysolitaire — PARTIAL (L1)
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, savedstate-registry

### org.secuso.privacyfriendlysudoku — PARTIAL (L1)
- families: compose-runtime, constraint-layout, coordinatorlayout, lifecycle-adapter, multidex-family, savedstate-registry

### si.palcka.tarok — PARTIAL (L1)
- families: compose-runtime

### x653.all_in_gold — PARTIAL (L2)
- exceptions:
  - `Exception|unwound Landroid/support/design/internal/ThemeEnforcement;.checkAppCompatTheme` x4
  - `Exception|unwound Landroid/support/design/internal/ThemeEnforcement;.checkCompatibleTheme` x4
  - `Exception|unwound Landroid/support/design/internal/ThemeEnforcement;.obtainStyledAttributes` x4
  - `Exception|unwound Landroid/support/design/widget/ViewUtilsLollipop;.setStateListAnimatorFromAttrs` x2
  - `Exception|` x4
  - `Exception|at Lx653/all_in_gold/MainActivity;.onCreate` x4
- families: appcompat-decor-toolbar, compose-runtime, coordinatorlayout, lifecycle-adapter, theme-gate, unclassified

### xyz.deepdaikon.quinb — PARTIAL (L1)
- families: compose-runtime
