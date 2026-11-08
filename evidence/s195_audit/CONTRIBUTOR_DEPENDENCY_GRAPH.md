# CONTRIBUTOR DEPENDENCY GRAPH — S195 AUDIT (2026-11-08)

One runtime, shared paths (mission §5). `■` = landed on the integration
binary `31be843614e67bab`; `□` = published but pending; `·` = observed only.

## Path C — libGDX (the this-wave frontier)
```
APK → Manifest → [■ route profile (S188 §4, 49 pinned)]
   → Application/Activity [■]
   → libGDX init: EGL family [■ W17 F-NEW-601..604]
   → AssetManager → F-NEW-580/580b String boundary [□ S196 pending] ← tictactoe dies HERE
   → JNI natives: [■ W18 F-NEW-605..613] + [□ C3 f582 registry shapes]
   → FreeType: [■ W18 $-mangling + persistent direct buffers]
   → Gdx2DPixmap: [■ W18] → FT bitmap-render leg [□ W19a]
   → GL: [■ C3 S198a spec→PGL map + marshal fallback] [□ S198c typed-view setters]
   → SpriteBatch C-shaders [■ S198a] → Framebuffer [□ composite leg]
```

## Path A — real graphical View app
```
APK → Manifest → PackageManager [■/□ C7 waves pending full graph]
   → Activity [■] → ViewTree [■] → Adapter [■ C3 gmdice]
   → Measure/Layout/Draw [■] → Canvas [■ CLASSIC_CANVAS]
   → Framebuffer [■ — gmdice/opencalc/chessclock/microtimer REAL_APP_CONTENT ×3]
```

## Path B — resource-heavy app
```
APK → ARSC [■ C9-1..3 + S194] → AssetManager [■]
   → BitmapFactory [■ C9-1 density] → Drawable [■]
   → NinePatch npTc [■ f053 = C9-28 equivalent] → ImageView [■]
   → provider-authority resource refs [□ C4 F-C4-631 pending]
```

## Path D — background execution
```
APK → Activity [■] → Service/Handler/Executor [■/□ C8 waves 8–10 integrated;
   97/97 marker probe re-run pending] → Kotlin Coroutines [□ C8 W11+W12]
   → Lifecycle [■] → UI update [■]
```

## Path E — multi-app
```
install → package index [■/□ C7] → Intent resolution [□]
   → cross-package DEX [□] → component lifecycle [□]
```

## Shared intersections proven this wave
- **One direct-buffer registry**: C3's S196 f582 registry shape and the
  W18 f590 engine-hook registry now serve ONE lookup
  (`nativeexec::lookup_direct_buffer`) consumed by the C3 S198 GLES
  marshal fallback — no second registry (mission §4 C6: "do not build
  two independent GL execution systems").
- **Route law + cohort**: 7 new route profiles; tictactoe run became
  ROUTE-DECIDED (was route-blind — the console itself warned "NOT a pass").
- **Ancestry law shared**: C3 S197 GLSurfaceView→SurfaceView edge fixed
  dooz uncaught 6→0 — a Coder-3 law improving a Coder-1-era golden app.
