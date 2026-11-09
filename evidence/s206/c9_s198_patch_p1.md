**S198 rebased phase-3 patch part 1/4** (base `0979678e`; verified `git apply --check` APPLIES_CLEAN on a pristine `0979678e` worktree; the applied result is byte-identical to the in-container-verified tree that produced binary `4d832c255bed513c`: c9_phase3_laws_test **46/46**, density 36/36, zip 42/42, §5/§6 harness **48/49** with ONLY the P-NEW-5 size-word law failing, resourceval **30/31** with ONLY law 29 failing)

```diff
diff --git a/miniandroid/Makefile b/miniandroid/Makefile
index e43fa77a..1b3ed607 100755
--- a/miniandroid/Makefile
+++ b/miniandroid/Makefile
@@ -42,7 +42,7 @@ APK_SOURCES = $(SRCDIR)/apk/apk_parser.cpp $(SRCDIR)/apk/manifest_reader.cpp
 DEX_SOURCES = $(SRCDIR)/dex/dex_parser.cpp $(SRCDIR)/dex/mutf8.cpp $(SRCDIR)/dex/class_resolver.cpp $(SRCDIR)/dex/dex_interpreter_batch.cpp $(SRCDIR)/dex/dalvik_engine.cpp $(SRCDIR)/dex/trace_exporter.cpp  # EXP-031.5: Trace exporter
 RUNTIME_SOURCES = $(SRCDIR)/runtime/execution_engine.cpp $(SRCDIR)/runtime/application_runtime.cpp $(SRCDIR)/runtime/route_law.cpp
 DIAGNOSTICS_SOURCES = $(SRCDIR)/diagnostics/trace_engine.cpp $(SRCDIR)/diagnostics/crash_forensics.cpp $(SRCDIR)/diagnostics/trace_overlay.cpp $(SRCDIR)/diagnostics/install_inspection.cpp
-RESOURCES_SOURCES = $(SRCDIR)/resources/res_id.cpp $(SRCDIR)/resources/res_config.cpp $(SRCDIR)/resources/resource_parser.cpp $(SRCDIR)/resources/string_pool.cpp $(SRCDIR)/resources/arsc_parser.cpp $(SRCDIR)/resources/axml_parser.cpp $(SRCDIR)/resources/layout_inflater.cpp $(SRCDIR)/resources/vector_inflater.cpp $(SRCDIR)/resources/s132_svg_reader.cpp $(SRCDIR)/resources/resource_runtime.cpp
+RESOURCES_SOURCES = $(SRCDIR)/resources/res_id.cpp $(SRCDIR)/resources/res_config.cpp $(SRCDIR)/resources/resource_parser.cpp $(SRCDIR)/resources/string_pool.cpp $(SRCDIR)/resources/arsc_parser.cpp $(SRCDIR)/resources/axml_parser.cpp $(SRCDIR)/resources/layout_inflater.cpp $(SRCDIR)/resources/vector_inflater.cpp $(SRCDIR)/resources/s132_svg_reader.cpp $(SRCDIR)/resources/resource_runtime.cpp $(SRCDIR)/resources/font_family.cpp $(SRCDIR)/resources/plurals.cpp
 RENDERER_SOURCES = $(SRCDIR)/renderer/software_renderer.cpp $(SRCDIR)/renderer/vector_decode.cpp $(SRCDIR)/renderer/gif_decoder.cpp $(SRCDIR)/gles/pgl_backend.cpp $(SRCDIR)/gles/gles20_bridge.cpp $(SRCDIR)/gles/gl_copy_bridge.cpp  # F-NEW-586: glCopyTexImage2D/ glCopyTexSubImage2D dlopen contract (libgdx)
 # UNIFIED_007 text pipeline — REAL FriBidi/HarfBuzz/FreeType shaping now
 # feeds BOTH the layout measure pass and the view draw path (was: orphaned
```
