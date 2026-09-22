# Root-Cause Registry — S84 fan-out families

> **ONE family = ONE root-cause record.** Every blocked/partial title in
> [ACHIEVEMENTS.md](../ACHIEVEMENTS.md) references an ID here instead of
> duplicating an investigation. A/B proofs, fan-out counts and first
> divergence signatures are recorded per family. (S84 §7 user law.)

## F-NEW-160 — Class.forName framework bridge — **FIXED (S84)**

- **Signature:** `[R350-FORNAME] "android.os.Build$VERSION" → ClassNotFoundException`
  although the framework class exists on every device and the engine seeds
  its statics (`SDK_INT=34`, `RELEASE=14`).
- **Root cause:** the R350-FORNAME law resolved names against the APK DEX
  class index only; framework classes were unreachable by forName.
- **Fix:** framework bridge for the pure-data `Build` family
  (`Build`, `Build$VERSION`, `Build$VERSION_CODES`) — resolved as Class
  objects; member access rides the normal shadow paths
  (`miniandroid/src/dex/dalvik_engine.cpp`, S84 comment block).
- **A/B proof:** 9/50 S84 titles hit the CNFE pre-fix; post-fix the CNFE
  lines are gone; battery 26/26 + golden ladder 10/10 unchanged.
- **A/B regression guard (foehnix.widget):** bridging instantiable
  artifacts (`dalvik.system.CloseGuard`) pushed the app into a
  `Class.getMethod`/`Method.invoke` recursion storm (L2→L0 frame-drop
  cascade) — so instantiable classes STAY on the caught-CNFE path that
  real apps handle gracefully. The bridge is deliberately minimal.

## F-NEW-161 — Compose UI runtime internals — **OPEN (fan-out ≈ 24 titles)**

- **Signature chain:** `kotlin.reflect.jvm.internal.ReflectionFactoryImpl`
  forName CNFE (**caught, faithful** — kotlin-reflect is optional on
  devices too) → later compose-runtime NPEs (null `Iterator.hasNext` in
  the recomposition chain, null `View.getWidth` in compose layout,
  `IllegalStateException` in `setContent`) → ART process-death law
  PARTIAL.
- **Why not fixed here:** compose recomposition is an S83-GFX-BASE P4
  scope family (measure/layout semantics on top of the software raster
  base), not a one-law fix; recorded as the pinned frontier with per-title
  first-divergence signatures in `run/s84/<pkg>/obs_obs.log`.
- **Fan-out list (S84):** com.justdeax.composeStopwatch,
  com.vayunmathur.clock, com.vayunmathur.games.alchemist,
  com.ma.tehro, com.hfut.schedule, me.timeto.app, me.river.nightbell,
  com.hegocre.nextcloudpasswords, com.kompact, com.octbit.rutmath,
  com.galaxyrio.sudokusolver, com.sanskritbasics.memory,
  com.serwylo.retrowars, com.willie.mancala, com.sidhant.puzzle-family
  variants, de.seemoo.at_tracking_detection, com.bupkis.tirailleur-class
  titles and others — every `rc=1` S84 run with compose frames in its log.

## F-NEW-162 — androidx generated-adapter forName family — **OPEN (12 titles)**

- **Signature:** `androidx.savedstate.Recreator_LifecycleAdapter`
  deferred CNFE (verified NOT packaged in the APKs — the adapter is an
  optional build-time artifact, so the CNFE itself is faithful; the gap
  is that the app's fallback path still ends in deferred unwind
  PARTIAL).
- **Same family:** `androidx.activity.ComponentActivity$$ExternalSyntheticLambda`
  and datastore-preferences protobuf generated classes
  (me.river.nightbell).
- **Next action:** implement the androidx fallback semantics
  (reflective-lookup-with-catch) as one semantic shadow — expected to
  clean the deferred-unwind PARTIAL of all 12 consumers at once.

## EVID-CLASS-S84 — shared near-blank evidence class — **CAUGHT + QUARANTINED**

- **Signature:** 16 S83 evidence JPGs byte-identical (f817c243…), plus
  ×2 classes (boxcars/no-thanks, ball2box/blackjack) — apps whose
  8-frame campaign run renders a status-bar-only framebuffer
  (2–3 unique colors).
- **Detection:** the S84 validator (R5 content-hash duplicate check) —
  exactly the class of fake-by-repetition the user's canonical law
  targets.
- **Disposition:** all members demoted to OBSERVED (no canonical
  artifact, log references only); near-blank frames are not visual
  evidence per the S54 gate law. Real-UI evidence for dooz restored from
  the s83b sweep (content-verified distinct).
- **Rule going forward:** no campaign ships a screenshot whose content
  hash equals another title's — the validator enforces this on every
  wave.

## Engine laws landed in S84 (summary)

| Law | Status | Proof |
|---|---|---|
| F-NEW-160 forName framework bridge (Build family) | FIXED | 9-title CNFE eliminated; battery 26/26; ladder 10/10; foehnix A/B guard |
| F-NEW-161 compose internals | OPEN (P4 scope) | ~24-title fan-out with first-divergence signatures |
| F-NEW-162 androidx adapter fallback | OPEN | 12-title fan-out, verified packaging state |
| EVID-CLASS-S84 evidence quarantine | ENFORCED | validator R5 + 20-title demotion |
