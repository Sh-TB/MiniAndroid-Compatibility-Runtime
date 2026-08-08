# MiniAndroid Runtime — Execution Flow Document

## Overview

This document traces the complete execution flow from APK input to screenshot output, documenting every step, decision point, and potential failure mode.

---

## Complete Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXECUTION FLOW: EXP-001                          │
│                    Target: HelloWorld.apk                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  START                                                              │
│    │                                                                │
│    ▼                                                                │
│  ┌─────────────────┐                                               │
│  │ 1. VALIDATE     │ ◄── Check file exists, is valid ZIP           │
│  │    INPUT        │     Check magic bytes: PK\x03\x04             │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │ 2. PARSE APK    │ ◄── Extract ZIP entries                       │
│  │                 │     Locate AndroidManifest.xml                │
│  │                 │     Locate classes.dex                        │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ├──────────────────────┐                                  │
│           ▼                      ▼                                  │
│  ┌─────────────────┐    ┌─────────────────┐                        │
│  │ 3a. PARSE       │    │ 3b. PARSE DEX   │                        │
│  │     MANIFEST    │    │                 │                        │
│  └────────┬────────┘    └────────┬────────┘                        │
│           │                      │                                  │
│           ▼                      ▼                                  │
│  ┌─────────────────┐    ┌─────────────────┐                        │
│  │ apk_info.json   │    │ dex_report.json │                        │
│  └────────┬────────┘    └────────┬────────┘                        │
│           │                      │                                  │
│           └──────────┬───────────┘                                  │
│                      ▼                                              │
│  ┌─────────────────────────────────────────┐                       │
│  │ 4. INITIALIZE RUNTIME                   │                       │
│  │     • Create memory pool (4MB)          │                       │
│  │     • Register API stubs                │                       │
│  │     • Initialize class loader           │                       │
│  │     • Setup graphics context            │                       │
│  └────────┬────────────────────────────────┘                       │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │ 5. LOAD CLASSES │ ◄── Load MainActivity class                  │
│  │                 │     Load superclasses (Activity)              │
│  │                 │     Resolve method references                 │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────┐                       │
│  │ 6. SIMULATE LIFECYCLE                   │                       │
│  │                                         │                       │
│  │   Activity.construct()                  │                       │
│  │         │                              │                       │
│  │         ▼                              │                       │
│  │   Activity.onCreate(null)              │◄── TRACE               │
│  │         │                              │                       │
│  │         ├── setContentView(R.layout.main) │                    │
│  │         │         │                     │                       │
│  │         │         ▼                     │                       │
│  │         │   Inflate XML layout         │◄── TRACE               │
│  │         │         │                     │                       │
│  │         │         ├── TextView created  │◄── TRACE             │
│  │         │         ├── Attributes set    │◄── TRACE             │
│  │         │         └── View hierarchy    │                       │
│  │         │                              │                       │
│  │         └── return void                │                       │
│  │                                       │                       │
│  │   Activity.onStart()                  │◄── TRACE               │
│  │   Activity.onResume()                 │◄── TRACE               │
│  │                                         │                       │
│  └────────┬────────────────────────────────┘                       │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────┐                       │
│  │ 7. RENDER FRAME                         │                       │
│  │                                         │                       │
│  │   root.measure(width, height)           │◄── TRACE               │
│  │   root.layout(0, 0, w, h)              │◄── TRACE               │
│  │   root.draw(canvas)                    │◄── TRACE               │
│  │         │                              │                       │
│  │         ├── Canvas.drawColor(BG)      │◄── TRACE               │
│  │         ├── TextView.draw(canvas)      │◄── TRACE               │
│  │         │   └── Canvas.drawText()      │◄── TRACE               │
│  │         └── [more views...]            │                       │
│  │                                         │                       │
│  └────────┬────────────────────────────────┘                       │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │ 8. CAPTURE      │ ◄── Read framebuffer                         │
│  │    SCREENSHOT   │     Encode as PNG                            │
│  │                 │     Save to run/screenshot.png               │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────┐                       │
│  │ 9. GENERATE REPORTS                     │                       │
│  │     • api_trace.json (all traced calls) │                       │
│  │     • crash.log (any errors)            │                       │
│  │     • report.md (human readable)        │                       │
│  └────────┬────────────────────────────────┘                       │
│           │                                                         │
│           ▼                                                         │
│  END (exit code: 0=SUCCESS, 1=FAILURE)                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Step Analysis

### Step 1: Input Validation

```cpp
// Pseudocode for input validation
Result validate_apk(const std::string& path) {
    // 1.1 Check file exists
    if (!file_exists(path)) {
        return Error::FILE_NOT_FOUND;
    }
    
    // 1.2 Check file size (minimum ~100 bytes for valid APK)
    auto size = file_size(path);
    if (size < MIN_APK_SIZE) {
        return Error::FILE_TOO_SMALL;
    }
    
    // 1.3 Verify ZIP magic bytes
    auto magic = read_bytes(path, 0, 4);
    if (magic != "\x50\x4b\x03\x04") {  // "PK\3\4"
        return Error::INVALID_ZIP;
    }
    
    // 1.4 Verify required entries exist
    auto entries = list_zip_entries(path);
    if (!entries.contains("AndroidManifest.xml")) {
        return Error::NO_MANIFEST;
    }
    if (!entries.contains("classes.dex")) {
        return Error::NO_DEX;
    }
    
    return Result::OK;
}
```

**Evidence Generated:** None (validation only)

**Failure Modes:**
| Error | Cause | Action |
|-------|-------|--------|
| FILE_NOT_FOUND | Path incorrect | Report error, exit |
| INVALID_ZIP | Corrupted or not APK | Report error, exit |
| NO_MANIFEST | Invalid APK structure | Report error, exit |
| NO_DEX | Native-only APK | Report warning, continue |

---

### Step 2: APK Parsing

```cpp
// Pseudocode for APK parsing
ApkInfo parse_apk(const std::string& path) {
    ApkInfo info;
    
    // 2.1 Open as ZIP archive
    ZipArchive zip(path);
    
    // 2.2 Extract and parse manifest
    auto manifest_data = zip.extract("AndroidManifest.xml");
    info.manifest = parse_axml(manifest_data);
    
    // 2.3 Extract package info from manifest
    info.package_name = manifest.get_attribute("package");
    info.version_name = manifest.get_attribute("android:versionName");
    info.version_code = manifest.get_int_attribute("android:versionCode");
    
    // 2.4 Find main activity
    auto activities = manifest.find_elements("activity");
    for (auto& activity : activities) {
        if (activity.has_intent_filter("android.intent.action.MAIN")) {
            info.main_activity = activity.get_attribute("android:name");
            break;
        }
    }
    
    // 2.5 Extract permissions
    info.permissions = manifest.find_attributes("uses-permission", "android:name");
    
    // 2.6 List all DEX files
    info.dex_files = zip.list_entries_matching("^classes.*\\.dex$");
    
    // 2.7 List native libraries
    info.native_libraries = zip.list_entries_matching("^lib/.*\\.so$");
    
    return info;
}
```

**Evidence Generated:** `run/apk_info.json`

**Failure Modes:**
| Error | Cause | Action |
|-------|-------|--------|
| AXML_PARSE_ERROR | Corrupted manifest | Report error, exit |
| NO_MAIN_ACTIVITY | No launch activity | Use first activity or report |

---

### Step 3a: Manifest Parsing (AXML Format)

AndroidManifest.xml in APK is **binary XML**, not text:

```
Binary XML Structure:
┌──────────────────────────────────┐
│ AXML Header                      │
├──────────────────────────────────┤
│ String Pool (resource strings)   │
├──────────────────────────────────┤
│ Resource IDs (attr references)   │
├──────────────────────────────────┤
│ Start Namespace (android)        │
├──────────────────────────────────┤
│ Start Element (manifest)         │
│   ├─ Attribute: package          │
│   ├─ Attribute: versionCode      │
│   └─ Attribute: versionName      │
├──────────────────────────────────┤
│ Start Element (application)      │
│   └─ Start Element (activity)    │
│       └─ Start Element (intent-filter) │
│           └─ Start Element (action)    │
│               └─ Attribute: name="MAIN" │
├──────────────────────────────────┤
│ ... more elements ...            │
├──────────────────────────────────┤
│ End Elements (reverse order)     │
└──────────────────────────────────┘
```

---

### Step 3b: DEX Parsing

```cpp
// Pseudocode for DEX parsing
DexReport parse_dex(const uint8_t* data, size_t size) {
    DexReport report;
    
    // 3b.1 Validate DEX header
    DexHeader header = *reinterpret_cast<const DexHeader*>(data);
    
    if (std::memcmp(header.magic, "dex\n035\0", 8) != 0) {
        throw DexError::INVALID_MAGIC;
    }
    
    report.dex_version = std::string(header.magic + 4, 3);  // "035"
    
    // 3b.2 Parse string table
    auto string_ids = parse_string_ids(data, header);
    report.strings_count = string_ids.size();
    
    // 3b.3 Parse type table
    auto type_ids = parse_type_ids(data, header, string_ids);
    report.types_count = type_ids.size();
    
    // 3b.4 Parse method table
    auto method_ids = parse_method_ids(data, header, string_ids, type_ids);
    report.methods_count = method_ids.size();
    
    // 3b.5 Parse class definitions
    auto class_defs = parse_class_defs(data, header, string_ids, type_ids, method_ids);
    report.classes_count = class_defs.size();
    
    // 3b.6 Extract class details
    for (auto& class_def : class_defs) {
        ClassInfo info;
        info.name = get_type_name(class_def.class_idx, type_ids, string_ids);
        info.superclass = get_type_name(class_def.superclass_idx, type_ids, string_ids);
        
        // Parse class data for methods
        auto class_data = parse_class_data(data, class_def);
        info.methods = extract_methods(class_data, method_ids, string_ids);
        
        report.classes.push_back(info);
    }
    
    return report;
}
```

**Evidence Generated:** `run/dex_report.json`

**Failure Modes:**
| Error | Cause | Action |
|-------|-------|--------|
| INVALID_MAGIC | Not a DEX file | Report error, exit |
| CHECKSUM_FAIL | Corrupted DEX | Report warning, attempt parse |
| CLASS_DATA_ERROR | Malformed class | Skip class, continue |

---

### Step 4: Runtime Initialization

```cpp
// Pseudocode for runtime initialization
Runtime initialize_runtime(const ApkInfo& apk_info) {
    Runtime runtime;
    
    // 4.1 Create memory pool
    runtime.memory = MemoryPool(4 * 1024 * 1024);  // 4MB initial
    
    // 4.2 Register API stubs
    runtime.api_registry.register_stub<ActivityStub>();
    runtime.api_registry.register_stub<ViewStub>();
    runtime.api_registry.register_stub<TextViewStub>();
    runtime.api_registry.register_stub<CanvasStub>();
    runtime.api_registry.register_stub<PaintStub>();
    // ... more stubs
    
    // 4.3 Initialize class loader
    runtime.class_loader.set_apk_info(apk_info);
    
    // 4.4 Setup graphics context
    runtime.graphics = SoftwareRenderer(1080, 1920);  // Default resolution
    
    // 4.5 Initialize diagnostics
    runtime.diagnostics = TraceEngine();
    runtime.diagnostics.start_session();
    
    return runtime;
}
```

**Evidence Generated:** Diagnostic session started

---

### Step 5: Class Loading

```cpp
// Pseudocode for class loading
void load_classes(Runtime& runtime, const DexReport& dex_report) {
    for (auto& class_info : dex_report.classes) {
        // 5.1 Create class object
        JavaClass clazz;
        clazz.name = class_info.name;
        clazz.superclass_name = class_info.superclass;
        
        // 5.2 Resolve superclass chain
        resolve_superclass_chain(clazz, runtime);
        
        // 5.3 Register methods
        for (auto& method : class_info.methods) {
            JavaMethod jmethod;
            jmethod.name = method.name;
            jmethod.descriptor = method.descriptor;
            
            // Check if we have a stub for this
            if (runtime.api_registry.has_stub(clazz.name, method.name)) {
                jmethod.implementation = runtime.api_registry.get_stub(clazz.name, method.name);
            } else {
                jmethod.implementation = UnimplementedStub;  // Will throw!
            }
            
            clazz.add_method(jmethod);
        }
        
        // 5.4 Register in class loader
        runtime.class_loader.register_class(clazz);
    }
}
```

**Evidence Generated:** Class load events in trace

---

### Step 6: Lifecycle Simulation

This is the core execution phase for v0.1:

```cpp
// Pseudocode for lifecycle simulation
void execute_lifecycle(Runtime& runtime, const std::string& main_activity) {
    tracer trace(runtime.diagnostics);
    
    // 6.1 Get main activity class
    auto& activity_class = runtime.class_loader.get_class(main_activity);
    
    // 6.2 Create instance
    trace.enter("<init>", activity_class.name);
    auto activity = activity_class.newInstance();
    trace.exit();
    
    // 6.3 Call onCreate()
    trace.enter("onCreate", "android.app.Activity");
    
    // For v0.1: Simulate what onCreate does
    Bundle null_bundle;  // First launch has no saved state
    
    // The actual APK's onCreate would:
    // 1. Call super.onCreate(bundle)
    // 2. Call setContentView(R.layout.activity_main)
    // 3. Optionally find views and set properties
    
    // We simulate this by reading the layout resource
    auto layout_resource = inflate_layout(runtime, R_layout_activity_main);
    activity.content_view = layout_resource.root_view;
    
    trace.arg("bundle", "null");
    trace.exit();
    
    // 6.4 Call onStart()
    trace.enter("onStart", "android.app.Activity");
    activity.state = ActivityState::STARTED;
    trace.exit();
    
    // 6.5 Call onResume()
    trace.enter("onResume", "android.app.Activity");
    activity.state = ActivityState::RESUMED;
    trace.exit();
    
    // Store activity for rendering
    runtime.current_activity = activity;
}
```

**Evidence Generated:** Lifecycle calls in `api_trace.json`

---

### Step 7: Frame Rendering

```cpp
// Pseudocode for rendering
void render_frame(Runtime& runtime) {
    tracer trace(runtime.diagnostics);
    auto& renderer = runtime.graphics;
    auto& activity = runtime.current_activity;
    
    int width = renderer.width();
    int height = renderer.height();
    
    // 7.1 Measure phase
    trace.enter("measure", "android.view.View");
    int width_spec = MeasureSpec::makeMeasureSpec(width, EXACTLY);
    int height_spec = MeasureSpec::makeMeasureSpec(height, EXACTLY);
    activity.content_view->measure(width_spec, height_spec);
    trace.exit();
    
    // 7.2 Layout phase
    trace.enter("layout", "android.view.View");
    activity.content_view->layout(0, 0, width, height);
    trace.exit();
    
    // 7.3 Draw phase
    trace.enter("draw", "android.view.View");
    Canvas canvas(renderer.framebuffer());
    
    // Draw background
    trace.enter("drawColor", "android.graphics.Canvas");
    canvas.draw_color(0xFFFFFFFF);  // White background
    trace.arg("color", "#FFFFFF");
    trace.exit();
    
    // Draw view hierarchy
    activity.content_view->draw(canvas);
    
    trace.exit();
    
    // 7.4 Mark frame complete
    renderer.present();
}
```

**TextView.draw() implementation:**
```cpp
void TextView::draw(Canvas& canvas) {
    tracer trace(get_diagnostics());
    trace.enter("draw", "android.widget.TextView");
    
    // Draw text at position
    trace.enter("drawText", "android.graphics.Canvas");
    canvas.draw_text(m_text, m_x, m_y, m_paint);
    trace.arg("text", m_text);
    trace.arg("x", m_x);
    trace.arg("y", m_y);
    trace.exit();
    
    trace.exit();
}
```

**Evidence Generated:** Render calls in trace, framebuffer updated

---

### Step 8: Screenshot Capture

```cpp
// Pseudocode for screenshot capture
void capture_screenshot(Runtime& runtime, const std::string& output_path) {
    auto& renderer = runtime.graphics;
    
    // 8.1 Get framebuffer data
    auto* pixels = renderer.framebuffer_data();
    int width = renderer.width();
    int height = renderer.height();
    
    // 8.2 Encode to PNG
    PNGEncoder encoder;
    encoder.set_width(width);
    encoder.set_height(height);
    encoder.set_data(pixels);  // RGBA format
    
    auto png_data = encoder.encode();
    
    // 8.3 Write to file
    write_file(output_path, png_data);
    
    // 8.4 Log to diagnostics
    runtime.diagnostics.log_screenshot(output_path, width, height, png_data.size());
}
```

**Evidence Generated:** `run/screenshot.png`

---

### Step 9: Report Generation

```cpp
// Pseudocode for report generation
void generate_reports(Runtime& runtime, const ExecutionResult& result) {
    auto& diag = runtime.diagnostics;
    
    // 9.1 Write API trace JSON
    json api_trace;
    api_trace["session_id"] = diag.session_id();
    api_trace["timestamp"] = current_timestamp();
    api_trace["calls"] = diag.get_traced_calls();
    write_json("run/api_trace.json", api_trace);
    
    // 9.2 Write crash log (if any errors)
    if (!result.errors.empty()) {
        CrashLog log;
        log.timestamp = current_timestamp();
        log.errors = result.errors;
        log.stack_traces = result.stack_traces;
        write_file("run/crash.log", log.serialize());
    }
    
    // 9.3 Generate human-readable report
    MarkdownReport report;
    report.title = "MiniAndroid Execution Report";
    report.application = runtime.apk_info.package_name;
    report.status = result.success ? "SUCCESS" : "FAILURE";
    report.metrics = {
        {"apis_called", diag.call_count()},
        {"frames_rendered", result.frame_count},
        {"execution_time_ms", result.duration_ms},
        {"memory_peak_bytes", runtime.memory.peak_usage()}
    };
    report.api_summary = diag.get_call_summary();
    report.screenshot_path = "screenshot.png";
    
    write_file("run/report.md", report.generate());
}
```

**Evidence Generated:**
- `run/api_trace.json`
- `run/crash.log` (if errors)
- `run/report.md`

---

## Error Handling Flow

```
Error Occurred
      │
      ▼
┌─────────────────┐
│ Log to crash.log │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Is it recoverable?│───▶│ Yes: Continue   │
└────────┬────────┘     │ (log warning)   │
         │             └─────────────────┘
         ▼ No
┌─────────────────┐
│ Set status:     │
│ FAILURE         │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Generate partial reports with what we   │
│ have (partial trace, error details)     │
└────────┬────────────────────────────────┘
         │
         ▼
    Exit with code 1
```

---

## Example: Complete HelloWorld Execution

### Input APK Structure
```
HelloWorld.apk
├── AndroidManifest.xml (binary)
├── classes.dex
├── resources.arsc
└── res/
    ├── layout/
    │   └── activity_main.xml (binary)
    └── values/
        └── strings.xml (binary)
```

### Expected Output Files
```
run/
├── apk_info.json
│   {
│     "apk_name": "HelloWorld.apk",
│     "package_name": "com.miniandroid.helloworld",
│     "version_name": "1.0",
│     "main_activity": ".MainActivity",
│     "permissions": []
│   }
│
├── dex_report.json
│   {
│     "classes": [
│       {
│         "name": "Lcom/miniandroid/helloworld/MainActivity;",
│         "methods": ["<init>", "onCreate"]
│       },
│       {
│         "name": "Landroid/app/Activity;",
│         "methods": ["<init>", "onCreate", "setContentView", ...]
│       }
│     ]
│   }
│
├── api_trace.json
│   [
│     {"ts": 0, "call": "Activity.<init>"},
│     {"ts": 1, "call": "Activity.onCreate", "args": ["null"]},
│     {"ts": 2, "call": "Activity.setContentView", "args": ["R.layout.main"]},
│     {"ts": 3, "call": "View.inflate"},
│     {"ts": 4, "call": "TextView.<init>"},
│     {"ts": 5, "call": "TextView.setText", "args": ["Hello MiniAndroid"]},
│     {"ts": 6, "call": "Activity.onStart"},
│     {"ts": 7, "call": "Activity.onResume"},
│     {"ts": 8, "call": "View.measure"},
│     {"ts": 9, "call": "View.layout"},
│     {"ts": 10, "call": "View.draw"},
│     {"ts": 11, "call": "Canvas.drawColor"},
│     {"ts": 12, "call": "TextView.draw"},
│     {"ts": 13, "call": "Canvas.drawText", "args": ["Hello MiniAndroid"]}
│   ]
│
├── screenshot.png
│   [Image showing white background with "Hello MiniAndroid" text]
│
└── report.md
    # MiniAndroid Execution Report
    
    ## Application: com.miniandroid.helloworld
    ## Status: SUCCESS ✅
    
    ### Metrics
    - APIs Called: 14
    - Frames: 1
    - Time: 12ms
    
    ### Screenshot
    ![Screenshot](screenshot.png)
```

---

*Document Version: 1.0*  
*Last Updated: EXP-001 Start*
