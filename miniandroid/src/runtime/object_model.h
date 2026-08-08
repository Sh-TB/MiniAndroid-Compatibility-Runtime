/*
 * MiniAndroid Runtime v0.1 - Android Object Model Foundation
 * EXP-004: Android Object Model Foundation
 * 
 * Creates the minimum Android object runtime layer required for HelloWorld execution.
 * Implements:
 *   - RuntimeObject base class
 *   - ClassMetadata with inheritance
 *   - Object ID management
 *   - Type-safe object heap
 *   - Activity/View/TextView runtime objects
 * 
 * Golden Debug Protocol Compliant
 */

#ifndef MINIANDROID_OBJECT_MODEL_H
#define MINIANDROID_OBJECT_MODEL_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <chrono>
#include <functional>
#include <sstream>
#include <iomanip>
#include <optional>
#include <set>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace runtime {

using json = nlohmann::json;

// ============================================================================
// Object Lifetime States (Task #4)
// ============================================================================

enum class ObjectLifetime {
    ALLOCATED,      // Object created, not yet initialized
    INITIALIZING,   // Constructor in progress
    ACTIVE,         // Fully initialized and usable
    FINALIZING,     // Being destroyed
    COLLECTED       // Garbage collected (for tracking)
};

std::string lifetime_to_string(ObjectLifetime state);
ObjectLifetime string_to_lifetime(const std::string& str);

// ============================================================================
// Class Metadata (Task #2)
// ============================================================================

struct MethodMetadata {
    std::string name;
    std::string descriptor;  // e.g., "(Ljava/lang/String;)V"
    bool is_constructor = false;
    bool is_virtual = true;
    bool is_static = false;
    
    json to_json() const {
        json j;
        j["name"] = name;
        j["descriptor"] = descriptor;
        j["is_constructor"] = is_constructor;
        j["is_virtual"] = is_virtual;
        j["is_static"] = is_static;
        return j;
    }
};

struct FieldMetadata {
    std::string name;
    std::string type;        // e.g., "Ljava/lang/String;", "I", "Z"
    bool is_static = false;
    bool is_public = true;
    
    json to_json() const {
        json j;
        j["name"] = name;
        j["type"] = type;
        j["is_static"] = is_static;
        j["is_public"] = is_public;
        return j;
    }
};

class ClassMetadata {
public:
    ClassMetadata() {}
    
    ClassMetadata(const std::string& class_name, 
                  const std::string& parent_class = "",
                  const std::string& descriptor = "")
        : class_name_(class_name)
        , parent_class_(parent_class)
        , descriptor_(descriptor) 
    {}
    
    // Identity
    const std::string& get_class_name() const { return class_name_; }
    const std::string& get_parent_class() const { return parent_class_; }
    const std::string& get_descriptor() const { return descriptor_; }
    
    void set_class_name(const std::string& name) { class_name_ = name; }
    void set_parent_class(const std::string& parent) { parent_class_ = parent; }
    void set_descriptor(const std::string& desc) { descriptor_ = desc; }
    
    // Methods management
    void add_method(const MethodMetadata& method) {
        methods_[method.name] = method;
        method_list_.push_back(method.name);
    }
    
    void add_method(const std::string& name, const std::string& descriptor,
                    bool is_ctor = false, bool is_virtual = true) {
        MethodMetadata m;
        m.name = name;
        m.descriptor = descriptor;
        m.is_constructor = is_ctor;
        m.is_virtual = is_virtual;
        add_method(m);
    }
    
    bool has_method(const std::string& name) const {
        return methods_.count(name) > 0;
    }
    
    std::optional<MethodMetadata> get_method(const std::string& name) const {
        auto it = methods_.find(name);
        if (it != methods_.end()) {
            return it->second;
        }
        return std::nullopt;
    }
    
    const std::vector<std::string>& get_method_list() const { return method_list_; }
    size_t get_method_count() const { return methods_.size(); }
    
    // Fields management
    void add_field(const FieldMetadata& field) {
        fields_[field.name] = field;
        field_list_.push_back(field.name);
    }
    
    void add_field(const std::string& name, const std::string& type,
                   bool is_static = false, bool is_public = true) {
        FieldMetadata f;
        f.name = name;
        f.type = type;
        f.is_static = is_static;
        f.is_public = is_public;
        add_field(f);
    }
    
    bool has_field(const std::string& name) const {
        return fields_.count(name) > 0;
    }
    
    std::optional<FieldMetadata> get_field(const std::string& name) const {
        auto it = fields_.find(name);
        if (it != fields_.end()) {
            return it->second;
        }
        return std::nullopt;
    }
    
    const std::vector<std::string>& get_field_list() const { return field_list_; }
    size_t get_field_count() const { return fields_.size(); }
    
    // Inheritance helpers
    bool has_parent() const { return !parent_class_.empty(); }
    bool is_derived_from(const std::string& base_class) const {
        if (class_name_ == base_class) return true;
        if (parent_class_.empty()) return false;
        // Would need registry for full check
        return parent_class_ == base_class;
    }
    
    // Serialization
    json to_json() const {
        json j;
        j["class_name"] = class_name_;
        j["descriptor"] = descriptor_;
        j["parent_class"] = parent_class_;
        
        json methods_arr = json::array();
        for (const auto& name : method_list_) {
            if (methods_.count(name)) {
                methods_arr.push_back(methods_.at(name).to_json());
            }
        }
        j["methods"] = methods_arr;
        
        json fields_arr = json::array();
        for (const auto& name : field_list_) {
            if (fields_.count(name)) {
                fields_arr.push_back(fields_.at(name).to_json());
            }
        }
        j["fields"] = fields_arr;
        
        j["method_count"] = get_method_count();
        j["field_count"] = get_field_count();
        
        return j;
    }

private:
    std::string class_name_;
    std::string parent_class_;
    std::string descriptor_;
    
    std::map<std::string, MethodMetadata> methods_;
    std::vector<std::string> method_list_;
    
    std::map<std::string, FieldMetadata> fields_;
    std::vector<std::string> field_list_;
};

// ============================================================================
// RuntimeObject Base (Task #1)
// ============================================================================

/**
 * Base class for all runtime objects in MiniAndroid.
 * Every object created during DEX execution derives from this.
 */
class RuntimeObject {
public:
    virtual ~RuntimeObject() = default;
    
    // Object identity
    uint32_t get_object_id() const { return object_id_; }
    const std::string& get_runtime_class() const { return runtime_class_; }
    const std::string& get_class_descriptor() const { return class_descriptor_; }
    
    // Lifetime management
    ObjectLifetime get_lifetime() const { return lifetime_; }
    void set_lifetime(ObjectLifetime state) { lifetime_ = state; }
    
    bool is_active() const { return lifetime_ == ObjectLifetime::ACTIVE; }
    bool is_initialized() const { 
        return lifetime_ == ObjectLifetime::ACTIVE || 
               lifetime_ == ObjectLifetime::FINALIZING; 
    }
    
    // Creation metadata
    uint64_t get_creation_time() const { return creation_timestamp_; }
    uint32_t get_creator_pc() const { return creator_pc_; }
    uint64_t get_creation_sequence() const { return creation_sequence_; }
    
    // Type checking
    virtual bool is_instance_of(const std::string& class_name) const {
        return runtime_class_ == class_name;
    }
    
    virtual bool is_kind_of(const std::string& base_class) const {
        // Override in derived classes for proper inheritance
        return runtime_class_ == base_class;
    }
    
    // String representation
    virtual std::string to_string() const {
        std::ostringstream oss;
        oss << "RuntimeObject[id=" << object_id_ 
            << ", class=" << runtime_class_
            << ", state=" << lifetime_to_string(lifetime_)
            << "]";
        return oss.str();
    }
    
    // JSON serialization for evidence
    virtual json to_json() const {
        json obj;
        obj["object_id"] = object_id_;
        obj["runtime_class"] = runtime_class_;
        obj["class_descriptor"] = class_descriptor_;
        obj["lifetime_state"] = lifetime_to_string(lifetime_);
        obj["creation_timestamp"] = creation_timestamp_;
        obj["creator_pc"] = creator_pc_;
        obj["creation_sequence"] = creation_sequence_;
        obj["is_initialized"] = is_initialized();
        return obj;
    }
    
protected:
    RuntimeObject(uint32_t id, const std::string& cls, const std::string& desc,
                 uint32_t pc, uint64_t seq)
        : object_id_(id)
        , runtime_class_(cls)
        , class_descriptor_(desc)
        , creator_pc_(pc)
        , creation_sequence_(seq)
        , lifetime_(ObjectLifetime::ALLOCATED)
    {
        creation_timestamp_ = static_cast<uint64_t>(
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()
            ).count()
        );
    }
    
    void set_runtime_class(const std::string& cls) { runtime_class_ = cls; }
    
private:
    uint32_t object_id_;
    std::string runtime_class_;
    std::string class_descriptor_;
    
    ObjectLifetime lifetime_;
    uint64_t creation_timestamp_;
    uint32_t creator_pc_;
    uint64_t creation_sequence_;
};

// ============================================================================
// Object ID Manager (Task #1)
// ============================================================================

class ObjectIdManager {
public:
    ObjectIdManager() : next_id_(1), total_allocated_(0), total_freed_(0) {}
    
    uint32_t allocate_id() {
        uint32_t id = next_id_++;
        total_allocated_++;
        active_ids_.insert(id);
        allocation_log_.push_back({id, "ALLOCATED"});
        return id;
    }
    
    void free_id(uint32_t id) {
        if (active_ids_.erase(id) > 0) {
            total_freed_++;
            allocation_log_.push_back({id, "FREED"});
        }
    }
    
    bool is_active(uint32_t id) const {
        return active_ids_.count(id) > 0;
    }
    
    size_t get_active_count() const { return active_ids_.size(); }
    uint32_t get_total_allocated() const { return total_allocated_; }
    uint32_t get_total_freed() const { return total_freed_; }
    
    std::vector<uint32_t> get_all_active_ids() const {
        return std::vector<uint32_t>(active_ids_.begin(), active_ids_.end());
    }
    
    json to_json() const {
        json j;
        j["next_id"] = next_id_;
        j["total_allocated"] = total_allocated_;
        j["total_freed"] = total_freed_;
        j["active_count"] = get_active_count();
        
        json log = json::array();
        for (const auto& entry : allocation_log_) {
            json e;
            e["object_id"] = entry.first;
            e["action"] = entry.second;
            log.push_back(e);
        }
        j["allocation_log"] = log;
        
        return j;
    }

private:
    uint32_t next_id_;
    uint32_t total_allocated_;
    uint32_t total_freed_;
    std::set<uint32_t> active_ids_;
    std::vector<std::pair<uint32_t, std::string>> allocation_log_;
};

// ============================================================================
// Enhanced ObjectHeap (Task #4)
// ============================================================================

struct AllocationRecord {
    uint32_t object_id;
    std::string class_descriptor;
    uint32_t pc;
    uint64_t sequence;
    uint64_t timestamp_ms;
    ObjectLifetime final_state;
    
    json to_json() const {
        json j;
        j["object_id"] = object_id;
        j["class_descriptor"] = class_descriptor;
        j["pc_hex"] = "0x" + [&]() {
            std::ostringstream oss;
            oss << std::hex << pc;
            return oss.str();
        }();
        j["sequence"] = sequence;
        j["timestamp_ms"] = timestamp_ms;
        j["final_state"] = lifetime_to_string(final_state);
        return j;
    }
};

class EnhancedObjectHeap {
public:
    EnhancedObjectHeap() : allocation_sequence_(0) {}
    
    /**
     * Allocate a new runtime object
     */
    template<typename T, typename... Args>
    T* allocate(const std::string& class_desc, uint32_t pc, Args&&... args) {
        uint32_t id = id_manager_.allocate_id();
        ++allocation_sequence_;
        
        T* obj = new T(id, class_desc, pc, allocation_sequence_, 
                       std::forward<Args>(args)...);
        
        objects_[id] = std::unique_ptr<RuntimeObject>(obj);
        
        AllocationRecord record;
        record.object_id = id;
        record.class_descriptor = class_desc;
        record.pc = pc;
        record.sequence = allocation_sequence_;
        record.timestamp_ms = static_cast<uint64_t>(
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()
            ).count()
        );
        record.final_state = ObjectLifetime::ALLOCATED;
        
        allocation_history_[id] = record;
        
        return obj;
    }
    
    /**
     * Register externally created object
     */
    void register_object(std::unique_ptr<RuntimeObject> obj, uint32_t pc) {
        uint32_t id = obj->get_object_id();
        ++allocation_sequence_;
        
        objects_[id] = std::move(obj);
        
        AllocationRecord record;
        record.object_id = id;
        record.class_descriptor = objects_[id]->get_class_descriptor();
        record.pc = pc;
        record.sequence = allocation_sequence_;
        record.timestamp_ms = static_cast<uint64_t>(
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()
            ).count()
        );
        record.final_state = ObjectLifetime::ALLOCATED;
        
        allocation_history_[id] = record;
    }
    
    /**
     * Get object by ID with type casting
     */
    template<typename T>
    T* get_as(uint32_t id) {
        auto it = objects_.find(id);
        if (it != objects_.end()) {
            return dynamic_cast<T*>(it->second.get());
        }
        return nullptr;
    }
    
    /**
     * Get raw object pointer
     */
    RuntimeObject* get(uint32_t id) {
        auto it = objects_.find(id);
        if (it != objects_.end()) {
            return it->second.get();
        }
        return nullptr;
    }
    
    const RuntimeObject* get(uint32_t id) const {
        auto it = objects_.find(id);
        if (it != objects_.end()) {
            return it->second.get();
        }
        return nullptr;
    }
    
    /**
     * Check if object exists and is of expected type
     */
    bool is_type(uint32_t id, const std::string& expected_class) const {
        auto* obj = get(id);
        if (!obj) return false;
        return obj->is_instance_of(expected_class);
    }
    
    /**
     * Update object lifetime state
     */
    void set_lifetime(uint32_t id, ObjectLifetime state) {
        auto* obj = get(id);
        if (obj) {
            obj->set_lifetime(state);
        }
        if (allocation_history_.count(id)) {
            allocation_history_[id].final_state = state;
        }
    }
    
    /**
     * Free an object
     */
    void free(uint32_t id) {
        set_lifetime(id, ObjectLifetime::COLLECTED);
        objects_.erase(id);
        id_manager_.free_id(id);
    }
    
    // Query methods
    size_t size() const { return objects_.size(); }
    bool contains(uint32_t id) const { return objects_.count(id) > 0; }
    
    std::vector<uint32_t> get_all_ids() const {
        std::vector<uint32_t> ids;
        for (const auto& pair : objects_) {
            ids.push_back(pair.first);
        }
        return ids;
    }
    
    std::vector<uint32_t> get_objects_by_class(const std::string& cls) const {
        std::vector<uint32_t> result;
        for (const auto& pair : objects_) {
            if (pair.second->get_runtime_class() == cls) {
                result.push_back(pair.first);
            }
        }
        return result;
    }
    
    // Statistics
    const ObjectIdManager& get_id_manager() const { return id_manager_; }
    uint64_t get_allocation_sequence() const { return allocation_sequence_; }
    
    // Serialization
    json dump_objects() const {
        json arr = json::array();
        for (const auto& pair : objects_) {
            arr.push_back(pair.second->to_json());
        }
        return arr;
    }
    
    json dump_allocations() const {
        json arr = json::array();
        for (const auto& pair : allocation_history_) {
            arr.push_back(pair.second.to_json());
        }
        return arr;
    }
    
    json to_full_report() const {
        json report;
        report["heap_size"] = size();
        report["total_allocated"] = id_manager_.get_total_allocated();
        report["total_freed"] = id_manager_.get_total_freed();
        report["active_objects"] = id_manager_.get_active_count();
        report["allocation_sequence"] = allocation_sequence_;
        report["objects"] = dump_objects();
        report["allocation_history"] = dump_allocations();
        report["id_manager"] = id_manager_.to_json();
        return report;
    }

private:
    std::map<uint32_t, std::unique_ptr<RuntimeObject>> objects_;
    ObjectIdManager id_manager_;
    uint64_t allocation_sequence_;
    std::map<uint32_t, AllocationRecord> allocation_history_;
};

// ============================================================================
// Inheritance Chain Registry (Task #3)
// ============================================================================

struct InheritanceNode {
    std::string class_name;
    std::string parent_class;
    std::string descriptor;
    int depth = 0;  // Distance from root (java.lang.Object = 0)
    
    json to_json() const {
        json j;
        j["class_name"] = class_name;
        j["parent_class"] = parent_class;
        j["descriptor"] = descriptor;
        j["depth"] = depth;
        return j;
    }
};

struct InheritancePath {
    std::string from_class;
    std::string to_class;
    std::vector<std::string> path;
    bool found = false;
    
    json to_json() const {
        json j;
        j["from"] = from_class;
        j["to"] = to_class;
        j["path"] = path;
        j["found"] = found;
        j["length"] = path.size();
        return j;
    }
};

class InheritanceRegistry {
public:
    InheritanceRegistry() {
        // Initialize with Java/Android core hierarchy
        initialize_core_hierarchy();
    }
    
    void register_class(const std::string& class_name, 
                        const std::string& parent_class,
                        const std::string& descriptor = "") {
        classes_[class_name] = {class_name, parent_class, descriptor, 0};
        recalculate_depths();
    }
    
    bool has_class(const std::string& class_name) const {
        return classes_.count(class_name) > 0;
    }
    
    std::optional<InheritanceNode> get_class(const std::string& class_name) const {
        auto it = classes_.find(class_name);
        if (it != classes_.end()) {
            return it->second;
        }
        return std::nullopt;
    }
    
    std::string get_parent(const std::string& class_name) const {
        auto node = get_class(class_name);
        if (node) {
            return node->parent_class;
        }
        return "";
    }
    
    /**
     * Get full inheritance chain from this class to java.lang.Object
     */
    std::vector<std::string> get_chain(const std::string& class_name) const {
        std::vector<std::string> chain;
        std::string current = class_name;
        
        while (!current.empty() && classes_.count(current)) {
            chain.push_back(current);
            current = classes_.at(current).parent_class;
            
            // Prevent infinite loops
            if (chain.size() > 20) break;
        }
        
        return chain;
    }
    
    /**
     * Check if 'derived' is a subclass of 'base'
     */
    bool is_subclass(const std::string& derived, const std::string& base) const {
        std::string current = derived;
        int guard = 0;
        
        while (!current.empty() && guard < 30) {
            if (current == base) return true;
            
            auto it = classes_.find(current);
            if (it == classes_.end()) break;
            
            current = it->second.parent_class;
            guard++;
        }
        
        return false;
    }
    
    /**
     * Find path between two classes
     */
    InheritancePath find_path(const std::string& from, const std::string& to) const {
        InheritancePath result;
        result.from_class = from;
        result.to_class = to;
        
        std::string current = from;
        while (!current.empty()) {
            result.path.push_back(current);
            if (current == to) {
                result.found = true;
                break;
            }
            
            auto it = classes_.find(current);
            if (it == classes_.end()) break;
            current = it->second.parent_class;
            
            if (result.path.size() > 20) break;
        }
        
        return result;
    }
    
    // Get all registered classes
    std::vector<std::string> get_all_classes() const {
        std::vector<std::string> result;
        for (const auto& pair : classes_) {
            result.push_back(pair.first);
        }
        return result;
    }
    
    size_t get_class_count() const { return classes_.size(); }
    
    // Serialization
    json to_json() const {
        json j;
        j["registry_name"] = "Android_Inheritance_Registry";
        j["class_count"] = get_class_count();
        
        json classes_arr = json::array();
        for (const auto& pair : classes_) {
            classes_arr.push_back(pair.second.to_json());
        }
        j["classes"] = classes_arr;
        
        return j;
    }
    
    json trace_inheritance(const std::string& class_name) const {
        json trace;
        trace["target_class"] = class_name;
        trace["chain"] = get_chain(class_name);
        
        json details = json::array();
        auto chain = get_chain(class_name);
        for (size_t i = 0; i < chain.size(); i++) {
            json node;
            node["position"] = i;
            node["class"] = chain[i];
            if (i < chain.size() - 1) {
                node["inherits_from"] = chain[i + 1];
            } else {
                node["inherits_from"] = "(root)";
            }
            details.push_back(node);
        }
        trace["details"] = details;
        
        return trace;
    }

private:
    std::map<std::string, InheritanceNode> classes_;
    
    void initialize_core_hierarchy() {
        // Java foundation
        register_class("java.lang.Object", "", "Ljava/lang/Object;");
        
        // Android framework
        register_class("android.content.Context", "java.lang.Object", "Landroid/content/Context;");
        register_class("android.app.Activity", "android.content.Context", "Landroid/app/Activity;");
        
        // View hierarchy
        register_class("android.view.View", "java.lang.Object", "Landroid/view/View;");
        register_class("android.view.ViewGroup", "android.view.View", "Landroid/view/ViewGroup;");
        register_class("android.widget.TextView", "android.view.View", "Landroid/widget/TextView;");
        
        recalculate_depths();
    }
    
    void recalculate_depths() {
        for (auto& pair : classes_) {
            pair.second.depth = calculate_depth(pair.first);
        }
    }
    
    int calculate_depth(const std::string& class_name) const {
        std::string current = class_name;
        int depth = 0;
        int guard = 0;
        
        while (!current.empty() && guard < 30) {
            auto it = classes_.find(current);
            if (it == classes_.end()) break;
            current = it->second.parent_class;
            depth++;
            guard++;
        }
        
        return depth;
    }
};

// ============================================================================
// Activity Runtime Object (Task #5)
// ============================================================================

enum class RuntimeActivityState {
    UNINITIALIZED,
    CREATED,
    STARTED,
    RESUMED,
    PAUSED,
    STOPPED,
    DESTROYED
};

std::string activity_state_to_string(RuntimeActivityState state);

class ActivityRuntimeObject : public RuntimeObject {
public:
    ActivityRuntimeObject(uint32_t id, const std::string& desc, 
                         uint32_t pc, uint64_t seq)
        : RuntimeObject(id, "android.app.Activity", desc, pc, seq)
        , activity_state_(RuntimeActivityState::UNINITIALIZED)
        , context_ref_(0)
        , created_flag_(false)
    {}
    
    // State management
    RuntimeActivityState get_activity_state() const { return activity_state_; }
    void set_activity_state(RuntimeActivityState state) { activity_state_ = state; }
    
    // Context reference
    uint32_t get_context_reference() const { return context_ref_; }
    void set_context_reference(uint32_t ctx_id) { context_ref_ = ctx_id; }
    
    // Lifecycle flags
    bool is_created() const { return created_flag_; }
    void mark_created() { 
        created_flag_ = true; 
        activity_state_ = RuntimeActivityState::CREATED;
        set_lifetime(ObjectLifetime::ACTIVE);
    }
    
    // Content view
    uint32_t get_content_view_id() const { return content_view_id_; }
    void set_content_view_id(uint32_t view_id) { content_view_id_ = view_id; }
    
    // Type checking overrides
    bool is_instance_of(const std::string& class_name) const override {
        if (class_name == "android.app.Activity") return true;
        if (class_name == "android.content.Context") return true;
        if (class_name == "java.lang.Object") return true;
        return RuntimeObject::is_instance_of(class_name);
    }
    
    bool is_kind_of(const std::string& base_class) const override {
        return is_instance_of(base_class);
    }
    
    // Serialization
    json to_json() const override {
        json obj = RuntimeObject::to_json();
        obj["activity_state"] = activity_state_to_string(activity_state_);
        obj["context_reference"] = context_ref_;
        obj["created_flag"] = created_flag_;
        obj["content_view_id"] = content_view_id_;
        return obj;
    }
    
    std::string to_string() const override {
        std::ostringstream oss;
        oss << "ActivityRuntimeObject[id=" << get_object_id()
            << ", state=" << activity_state_to_string(activity_state_)
            << ", created=" << (created_flag_ ? "true" : "false")
            << "]";
        return oss.str();
    }

private:
    RuntimeActivityState activity_state_;
    uint32_t context_ref_;
    bool created_flag_;
    uint32_t content_view_id_ = 0;
};

// ============================================================================
// View Base Runtime Object (Task #6)
// ============================================================================

enum class RuntimeViewVisibility {
    VISIBLE,
    INVISIBLE,
    GONE
};

std::string visibility_to_string(RuntimeViewVisibility vis);

class ViewRuntimeObject : public RuntimeObject {
public:
    ViewRuntimeObject(uint32_t id, const std::string& desc,
                     uint32_t pc, uint64_t seq)
        : RuntimeObject(id, "android.view.View", desc, pc, seq)
        , visibility_(RuntimeViewVisibility::VISIBLE)
        , invalidated_(false)
        , parent_ref_(0)
        , left_(0), top_(0), width_(0), height_(0)
    {}
    
    // Visibility
    RuntimeViewVisibility get_visibility() const { return visibility_; }
    void set_visibility(RuntimeViewVisibility v) { visibility_ = v; }
    
    // Invalidation tracking
    bool is_invalidated() const { return invalidated_; }
    void invalidate() { invalidated_ = true; }
    void validate() { invalidated_ = false; }
    
    // Parent reference
    uint32_t get_parent_reference() const { return parent_ref_; }
    void set_parent_reference(uint32_t parent_id) { parent_ref_ = parent_id; }
    
    // Geometry
    struct Geometry { int left, top, width, height; };
    Geometry get_geometry() const { return {left_, top_, width_, height_}; }
    void set_geometry(int l, int t, int w, int h) {
        left_ = l; top_ = t; width_ = w; height_ = h;
    }
    
    // Type checking
    bool is_instance_of(const std::string& class_name) const override {
        if (class_name == "android.view.View") return true;
        if (class_name == "java.lang.Object") return true;
        return RuntimeObject::is_instance_of(class_name);
    }
    
    bool is_kind_of(const std::string& base_class) const override {
        return is_instance_of(base_class);
    }
    
    // Serialization
    json to_json() const override {
        json obj = RuntimeObject::to_json();
        obj["visibility"] = visibility_to_string(visibility_);
        obj["is_invalidated"] = invalidated_;
        obj["parent_reference"] = parent_ref_;
        obj["geometry"] = {
            {"left", left_},
            {"top", top_},
            {"width", width_},
            {"height", height_}
        };
        return obj;
    }
    
    std::string to_string() const override {
        std::ostringstream oss;
        oss << "ViewRuntimeObject[id=" << get_object_id()
            << ", visible=" << visibility_to_string(visibility_)
            << ", invalid=" << (invalidated_ ? "true" : "false")
            << "]";
        return oss.str();
    }

private:
    RuntimeViewVisibility visibility_;
    bool invalidated_;
    uint32_t parent_ref_;
    int left_, top_, width_, height_;
};

// ============================================================================
// TextView Runtime Object (Task #7)
// ============================================================================

class TextViewRuntimeObject : public ViewRuntimeObject {
public:
    TextViewRuntimeObject(uint32_t id, const std::string& desc,
                         uint32_t pc, uint64_t seq)
        : ViewRuntimeObject(id, desc, pc, seq)
        , text_color_(0xFF000000)
        , text_size_(16.0f)
    {
        set_runtime_class("android.widget.TextView");
    }
    
    // Text property (main feature for HelloWorld)
    const std::string& get_text() const { return text_; }
    
    void set_text(const std::string& text) {
        text_ = text;
        invalidate();  // Text change requires redraw
    }
    
    // Text styling
    uint32_t get_text_color() const { return text_color_; }
    void set_text_color(uint32_t color) { text_color_ = color; }
    
    float get_text_size() const { return text_size_; }
    void set_text_size(float size) { text_size_ = size; }
    
    // Type checking
    bool is_instance_of(const std::string& class_name) const override {
        if (class_name == "android.widget.TextView") return true;
        if (class_name == "android.view.View") return true;
        if (class_name == "java.lang.Object") return true;
        return ViewRuntimeObject::is_instance_of(class_name);
    }
    
    bool is_kind_of(const std::string& base_class) const override {
        return is_instance_of(base_class);
    }
    
    // Serialization
    json to_json() const override {
        json obj = ViewRuntimeObject::to_json();
        obj["text"] = text_;
        obj["text_color_hex"] = [&]() {
            std::ostringstream oss;
            oss << "#" << std::hex << std::setw(8) << std::setfill('0') << text_color_;
            return oss.str();
        }();
        obj["text_size"] = text_size_;
        return obj;
    }
    
    std::string to_string() const override {
        std::ostringstream oss;
        oss << "TextViewRuntimeObject[id=" << get_object_id()
            << ", text=\"" << text_ << "\""
            << ", visible=" << visibility_to_string(get_visibility())
            << "]";
        return oss.str();
    }

private:
    std::string text_;
    uint32_t text_color_;
    float text_size_;
};

// ============================================================================
// Helper Functions
// ============================================================================

inline std::string lifetime_to_string(ObjectLifetime state) {
    switch (state) {
        case ObjectLifetime::ALLOCATED: return "ALLOCATED";
        case ObjectLifetime::INITIALIZING: return "INITIALIZING";
        case ObjectLifetime::ACTIVE: return "ACTIVE";
        case ObjectLifetime::FINALIZING: return "FINALIZING";
        case ObjectLifetime::COLLECTED: return "COLLECTED";
        default: return "UNKNOWN";
    }
}

inline ObjectLifetime string_to_lifetime(const std::string& str) {
    if (str == "ALLOCATED") return ObjectLifetime::ALLOCATED;
    if (str == "INITIALIZING") return ObjectLifetime::INITIALIZING;
    if (str == "ACTIVE") return ObjectLifetime::ACTIVE;
    if (str == "FINALIZING") return ObjectLifetime::FINALIZING;
    if (str == "COLLECTED") return ObjectLifetime::COLLECTED;
    return ObjectLifetime::ALLOCATED;
}

inline std::string activity_state_to_string(RuntimeActivityState state) {
    switch (state) {
        case RuntimeActivityState::UNINITIALIZED: return "UNINITIALIZED";
        case RuntimeActivityState::CREATED: return "CREATED";
        case RuntimeActivityState::STARTED: return "STARTED";
        case RuntimeActivityState::RESUMED: return "RESUMED";
        case RuntimeActivityState::PAUSED: return "PAUSED";
        case RuntimeActivityState::STOPPED: return "STOPPED";
        case RuntimeActivityState::DESTROYED: return "DESTROYED";
        default: return "UNKNOWN";
    }
}

inline std::string visibility_to_string(RuntimeViewVisibility vis) {
    switch (vis) {
        case RuntimeViewVisibility::VISIBLE: return "VISIBLE";
        case RuntimeViewVisibility::INVISIBLE: return "INVISIBLE";
        case RuntimeViewVisibility::GONE: return "GONE";
        default: return "UNKNOWN";
    }
}

} // namespace runtime
} // namespace miniandroid

#endif // MINIANDROID_OBJECT_MODEL_H
