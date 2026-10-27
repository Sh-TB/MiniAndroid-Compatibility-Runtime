# MiniAndroid Runtime v0.1 - CMake Build Configuration
# EXP-001: HelloWorld Loader
# EXP-002: Runtime Stub (Class Resolution)

cmake_minimum_required(VERSION 3.16)
project(MiniAndroid VERSION 0.1 LANGUAGES CXX DESCRIPTION "Minimal Android Compatibility Runtime")

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
if(USE_VULCAN)
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
add_library(miniandroid_core STATIC
    # APK Parser
    src/apk/apk_parser.cpp
    src/apk/manifest_reader.cpp
    
    # DEX Parser
    src/dex/dex_parser.cpp
    src/dex/class_resolver.cpp
    src/dex/dex_interpreter_batch.cpp
    
    # Runtime
    src/runtime/execution_engine.cpp
    
    # Resources (EXP-006)
    src/resources/resource_parser.cpp
    
    # Renderer (EXP-005)
    src/renderer/software_renderer.cpp
    src/renderer/vector_decode.cpp
    
    # API Stubs
    # (header-only, no separate .cpp needed for now)
    
    # Diagnostics
    src/diagnostics/trace_engine.cpp
)

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

if(TARGET nlohmann_json::nlohmann_json)
    # BUILD-TRAIN fix: stray "()" typo became "-l(" "-l)" link items
    target_link_libraries(miniandroid_core PUBLIC nlohmann_json::nlohmann_json)
elseif(json_SOURCE_DIR)
    target_link_libraries(miniandroid_core PUBLIC nlohmann_json::nlohmann_json)
else()
    message(FATAL_ERROR "nlohmann/json library not found")
endif()

if(USE_VULCAN AND Vulkan_FOUND)
    target_link_libraries(miniandroid_core PUBLIC Vulkan::Vulkan)
endif()

# Platform-specific settings
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

# ============== EXP-002 Executable (Class Resolution) ==============
add_executable(miniandroid_exp002
    src/exp002_main.cpp
)

target_link_libraries(miniandroid_exp002 PRIVATE miniandroid_core)

# ============== EXP-003-A Executable (const-string Opcode) ==============
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/src/exp003a_main.cpp)  # BUILD-TRAIN: dead-target guard (cleanup waves removed sources; cmake-4.x generate fails otherwise)
add_executable(miniandroid_exp003a
    src/exp003a_main.cpp
    src/dex/dex_interpreter.cpp
)

target_link_libraries(miniandroid_exp003a PRIVATE miniandroid_core)
endif()

# ============== EXP-003-A.1 Validator (Const-String Validation) ==============
add_executable(miniandroid_exp003a1_validate
    src/exp003a1_validate.cpp
)

target_link_libraries(miniandroid_exp003a1_validate PRIVATE miniandroid_core)

# ============== EXP-003-BATCH (Minimal DEX Execution Engine) ==============
add_executable(miniandroid_batch
    src/exp003batch_main.cpp
    src/dex/dex_interpreter_batch.cpp
)

target_link_libraries(miniandroid_batch PRIVATE miniandroid_core)

# ============== EXP-004 (Android Object Model Foundation) ==============
add_executable(miniandroid_exp004
    src/exp004_main.cpp
    src/dex/dex_interpreter_batch.cpp
)

target_link_libraries(miniandroid_exp004 PRIVATE miniandroid_core)

# ============== EXP-005 (Minimal Software Rendering Pipeline) ==============
add_executable(miniandroid_exp005
    src/exp005_main.cpp
    src/renderer/software_renderer.cpp
    src/renderer/vector_decode.cpp
)

target_link_libraries(miniandroid_exp005 PRIVATE miniandroid_core)

# ============== EXP-006 (Android Resource and Layout Foundation) ==============
add_executable(miniandroid_exp006
    src/exp006_main.cpp
)

target_link_libraries(miniandroid_exp006 PRIVATE miniandroid_core)

# ============== EXP-007→EXP-012 MEGA BATCH (Unified Runtime Integration) ==============
add_executable(miniandroid_megabatch
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
option(BUILD_TESTS "Build unit tests" ON)

if(BUILD_TESTS)
    enable_testing()
    
    # Try to find Google Test
    find_package(GTest QUIET)
    
    if(GTest_FOUND OR TARGET GTest::gtest)
        if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/tests/main.cpp)  # BUILD-TRAIN: dead-target guard (cleanup waves removed sources; cmake-4.x generate fails otherwise)
add_executable(miniandroid_test
            tests/main.cpp
        )
        
        target_link_libraries(miniandroid_test PRIVATE 
            miniandroid_core
            GTest::gtest_main
        )
endif()
        
        include(GoogleTest)
        gtest_discover_tests(miniandroid_test)
        
        message(STATUS "Tests enabled")
    else()
        message(STATUS "Google Test not found, disabling tests")
        
        # Create a simple test executable without GTest
        add_executable(miniandroid_test
            tests/simple_test.cpp
        )
        
        target_link_libraries(miniandroid_test PRIVATE miniandroid_core)
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
message(STATUS "Vulkan: ${USE_VULCAN}")
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
