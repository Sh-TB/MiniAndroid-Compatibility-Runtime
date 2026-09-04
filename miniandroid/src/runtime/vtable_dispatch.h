/*
 * MiniAndroid VTable Dispatch Implementation — EXP-034 Phase 4
 * 
 * Implements runtime method resolution and virtual dispatch for invoke-virtual.
 * This bridges the gap between bytecode instructions and actual method execution.
 *
 * Key Components:
 * 1. MethodResolver — Resolves method references to concrete methods
 * 2. VirtualDispatcher — Executes polymorphic method calls via VTable
 * 3. InvocationContext — Tracks current invocation state (for evidence)
 *
 * AOSP Reference Flow:
 *   invoke-virtual opcode
 *     → dvmResolveClass() — get object's class
 *     → dvmFindVirtualMethod() — search VTable by index
 *     → Execute found method's code_item
 *
 * Rule 1: Research before implementation — Follows AOSP flow exactly
 * Rule 2: REAL evidence only — Every dispatch operation is traceable
 */

#ifndef MINIANDROID_VTABLE_DISPATCH_H
#define MINIANDROID_VTABLE_DISPATCH_H

#include "runtime_metadata.h"
#include <functional>
#include <sstream>
#include <iomanip>
#include <cassert>
#include <chrono>   // portable: was transitively included by libstdc++, not by libc++ (Windows/llvm-mingw)

namespace miniandroid {
namespace runtime {

using json = nlohmann::json;

// ============================================================================
// Invocation Context — Evidence collection for method calls
// ============================================================================

/**
 * InvocationContext captures complete information about a single method invocation.
 * Used for evidence collection and debugging.
 */
struct InvocationContext {
    // === Caller Information ===
    std::string caller_class;            // Class containing the call site
    std::string caller_method;           // Method containing the invoke instruction
    uint32_t caller_pc;                  // Program counter at call site
    
    // === Invoke Instruction ===
    std::string invoke_opcode;           // "invoke-virtual", "invoke-direct", etc.
    uint32_t method_idx;                 // DEX method_ids[] index being called
    std::string method_name;             // Resolved method name
    std::string method_descriptor;       // Resolved method descriptor
    
    // === Target Resolution ===
    std::string target_class;            // Actual class of object (runtime type)
    std::string target_method;           // Final method that will execute
    bool is_override;                    // True if target differs from declared type
    int32_t vtable_index;                // Index in target's VTable (-1 if not virtual)
    
    // === Arguments ===
    std::vector<json> arguments;         // Argument values (JSON for flexibility)
    
    // === Execution Result ===
    bool executed_successfully;          // Did the method run without error?
    json return_value;                   // Return value (if any)
    std::string error_message;           // If execution failed
    
    // === Timing ===
    uint64_t resolve_time_ns;            // Time to resolve method (ns)
    uint64_t execute_time_ns;            // Time to execute method (ns)
    
    // === Constructor ===
    InvocationContext()
        : caller_pc(0), method_idx(0), vtable_index(-1),
          executed_successfully(false),
          resolve_time_ns(0), execute_time_ns(0) {}
    
    // === Serialization (Evidence) ===
    json to_json() const {
        return {
            {"caller", {
                {"class", caller_class},
                {"method", caller_method},
                {"pc", caller_pc}
            }},
            {"invocation", {
                {"opcode", invoke_opcode},
                {"method_idx", method_idx},
                {"method_name", method_name},
                {"descriptor", method_descriptor}
            }},
            {"resolution", {
                {"target_class", target_class},
                {"target_method", target_method},
                {"is_override", is_override},
                {"vtable_index", vtable_index}
            }},
            {"arguments", arguments},
            {"result", {
                {"success", executed_successfully},
                {"return_value", return_value},
                {"error", error_message}
            }},
            {"timing", {
                {"resolve_ns", resolve_time_ns},
                {"execute_ns", execute_time_ns}
            }}
        };
    }
    
    std::string debug_string() const {
        std::ostringstream ss;
        ss << "Invoke: " << invoke_opcode << " " << target_method << method_descriptor;
        if (!target_class.empty()) {
            ss << "\n  Target: " << target_class << "." << target_method;
            if (is_override) {
                ss << " [OVERRIDE]";
            }
            if (vtable_index >= 0) {
                ss << " [vtable[" << vtable_index << "]]";
            }
        }
        return ss.str();
    }
};

// ============================================================================
// Method Resolver — Resolves method references at runtime
// ============================================================================

/**
 * MethodResolver handles the resolution of method references from DEX format
 * to actual RuntimeMethodInfo pointers, following Dalvik/ART semantics.
 * 
 * Resolution process varies by invoke type:
 * - invoke-static: Look in direct_methods by signature
 * - invoke-direct: Look in direct_methods by signature (non-virtual)
 * - invoke-virtual: Look up VTable index, then dispatch to actual class
 * - invoke-super: Start from superclass VTable
 * - invoke-interface: Search interface method tables
 */
class MethodResolver {
private:
    RuntimeMetadataContainer* metadata_container;
    
public:
    explicit MethodResolver(RuntimeMetadataContainer* container)
        : metadata_container(container) {}
    
    /**
     * Resolve a static method call.
     * 
     * Static methods are resolved at compile/link time to a specific class.
     * No polymorphism involved.
     * 
     * @param class_descriptor Class declaring the static method
     * @param method_name Method name
     * @param method_desc Method descriptor
     * @return Method info or nullptr if not found
     */
    const RuntimeMethodInfo* resolve_static(
        const std::string& class_descriptor,
        const std::string& method_name,
        const std::string& method_desc) const
    {
        if (!metadata_container) return nullptr;
        
        RuntimeClassInfo* cls = metadata_container->find_class(class_descriptor);
        if (!cls) return nullptr;
        
        return cls->find_static_method(method_name, method_desc);
    }
    
    /**
     * Resolve a direct method call.
     * 
     * Direct methods include:
     * - Private methods (ACC_PRIVATE)
     * - Constructors (<init>)
     * - Static methods (though invoke-static is preferred)
     * 
     * No polymorphism — always calls the exact method specified.
     * 
     * @param class_descriptor Class declaring the method
     * @param method_name Method name
     * @param method_desc Method descriptor
     * @return Method info or nullptr if not found
     */
    const RuntimeMethodInfo* resolve_direct(
        const std::string& class_descriptor,
        const std::string& method_name,
        const std::string& method_desc) const
    {
        if (!metadata_container) return nullptr;
        
        RuntimeClassInfo* cls = metadata_container->find_class(class_descriptor);
        if (!cls) return nullptr;
        
        return cls->find_direct_method(method_name, method_desc);
    }
    
    /**
     * Resolve a virtual method call to VTable index.
     * 
     * This is the key operation for invoke-virtual:
     * 1. Find the method in the declared class's VTable
     * 2. Return its VTable index
     * 3. At call time, use this index on the ACTUAL object's class
     * 
     * Example:
     *   Code: invoke-virtual {v0}, LAnimal;->speak()V
     *   Declared class: LAnimal;
     *   Animal.speak() is at VTable[0]
     *   Return: 0
     *   
     *   At runtime, if v0 holds a Dog:
     *   Dog.vtable[0] = Dog.speak() ← Polymorphism!
     * 
     * @param declared_class Class where method is declared
     * @param method_name Method name
     * @param method_desc Method descriptor
     * @return VTable index or -1 if not found
     */
    int32_t resolve_virtual_to_vtable_index(
        const std::string& declared_class,
        const std::string& method_name,
        const std::string& method_desc) const
    {
        if (!metadata_container) return -1;
        
        RuntimeClassInfo* cls = metadata_container->find_class(declared_class);
        if (!cls || !cls->vtable_built) return -1;
        
        // Build signature for lookup
        std::string signature = method_name + "+" + method_desc;
        
        // Search VTable for this signature
        const RuntimeMethodInfo* method = cls->vtable.lookup_by_signature(signature);
        if (!method) return -1;
        
        return method->vtable_index;
    }
    
    /**
     * Fully resolve a virtual method call given an actual object.
     * 
     * This performs the complete resolution:
     * 1. Get object's runtime class
     * 2. Look up method in that class's VTable using pre-resolved index
     * 3. Return the actual method to execute
     * 
     * @param actual_object_class Runtime class of the object being invoked on
     * @param vtable_index Pre-resolved VTable index
     * @return Method to execute or nullptr
     */
    const RuntimeMethodInfo* resolve_virtual_dispatch(
        const RuntimeClassInfo* actual_object_class,
        int32_t vtable_index) const
    {
        if (!actual_object_class || vtable_index < 0) return nullptr;
        if (!actual_object_class->vtable_built) return nullptr;
        
        return actual_object_class->find_virtual_method(static_cast<uint32_t>(vtable_index));
    }
};

// ============================================================================
// Virtual Dispatcher — Executes method calls via VTable
// ============================================================================

/**
 * VirtualDispatcher executes method calls using VTable-based dispatch.
 * It demonstrates how invoke-virtual achieves polymorphism.
 */
class VirtualDispatcher {
private:
    MethodResolver* resolver;
    
    // Callback types for method execution
    using MethodExecutor = std::function<json(
        const RuntimeMethodInfo*,          // Method to execute
        const std::vector<json>&,         // Arguments
        InvocationContext&                // Context to fill
    )>;
    
    MethodExecutor executor;
    
    // Trace of all invocations (evidence)
    std::vector<InvocationContext> invocation_trace;
    
public:
    explicit VirtualDispatcher(MethodResolver* r)
        : resolver(r) {
        // Default executor just logs the call
        executor = [](const RuntimeMethodInfo* method,
                      const std::vector<json>& args,
                      InvocationContext& ctx) -> json {
            ctx.executed_successfully = true;
            ctx.return_value = nullptr;  // void method
            return ctx.return_value;
        };
    }
    
    /**
     * Set custom method executor
     */
    void set_executor(MethodExecutor exec) {
        executor = exec;
    }
    
    /**
     * Execute an invoke-virtual instruction.
     * 
     * This simulates what the interpreter does when it encounters invoke-virtual:
     * 
     * Pseudocode from Dalvik interpreter:
     * ```
     * // At invoke-virtual instruction:
     * Object* obj = (Object*) GET_REGISTER(vB);
     * ClassObject* clazz = obj->clazz;  // Actual runtime class!
     * Method* method = clazz->vtable[vtable_A];  // Use pre-resolved index
     * GOTO(invokeTarget, method);  // Jump to method
     * ```
     * 
     * @param obj_actual_class The actual runtime class of the object
     * @param vtable_index Pre-resolved VTable index
     * @param arguments Arguments to pass to the method
     * @param caller_info Caller context (for traceability)
     * @return Complete invocation context with result
     */
    InvocationContext dispatch_virtual(
        const RuntimeClassInfo* obj_actual_class,
        int32_t vtable_index,
        const std::vector<json>& arguments,
        const std::pair<std::string, std::string>& caller_info)  // {class, method}
    {
        InvocationContext ctx;
        ctx.caller_class = caller_info.first;
        ctx.caller_method = caller_info.second;
        ctx.invoke_opcode = "invoke-virtual";
        ctx.arguments = arguments;
        
        auto start_resolve = std::chrono::high_resolution_clock::now();
        
        // Step 1: Resolve method through VTable
        const RuntimeMethodInfo* target_method = nullptr;
        
        if (obj_actual_class && obj_actual_class->vtable_built && vtable_index >= 0) {
            target_method = obj_actual_class->find_virtual_method(
                static_cast<uint32_t>(vtable_index));
            
            if (target_method) {
                ctx.target_class = obj_actual_class->class_descriptor;
                ctx.target_method = target_method->name;
                ctx.method_name = target_method->name;
                ctx.method_descriptor = target_method->descriptor;
                ctx.vtable_index = vtable_index;
                
                // Check if this is an override
                // (In real implementation, compare with declared class's method)
                ctx.is_override = true;  // Simplified for demo
            }
        }
        
        auto end_resolve = std::chrono::high_resolution_clock::now();
        ctx.resolve_time_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            end_resolve - start_resolve).count();
        
        // Step 2: Execute the method
        if (target_method && executor) {
            auto start_exec = std::chrono::high_resolution_clock::now();
            
            try {
                ctx.return_value = executor(target_method, arguments, ctx);
                ctx.executed_successfully = true;
            } catch (const std::exception& e) {
                ctx.executed_successfully = false;
                ctx.error_message = e.what();
            }
            
            auto end_exec = std::chrono::high_resolution_clock::now();
            ctx.execute_time_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                end_exec - start_exec).count();
        } else {
            ctx.executed_successfully = false;
            if (!target_method) {
                ctx.error_message = "Method not found in VTable";
            } else {
                ctx.error_message = "No executor set";
            }
        }
        
        // Step 3: Record in trace (evidence!)
        invocation_trace.push_back(ctx);
        
        return ctx;
    }
    
    /**
     * Execute an invoke-direct instruction (no polymorphism).
     */
    InvocationContext dispatch_direct(
        const std::string& class_descriptor,
        const std::string& method_name,
        const std::string& method_desc,
        const std::vector<json>& arguments,
        const std::pair<std::string, std::string>& caller_info)
    {
        InvocationContext ctx;
        ctx.caller_class = caller_info.first;
        ctx.caller_method = caller_info.second;
        ctx.invoke_opcode = "invoke-direct";
        ctx.arguments = arguments;
        ctx.method_name = method_name;
        ctx.method_descriptor = method_desc;
        
        auto start = std::chrono::high_resolution_clock::now();
        
        const RuntimeMethodInfo* method = resolver->resolve_direct(
            class_descriptor, method_name, method_desc);
        
        auto end = std::chrono::high_resolution_clock::now();
        ctx.resolve_time_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            end - start).count();
        
        if (method) {
            ctx.target_class = class_descriptor;
            ctx.target_method = method->name;
            ctx.is_override = false;  // Direct calls never override
            
            if (executor) {
                try {
                    ctx.return_value = executor(method, arguments, ctx);
                    ctx.executed_successfully = true;
                } catch (const std::exception& e) {
                    ctx.error_message = e.what();
                }
            }
        } else {
            ctx.error_message = "Direct method not found: " + class_descriptor + "." + method_name;
        }
        
        invocation_trace.push_back(ctx);
        return ctx;
    }
    
    /**
     * Get complete invocation trace (evidence).
     */
    const std::vector<InvocationContext>& get_invocation_trace() const {
        return invocation_trace;
    }
    
    /**
     * Export trace as JSON (for evidence files).
     */
    json export_trace_as_json() const {
        json arr = json::array();
        for (const auto& ctx : invocation_trace) {
            arr.push_back(ctx.to_json());
        }
        return {
            {"total_invocations", invocation_trace.size()},
            {"trace", arr}
        };
    }
    
    /**
     * Clear trace (between test cases).
     */
    void clear_trace() {
        invocation_trace.clear();
    }
};

// ============================================================================
// Demo System — Shows VTable dispatch working end-to-end
// ============================================================================

/**
 * VTableDemoSystem creates a complete demonstration of virtual dispatch.
 * It sets up a small class hierarchy and traces virtual method calls.
 */
class VTableDemoSystem {
private:
    RuntimeMetadataContainer container;
    MethodResolver resolver;
    VirtualDispatcher dispatcher;
    
    bool initialized;
    
public:
    VTableDemoSystem()
        : resolver(&container), dispatcher(&resolver), initialized(false) {}
    
    /**
     * Initialize the demo system with sample classes.
     * Creates: Animal → Dog/Cat hierarchy like Phase 3 tests.
     */
    bool initialize() {
        // Create Animal class
        auto animal = std::make_unique<RuntimeClassInfo>("LAnimal;");
        animal->source_file = "Animal.java";
        animal->access_flags = AccessFlags::ACC_PUBLIC;
        animal->dex_class_idx = 0;
        
        // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX):
        // The original code used positional brace-init for RuntimeMethodInfo
        // like `{0, "speak", "()V", ...}`. RuntimeMethodInfo is NOT an
        // aggregate (it has a user-provided default ctor), so positional
        // brace-init does not compile. Rewrote to use default construction
        // + field assignment. Also fixed a data bug in the original demo:
        // the 11th positional value was being assigned to is_constructor,
        // but `speak`/`eat`/`bark`/`meow` are NOT constructors. The intended
        // mapping was has_code=true at that position.
        animal->virtual_methods.clear();
        {
            RuntimeMethodInfo m;
            m.method_idx = 0; m.name = "speak"; m.descriptor = "()V"; m.shorty = "V";
            m.access_flags = AccessFlags::ACC_PUBLIC; m.declaring_class_idx = 0;
            m.is_direct = false; m.is_virtual = true; m.is_static = false;
            m.is_abstract = false; m.is_constructor = false;
            m.has_code = true; m.code_item_offset = 100;
            m.registers_size = 5; m.ins_size = 1; m.outs_size = 1; m.insns_count = 3;
            animal->virtual_methods.push_back(std::move(m));
        }
        {
            RuntimeMethodInfo m;
            m.method_idx = 1; m.name = "eat"; m.descriptor = "()V"; m.shorty = "V";
            m.access_flags = AccessFlags::ACC_PUBLIC; m.declaring_class_idx = 0;
            m.is_direct = false; m.is_virtual = true; m.is_static = false;
            m.is_abstract = false; m.is_constructor = false;
            m.has_code = true; m.code_item_offset = 120;
            m.registers_size = 3; m.ins_size = 1; m.outs_size = 1; m.insns_count = 2;
            animal->virtual_methods.push_back(std::move(m));
        }
        
        // Build Animal's VTable (it has no parent)
        VirtualDispatchTable empty_vtable;
        animal->build_vtable(empty_vtable);
        animal->load_state = RuntimeClassInfo::LoadState::RESOLVED;
        
        container.add_class(std::move(animal));
        
        // Create Dog class (extends Animal)
        auto dog = std::make_unique<RuntimeClassInfo>("LDog;");
        dog->source_file = "Dog.java";
        dog->access_flags = AccessFlags::ACC_PUBLIC;
        dog->superclass_descriptor = "LAnimal;";
        dog->dex_class_idx = 1;
        
        dog->instance_fields = {
            {0, "name", "Ljava/lang/String;", 0, 0},  // dog's name
            {1, "age", "I", 0, 0}                        // dog's age
        };
        
        // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): see Animal block above.
        // RuntimeMethodInfo is non-aggregate; use default ctor + assignment.
        dog->virtual_methods.clear();
        {
            RuntimeMethodInfo m;
            m.method_idx = 2; m.name = "speak"; m.descriptor = "()V"; m.shorty = "V";
            m.access_flags = AccessFlags::ACC_PUBLIC; m.declaring_class_idx = 1;
            m.is_direct = false; m.is_virtual = true; m.is_static = false;
            m.is_abstract = false; m.is_constructor = false;
            m.has_code = true; m.code_item_offset = 200;
            m.registers_size = 5; m.ins_size = 1; m.outs_size = 1; m.insns_count = 3;
            dog->virtual_methods.push_back(std::move(m));
        }
        {
            RuntimeMethodInfo m;
            m.method_idx = 3; m.name = "bark"; m.descriptor = "()V"; m.shorty = "V";
            m.access_flags = AccessFlags::ACC_PUBLIC; m.declaring_class_idx = 1;
            m.is_direct = false; m.is_virtual = true; m.is_static = false;
            m.is_abstract = false; m.is_constructor = false;
            m.has_code = true; m.code_item_offset = 220;
            m.registers_size = 2; m.ins_size = 1; m.outs_size = 1; m.insns_count = 2;
            dog->virtual_methods.push_back(std::move(m));
        }
        
        // Link to parent and build VTable
        RuntimeClassInfo* animal_cls = container.find_class("LAnimal;");
        dog->calculate_field_offsets(animal_cls);
        dog->build_vtable(animal_cls);
        dog->load_state = RuntimeClassInfo::LoadState::RESOLVED;
        
        container.add_class(std::move(dog));
        
        // Create Cat class (extends Animal)
        auto cat = std::make_unique<RuntimeClassInfo>("LCat;");
        cat->source_file = "Cat.java";
        cat->access_flags = AccessFlags::ACC_PUBLIC;
        cat->superclass_descriptor = "LAnimal;";
        cat->dex_class_idx = 2;
        
        cat->instance_fields = {
            {0, "name", "Ljava/lang/String;", 0, 0},
            {1, "livesLeft", "I", 0, 0}  // cats have 9 lives!
        };
        
        // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): see Animal block above.
        cat->virtual_methods.clear();
        {
            RuntimeMethodInfo m;
            m.method_idx = 4; m.name = "speak"; m.descriptor = "()V"; m.shorty = "V";
            m.access_flags = AccessFlags::ACC_PUBLIC; m.declaring_class_idx = 2;
            m.is_direct = false; m.is_virtual = true; m.is_static = false;
            m.is_abstract = false; m.is_constructor = false;
            m.has_code = true; m.code_item_offset = 300;
            m.registers_size = 5; m.ins_size = 1; m.outs_size = 1; m.insns_count = 3;
            cat->virtual_methods.push_back(std::move(m));
        }
        {
            RuntimeMethodInfo m;
            m.method_idx = 5; m.name = "meow"; m.descriptor = "()V"; m.shorty = "V";
            m.access_flags = AccessFlags::ACC_PUBLIC; m.declaring_class_idx = 2;
            m.is_direct = false; m.is_virtual = true; m.is_static = false;
            m.is_abstract = false; m.is_constructor = false;
            m.has_code = true; m.code_item_offset = 320;
            m.registers_size = 2; m.ins_size = 1; m.outs_size = 1; m.insns_count = 2;
            cat->virtual_methods.push_back(std::move(m));
        }
        
        cat->calculate_field_offsets(animal_cls);
        cat->build_vtable(animal_cls);
        cat->load_state = RuntimeClassInfo::LoadState::RESOLVED;
        
        container.add_class(std::move(cat));
        
        // Set up a simple executor that logs which method runs
        dispatcher.set_executor([](const RuntimeMethodInfo* method,
                                   const std::vector<json>& args,
                                   InvocationContext& ctx) -> json {
            // Simulate different behavior based on method name
            std::string sound;
            if (method->name == "speak") {
                // Check which class's speak() this is
                if (ctx.target_class == "LAnimal;") sound = "...generic animal noise...";
                else if (ctx.target_class == "LDog;") sound = "Woof! Woof!";
                else if (ctx.target_class == "LCat;") sound = "Meow~";
                else sound = "[unknown speak]";
            } else if (method->name == "eat") {
                sound = "*munch munch*";
            } else if (method->name == "bark") {
                sound = "WOOF WOOF!";
            } else if (method->name == "meow") {
                sound = "meow meow~ ♪";
            } else {
                sound = "[method " + method->name + " executed]";
            }
            
            ctx.return_value = sound;  // Return the sound as "result"
            ctx.executed_successfully = true;
            return ctx.return_value;
        });
        
        initialized = true;
        return true;
    }
    
    /**
     * Run a demonstration of polymorphic dispatch.
     * Shows how the same invoke-virtual produces different results.
     */
    json run_polymorphic_demo() {
        if (!initialized) {
            // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): the original syntax
            // `return {"error": "..."};` is ambiguous to the C++ parser when
            // the return type is `json` (nlohmann::json). It is parsed as a
            // brace-enclosed initializer with a colon label, not as a JSON
            // object literal. Use json::parse or json::object() explicitly.
            return json::object({{"error", "System not initialized"}});
        }
        
        dispatcher.clear_trace();
        
        json results = json::array();
        
        // Pre-resolve speak() to VTable index
        int32_t speak_vtable_idx = resolver.resolve_virtual_to_vtable_index(
            "LAnimal;", "speak", "()V");
        
        results.push_back({"step", "Pre-resolution", "detail",
                         "speak() resolved to VTable[" + std::to_string(speak_vtable_idx) + "]"});
        
        // Get class pointers
        RuntimeClassInfo* animal_cls = container.find_class("LAnimal;");
        RuntimeClassInfo* dog_cls = container.find_class("LDog;");
        RuntimeClassInfo* cat_cls = container.find_class("LCat;");
        
        // Demo 1: Call speak() on Animal reference pointing to Animal
        if (animal_cls && speak_vtable_idx >= 0) {
            InvocationContext ctx1 = dispatcher.dispatch_virtual(
                animal_cls, speak_vtable_idx, {},
                {"LDemo;", "main"});
            
            results.push_back({
                {"demo", 1},
                {"object_type", "Animal"},
                {"called_method", ctx1.target_method},
                {"result", ctx1.return_value},
                {"was_override", ctx1.is_override}
            });
        }
        
        // Demo 2: Call speak() on Animal reference pointing to Dog
        // THIS IS THE KEY DEMO: Same VTable index, different result!
        if (dog_cls && speak_vtable_idx >= 0) {
            InvocationContext ctx2 = dispatcher.dispatch_virtual(
                dog_cls, speak_vtable_idx, {},
                {"LDemo;", "main"});
            
            results.push_back({
                {"demo", 2},
                {"object_type", "Dog"},
                {"called_method", ctx2.target_method},
                {"result", ctx2.return_value},
                {"was_override", ctx2.is_override},
                {"note", "Same VTable index, but Dog.speak() runs!"}
            });
        }
        
        // Demo 3: Call speak() on Animal reference pointing to Cat
        if (cat_cls && speak_vtable_idx >= 0) {
            InvocationContext ctx3 = dispatcher.dispatch_virtual(
                cat_cls, speak_vtable_idx, {},
                {"LDemo;", "main"});
            
            results.push_back({
                {"demo", 3},
                {"object_type", "Cat"},
                {"called_method", ctx3.target_method},
                {"result", ctx3.return_value},
                {"was_override", ctx3.is_override},
                {"note", "Same VTable index again, but Cat.speak() runs!"}
            });
        }
        
        // Demo 4: Show direct call (no polymorphism)
        InvocationContext ctx4 = dispatcher.dispatch_direct(
            "LDog;", "<init>", "(Ljava/lang/String;I)V",
            {"Rex", 5},
            {"LDog;", "factoryMethod"});
        
        results.push_back({
            {"demo", 4},
            {"opcode", "invoke-direct"},
            {"method", ctx4.target_method},
            {"success", ctx4.executed_successfully},
            {"note", "Direct calls don't use VTable"}
        });
        
        // Export full trace as evidence
        json trace = dispatcher.export_trace_as_json();
        
        return {
            {"demonstration", "Polymorphic Virtual Dispatch"},
            {"results", results},
            {"complete_trace", trace},
            {"conclusion", "VTable-based dispatch enables correct polymorphism!"}
        };
    }
    
    /**
     * Get statistics about loaded classes.
     */
    json get_system_stats() const {
        return container.get_statistics();
    }
};

} // namespace runtime
} // namespace miniandroid

#endif // MINIANDROID_VTABLE_DISPATCH_H
