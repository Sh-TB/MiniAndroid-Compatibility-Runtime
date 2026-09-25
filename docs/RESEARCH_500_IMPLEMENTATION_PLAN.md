# R500 IMPLEMENTATION PLAN (next wave queue, evidence-ranked)

Only entries with source law + repo divergence + (where shown) runtime
reproduction are listed. Each entry names the law, the exact code target and
the regression gate. Priorities are MEASURED (corpus fan-out / probe proof),
never the input document's labels.

## Queue

### 1. ROOT-005 — CLASS-IDENTITY dual-identity instanceof (R500-009/086/087/088)
- Law: AppCompatViewInflater substitution means the runtime object IS the
  AppCompat class; type tests must consult the real descriptor.
- Target: `layout_inflater.cpp` record the ORIGINAL requested descriptor on
  inflated nodes (dual identity); `dalvik_engine.cpp is_subclass_of` +
  `instanceof` consult it; check-cast strictness measured BEFORE flipping.
- Measured demand: 22/59 corpus APKs type-test mapped-away classes
  (run/s103/u001_typescan.json). Regression gate: full census + battery
  105/105 + check-cast CCE delta measured.
- Risk note: the optimistic check-cast currently ABSORBS latent CCEs; flip
  only together with the dual-identity fix that makes real Android also
  answer TRUE.

### 2. ROOT-004 — DECOR-LINKAGE sub-decor attach (R500-096/097/099)
- Law: createSubDecor output must be linked under the window DecorView root
  so WindowDecorActionBar.findViewById resolves decor_content_parent /
  action_bar (S103 3/3 evidence: root=70 NOT FOUND vs receiver=cf FOUND).
- Target: `layout_inflater.cpp` sub-decor attach model + ticket #348 stages
  (menu XmlPullParser, WindowInsets non-null producer).
- Fan-out: decor-toolbar family (6 titles) + every decor.findViewById.

### 3. ROOT-GLSL — GLSL shader execution frontier (R500-047, blocks 023/033)
- Law: GLES20.glShaderSource+compile+link must produce executable programs
  (GLSL). Current: source stored verbatim; PGL executes C-function shaders.
- Route: GLSL->C translator or Mesa llvmpipe adoption
  (GLES_BACKEND_COMPARISON_010.md). Gate: libGDX titles (tictactoe,
  klooni, halma) currently gl-native blocked.

### 4. ROOT-GL-BRIDGE — texture-upload dispatch (R500-023/035/046/055)
- Law: the GLES bridge must dispatch glTexImage2D/glTexSubImage2D/
  glFramebufferTexture2D/glReadPixels to PGL (C-level already implemented).
- Gate: corpus GL-title demand scan; ship with a texture-upload fixture
  (screenshot-diff golden).

### 5. Compose host wiring (ticket #350; downstream of ROOT-001 fix)
- After the field-identity law: re-run solitaire; expected next divergences
  in ViewModelProvider/LifecycleOwner/View.getHandler/BroadcastFrameClock/
  Recomposer (S103 downstream list). One law per commit.

### 6. SavedState wave preparation (S102 R16 map)
- COMPOSE_REQUIRED/BOTH/SAVEDSTATE_REQUIRED/NOT_REQUIRED classification is
  in docs/S102_REPORT.md; SavedStateRegistry/Controller laws land after the
  compose host wiring advances.

### 7. Latent guards (implement only when corpus demands)
- ARSC OFFSET16/COMPACT (0/54 exposure), CDEX (0 exposure, clean rejection),
  SQLite WAL journal mode (byte-determinism decision documented), ETC1/S3TC/
  ATC/PVRTC (asset scan pending), Theme.applyStyle producer (fixture first).

## Regression protocol (per law, binding)
1. minimal fixture (build_fixture_apk.sh) — 3/3 byte-identical screenshots
2. relevant unit/battery stages
3. previously failing real APK + sibling APKs
4. full battery 105/105
5. full census rerun (scripts/r500/r500_full_load.py) — flip table vs prior
   census; zero-regression gate
