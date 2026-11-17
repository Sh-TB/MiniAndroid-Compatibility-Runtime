# MiniAndroid Runtime v0.1 - CMake Build Configuration
# EXP-001: HelloWorld Loader
# EXP-002: Runtime Stub (Class Resolution)

# ============== Build recipes (issue #612 P0) ==============
#   runtime only (the default `all`):   cmake --build .            # = miniandroid + core lib
#   runtime binary alone:               cmake --build . --target miniandroid
#   the full test battery (opt-in):     cmake -DBUILD_TESTS=ON .. && cmake --build .
#   one law test binary:                cmake --build . --target s247_grid_rtl_law_test
#   experiments (opt-in, never `all`):  cmake --build . --target miniandroid_exp005
# Default `all` builds ONLY the distributable runtime (miniandroid + core
# lib); EXP-00x/batch/megabatch executables are EXCLUDE_FROM_ALL, and the
# test battery is behind -DBUILD_TESTS=ON — a normal runtime build compiles
# no experiments and no tests.
cmake_minimum_required(VERSION 3.16)
# #612-A1: the jni compat shims are C (bionic_compat.c, pthread_shadow.c)
# and the thunk is ASM — all three languages are declared up front so the
# shims compile as normal target sources, never as hand-built .o files.
project(MiniAndroid VERSION 0.1 LANGUAGES C CXX ASM DESCRIPTION "Minimal Android Compatibility Runtime")

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O2")

# Find required packages
find_package(ZLIB REQUIRED)

# Optional: Vulkan (for future GPU rendering)
option(USE_VULKAN "Enable Vulkan backend" OFF)
# GP583-BUILD-003 fix: the option is spelled USE_VULKAN; the branches below
# tested USE_VULCAN (missing K), so -DUSE_VULKAN=ON configured fine but the
# discovery/link/summary branches never fired (empty Vulkan row in the
# summary). One spelling everywhere.
if(USE_VULKAN)
    find_package(Vulkan)
    if(Vulkan_FOUND)
        message(STATUS "Vulkan found, enabling GPU backend")
        add_definitions(-DUSE_VULKAN)
    else()
        message(WARNING "Vulkan requested but not found, using software renderer")
    endif()
endif()

# nlohmann/json - use FetchContent if not installed
option(USE_SYSTEM_JSON "Use system-installed nlohmann/json" OFF)

if(USE_SYSTEM_JSON)
    find_package(nlohmann_json CONFIG)
else()
    include(FetchContent)
    FetchContent_Declare(
        json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.3
    )
    
    # cmake-4.x compat (BUILD-TRAIN): legacy FetchContent_Populate lowercase
    # vars are gone in CMake >= 4.4 — prefer the vendored third_party tree,
    # fall back to FetchContent only when the vendored copy is absent.
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/nlohmann_json/CMakeLists.txt)
        add_subdirectory(third_party/nlohmann_json EXCLUDE_FROM_ALL)
    elseif(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/nlohmann_json/include/nlohmann/json.hpp)
        message(STATUS "nlohmann/json: vendored single-header (cmake-4.x compat path)")
        add_library(nlohmann_json INTERFACE)
        target_include_directories(nlohmann_json INTERFACE
            ${CMAKE_CURRENT_SOURCE_DIR}/third_party/nlohmann_json/include)
        add_library(nlohmann_json::nlohmann_json ALIAS nlohmann_json)
    else()
        FetchContent_GetProperties(json)
        IF(NOT json_POPULATED)
            FetchContent_Populate(json)
            add_subdirectory(${json_source_dir} ${json_binary_dir} EXCLUDE_FROM_ALL)
        ENDIF()
    endif()
endif()

# ============== Core Library ==============
# GP583-BUILD-002 fix: the source list now comes from the SAME manifest the
# Makefile consumes (miniandroid/core_sources.manifest, 74 TUs). The old
# hand-maintained CMake list carried only 12 translation units while the
# Makefile linked 74 — two build commands produced materially different
# runtime capability (dalvik_engine, shadows, JNI loader/bridge, ARSC/
# string-pool/layout-inflater, GLES backend, HTTP/storage/audio/font,
# QuickJS WebView were all absent from the CMake runtime).
file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/core_sources.manifest" MINIANDROID_CORE_SOURCES
    REGEX "^[^#].*\\.cpp$")
# ISSUE-612 WAVE-4: DALVIK_SPLIT mirror of the Makefile switch (default ON).
# OFF (-DDALVIK_SPLIT=0) restores the original dalvik_engine.cpp monolith and
# excludes the five split part TUs; ON excludes the monolith (kept in the
# repo as the documented fallback).
option(DALVIK_SPLIT "Build the split dalvik engine TUs instead of the monolith" ON)
set(MINIANDROID_SPLIT_PARTS
    src/dex/dalvik_engine_core.cpp
    src/dex/dalvik_engine_invoke.cpp
    src/dex/dalvik_opcodes.cpp
    src/dex/dalvik_bridge.cpp
    src/dex/dalvik_engine_tail.cpp)
if(DALVIK_SPLIT)
    list(REMOVE_ITEM MINIANDROID_CORE_SOURCES "src/dex/dalvik_engine.cpp")
else()
    list(REMOVE_ITEM MINIANDROID_CORE_SOURCES ${MINIANDROID_SPLIT_PARTS})
    list(APPEND MINIANDROID_CORE_SOURCES "src/dex/dalvik_engine.cpp")
endif()
list(LENGTH MINIANDROID_CORE_SOURCES MINIANDROID_CORE_SOURCE_COUNT)
message(STATUS "miniandroid_core: ${MINIANDROID_CORE_SOURCE_COUNT} TUs from core_sources.manifest (shared with Makefile)")
add_library(miniandroid_core STATIC ${MINIANDROID_CORE_SOURCES})

target_include_directories(miniandroid_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/src/apk
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dex
    ${CMAKE_CURRENT_SOURCE_DIR}/src/runtime
    ${CMAKE_CURRENT_SOURCE_DIR}/src/api
    ${CMAKE_CURRENT_SOURCE_DIR}/src/graphics
    ${CMAKE_CURRENT_SOURCE_DIR}/src/diagnostics
    ${CMAKE_CURRENT_SOURCE_DIR}/src/resources
    ${CMAKE_CURRENT_SOURCE_DIR}/src/renderer
    ${CMAKE_CURRENT_SOURCE_DIR}/src/framework
    ${CMAKE_CURRENT_SOURCE_DIR}/src/storage
    ${CMAKE_CURRENT_SOURCE_DIR}/src/fonts
    ${CMAKE_CURRENT_SOURCE_DIR}/src/gles
    ${CMAKE_CURRENT_SOURCE_DIR}/src/jni
    ${CMAKE_CURRENT_SOURCE_DIR}/src/audio
    ${CMAKE_CURRENT_SOURCE_DIR}/src/webview
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/portablegl
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/nlohmann_json/include
    /usr/include/freetype2
)

target_link_libraries(miniandroid_core PUBLIC
    ZLIB::ZLIB
)

# BUILD-TRAIN: software_renderer consumes libpng/libjpeg directly (undefined
# png_error/jpeg_std_error at link) — system libs are present in the container.
find_library(PNG_LIB NAMES png)
find_library(JPEG_LIB NAMES jpeg)
if(PNG_LIB)
    target_link_libraries(miniandroid_core PUBLIC ${PNG_LIB})
endif()
if(JPEG_LIB)
    target_link_libraries(miniandroid_core PUBLIC ${JPEG_LIB})
endif()
# BUILD-TRAIN: crypto (EVP sha256) + sqlite3 consumers — same direct-consumption law
foreach(_syslib crypto sqlite3)
    find_library(_FOUND_${_syslib} NAMES ${_syslib})
    if(_FOUND_${_syslib})
        target_link_libraries(miniandroid_core PUBLIC ${_FOUND_${_syslib}})
    endif()
endforeach()

# GP583-BUILD-002: the Makefile runtime links the FULL library set; the CMake
# runtime must consume the same capability surface or the two build commands
# still diverge. Every entry is optional-found (silent skip when absent) so
# minimal hosts keep configuring; the summary prints what actually resolved.
foreach(_syslib jpeg sndfile mpg123 ssl webp webpdemux freetype harfbuzz fribidi)
    find_library(_FOUND_${_syslib} NAMES ${_syslib})
    if(_FOUND_${_syslib})
        target_link_libraries(miniandroid_core PUBLIC ${_FOUND_${_syslib}})
    endif()
endforeach()
find_package(Threads REQUIRED)
target_link_libraries(miniandroid_core PUBLIC Threads::Threads)

if(TARGET nlohmann_json::nlohmann_json)
    # BUILD-TRAIN fix: stray "()" typo became "-l(" "-l)" link items
    target_link_libraries(miniandroid_core PUBLIC nlohmann_json::nlohmann_json)
elseif(json_SOURCE_DIR)
    target_link_libraries(miniandroid_core PUBLIC nlohmann_json::nlohmann_json)
else()
    message(FATAL_ERROR "nlohmann/json library not found")
endif()

if(USE_VULKAN AND Vulkan_FOUND)
    target_link_libraries(miniandroid_core PUBLIC Vulkan::Vulkan)
endif()

# Platform-specific settings
# #612-C: mirror the Makefile's source-specific debug-info exception —
# dalvik_engine.cpp (~5.0 MiB) and android_shadows.cpp (~646 KiB) blow the
# compiler's memory budget when debug info is generated (documented Makefile
# -g0 override). -g0 is appended LAST so it overrides any config -g
# (Debug/RelWithDebInfo), matching the Makefile semantics in every config.
set(MINIANDROID_BIG_TUS
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dex/dalvik_engine.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dex/dalvik_engine_core.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dex/dalvik_engine_invoke.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dex/dalvik_opcodes.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dex/dalvik_bridge.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dex/dalvik_engine_tail.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/framework/android_shadows.cpp
)
set_source_files_properties(${MINIANDROID_BIG_TUS} PROPERTIES
    COMPILE_OPTIONS "-g0")

if(APPLE)
    target_compile_options(miniandroid_core PRIVATE -Wno-everything)
elseif(UNIX)
    # Linux-specific
endif()

# ============== Main Executable (EXP-001) ==============
add_executable(miniandroid
    src/main.cpp
)

target_link_libraries(miniandroid PRIVATE miniandroid_core)

# GP583-BUILD-002 + #612-A1/A2: the executable-side native sources the
# Makefile links (S-2 thunk assembly + bionic C compat shims) are declared
# as NORMAL target sources — CMake compiles them into the build tree with
# declared dependencies. The old PRE_LINK design compiled
# src/jni/*.o INTO THE SOURCE TREE and linked files that did not exist at
# configure time (Ninja: "missing and no known rule to make it") — that
# was a broken generated-file dependency, not compiler slowness.
target_sources(miniandroid PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/jni/native_thunk.S
    ${CMAKE_CURRENT_SOURCE_DIR}/src/jni/bionic_compat.c
    ${CMAKE_CURRENT_SOURCE_DIR}/src/jni/pthread_shadow.c
    # #612-A5: the QuickJS WebView engine's C runtime — the Makefile links
    # QUICKJS_OBJECTS (5 third_party C files); the manifest-parity wave
    # (GP583-BUILD-002) covered only the .cpp core, so the CMake runtime
    # linked with undefined JS_* references (webview_engine.cpp). Same
    # sources, same role, now as normal target sources (C language enabled
    # up front).
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/quickjs.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/libregexp.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/libunicode.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/cutils.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/libbf.c
)
# #612-A5: the Makefile builds QuickJS with its own QUIET C dialect
# (QUICKJS_CFLAGS: gnu11, _GNU_SOURCE, CONFIG_VERSION, CONFIG_BIGNUM, -w).
# C++17 flags + missing CONFIG_VERSION broke the build inside quickjs.c
# (expected ')' before CONFIG). Same flags, same dialect, per source.
set(MINIANDROID_QUICKJS_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/quickjs.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/libregexp.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/libunicode.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/cutils.c
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs/libbf.c
)
set_source_files_properties(${MINIANDROID_QUICKJS_SOURCES} PROPERTIES
    LANGUAGE C
    C_STANDARD 11
    C_EXTENSIONS ON
    COMPILE_OPTIONS "-w;-D_GNU_SOURCE;-DCONFIG_VERSION=\"2024-01-13\";-DCONFIG_BIGNUM;-I${CMAKE_CURRENT_SOURCE_DIR}/third_party/quickjs")
set_source_files_properties(${CMAKE_CURRENT_SOURCE_DIR}/src/jni/native_thunk.S
    PROPERTIES LANGUAGE ASM)

# ============== EXP-002 Executable (Class Resolution) ==============
add_executable(miniandroid_exp002 EXCLUDE_FROM_ALL
    src/exp002_main.cpp
)

target_link_libraries(miniandroid_exp002 PRIVATE miniandroid_core)

# ============== EXP-003-A Executable (const-string Opcode) ==============
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/src/exp003a_main.cpp)  # BUILD-TRAIN: dead-target guard (cleanup waves removed sources; cmake-4.x generate fails otherwise)
add_executable(miniandroid_exp003a EXCLUDE_FROM_ALL
    src/exp003a_main.cpp
    src/dex/dex_interpreter.cpp
)

target_link_libraries(miniandroid_exp003a PRIVATE miniandroid_core)
endif()

# ============== EXP-003-A.1 Validator (Const-String Validation) ==============
add_executable(miniandroid_exp003a1_validate EXCLUDE_FROM_ALL
    src/exp003a1_validate.cpp
)

target_link_libraries(miniandroid_exp003a1_validate PRIVATE miniandroid_core)

# ============== EXP-003-BATCH (Minimal DEX Execution Engine) ==============
add_executable(miniandroid_batch EXCLUDE_FROM_ALL
    src/exp003batch_main.cpp
    src/dex/dex_interpreter_batch.cpp
)

target_link_libraries(miniandroid_batch PRIVATE miniandroid_core)

# ============== EXP-004 (Android Object Model Foundation) ==============
add_executable(miniandroid_exp004 EXCLUDE_FROM_ALL
    src/exp004_main.cpp
    src/dex/dex_interpreter_batch.cpp
)

target_link_libraries(miniandroid_exp004 PRIVATE miniandroid_core)

# ============== EXP-005 (Minimal Software Rendering Pipeline) ==============
add_executable(miniandroid_exp005 EXCLUDE_FROM_ALL
    src/exp005_main.cpp
    src/renderer/software_renderer.cpp
    src/renderer/vector_decode.cpp
)

target_link_libraries(miniandroid_exp005 PRIVATE miniandroid_core)

# ============== EXP-006 (Android Resource and Layout Foundation) ==============
add_executable(miniandroid_exp006 EXCLUDE_FROM_ALL
    src/exp006_main.cpp
)

target_link_libraries(miniandroid_exp006 PRIVATE miniandroid_core)

# ============== EXP-007→EXP-012 MEGA BATCH (Unified Runtime Integration) ==============
add_executable(miniandroid_megabatch EXCLUDE_FROM_ALL
    src/exp007_012_megabatch_main.cpp
    src/runtime/application_runtime.cpp
)

target_link_libraries(miniandroid_megabatch PRIVATE miniandroid_core)

# Install targets
install(TARGETS miniandroid
    RUNTIME DESTINATION bin
)

install(TARGETS miniandroid_core
    ARCHIVE DESTINATION lib
)

install(DIRECTORY src/
    DESTINATION include/miniandroid
    FILES_MATCHING PATTERN "*.h"
)

# ============== Test Target (Optional) ==============
# #612-B3: tests are available and registered, but a normal runtime build
# must not compile the full battery — opt in with -DBUILD_TESTS=ON.
option(BUILD_TESTS "Build unit tests" OFF)

if(BUILD_TESTS)
    enable_testing()

    # Try to find Google Test
    find_package(GTest QUIET)

    # GP583-TEST-002 fix: the GoogleTest branch created `miniandroid_test`
    # ONLY when tests/main.cpp exists but then called
    # gtest_discover_tests(miniandroid_test) UNCONDITIONALLY — with main.cpp
    # absent (the audited tree) CMake configure died at
    # "get_property could not find TARGET miniandroid_test". Target
    # existence is now the outer condition for discovery.
    # GP583-TEST-001 fix (CMake face): the no-GTest fallback created the
    # simple_test executable without any add_test registration — ctest -N
    # reported Total Tests: 0 and a green ctest coexisted with zero executed
    # tests. Every branch now registers at least one real test.
    if(GTest_FOUND OR TARGET GTest::gtest)
        if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/tests/main.cpp)
            add_executable(miniandroid_test EXCLUDE_FROM_ALL
                tests/main.cpp
            )
            target_link_libraries(miniandroid_test PRIVATE
                miniandroid_core
                GTest::gtest_main
            )
            include(GoogleTest)
            gtest_discover_tests(miniandroid_test)
            message(STATUS "Tests enabled (GoogleTest discovered)")
        else()
            # GTest present but the maintained GTest main.cpp is not —
            # fall through to the simple-test executable (created below) and
            # register it; never discover tests from a nonexistent target.
            message(STATUS "GoogleTest found but tests/main.cpp absent — simple-test fallback (registered)")
        endif()
    endif()

    if(NOT TARGET miniandroid_test)
        # Create a simple test executable without GTest
        add_executable(miniandroid_test EXCLUDE_FROM_ALL
            tests/simple_test.cpp
        )

        target_link_libraries(miniandroid_test PRIVATE miniandroid_core)
        add_test(NAME miniandroid-smoke COMMAND miniandroid_test)
        set_tests_properties(miniandroid-smoke PROPERTIES TIMEOUT 300)
        if(NOT (GTest_FOUND OR TARGET GTest::gtest))
            message(STATUS "Google Test not found — simple-test fallback registered with CTest (miniandroid-smoke)")
        endif()
    endif()
endif()

# ============== Custom Commands ==============

# Version info command
add_custom_target(version
    COMMAND ${CMAKE_BINARY_DIR}/miniandroid version
    DEPENDS miniandroid
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    COMMENT "Show MiniAndroid version"
)

# Analysis command example
add_custom_target(analyze-example
    COMMAND ${CMAKE_BINARY_DIR}/miniandroid analyze ${CMAKE_SOURCE_DIR}/tests/samples/HelloWorld.apk || echo "No sample APK found"
    DEPENDS miniandroid
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    COMMENT "Analyze sample HelloWorld.apk"
)

# ============== EXP-018 Executable (Real Android Execution Core Batch) ==============
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/src/exp018_main.cpp)  # BUILD-TRAIN: dead-target guard (cleanup waves removed sources; cmake-4.x generate fails otherwise)
add_executable(miniandroid_exp018
    src/exp018_main.cpp
    src/dex/dex_interpreter_exp018.cpp
    src/runtime/application_runtime.cpp
)

target_link_libraries(miniandroid_exp018 PRIVATE miniandroid_core)
endif()

# ============== EXP-019 Executable (Android Application Runtime Integration) ==============
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/src/exp019_main.cpp)  # BUILD-TRAIN: dead-target guard (cleanup waves removed sources; cmake-4.x generate fails otherwise)
add_executable(miniandroid_exp019
    src/exp019_main.cpp
    src/runtime/runtime_integration_exp019.cpp
    src/dex/dex_interpreter_exp018.cpp
    src/runtime/application_runtime.cpp
)

target_link_libraries(miniandroid_exp019 PRIVATE miniandroid_core)
endif()

# ============== EXP-088 Phase A4 PNG Decoder Test ==============
# Standalone test that decodes known-PNG reproducer files with MiniAndroid's
# own PNGDecoder and compares the result against an independently-PIL-verified
# expected RGBA buffer. See scripts/a4_01_create_known_png.py.
add_executable(exp088_a4_png_decoder_test
    tests/exp088_a4_png_decoder_test.cpp
)
target_link_libraries(exp088_a4_png_decoder_test PRIVATE miniandroid_core)

# ============== Summary ==============
message(STATUS "")
message(STATUS "========== MiniAndroid Build Configuration ==========")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(Status "Install Prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "Vulkan: ${USE_VULKAN}")
message(STATUS "Tests: ${BUILD_TESTS}")
message(STATUS "=====================================================")
message(STATUS "")

# Print build instructions
message(STATUS "Build commands:")
message(STATUS "  cmake --build . --config Release")
message(STATUS "")
message(STATUS "Usage:")
message(STATUS "  ./miniandroid analyze <apk_path>     (EXP-001)")
message(STATUS "  ./miniandroid dex <apk_path>         (EXP-001)")
message(STATUS "  ./miniandroid run <apk_path>         (Future)")
message(STATUS "  ./miniandroid version               (EXP-001)")
message(STATUS "")
message(STATUS "EXP-002 (Class Resolution):")
message(STATUS "  ./miniandroid_exp002 [apk_path]     (Default: test_apks/HelloWorld.apk)")
