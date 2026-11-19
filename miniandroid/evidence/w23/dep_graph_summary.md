# W23 include-graph summary (auto: scripts/w23_dep_graph.py)

## Header cascade cost ranking (linked TUs, W22 seconds)

| header | lines | fan-out | cascade s | max TU s |
|---|---:|---:|---:|---:|
| src/dex/dalvik_engine.h | 4744 | 14 | 240.7 | 32.5 |
| src/dex/dalvik_engine_internal.h | 583 | 12 | 216.2 | 32.5 |
| src/dex/dalvik_bridge_frame.h | 190 | 6 | 140.6 | 32.5 |
| src/runtime/object_model.h | 1107 | 3 | 28.4 | 20.6 |
| src/resources/resource_parser.h | 573 | 2 | 24.5 | 20.6 |
| src/apk/apk_parser.h | 282 | 2 | 24.5 | 20.6 |
| src/renderer/software_renderer.h | 700 | 1 | 20.6 | 20.6 |
| src/dex/dex_parser.h | 484 | 1 | 20.6 | 20.6 |
| src/dex/class_resolver.h | 185 | 1 | 20.6 | 20.6 |
| src/dex/dex_interpreter_batch.h | 640 | 1 | 20.6 | 20.6 |
| src/storage/data_root.h | 163 | 1 | 20.6 | 20.6 |
| src/apk/manifest_reader.h | 580 | 1 | 20.6 | 20.6 |
| src/jni/jni_bridge.h | 743 | 1 | 20.6 | 20.6 |
| src/jni/telegram_sqlite_jni.h | 341 | 1 | 20.6 | 20.6 |
| src/diagnostics/mem_probe.h | 27 | 1 | 20.6 | 20.6 |
| src/diagnostics/trace_engine.h | 440 | 1 | 20.6 | 20.6 |
| src/framework/canvas_shadow.h | 451 | 1 | 20.6 | 20.6 |
| src/framework/shadow_registry.h | 515 | 1 | 20.6 | 20.6 |
| src/framework/dialog_shadow.h | 252 | 1 | 20.6 | 20.6 |
| src/framework/pending_intent_shadow.h | 155 | 1 | 20.6 | 20.6 |
| src/framework/clipboard_shadow.h | 60 | 1 | 20.6 | 20.6 |
| src/framework/heap_adapter.h | 410 | 1 | 20.6 | 20.6 |
| src/framework/android_shadows.h | 3241 | 1 | 20.6 | 20.6 |
| src/compat/glibc_mallinfo2.h | 50 | 1 | 20.4 | 20.4 |
| src/gles/pgl_backend.h | 113 | 2 | 7.8 | 3.9 |
| src/fonts/text_shaper.h | 366 | 2 | 7.8 | 3.9 |
| src/resources/arsc_parser.h | 449 | 1 | 3.9 | 3.9 |
| src/resources/string_pool.h | 60 | 1 | 3.9 | 3.9 |
| src/dex/mutf8.h | 106 | 1 | 3.9 | 3.9 |
| src/storage/file_sandbox.h | 607 | 1 | 3.9 | 3.9 |
| src/gles/gles20_bridge.h | 186 | 1 | 3.9 | 3.9 |
| src/jni/dlopen_exec.h | 225 | 1 | 3.9 | 3.9 |
| src/diagnostics/gfx_trace.h | 286 | 1 | 3.9 | 3.9 |
| src/framework/bitmap_shadow.h | 280 | 1 | 3.9 | 3.9 |
| src/framework/state_list.h | 62 | 1 | 3.9 | 3.9 |

## TU header weight ranking

| TU | direct includes | transitive headers | header lines | own s |
|---|---:|---:|---:|---:|
| src/runtime/application_runtime.cpp | 21 | 21 | 16093 | 20.6 |
| src/dex/dalvik_bridge.cpp | 8 | 3 | 5517 | 3.9 |
| src/dex/dalvik_bridge_domain_android_core.cpp | 1 | 3 | 5517 | 25.1 |
| src/dex/dalvik_bridge_domain_app_runtime.cpp | 1 | 3 | 5517 | 29.8 |
| src/dex/dalvik_bridge_domain_io_lang.cpp | 1 | 3 | 5517 | 28.1 |
| src/dex/dalvik_bridge_domain_jdk.cpp | 1 | 3 | 5517 | 21.3 |
| src/dex/dalvik_bridge_domain_ui_graphics.cpp | 1 | 3 | 5517 | 32.5 |
| src/dex/dalvik_interpreter.cpp | 32 | 3 | 5377 | 20.4 |
| src/dex/dalvik_engine_core.cpp | 31 | 2 | 5327 | 22.0 |
| src/dex/dalvik_engine_invoke.cpp | 31 | 2 | 5327 | 21.4 |
| src/dex/dalvik_engine_tail.cpp | 30 | 2 | 5327 | 3.9 |
| src/dex/dalvik_opcodes.cpp | 31 | 2 | 5327 | 3.9 |
| src/dex/dalvik_opcodes_invoke.cpp | 31 | 2 | 5327 | 3.9 |
| src/dex/dalvik_value_glue.cpp | 1 | 1 | 4744 | 3.9 |
| src/resources/resource_parser.cpp | 3 | 3 | 1962 | 3.9 |
| src/renderer/software_renderer.cpp | 6 | 1 | 1107 | 3.9 |
| src/framework/gl_surface_shadow.cpp | 5 | 4 | 810 | 3.9 |
| src/api/application_context.cpp | 3 | 1 | 607 | 3.9 |
| src/apk/manifest_reader.cpp | 3 | 2 | 509 | 3.9 |
| src/jni/ma_native_bridge.cpp | 2 | 2 | 393 | 3.9 |
| src/webview/canvas2d.cpp | 2 | 1 | 366 | 3.9 |
| src/webview/webview_engine.cpp | 7 | 1 | 366 | 3.9 |
| src/resources/string_pool.cpp | 2 | 1 | 106 | 3.9 |
| src/resources/resource_runtime.cpp | 5 | 1 | 62 | 3.9 |
| src/api/http_client.cpp | 1 | 0 | 0 | 3.9 |
