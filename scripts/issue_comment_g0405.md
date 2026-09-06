## G04+G05 — DRAWABLE/IMAGE + LAYOUT/MEASURE/RENDER CLOSURE (VERIFIED WITH EXPLICIT NON-BLOCKING BOUNDARIES)

Baseline blind-verified this session: HEAD cc42a891 → campaign HEAD (7 commits),
battery 26 → 31 stages ALL PASS, all frozen goldens byte-identical
(EXT-01 3× `142238fd92b69e11`), corpus 3/3, EXT-01 fixture re-frozen SHA-exact.

### Finding
Four real defects + one architectural violation in the drawable/layout layer:
ZIP-path-string density ranking bypassed the canonical config engine; zero
density scaling (inDensity/inTargetDensity law absent); no ImageView scaleType
law ((left+5,top+5) natural-size draws / FIT_XY stretches); EXACTLY containers
double-counted padding; weighted subtrees never re-measured; drawable
resolution via R-field-name indirection (0/35 on Markor);
`tools/resource_trace.cpp` claimed by d306f1e2 but never committed.

### Android law
ResourceTypes.cpp `ResTable_config::isBetterThan` L2690–2737 (bucket
selection: exact > both-above→smaller > straddle→higher);
BitmapFactory.java `decodeResourceStream` + BitmapFactory.cpp L347–353
(inDensity → inTargetDensity scaling, DENSITY_NONE);
ImageView.java L255 (FIT_CENTER default) + onMeasure intrinsic law;
LinearLayout.java L855/L985–1045/L1385–1445 (weight: sequential share with
remainingWeightSum decrement, 0dp+weight from scratch, base+share
shrinkable, weightSum cap, EXACTLY re-measure). All @ android-14.0.0_r2.

### Fix
select_file() canonical file-resource selection (chain-safe, selected-config
reporting); single 420dpi device law; BitmapFactory scaling; FIT_CENTER +
intrinsic measure via allocation-free header probe (PNG/WebP/JPEG); EXACT
weight law port with second-pass re-measure; direct resid→drawable
resolution; resource_trace rebuilt with G04/G05 channels.

### Verification
- New batteries: LinearLayout/MeasureSpec law 24/24; G04 hostile 24/24;
  density-matrix oracle 11/11 — battery now 31 stages ALL PASS.
- Density-matrix differential oracle (real aapt2-built APK, color-coded
  buckets): @420dpi straddle law picks xxxhdpi → 26×13 (scale 420/640);
  @320dpi exact bucket picks xhdpi → 40×20; DENSITY_NONE never scaled;
  alias chain terminal-config governs; exact pixel bboxes; 3-run
  byte-identical (`351340a7a92e645c`).

### Runtime evidence
Density matrix: same request, two devices — bucket + scale change visible in
pixels. Corpus: EXT-01 + 3 registry apps SUCCESS; KISS/Markor boot + real DEX
with AppCompat-shell boundary documented (G06+).

### Commits
e98cf4b0 (audit) · 768b1481 (drawable/density law) · 291914c7 (trace tool) ·
894e6ef3 (weight/measure law) · e7e6ec1b (density oracle) · ae37abf4 (hostile)
· 3d1eba51 (direct resid resolution + boundaries) — PUSH_BLOCKED (no token
this session; fast-forward-ready on origin/main 748c4337).

### Status
researched / implemented / tested / runtime-proven / visually-proven for the
density+drawable+measure+layout+render pipeline on classic-View APKs;
VERIFIED WITH EXPLICIT NON-BLOCKING BOUNDARIES: AppCompatDelegateImpl shell
(KISS/Markor blank windows, root cause + evidence), NinePatch chunk stretching
(unreachable pre-shell), nearest-neighbour resampling note; Compose corpus
item NOT APPLICABLE (Fossify Notes ships androidx.compose).
