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
    
    # Check if already available
    FetchContent_GetProperties(json)
    IF(NOT json_POPULATED)
        FetchContent_Populate(json)
        add_subdirectory(${json_source_dir} ${json_binary_dir} EXCLUDE_FROM_ALL)
    ENDIF()
endif()

# ============== Core Library ==============
add_library(miniandroid_core STATIC
    # APK Parser
    src/apk/apk_parser.cpp
    src/apk/manifest_reader.cpp
    
    # DEX Parser
    src/dex/dex_parser.cpp
    src/dex/class_resolver.cpp
    
    # Runtime
    src/runtime/execution_engine.cpp
    
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
)

target_link_libraries(miniandroid_core PUBLIC
    ZLIB::ZLIB
)

if(TARGET nlohmann_json::nlohmann_json)
    target_link_libraries(miniandroid_core PUBLIC nlohmann_json::nlohmann_json())
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
add_executable(miniandroid_exp003a
    src/exp003a_main.cpp
    src/dex/dex_interpreter.cpp
)

target_link_libraries(miniandroid_exp003a PRIVATE miniandroid_core)

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
)

target_link_libraries(miniandroid_exp005 PRIVATE miniandroid_core)

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
        add_executable(miniandroid_test
            tests/main.cpp
        )
        
        target_link_libraries(miniandroid_test PRIVATE 
            miniandroid_core
            GTest::gtest_main
        )
        
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
