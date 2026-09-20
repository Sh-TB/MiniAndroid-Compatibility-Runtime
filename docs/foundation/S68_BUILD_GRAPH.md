# S68 BUILD GRAPH AUDIT (FINAL BASE CLOSURE)

Method: Makefile `CORE_SOURCES` + `main.cpp` = LIVE-COMPILED roots; transitive `#include` closure = LIVE-INCLUDED; rest = DEAD.

## Engine binary symbol presence (nm -C)

| symbol | defs |
|---|---|
| SoftwareRenderer | 0 |
| ViewRenderer | 0 |
| RealLayout | 0 |
| ExceptionSystem | 0 |
| ApiDispatcher | 0 |
| LayoutInflater | 138 |
| TouchDispatcher | 21 |
| CanvasShadow | 28 |

## Counts

- LIVE-COMPILED: 40
- LIVE-INCLUDED: 50
- DEAD: 27

## DEAD files (not compiled by Makefile, not transitively included)

| file | bytes |
|---|---|
| src/audio/audio_engine.cpp | 12503 |
| src/audio/audio_engine.h | 5401 |
| src/dex/api_dispatcher.cpp | 22529 |
| src/dex/api_dispatcher.h | 13805 |
| src/dex/exception_system.cpp | 7782 |
| src/dex/exception_system.h | 13543 |
| src/dex/execution_guard.cpp | 10468 |
| src/dex/execution_guard.h | 9904 |
| src/dex/execution_observatory.cpp | 21861 |
| src/dex/execution_observatory.h | 19328 |
| src/exp002_main.cpp | 16922 |
| src/exp003a1_validate.cpp | 27648 |
| src/exp003batch_main.cpp | 27430 |
| src/exp004_main.cpp | 59491 |
| src/exp005_main.cpp | 41632 |
| src/exp006_main.cpp | 52468 |
| src/exp007_012_megabatch_main.cpp | 26755 |
| src/exp007_012_megatch_main_temp.cpp | 478 |
| src/games/tictactoe3d.h | 16774 |
| src/gles/gles20_bridge.cpp | 5848 |
| src/gles/gles20_bridge.h | 2836 |
| src/gles/pgl_backend.cpp | 1489 |
| src/gles/pgl_backend.h | 1767 |
| src/renderer/view_renderer.cpp | 30349 |
| src/renderer/view_renderer.h | 3026 |
| src/resources/real_layout.cpp | 19836 |
| src/resources/real_layout.h | 5282 |

## LIVE-COMPILED (Makefile)

- src/api/application_context.cpp
- src/api/shared_prefs.cpp
- src/apk/apk_parser.cpp
- src/apk/manifest_reader.cpp
- src/dex/class_resolver.cpp
- src/dex/dalvik_engine.cpp
- src/dex/dex_interpreter_batch.cpp
- src/dex/dex_parser.cpp
- src/dex/mutf8.cpp
- src/dex/trace_exporter.cpp
- src/diagnostics/trace_engine.cpp
- src/fonts/text_shaper.cpp
- src/framework/android_shadows.cpp
- src/framework/atomic_shadow.cpp
- src/framework/canvas_shadow.cpp
- src/framework/choreographer_shadow.cpp
- src/framework/clipboard_shadow.cpp
- src/framework/dialog_shadow.cpp
- src/framework/executor_shadow.cpp
- src/framework/lifecycle_controller.cpp
- src/framework/locks_shadow.cpp
- src/framework/pending_intent_shadow.cpp
- src/framework/shadow_registry.cpp
- src/framework/state_list.cpp
- src/framework/touch_dispatcher.cpp
- src/main.cpp
- src/renderer/software_renderer.cpp
- src/resources/arsc_parser.cpp
- src/resources/axml_parser.cpp
- src/resources/layout_inflater.cpp
- src/resources/res_config.cpp
- src/resources/res_id.cpp
- src/resources/resource_parser.cpp
- src/resources/resource_runtime.cpp
- src/resources/string_pool.cpp
- src/runtime/application_runtime.cpp
- src/runtime/execution_engine.cpp
- src/storage/data_root.cpp
- src/storage/file_sandbox.cpp
- src/storage/sqlite_shadow.cpp

## LIVE-INCLUDED (headers pulled in transitively)

- src/api/android_context.h
- src/api/android_stubs.h
- src/api/shared_prefs.h
- src/apk/apk_parser.h
- src/apk/manifest_reader.h
- src/dex/class_resolver.h
- src/dex/dalvik_engine.h
- src/dex/dex_interpreter_batch.h
- src/dex/dex_parser.h
- src/dex/encoded_value.h
- src/dex/mutf8.h
- src/dex/trace_exporter.h
- src/diagnostics/click_audit.h
- src/diagnostics/mem_probe.h
- src/diagnostics/trace_engine.h
- src/fonts/text_shaper.h
- src/framework/android_shadows.h
- src/framework/atomic_shadow.h
- src/framework/canvas_shadow.h
- src/framework/choreographer_shadow.h
- src/framework/clipboard_shadow.h
- src/framework/dialog_shadow.h
- src/framework/executor_shadow.h
- src/framework/heap_adapter.h
- src/framework/lifecycle_controller.h
- src/framework/locks_shadow.h
- src/framework/pending_intent_shadow.h
- src/framework/shadow_registry.h
- src/framework/state_list.h
- src/framework/touch_dispatcher.h
- src/framework/view_ancestry.h
- src/jni/jni_bridge.h
- src/renderer/bitmap_font_data.h
- src/renderer/software_renderer.h
- src/resources/arsc_parser.h
- src/resources/axml_parser.h
- src/resources/layout_inflater.h
- src/resources/res_config.h
- src/resources/res_id.h
- src/resources/resource_parser.h
- src/resources/resource_runtime.h
- src/resources/string_pool.h
- src/runtime/application_runtime.h
- src/runtime/execution_engine.h
- src/runtime/object_model.h
- src/runtime/runtime_metadata.h
- src/runtime/vtable_dispatch.h
- src/storage/data_root.h
- src/storage/file_sandbox.h
- src/storage/sqlite_shadow.h
