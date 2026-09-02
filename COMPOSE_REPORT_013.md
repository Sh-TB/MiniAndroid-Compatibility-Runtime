# COMPOSE_REPORT_013 (§16/§17)

## Status: boundary unchanged, but the approach zone narrowed — honest record

§16 forbids declaring Compose unsupported; it also forbids adding stubs
without runtime evidence. This campaign produced the following **runtime
evidence** on the two Compose corpus apps:

### dooz (io.github.yamin8000.dooz, SHA `d81292cd…`)
- Baseline and AFTER: PARTIAL_UI (1 view, 0 px). Compose code executes deep
  (011.x: livelock fixed, ComponentActivity.setContentView reached,
  ComposeView created with 0 children). The first unsolved primitive is
  unchanged: **Compose children composition** — the ComposeView never
  materializes a node tree (Composer/composition → node creation).
- Campaign-013 additions that matter to Compose apps downstream of the
  composition gap: dialog layer (Compose dialogs go through their own
  window machinery — now modeled), hierarchy shadow dispatch (Compose
  ViewRoot classes now inherit framework shadow semantics generically).

### droidify (com.looker.droidify, SHA `08d5a826…`, NEW corpus entry)
- Baseline and AFTER: ACTIVITY_FAILED. Runtime trace: `MainActivity.
  backHandler` recursive invoke COMPLETES — Compose-adjacent app code runs —
  but the activity-init chain (appcompat/appactivity attach + setContent
  bridge) never reaches a composition root; no view tree, fallback screen.
- First unsolved primitive for droidify: **AppCompatActivity attach chain**
  (shared with OB-2), NOT the Compose runtime itself.

## §17 required deliverable (if no genuine frame)

- **Exact first unsolved primitive (dooz):** composition of child composables
  into the ComposeView node tree (Composer.start/apply/change machinery).
- **Runtime trace:** 011.x evidence stands: ComposeView created with
  children=0 (render log), execution completes without composition.
- **Minimal reproducer:** dooz is the reproducer (single-activity Compose
  tic-tac-toe; setContent → ComposeView with zero children).
- **Architectural reason:** the runtime models views as ViewShadow trees
  populated by the inflater/bridge; Compose builds its own node graph at
  runtime and then expects the owner view's draw to walk THAT graph. The
  missing piece is a Composition→ViewShadow bridge (node creation hooks),
  not a renderer change.
- **Next implementation boundary:** instrument Composer entry points in a
  Compose APK; implement the smallest node-creation hook that yields ONE
  composed child in ComposeView, then re-run dooz + droidify (§16 loop).
