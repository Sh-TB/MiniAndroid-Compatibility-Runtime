# MiniAndroid Runtime v0.1 - Simple Makefile
# For systems without CMake

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -g -O2 -MMD -MP
# Repo-root discovery (R11/R23: builds must work outside one developer's VM).
REPO_ROOT := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
# EXP-097 §7: rlottie headers + rlottie static lib for Lottie rendering.
RLOTTIE_DIR ?= $(REPO_ROOT)/tools/rlottie
# Optional codecs (AOSP-style codec availability): WebP/Lottie are compile-time
# optional so the runtime also builds where those libs are not ported yet.
MINIANDROID_HAVE_WEBP ?= 1
MINIANDROID_HAVE_LOTTIE ?= 0
# GP583-BUILD-001 fix: the BASE include assignment must come BEFORE every
# optional `INCLUDES +=` block. The old order appended the Lottie include
# first and then REPLACED INCLUDES wholesale on the next line, so a custom
# RLOTTIE_DIR build enabled the feature and linked librlottie.a yet could
# not find rlottie_capi.h (make -pn showed the expanded INCLUDES without
# the Lottie path). Base first, appends after — the += blocks now survive.
INCLUDES = -Isrc -Isrc/webview -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Isrc/fonts -Isrc/gles -Isrc/jni -Isrc/audio -Ithird_party/portablegl -I/usr/include/freetype2 -Ithird_party/nlohmann_json/include
ifeq ($(MINIANDROID_HAVE_WEBP),1)
CXXFLAGS += -DMINIANDROID_HAVE_WEBP
endif
ifeq ($(MINIANDROID_HAVE_LOTTIE),1)
INCLUDES += -I$(RLOTTIE_DIR)/inc
CXXFLAGS += -DMINIANDROID_HAVE_LOTTIE
endif
# EXP-097 §5/§6: image codec libraries.
# libwebp — Google reference WebP decoder (used by AOSP Skia / BitmapFactory)
# libjpeg — IJG reference JPEG decoder (Android uses libjpeg-turbo, drop-in API)
# rlottie  — Samsung reference Lottie renderer (Telegram uses it directly)
LIBS = -lz -ljpeg -lstdc++ -lm -lpthread -lsqlite3 -lssl -lcrypto -lmpg123 -lsndfile  # S100 NET-001: TLS through OpenSSL (BoringSSL lineage)  # M3 F-ROOM-CHAIN: real SQLite backend
ifeq ($(MINIANDROID_HAVE_WEBP),1)
LIBS += -lwebp -lwebpdemux
endif
ifeq ($(MINIANDROID_HAVE_LOTTIE),1)
LIBS += $(RLOTTIE_DIR)/build/src/librlottie.a
endif
# UNIFIED_007: font pipeline + PNG drawable decode
FONTS_LIBS = -lfreetype -lharfbuzz -lfribidi -lpng

# Directories
SRCDIR = src
BUILDDIR = build
TESTDIR = tests

# GP583-BUILD-002: ONE shared source manifest consumed by BOTH build
# graphs. The old duplicated list drifted (CMake carried 12 TUs while the
# Makefile linked 74) so two build commands produced materially different
# runtime capability. core_sources.manifest is the single source of truth:
# the Makefile and miniandroid/CMakeLists.txt both read it, and
# `make check-source-parity` asserts the Makefile expansion equals the
# manifest (run in the test battery).
CORE_SOURCES := $(shell grep -v '^#' core_sources.manifest)
# Per-lane views of the manifest are kept for documentation purposes only;
# the canonical list is the manifest. (The old hand-maintained duplicates
# were removed — they were the drift surface BUILD-002 documents.)
QUICKJS_DIR = third_party/quickjs
QUICKJS_SOURCES = $(QUICKJS_DIR)/quickjs.c $(QUICKJS_DIR)/libregexp.c $(QUICKJS_DIR)/libunicode.c $(QUICKJS_DIR)/cutils.c $(QUICKJS_DIR)/libbf.c
QUICKJS_OBJECTS = $(patsubst $(QUICKJS_DIR)/%.c,$(BUILDDIR)/quickjs/%.o,$(QUICKJS_SOURCES))
QUICKJS_CFLAGS = -O2 -std=gnu11 -D_GNU_SOURCE -DCONFIG_VERSION=\"2024-01-13\" -DCONFIG_BIGNUM -w -I$(QUICKJS_DIR)

CORE_OBJECTS = $(patsubst $(SRCDIR)/%.cpp,$(BUILDDIR)/%.o,$(CORE_SOURCES))
# S-2 native execution thunk (System V x86_64 dynamic call)
THUNK_OBJECT = $(BUILDDIR)/jni/native_thunk.o

# Main executable
MAIN_SOURCE = $(SRCDIR)/main.cpp
MAIN_OBJECT = $(BUILDDIR)/main.o
EXECUTABLE = $(BUILDDIR)/miniandroid

# Test executable
TEST_SOURCE = $(TESTDIR)/simple_test.cpp
TEST_OBJECT = $(BUILDDIR)/test.o
TEST_EXECUTABLE = $(BUILDDIR)/miniandroid_test

# nlohmann/json (header-only, download if needed)
JSON_DIR = third_party/nlohmann_json
JSON_INCLUDE = -I$(JSON_DIR)/include

# F-NEW-387 anchor set (CONT-113): the Android-soname ELF anchors
# (libm.so/liblog.so/libc.so/libdl.so/libstdc++.so under build/anchor_libs)
# are a REQUIRED build artifact of the native loader, not an optional
# extra — a fresh container that rebuilds only the binary loses them and
# every libGDX-family APK dies with "dlopen failed: ... invalid ELF
# header" (the host libm.so is a GNU ld script, not an ELF). `all` builds
# them so the anchor set can never go stale/missing again.
.PHONY: all clean test test-core test-hostile test-law test-all run-battery check-source-parity run help version megabatch run-megabatch anchors laws130

# Explicit default goal: rule order must not silently demote `all`.
.DEFAULT_GOAL := all

ANCHOR_LIBS = $(BUILDDIR)/anchor_libs

anchors:
	@bash ../scripts/cont83_build_anchors.sh

all: $(EXECUTABLE) anchors

$(EXECUTABLE): $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(MAIN_OBJECT) $(BUILDDIR)/jni/bionic_compat.o $(BUILDDIR)/jni/pthread_shadow.o
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -rdynamic -o $@ $^ $(LIBS) $(FONTS_LIBS)
	@echo "Build complete: $(EXECUTABLE)"

$(THUNK_OBJECT): $(SRCDIR)/jni/native_thunk.S
	@mkdir -p $(dir $@)
	gcc -c -o $@ $<

$(BUILDDIR)/%.o: $(SRCDIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

# CONT-37 (F-NEW-298): dalvik_engine.cpp has grown past the -g debug-info
# cc1plus peak on the 4 GB build host (repeated OOM kills at -O2 -g; the
# -O2 -g0 compile of the same TU fits). Same optimization level (-O2),
# only the debug sections are dropped for THIS translation unit — the
# generated code is unchanged vs -O2. Recorded in evidence/cont37.
$(BUILDDIR)/dex/dalvik_engine.o: $(SRCDIR)/dex/dalvik_engine.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -g0 $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

# CONT-39 (F-NEW-301): android_shadows.cpp hit the SAME cc1plus -g peak
# (OOM kill at ~936 MB RSS during this wave's build — dmesg recorded).
# Same precedent, same contract: -O2 unchanged, debug sections dropped
# for THIS translation unit only.
$(BUILDDIR)/framework/android_shadows.o: $(SRCDIR)/framework/android_shadows.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -g0 $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<


$(BUILDDIR)/jni/bionic_compat.o: $(SRCDIR)/jni/bionic_compat.c
	@mkdir -p $(dir $@)
	gcc -O2 -fPIC -c -o $@ $<

# S188-W8 F-NEW-585: bionic pthread-attr shadow family — the exe exports
# the attr-family symbols (-rdynamic) so bionic-compiled libraries
# (libflutter etc.) get correct 56-byte-attr semantics without stack
# corruption; hot-path lock/unlock pass straight through (RTLD_NEXT).
$(BUILDDIR)/jni/pthread_shadow.o: $(SRCDIR)/jni/pthread_shadow.c
	@mkdir -p $(dir $@)
	gcc -O2 -fPIC -c -o $@ $<

$(BUILDDIR)/quickjs/%.o: $(QUICKJS_DIR)/%.c
	@mkdir -p $(dir $@)
	gcc $(QUICKJS_CFLAGS) -I$(QUICKJS_DIR) -c -o $@ $<

$(BUILDDIR)/main.o: $(MAIN_SOURCE)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

# Tests
# S130 law tests (pure models, deterministic). Full CORE closure so the
# battery gate can always rebuild them reproducibly.
LAWS130_SOURCE = $(TESTDIR)/s130_laws_test.cpp
LAWS130_EXECUTABLE = $(BUILDDIR)/s130_laws_test

laws130: $(LAWS130_EXECUTABLE)
	./$(LAWS130_EXECUTABLE)

$(LAWS130_EXECUTABLE): $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(LAWS130_SOURCE)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $(LAWS130_SOURCE) $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(LIBS) $(FONTS_LIBS)

# A-R5 (S220): the R25 declared!=runtime receiver dispatch matrix probe
# (roadmap section 5 C3's demanded deliverable) + the A-R4 mwr opcode probe —
# both linked per the LAWS130 pattern (+ THUNK_OBJECT, the S215 receipt's
# link correction: miniandroid_native_thunk lives in the thunk object).
# r25_dispatch_matrix_test ALSO joins the required-law battery below.
MWR_PROBE_SOURCE = $(TESTDIR)/mwr_opcode_probe_test.cpp
MWR_PROBE_EXECUTABLE = $(BUILDDIR)/mwr_opcode_probe
mwr_opcode_probe: $(MWR_PROBE_EXECUTABLE)
	./$(MWR_PROBE_EXECUTABLE)

$(MWR_PROBE_EXECUTABLE): $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(MWR_PROBE_SOURCE)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $(MWR_PROBE_SOURCE) $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(LIBS) $(FONTS_LIBS)

R25_SOURCE = $(TESTDIR)/r25_dispatch_matrix_test.cpp
R25_EXECUTABLE = $(BUILDDIR)/r25_dispatch_matrix
r25_matrix: $(R25_EXECUTABLE)
	./$(R25_EXECUTABLE)

$(R25_EXECUTABLE): $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(R25_SOURCE)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $(R25_SOURCE) $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(LIBS) $(FONTS_LIBS)

# A-R6 (S226 main): the Kotlin well-known-types family probe (roadmap §8 F1)
# — the A-R6 census rows (Unit identity · Pair/Triple product semantics ·
# interface default-body dispatch · Intrinsics null-safety contract) gated
# as hard asserts after the fix wave. Same LAWS130 + THUNK_OBJECT pattern.
KOTLIN_SOURCE = $(TESTDIR)/kotlin_family_probe_test.cpp
KOTLIN_EXECUTABLE = $(BUILDDIR)/kotlin_family_probe
kotlin_family: $(KOTLIN_EXECUTABLE)
	./$(KOTLIN_EXECUTABLE) --expect

$(KOTLIN_EXECUTABLE): $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(KOTLIN_SOURCE)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $(KOTLIN_SOURCE) $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(LIBS) $(FONTS_LIBS)

# GP583-TEST-001: the default `test` target ran ONLY simple_test while the
# tests/ directory carries the real regression battery (law tests, hostile-
# resource suites, the GP-582 engine boundary probe, opcode probes). A green
# `make test` therefore coexisted with dozens of unexecuted law tests. ONE
# pattern rule builds every tests/*.cpp against the full core closure; the
# battery targets below give every REQUIRED suite one automatic entry point
# with a timeout, an exit status and a machine-readable summary.
#
# Classification (GP583-TEST-001 remediation ledger):
#   required-core        : simple_test, s130_laws_test, gp582_engine_probe_test
#   required-hostile     : g04_hostile, g06g08_hostile, resource_hostile
#   required-law         : lifecycle, input_pipeline, linear_layout, g10_layout,
#                          g11_ctor, m3_arsc_style, mutf8_string_pool,
#                          resource_core, resource_config_selection, s98_prefs,
#                          s98_scroll_transform, s98_text, s106_* (6),
#                          c013_arsc_probe, encoded_value_law, gp583_gles_law,
#                          r25_dispatch_matrix (A-R5 ART dispatch law),
#                          gp583_img004_bounds (inJustDecodeBounds law)
#   manual diagnostic    : dbg_test, exp088_*, exp092, font_pipeline_probe,
#                          probe_arsc_layout, mwr_opcode_probe (run by hand /
#                          dedicated waves; not in test-all)
#   fixture-argument probe: m3_arsc_style_law_test, s106_drawables_law_test,
#                          c013_arsc_probe — these take a resources.arsc /
#                          APK fixture path as argv (exit 2 = usage); they
#                          run inside their dedicated waves with fixtures,
#                          NOT from the zero-arg battery.
TEST_CORE = simple_test s130_laws_test gp582_engine_probe_test
TEST_HOSTILE = g04_hostile_test g06g08_hostile_test resource_hostile_test
TEST_LAW = lifecycle_law_test input_pipeline_law_test linear_layout_law_test \
	g10_layout_law_test g11_ctor_law_test \
	mutf8_string_pool_test resource_core_law_test resource_config_selection_test \
	s98_prefs_law_test s98_scroll_transform_law_test s98_text_law_test \
	s106_cia_law_test s106_gif_law_test \
	s106_layout_net_law_test s106_text2_law_test \
	encoded_value_law_test gp583_gles_law_test c9_bitmap_density_law_test \
	r25_dispatch_matrix_test gp583_img004_bounds_law_test \
	gp_dex003_fuzz_law_test \
	s225m_wave_law_test s231_view_resource_law_test \
	s234_w26_engine_laws_test s235_lane_laws_test
TEST_BATTERY = $(TEST_CORE) $(TEST_HOSTILE) $(TEST_LAW)

# S225-M wave law test links pthread_shadow.o (the interposition object the
# real binary links) so the POSIX-error-semantics laws (findings 6+7) run
# against the SHADOW registry, not raw glibc.
$(BUILDDIR)/tests/s225m_wave_law_test: $(TESTDIR)/s225m_wave_law_test.cpp \
		$(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) \
		$(BUILDDIR)/jni/pthread_shadow.o
	@mkdir -p $(BUILDDIR)/tests
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $< \
		$(filter-out $<,$^) $(LIBS) $(FONTS_LIBS)
TEST_TIMEOUT = 300

$(BUILDDIR)/tests/%: $(TESTDIR)/%.cpp $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT)
	@mkdir -p $(BUILDDIR)/tests
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $< \
		$(filter-out $<,$^) $(LIBS) $(FONTS_LIBS)

# Run one battery with per-test timeout + PASS/FAIL lines + exit status.
# Usage: make run-battery TESTS="a b c"
define RUN_BATTERY
failed=0; total=0; \
for t in $(1); do \
	exe="$(BUILDDIR)/tests/$$t"; \
	total=$$((total+1)); \
	if timeout $(TEST_TIMEOUT) ./"$$exe" > "$(BUILDDIR)/tests/$$t.log" 2>&1; then \
		echo "[PASS] $$t"; \
	else \
		rc=$$?; echo "[FAIL] $$t (rc=$$rc) — log: $(BUILDDIR)/tests/$$t.log"; failed=$$((failed+1)); \
	fi; \
done; \
echo "BATTERY SUMMARY: total=$$total passed=$$((total-failed)) failed=$$failed"; \
test $$failed -eq 0
endef

run-battery:
	@$(call RUN_BATTERY,$(TESTS))

test-core: $(addprefix $(BUILDDIR)/tests/,$(TEST_CORE))
	@$(call RUN_BATTERY,$(TEST_CORE))

test-hostile: $(addprefix $(BUILDDIR)/tests/,$(TEST_HOSTILE))
	@$(call RUN_BATTERY,$(TEST_HOSTILE))

test-law: $(addprefix $(BUILDDIR)/tests/,$(TEST_LAW))
	@$(call RUN_BATTERY,$(TEST_LAW))

# ONE main-runtime test-all entry point (GP583-TEST-001 wave-B requirement):
# source-parity + core + hostile + law, every suite with timeout + status.
test-all: check-source-parity $(addprefix $(BUILDDIR)/tests/,$(TEST_BATTERY))
	@$(call RUN_BATTERY,$(TEST_BATTERY))

# GP583-BUILD-002 companion: the manifest is the single source of truth, so
# parity = (a) every manifest entry exists on disk, (b) every src/**.cpp is
# classified: in the manifest, the main executable, or on the documented
# dormant/experimental whitelist (headers present but not linked — never
# silently dropped).
DORMANT_SOURCES = src/dex/api_dispatcher.cpp src/dex/exception_system.cpp \
	src/dex/execution_guard.cpp src/dex/execution_observatory.cpp \
	src/renderer/view_renderer.cpp src/resources/real_layout.cpp
check-source-parity:
	@status=0; \
	for f in $(CORE_SOURCES); do \
		[ -f "$$f" ] || { echo "[PARITY-FAIL] manifest entry missing: $$f"; status=1; }; \
	done; \
	for f in $$(ls src/*/*.cpp src/*.cpp 2>/dev/null | sort); do \
		case "$$f" in \
			src/main.cpp|src/exp007_012_megabatch_main.cpp|src/exp*) continue;; \
		esac; \
		if echo "$(CORE_SOURCES)" | tr ' ' '\n' | grep -qx "$$f"; then continue; fi; \
		if echo "$(DORMANT_SOURCES)" | tr ' ' '\n' | grep -qx "$$f"; then echo "[PARITY-DORMANT] $$f (documented dormant — not linked)"; continue; fi; \
		echo "[PARITY-FAIL] unclassified source (not in manifest, not exp-main, not dormant): $$f"; status=1; \
	done; \
	if [ $$status -eq 0 ]; then echo "[PARITY-OK] $(words $(CORE_SOURCES)) core sources manifest-parity"; fi; \
	exit $$status

test: $(TEST_EXECUTABLE)
	./$(TEST_EXECUTABLE)

# S202 repair — the registered BROKEN-LINK defect: the test link used
# CORE_OBJECTS alone while webview_engine.o references the QuickJS API and
# the runtime references the S-2 native thunk — the EXECUTABLE rule (line
# 102) always linked QUICKJS_OBJECTS + THUNK_OBJECT; the test rule must
# match or `make test` dies on undefined JS_*/thunk symbols.
$(TEST_EXECUTABLE): $(CORE_OBJECTS) $(QUICKJS_OBJECTS) $(THUNK_OBJECT) $(TEST_OBJECT)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $^ $(LIBS) $(FONTS_LIBS)
	@echo "Test build complete: $(TEST_EXECUTABLE)"

$(BUILDDIR)/test.o: $(TEST_SOURCE)
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

# Run with sample APK (if exists)
run: $(EXECUTABLE)
	./$(EXECUTABLE) run -v ./test_apks/HelloWorld.apk || echo "No sample APK available"

analyze: $(EXECUTABLE)
	./$(EXECUTABLE) analyze ./test_apks/HelloWorld.apk || echo "No sample APK available"

version: $(EXECUTABLE)
	./$(EXECUTABLE) version

# MEGA BATCH (EXP-007→EXP-012)
MEGABATCH_SOURCE = $(SRCDIR)/exp007_012_megabatch_main.cpp
MEGABATCH_OBJECT = $(BUILDDIR)/exp007_012_megabatch_main.o
MEGABATCH_EXECUTABLE = $(BUILDDIR)/miniandroid_megabatch

megabatch: $(MEGABATCH_EXECUTABLE)
	@echo "MEGA BATCH build complete: $(MEGABATCH_EXECUTABLE)"
	@echo "Usage: ./$(MEGABATCH_EXECUTABLE) <apk_path> [output_dir]"

$(MEGABATCH_EXECUTABLE): $(CORE_OBJECTS) $(MEGABATCH_OBJECT)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $^ $(LIBS) $(FONTS_LIBS)

$(BUILDDIR)/exp007_012_megabatch_main.o: $(MEGABATCH_SOURCE)
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

run-megabatch: $(MEGABATCH_EXECUTABLE)
	./$(MEGABATCH_EXECUTABLE) test_apks/HelloWorld.apk run

help:
	@echo "MiniAndroid Runtime v0.1 Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all     - Build the main executable"
	@echo "  test   - Build and run unit tests"
	@echo "  run     - Execute sample APK"
	@echo "  analyze     - Analyze sample APK"
	@echo "  version     - Show version info"
	@echo "  megabatch   - Build MEGA BATCH (EXP-007→EXP-012)"
	@echo "  run-megabatch - Run MEGA BATCH with HelloWorld APK"
	@echo "  clean       - Remove build artifacts"
	@echo ""
	@echo "Output directory: $(BUILDDIR)"

clean:
	rm -rf $(BUILDDIR)
	# UNIFIED_011 (28): never delete run/ - it contains TRACKED evidence
	# (exp096/exp097 BEFORE/AFTER proof). Only build/ is a build artifact.
	@echo "Cleaned build artifacts"

# Download nlohmann/json if not present
$(JSON_DIR)/include/nlohmann/json.hpp:
	@mkdir -p $(JSON_DIR)
	@echo "Downloading nlohmann/json..."
	curl -sL https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp -o $(JSON_DIR)/include/nlohmann/json.hpp || \
	wget -q https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp -O $(JSON_DIR)/include/nlohmann/json.hpp || \
	echo "Please download json.hpp manually to $(JSON_DIR)/include/nlohmann/"

# Ensure JSON is present before building
$(CORE_OBJECTS): $(JSON_DIR)/include/nlohmann/json.hpp
$(MAIN_OBJECT): $(JSON_DIR)/include/nlohmann/json.hpp
$(TEST_OBJECT): $(JSON_DIR)/include/nlohmann/json.hpp
$(MEGABATCH_OBJECT): $(JSON_DIR)/include/nlohmann/json.hpp

# EXP-093/F017: Header dependency tracking.
# -MMD -MP in CXXFLAGS generates .d files alongside each .o file.
# This line includes them so that header changes trigger correct recompilation.
# Without this, stale .o files can cause ABI/layout corruption and false crashes.
-include $(CORE_OBJECTS:.o=.d)
-include $(MAIN_OBJECT:.o=.d)
-include $(TEST_OBJECT:.o=.d)
-include $(MEGABATCH_OBJECT:.o=.d)

# GOLDEN-03 §12: reusable resource trace facility (resource -> chain -> value)
resource_trace:
	$(CXX) $(CXXFLAGS) -Wl,--no-keep-memory $(INCLUDES) $(JSON_INCLUDE) -o $(BUILDDIR)/resource_trace tools/resource_trace.cpp $(CORE_OBJECTS) $(THUNK_OBJECT) $(QUICKJS_OBJECTS) $(LIBS) $(FONTS_LIBS)

