// SPDX-License-Identifier: MIT
// MiniAndroid Compatibility Runtime
// EXP-051 — HeapAllocator adapter that bridges DalvikHeap → ShadowRegistry
//
// DalvikHeap::allocate() takes (class_desc, pc, frame_id). The shadow
// registry doesn't know about pc or frame_id — it just wants a heap
// object_id. This adapter wraps DalvikHeap so shadows can call
// allocate("Lfoo/Bar;") and get back an id.

#ifndef MINIANDROID_FRAMEWORK_HEAP_ADAPTER_H
#define MINIANDROID_FRAMEWORK_HEAP_ADAPTER_H

#include "shadow_registry.h"
#include "../dex/dalvik_engine.h"

namespace miniandroid { namespace framework {

class DalvikHeapAdapter : public HeapAllocator {
public:
    explicit DalvikHeapAdapter(dalvik::DalvikHeap* heap,
                              dalvik::DalvikExecutionEngine* engine = nullptr)
        : heap_(heap), engine_(engine) {}

    uint32_t allocate(const std::string& class_desc) override {
        if (!heap_) return 0;
        // Allocate with pc=0 and frame_id=0 — the allocation log entry
        // will indicate this came from the shadow registry (not from a
        // specific bytecode location).
        return heap_->allocate(class_desc, /*pc=*/0, /*frame_id=*/0);
    }

    uint32_t get_singleton(const std::string& class_desc) override {
        if (!engine_) return 0;
        // Use the engine's singleton cache. We go through the engine's
        // public get_or_create_singleton_public() method so the cache
        // stays consistent across both legacy bridge and shadow dispatch.
        auto v = engine_->get_or_create_singleton_public(class_desc);
        return v.object_id;
    }

    uint32_t get_or_create(const std::string& class_desc) override {
        if (engine_) {
            auto v = engine_->get_or_create_singleton_public(class_desc);
            return v.object_id;
        }
        // Fall back to a plain allocate if no engine is set.
        return allocate(class_desc);
    }

    bool has_object(uint32_t object_id) override {
        if (!heap_) return false;
        return heap_->has_object(object_id);
    }

private:
    dalvik::DalvikHeap* heap_;
    dalvik::DalvikExecutionEngine* engine_;
};

}} // namespace miniandroid::framework

#endif // MINIANDROID_FRAMEWORK_HEAP_ADAPTER_H
