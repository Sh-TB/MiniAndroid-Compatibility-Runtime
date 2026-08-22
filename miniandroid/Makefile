# MiniAndroid Runtime v0.1 - Simple Makefile
# For systems without CMake

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -g -O2
INCLUDES = -Isrc -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics -Isrc/resources -Isrc/renderer -Isrc/framework -Isrc/storage -Ithird_party/nlohmann_json/include
LIBS = -lz

# Directories
SRCDIR = src
BUILDDIR = build
TESTDIR = tests

# Source files (excluding main.cpp for library)
APK_SOURCES = $(SRCDIR)/apk/apk_parser.cpp $(SRCDIR)/apk/manifest_reader.cpp
# Note: Use EITHER dex_interpreter.cpp OR dex_interpreter_batch.cpp, NOT BOTH
DEX_SOURCES = $(SRCDIR)/dex/dex_parser.cpp $(SRCDIR)/dex/class_resolver.cpp $(SRCDIR)/dex/dex_interpreter_batch.cpp $(SRCDIR)/dex/dalvik_engine.cpp $(SRCDIR)/dex/trace_exporter.cpp  # EXP-031.5: Trace exporter
RUNTIME_SOURCES = $(SRCDIR)/runtime/execution_engine.cpp $(SRCDIR)/runtime/application_runtime.cpp
DIAGNOSTICS_SOURCES = $(SRCDIR)/diagnostics/trace_engine.cpp
RESOURCES_SOURCES = $(SRCDIR)/resources/resource_parser.cpp
RENDERER_SOURCES = $(SRCDIR)/renderer/software_renderer.cpp
# EXP-084: framework and storage sources are required for linkage
FRAMEWORK_SOURCES = $(SRCDIR)/framework/android_shadows.cpp $(SRCDIR)/framework/shadow_registry.cpp
API_SOURCES = $(SRCDIR)/api/application_context.cpp $(SRCDIR)/api/shared_prefs.cpp
STORAGE_SOURCES = $(wildcard $(SRCDIR)/storage/*.cpp)

CORE_SOURCES = $(APK_SOURCES) $(DEX_SOURCES) $(RUNTIME_SOURCES) $(DIAGNOSTICS_SOURCES) $(RESOURCES_SOURCES) $(RENDERER_SOURCES) $(FRAMEWORK_SOURCES) $(API_SOURCES) $(STORAGE_SOURCES)
CORE_OBJECTS = $(patsubst $(SRCDIR)/%.cpp,$(BUILDDIR)/%.o,$(CORE_SOURCES))

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

# Default target
.PHONY: all clean test run help version megabatch run-megabatch

all: $(EXECUTABLE)

$(EXECUTABLE): $(CORE_OBJECTS) $(MAIN_OBJECT)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $^ $(LIBS)
	@echo "Build complete: $(EXECUTABLE)"

$(BUILDDIR)/%.o: $(SRCDIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

$(BUILDDIR)/main.o: $(MAIN_SOURCE)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

# Tests
test: $(TEST_EXECUTABLE)
	./$(TEST_EXECUTABLE)

$(TEST_EXECUTABLE): $(CORE_OBJECTS) $(TEST_OBJECT)
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $^ $(LIBS)
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
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -o $@ $^ $(LIBS)

$(BUILDDIR)/exp007_012_megabatch_main.o: $(MEGABATCH_SOURCE)
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

run-megabatch: $(MEGABATCH_EXECUTABLE)
	./$(MEGABATCH_EXECUTABLE) test_apks/HelloWorld.apk run

help:
	@echo "MiniAndroid Runtime v0.1 Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all         - Build the main executable"
	@echo "  test        - Build and run unit tests"
	@echo "  run         - Execute sample APK"
	@echo "  analyze     - Analyze sample APK"
	@echo "  version     - Show version info"
	@echo "  megabatch   - Build MEGA BATCH (EXP-007→EXP-012)"
	@echo "  run-megabatch - Run MEGA BATCH with HelloWorld APK"
	@echo "  clean       - Remove build artifacts"
	@echo ""
	@echo "Output directory: $(BUILDDIR)"

clean:
	rm -rf $(BUILDDIR)
	rm -rf run/
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
