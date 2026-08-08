# MiniAndroid Runtime v0.1 — Architecture Document

## Project Overview

**Experiment:** EXP-001 MiniAndroid HelloWorld Loader  
**Goal:** Execute a minimal Android APK without full emulator  
**Philosophy:** Evidence-driven development, minimal implementation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MiniAndroid Runtime v0.1                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐  │
│  │   APK    │───▶│   DEX    │───▶│     Execution Engine      │  │
│  │  Parser  │    │  Parser  │    │                          │  │
│  └──────────┘    └──────────┘    └────────────┬─────────────┘  │
│       │               │                     │                │
│       ▼               ▼                     ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐  │
│  │Manifest  │    │ Classes/ │    │   Android API Stubs      │  │
│  │ Reader   │    │ Methods  │    │   (Activity, View, etc)  │  │
│  └──────────┘    └──────────┘    └────────────┬─────────────┘  │
│                                              │                │
│                                              ▼                │
│                                   ┌──────────────────────────┐  │
│                                   │    Graphics Backend      │  │
│                                   │    (Vulkan/Software)     │  │
│                                   └────────────┬─────────────┘  │
│                                                │                │
│                                                ▼                │
│                                   ┌──────────────────────────┐  │
│                                   │    Diagnostics Engine    │  │
│                                   │    (Trace, Log, Report)  │  │
│                                   └──────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. APK Parser (`src/apk/`)

**Responsibility:** Parse Android Package (APK) files

**Input:** `.apk` file (ZIP format)  
**Output:** Structured package information

**Components:**
- `apk_parser.cpp/h` — Main ZIP extraction and parsing
- `manifest_reader.cpp/h` — AndroidManifest.xml decoder

**Supported Operations:**
```
- Extract ZIP contents
- Parse binary XML (AndroidManifest)
- Identify main Activity
- List permissions
- Extract resources
- Validate APK integrity
```

**Evidence Output:**
```json
{
  "apk_name": "HelloWorld.apk",
  "package_name": "com.miniandroid.helloworld",
  "version_name": "0.1",
  "version_code": 1,
  "main_activity": "com.miniandroid.helloworld.MainActivity",
  "permissions": [],
  "native_libraries": [],
  "dex_files": ["classes.dex"]
}
```

---

### 2. DEX Parser (`src/dex/`)

**Responsibility:** Parse Dalvik Executable format

**Input:** `classes.dex` from APK  
**Output:** Class/method metadata

**DEX Format Structure:**
```
DEX File Header:
├── magic: "dex\n035\0"
├── checksum
├── signature (SHA-1)
├── file_size
├── header_size (0x70)
├── endian_tag
├── string_ids_size/offset
├── type_ids_size/offset
├── proto_ids_size/offset
├── field_ids_size/offset
├── method_ids_size/offset
├── class_defs_size/offset
├── data_size/offset
```

**Components:**
- `dex_parser.cpp/h` — Full DEX format parser
- `metadata_reader.cpp/h` — Extract class/method info

**Evidence Output:**
```json
{
  "dex_version": "035",
  "classes_count": 3,
  "methods_count": 12,
  "classes": [
    {
      "name": "Lcom/miniandroid/helloworld/MainActivity;",
      "superclass": "Landroid/app/Activity;",
      "methods": [
        {"name": "<init>", "descriptor": "()V"},
        {"name": "onCreate", "descriptor": "(Landroid/os/Bundle;)V"}
      ]
    }
  ]
}
```

---

### 3. Execution Engine (`src/runtime/`)

**Responsibility:** Execute DEX bytecode with minimal VM

**Components:**
- `execution_engine.cpp/h` — Main runtime loop
- `interpreter.cpp/h` — Bytecode interpreter (minimal)
- `class_loader.cpp/h` — Class loading and linking

**Implementation Strategy (v0.1):**
```
Phase 1: Static analysis only (no execution)
Phase 2: Interpret onCreate() lifecycle
Phase 3: Full method interpretation
```

**Lifecycle Simulation:**
```
APK Loaded
    ↓
Class Loaded
    ↓
Activity.onCreate() called
    ↓
setContentView() processed
    ↓
View hierarchy built
    ↓
onStart() → onResume()
    ↓
draw() called
    ↓
Framebuffer generated
```

---

### 4. Android API Stubs (`src/api/`)

**Responsibility:** Provide minimal Android framework implementations

**Implemented Stubs (M3 Target):**

| Class | Methods | Status |
|-------|---------|--------|
| `android.app.Activity` | onCreate, onStart, onResume, setContentView, findViewById | PLANNED |
| `android.os.Bundle` | getString, getInt, putString, putInt | PLANNED |
| `android.view.View` | draw, measure, layout, invalidate | PLANNED |
| `android.view.ViewGroup` | addView, removeView | PLANNED |
| `android.widget.TextView` | setText, getText, setTextColor | PLANNED |
| `android.graphics.Canvas` | drawText, drawRect, drawColor | PLANNED |
| `android.graphics.Paint` | setColor, setTextSize, setAntiAlias | PLANNED |
| android.content.Context | getResources, getPackageManager | PLANNED |

**Tracing Behavior:**
Every API call generates a trace entry:
```json
{
  "timestamp": 1001,
  "thread": "main",
  "class": "android.app.Activity",
  "method": "onCreate",
  "args": ["bundle:non-null"],
  "return_value": "void",
  "call_depth": 1
}
```

---

### 5. Graphics Backend (`src/graphics/`)

**Responsibility:** Render Android View hierarchy to image

**Architecture:**
```
Android View Hierarchy
        ↓
MiniAndroid Renderer (Custom)
        ↓
Software Rasterizer (v0.1)
        ↓
Framebuffer (RGBA buffer)
        ↓
PNG Encoder
        ↓
screenshot.png
```

**Vulkan Backend (Future):**
```
View Hierarchy → Vulkan Command Buffer → GPU → Screenshot
```

**v0.1 Implementation:**
- Software rendering only
- Basic text rendering (bitmap fonts)
- Rectangle/Color fill
- PNG output via stb_image_write or libpng

---

### 6. Diagnostics Engine (`src/diagnostics/`)

**Responsibility:** Trace, log, and report everything

**Output Structure:**
```
run/
├── apk_info.json          # Parsed APK information
├── dex_report.json        # DEX analysis results
├── api_trace.json         # All API calls during execution
├── crash.log              # Error/crash information
├── screenshot.png         # Final rendered output
└── report.md              # Human-readable summary
```

**Report Template:**
```markdown
# MiniAndroid Execution Report

## Application
- **APK:** HelloWorld.apk
- **Package:** com.miniandroid.helloworld
- **Main Activity:** MainActivity

## Execution Status: SUCCESS / FAILURE

## Metrics
- APIs Called: 37
- Frames Rendered: 1
- Execution Time: 45ms
- Memory Peak: 2.4MB

## API Trace Summary
| Class | Method | Calls |
|-------|--------|-------|
| Activity | onCreate | 1 |
| TextView | setText | 1 |

## Errors/Warnings
[None or list of issues]

## Screenshot
![Screenshot](screenshot.png)
```

---

## Build System

### CMake Configuration

```cmake
cmake_minimum_required(VERSION 3.16)
project(MiniAndroid VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Core library
add_library(miniandroid_core STATIC
    src/apk/apk_parser.cpp
    src/apk/manifest_reader.cpp
    src/dex/dex_parser.cpp
    src/dex/metadata_reader.cpp
    src/runtime/execution_engine.cpp
    src/api/android_stubs.cpp
    src/graphics/renderer.cpp
    src/diagnostics/trace_engine.cpp
)

# CLI executable
add_executable(miniandroid
    src/main.cpp
)

target_link_libraries(miniandroid PRIVATE miniandroid_core)

# Dependencies
find_package(ZLIB REQUIRED)
target_link_libraries(miniandroid_core PRIVATE ZLIB::ZLIB)

# Optional: Vulkan
option(USE_VULKAN "Enable Vulkan backend" OFF)
if(USE_VULCAN)
    find_package(Vulkan REQUIRED)
    target_link_libraries(miniandroid_core PRIVATE Vulkan::Vulkan)
endif()
```

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | C++17 | - |
| Build System | CMake | 3.16+ |
| Compiler | Clang/GCC | 11+ |
| Compression | zlib | 1.2+ |
| Image Output | stb_image_write | - |
| Testing | Google Test | 1.12+ |
| Optional: Vulkan | Vulkan SDK | 1.3+ |

---

## Milestone Definitions

### M0 — Project Builds ✅
**Evidence:** `./miniandroid --version` prints `MiniAndroid v0.1`

### M1 — APK Parser Works ✅
**Evidence:** `./miniandroid analyze hello.apk` produces `apk_info.json`

### M2 — DEX Metadata Loaded ✅
**Evidence:** `./miniandroid dex hello.apk` produces `dex_report.json`

### M3 — HelloWorld Executes ✅
**Evidence:** `./miniandroid run hello.apk` produces `screenshot.png` showing "Hello MiniAndroid"

### M4 — API Tracing Works ✅
**Evidence:** `api_trace.json` contains complete call trace

---

## Failure Rules

1. **Never hide failures** — Every error is logged and reported
2. **No silent fake returns** — Missing APIs throw `UNIMPLEMENTED_API` exception
3. **Evidence required** — No milestone complete without proof files
4. **Trace everything** — Every function call, every branch, every error

---

## Future Roadmap

### Phase 2 — Simple 2D Games
- Native library loading (`libgame.so`)
- OpenGL ES stubs
- Audio output
- Input handling

### Phase 3 — Unity Games
- Unity runtime stubs (`libunity.so`)
- IL2CPP support
- Advanced JNI bridging
- Full Vulkan pipeline

### Phase 4 — Optimization
- Resolution scaling
- FPS control
- Texture compression
- Shader cache
- Memory limiter

---

*Document Version: 1.0*  
*Last Updated: EXP-001 Start*
