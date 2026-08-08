# MiniAndroid Runtime v0.1 - Simple Makefile
# For systems without CMake

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -g -O0
INCLUDES = -Isrc -Isrc/apk -Isrc/dex -Isrc/runtime -Isrc/api -Isrc/graphics -Isrc/diagnostics
LIBS = -lz

# Directories
SRCDIR = src
BUILDDIR = build
TESTDIR = tests

# Source files (excluding main.cpp for library)
APK_SOURCES = $(SRCDIR)/apk/apk_parser.cpp $(SRCDIR)/apk/manifest_reader.cpp
DEX_SOURCES = $(SRCDIR)/dex/dex_parser.cpp
RUNTIME_SOURCES = $(SRCDIR)/runtime/execution_engine.cpp
DIAGNOSTICS_SOURCES = $(SRCDIR)/diagnostics/trace_engine.cpp

CORE_SOURCES = $(APK_SOURCES) $(DEX_SOURCES) $(RUNTIME_SOURCES) $(DIAGNOSTICS_SOURCES)
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
.PHONY: all clean test run help version

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
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(JSON_INCLUDE) -c -o $@ $<

# Run with sample APK (if exists)
run: $(EXECUTABLE)
	./$(EXECUTABLE) run -v ./tests/samples/HelloWorld.apk || echo "No sample APK available"

analyze: $(EXECUTABLE)
	./$(EXECUTITY) analyze ./tests/samples/HelloWorld.apk || echo "No sample APK available"

version: $(EXECUTABLE)
	./$(EXECUTABLE) version

help:
	@echo "MiniAndroid Runtime v0.1 Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all       - Build the main executable"
	@echo "  test      - Build and run unit tests"
	@echo "  run       - Execute sample APK"
	@echo "  analyze   - Analyze sample APK"
	@echo "  version   - Show version info"
	@echo "  clean     - Remove build artifacts"
	@echo ""
	@echo "Output directory: $(BUILDDIR)"

clean:
	rm -rf $(BUILDDIR)
	rm -rf run/
	echo "Cleaned build artifacts"

# Download nlohmann/json if not present
$(JSON_DIR)/include/nlohmann/json.hpp:
	@mkdir -p $(JSON_DIR)
	@echo "Downloading nlohmann/json..."
	curl -sL https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp -o $(JSON_DIR)/include/nlohmann/json.hpp || \
	wget -q https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp -O $(JSON_DIR)/include/nlohmann/json.html || \
	echo "Please download json.hpp manually to $(JSON_DIR)/include/nlohmann/"

# Ensure JSON is present before building
$(CORE_OBJECTS): $(JSON_DIR)/include/nlohmann/json.hpp
$(MAIN_OBJECT): $(JSON_DIR)/include/nlohmann/json.hpp
$(TEST_OBJECT): $(JSON_DIR)/include/nlohmann/json.hpp
