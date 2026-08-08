# MiniAndroid Golden Debug Protocol

## Document Version: 1.0
**Experiment Framework Definition**
**Last Updated: EXP-003 Start**

---

## 1. Philosophy

### 1.1 Evidence-Driven Development

Every experiment **MUST** produce verifiable proof of execution. No simulated success. No fake returns. Every milestone requires artifact evidence.

**Core Principle:**  
> *"If it's not in the trace, it didn't happen."*

### 1.2 Golden Rules

| Rule | Code | Description |
|------|------|-------------|
| GR-1 | `NO_FAKE_SUCCESS` | Never return success without real execution |
| GR-2 | `TRACE_EVERYTHING` | Every instruction, every register, every branch |
| GR-3 | `EVIDENCE_REQUIRED` | No milestone complete without JSON proof |
| GR-4 | `MARK_SIMULATED` | Explicitly label stubs/fake implementations |
| GR-5 | `FAIL_FAST` | Crash on unexpected state, never hide errors |
| GR-6 | `MINIMAL_IMPLEMENTATION` | Only implement what current experiment requires |

---

## 2. Experiment Format

### 2.1 Experiment ID Convention

```
EXP-NNN[variant]
```

**Examples:**
- `EXP-001` - Initial experiment (APK Loader)
- `EXP-002` - Class Resolution
- `EXP-003-A` - DEX Interpreter Phase A (const-string only)
- `EXP-003-B` - DEX Interpreter Phase B (new-instance)
- `EXP-004` - Android Object Model

### 2.2 Experiment Directory Structure

```
miniandroid/
├── docs/
│   └── EXP_RULES.md          ← This document
│
├── experiments/
│   └── EXP-NNN/
│       ├── README.md         ← Experiment specification
│       ├── input/            ← Required inputs
│       │   ├── test.apk
│       │   └── expected.json
│       ├── output/           ← Generated artifacts (evidence)
│       │   ├── execution_trace.json
│       │   ├── instruction_trace.json
│       │   └── report.md
│       └── validation/       ← Validation scripts
│           └── validate.py
│
├── src/
│   └── dex/
│       └── interpreter/      ← Implementation per experiment
│           ├── opcode_const_string.cpp
│           ├── opcode_new_instance.cpp
│           └── ...
│
└── run/                       ← Active run output (symlink or copy)
    └── *.json
```

### 2.3 Experiment Metadata Schema

Every experiment MUST produce a manifest:

```json
{
  "experiment_id": "EXP-003-A",
  "name": "DEX Interpreter - const-string Opcode",
  "parent_experiment": "EXP-002",
  "status": {
    "code": "COMPLETE",
    "message": "All acceptance criteria met"
  },
  
  "goal": "Execute first DEX opcode (const-string)",
  "acceptance_criteria": [
    {
      "id": "AC-001",
      "description": "Parse const-string instruction format",
      "status": "PASS",
      "evidence": "instruction_trace.json"
    },
    {
      "id": "AC002", 
      "description": "Load string from string pool into register",
      "status": "PASS",
      "evidence": "register_state.json"
    }
  ],
  
  "implementation": {
    "opcodes_implemented": ["const-string (0x1A)"],
    "opcodes_not_implemented": [
      "new-instance", "invoke-virtual", 
      "return-void", "iget", "iput"
    ],
    "lines_of_code": 145,
    "test_coverage": "100% of implemented opcodes"
  },
  
  "artifacts": {
    "input": ["HelloWorld.apk"],
    "output": [
      "execution_trace.json",
      "instruction_trace.json",
      "report.md"
    ]
  },
  
  "timestamp": {
    "started": "2026-08-09T10:00:00Z",
    "completed": "2026-08-09T10:23:45Z",
    "duration_ms": 1425000
  }
}
```

---

## 3. Evidence Requirements

### 3.1 Mandatory Artifacts Per Experiment

| Artifact | Format | When Required | Description |
|----------|--------|---------------|-------------|
| `execution_trace.json` | JSON | Always | High-level pipeline trace |
| `instruction_trace.json` | JSON | Interpreter exps | Instruction-level detail |
| `register_state.json` | JSON | Interpreter exps | VM register contents |
| `api_trace.json` | JSON | API interaction exps | Android API calls made |
| `crash.log` | Text | On failure | Full crash dump with stack |
| `report.md` | Markdown | Always | Human-readable summary |

### 3.2 execution_trace.json Schema

```json
{
  "experiment_id": "EXP-NNN",
  "pipeline": [
    {
      "stage": "APK Loading",
      "status": "PASS",
      "duration_ms": 12.5,
      "evidence": "Loaded 1492 bytes"
    },
    {
      "stage": "DEX Parsing",
      "status": "PASS", 
      "duration_ms": 8.3,
      "evidence": "1 class, 4 methods, 11 strings"
    }
  ],
  
  "entry_point": {
    "class": "com.miniandroid.hello.MainActivity",
    "method": "onCreate",
    "descriptor": "(Landroid/os/Bundle;)V",
    "resolved": true,
    "bytecode_offset": "0x1D8",
    "instruction_count": 13
  },
  
  "execution_result": {
    "success": true,
    "instructions_executed": 1,
    "registers_modified": ["v0"],
    "final_state": "HALTED_ON_UNIMPLEMENTED"
  },
  
  "issues": [],
  "stop_reason": "Unimplemented opcode at PC+1"
}
```

### 3.3 instruction_trace.json Schema (Interpreter Experiments)

```json
{
  "experiment_id": "EXP-003-A",
  "method_context": {
    "class": "Lcom/miniandroid/hello/MainActivity;",
    "method": "onCreate",
    "descriptor": "(Landroid/os/Bundle;)V"
  },
  
  "initial_state": {
    "program_counter": 0,
    "registers": {},
    "call_stack_depth": 0
  },
  
  "instructions": [
    {
      "sequence": 0,
      "pc_before": 0,
      "opcode": "const-string",
      "opcode_hex": "0x1A",
      "operands": {
        "destination_register": "v0",
        "string_index": 8
      },
      "resolved_string": "Hello MiniAndroid",
      
      "execution": {
        "status": "SUCCESS",
        "cycles": 1,
        "side_effects": []
      },
      
      "state_change": {
        "registers_written": ["v0"],
        "v0": {
          "type": "java.lang.String",
          "value": "Hello MiniAndroid",
          "reference_id": "ref_0x001"
        }
      },
      
      "pc_after": 2
    }
  ],
  
  "final_state": {
    "program_counter": 2,
    "halted": true,
    "halt_reason": "UNIMPLEMENTED_OPCODE",
    "next_opcode_if_known": null
  },
  
  "statistics": {
    "total_instructions": 13,
    "executed_instructions": 1,
    "success_rate": "1/1 (100%)",
    "unimplemented_opcodes_encountered": 1
  }
}
```

### 3.4 Evidence Validation Rules

**EV-1: JSON Must Be Valid**
- All output JSON must pass schema validation
- No trailing commas, proper escaping
- Use `jq .` or equivalent to verify

**EV-2: Timestamps Must Be ISO-8601**
- Format: `YYYY-MM-DDTHH:MM:SSZ`
- UTC timezone required

**EV-3: Offsets Must Be Hex-Prefixed**
- Format: `"0x1234"` (lowercase, 0x prefix)
- Decimal allowed for counts/sizes

**EV-4: Status Codes Standardized**

| Code | Meaning | Usage |
|------|---------|-------|
| `PASS` | Success criteria met | Acceptance criteria |
| `FAIL` | Explicit failure | Errors that stop execution |
| `PARTIAL` | Incomplete but valid | Partial implementation |
| `SKIP` | Not applicable | Optional features |
| `BLOCKED` | Blocked by dependency | Waiting on other experiment |

---

## 4. Stop Conditions

### 4.1 Automatic Stop Triggers

The interpreter **MUST halt** when any of these conditions occur:

#### SC-01: Unimplemented Opcode
```cpp
// Pseudocode
if (!is_implemented(next_opcode)) {
    generate_instruction_trace();
    halt_with_reason("UNIMPLEMENTED_OPCODE");
    status = PARTIAL_SUCCESS;  // Not failure!
}
```

**Rule:** Unimplemented opcode = **HALT**, not crash. Mark as partial success.

#### SC-02: Invalid State
```cpp
if (register_index >= max_registers) {
    CRASH("Register out of bounds");  // This IS a failure
}
```

**Rule:** Invalid VM state = **CRASH**, not halt.

#### SC-03: Experiment Boundary Reached
```cpp
if (current_instruction_count >= EXPERIMENT_LIMIT) {
    halt_with_reason("EXPERIMENT_BOUNDARY");
    save_partial_results();
}
```

**Rule:** Each experiment defines its own scope. Stop at boundary.

#### SC-04: Infinite Loop Detection
```cpp
if (detect_loop(pc_history)) {
    halt_with_reason("INFINITE_LOOP_DETECTED");
    log_loop_details();
}
```

**Rule:** Max 1000 instructions per method unless configured otherwise.

### 4.2 Stop Condition Hierarchy

```
Priority 1: SC-02 (Invalid State)     → CRASH, FAIL
Priority 2: SC-04 (Infinite Loop)     → HALT, PARTIAL  
Priority 3: SC-01 (Unimplemented)    → HALT, SUCCESS (partial)
Priority 4: SC-03 (Boundary)          → HALT, SUCCESS (complete)
```

### 4.3 Resume Capability

Experiments **MUST** be resumable:

```json
{
  "checkpoint": {
    "valid": true,
    "experiment_completed": "EXP-003-A",
    "pc": 2,
    "register_file": {"v0": "ref_0x001"},
    "can_resume_with": ["EXP-003-B"]
  }
}
```

**Next experiment can load this checkpoint and continue execution.**

---

## 5. Experiment Progression Map

### 5.1 Current Roadmap

```
EXP-001 ✅ [COMPLETE]
  APK Parser + Manifest Reader + DEX Metadata
  Evidence: apk_info.json, dex_report.json
  
EXP-002 ✅ [COMPLETE]  
  Class Resolution Pipeline
  Evidence: execution_trace.json (entry point resolved)
  
EXP-003-A 🔄 [CURRENT]
  DEX Interpreter - const-string only
  Evidence: instruction_trace.json
  
EXP-003-B [PLANNED]
  DEX Interpreter - new-instance + invoke-virtual
  Evidence: object_creation_trace.json
  
EXP-003-C [PLANNED]
  DEX Interpreter - return-void + complete lifecycle
  Evidence: full_execution_trace.json
  
EXP-004 [PLANNED]
  Android Object Model (Activity, View, TextView stubs)
  Evidence: object_hierarchy.json
  
EXP-005 [PLANNED]
  Software Renderer (framebuffer output)
  Evidence: screenshot.png
  
EXP-006 [PLANNED]
  Vulkan Backend (GPU rendering)
  Evidence: vulkan_trace.log
```

### 5.2 Dependency Graph

```
EXP-001 ──→ EXP-002 ──→ EXP-003-A ──┬──→ EXP-003-B ──→ EXP-003-C
                                      │
                                      └──→ EXP-004 ──→ EXP-005 ──→ EXP-006
```

Each experiment produces a checkpoint usable by the next.

---

## 6. Opcodes Implementation Tracker

### 6.1 Dalvik Opcode Categories

| Category | Opcodes | Status | Experiment |
|----------|---------|--------|------------|
| **Type: Move** | move, move-object, move-result | — | Future |
| **Type: Literal** | **const-string** ⭐ | EXP-003-A | **CURRENT** |
| | const, const/16, const/high16 | — | Future |
| **Type: Instance** | **new-instance** ⭐ | EXP-003-B | Planned |
| | instance-of, check-cast | — | Future |
| **Type: Method** | **invoke-virtual** ⭐ | EXP-003-B | Planned |
| | invoke-direct, invoke-super | — | Future |
| | invoke-interface, invoke-static | — | Future |
| **Type: Return** | **return-void** ⭐ | EXP-003-C | Planned |
| | return, return-object | — | Future |
| **Type: Field** | iget, iput, sget, sput | — | Future |
| **Type: Array** | agput, aget, array-length | — | Future |
| **Type: Branch** | if-eq, if-nez, goto | — | Future |
| **Type: Compare** | cmpl-float, cmp-long | — | Future |
| **Type: Type Check** | instance-of, check-cast | — | Future |

### 6.2 Opcode Implementation Template

When implementing an opcode, use this template:

```cpp
/**
 * OPCODE: const-string (0x1A)
 * Experiment: EXP-003-A
 * Format: AA|op BBBB
 * 
 * Move reference to string specified by string index into register.
 * 
 * @param vAA Destination register (8-bit)
 * @paramBBBB String pool index (16-bit)
 */
void DexInterpreter::execute_const_string(uint8_t vAA, uint16_t BBBB) {
    // PRE-CONDITION CHECKS
    assert(vAA < registers_.size(), "Register out of bounds");
    assert(BBBB < dex_strings_.size(), "String index out of bounds");
    
    // LOG INSTRUCTION
    log_instruction("const-string", {
        {"dest", register_name(vAA)},
        {"string_idx", BBBB},
        {"value", dex_strings_[BBBBB]}
    });
    
    // EXECUTE
    std::string value = dex_strings_[BBBBB];
    registers_[vAA] = StringReference(value);
    
    // UPDATE STATE
    pc_ += 3;  // const-string is 3 code units (AA|op BBBB)
    
    // RECORD EVIDENCE
    add_to_instruction_trace({
        .opcode = "const-string",
        .result = {vAA, value},
        .status = "SUCCESS"
    });
}
```

---

## 7. Quality Gates

### 7.1 Pre-Experiment Checklist

Before starting an experiment, verify:

- [ ] Parent experiment completed successfully
- [ ] Checkpoint files exist and are valid
- [ ] Test APK available and parseable
- [ ] Output directories created
- [ ] Previous experiment's artifacts reviewed

### 7.2 Post-Experiment Validation

After completing an experiment, verify:

- [ ] All required JSON artifacts produced
- [ ] JSON validates against schema
- [ ] No crashes during execution
- [ ] Stop condition properly triggered
- [ ] Evidence matches expected behavior
- [ ] Checkpoint saved for next experiment

### 7.3 Smoke Tests

Run these after every change:

```bash
# 1. Parse HelloWorld.apk
./build_exp002/miniandroid_exp002 test_apks/HelloWorld.apk

# 2. Verify JSON is valid
cat run/execution_trace.json | jq .

# 3. Check entry point resolved
cat run/execution_trace.json | jq '.entry_point.resolved'

# 4. Verify instruction count > 0 (for interpreter exps)
cat run/instruction_trace.json | jq '.instructions | length'
```

---

## 8. Failure Handling

### 8.1 Failure Classification

| Type | Example | Action | Status |
|------|---------|--------|--------|
| **Input Error** | Corrupt APK | Stop, report error | FAIL |
| **Parse Error** | Invalid DEX header | Stop, report details | FAIL |
| **Runtime Error** | Null pointer dereference | Crash with stacktrace | FAIL |
| **Unimplemented** | Unknown opcode | Halt gracefully | PARTIAL |
| **Boundary** | End of experiment scope | Save checkpoint | SUCCESS |

### 8.2 Error Reporting Format

```json
{
  "error": {
    "code": "UNIMPLEMENTED_OPCODE",
    "severity": "HALT",
    "experiment": "EXP-003-A",
    "location": {
      "file": "dex_interpreter.cpp",
      "line": 245,
      "function": "execute_next_instruction"
    },
    "context": {
      "pc": 2,
      "opcode_hex": "0x22",
      "opcode_name": "new-instance",
      "reason": "Opcode not implemented in EXP-003-A scope"
    },
    "recovery": {
      "possible": true,
      "resume_with": "EXP-003-B",
      "checkpoint_saved": true
    }
  }
}
```

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-09 | Initial definition for EXP-003 start |

---

*This document is part of the Golden Debug Protocol for MiniAndroid Runtime development.*
*All experiments MUST adhere to these rules.*
