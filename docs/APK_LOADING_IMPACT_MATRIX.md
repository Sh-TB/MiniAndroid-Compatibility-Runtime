# APK LOADING IMPACT MATRIX — M8 (2026-09-10)

Chain-layer view (APK → ZIP → Manifest → resources → DEX parse → decode →
tag semantics → interpreter → frames → class resolution → Java/Kotlin →
reflection → framework → lifecycle → Handler/Looper → scheduling → View
tree → Compose → measure/layout/draw → Canvas → framebuffer). Each layer:
worst current blocker + fix generation that cleared it.

| Layer | Status | Cleared by | Remaining blocker |
|---|---|---|---|
| APK/ZIP/Manifest/resources | PASS (13 corpus APKs hash-verified) | EXP-06x resource chain | — |
| DEX parse/decode (24 formats) | PASS | EXP-059..071 family | — |
| Interpreter tag semantics | PASS | F-028/F-028b/F-030/F-035/F-035b/F-040/F-042/F-043/F-044/F-045 | — |
| Frames (recursive invoke, returns) | PASS | F-044 per-frame return-descriptor law | — |
| Class resolution / linking | PASS | EXP-061 default-interface + overload laws | — |
| Java/Kotlin core | PASS | F-030 zero law, F-036/F-039 collections, F-050b Throwable message, F-050c updater epochs, F-050d Boolean statics | WeakReference semantics (open) |
| Reflection | PASS | F-029 core + FIX-M3-012b reconciliation | — |
| Framework services | PASS | F-031/F-032/F-033 service registry; F-029a/b Handler family | remaining system-service entries (queued F-046 candidate) |
| Lifecycle | PASS | G07 state machine; ActivityLifecycleCallbacks family not yet exercised by corpus | — |
| Handler/Looper/scheduling | PASS (one MessageQueue law) | HandlerShadow virtual clock, drain_quiescent storm bounds | — |
| Choreographer/frame pump | **NEW PASS** | **F-050a** shadow + deterministic vsync pump | — |
| Compose runtime | PARTIAL | F-020 snapshot primitives, F-040 scatter-map, F-044 return descriptors | **Job-active cancellation of the frame await (M9 battle)** |
| Measure/layout/draw | PASS for View trees (corpus-proven); UNPROVEN for Compose trees | default-onMeasure law, real-DEX onMeasure | first Compose frame not yet composed |
| Canvas/framebuffer | PASS | Cycle-E validator | — |
| Input | PASS | G06 canonical tap pipeline | Compose tap→recompose unproven until first frame |
| Persistence/SQLite | PASS | F-024/F-026/F-027 + unote cross-APK | — |
| JNI/Telegram-class natives | BLOCKED (external) | — | Telegram 82 MB artifact unobtainable (1.2 MB stub served); JNI family unexercised |

Honesty note: dooz framebuffer remains 0 non-white (deterministic BLANK,
SHA 31ddd4d5…). The Compose first-frame chain advanced four blocker layers
this session (scheduler corruption → Boolean statics → channel-cancel →
frame-callback lifecycle); the frame is NOT yet composed and NO Compose
visual success is claimed.
