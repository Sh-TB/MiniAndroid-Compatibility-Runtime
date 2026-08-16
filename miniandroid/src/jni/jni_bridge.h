/*
 * MiniAndroid Runtime — JNI Bridge
 * EXP-046 Phase 2: Native method dispatch via host-side handlers
 *
 * Architecture:
 *   Dalvik engine encounters native method (access_flags & ACC_NATIVE)
 *   → invoke-* handler calls JNIBridge::invoke()
 *   → JNIBridge looks up handler in registry
 *   → handler returns DalvikValue
 *
 * All native methods are HOST_COMPATIBILITY_STUB unless they have a
 * real native library implementation.
 */

#ifndef MINIANDROID_JNI_BRIDGE_H
#define MINIANDROID_JNI_BRIDGE_H

#include <string>
#include <vector>
#include <map>
#include <functional>
#include <iostream>
#include <chrono>
#include <cstdint>

namespace miniandroid {
namespace jni {

// Forward declare DalvikValue to avoid circular dependency
struct NativeCallContext {
    std::string class_desc;
    std::string method_name;
    std::string signature;
    std::vector<int32_t> int_args;
    std::vector<std::string> string_args;
    std::vector<uint32_t> object_args;
};

enum class NativeImplType {
    HOST_COMPATIBILITY_STUB,
    REAL_NATIVE_LIBRARY,
    UNSUPPORTED_NATIVE,
};

using NativeHandler = std::function<void(
    const NativeCallContext& ctx,
    int32_t& int_result,
    int64_t& long_result,
    float& float_result,
    double& double_result,
    std::string& string_result,
    uint32_t& object_result,
    bool& is_object_result
)>;

struct NativeMethodEntry {
    std::string class_desc;
    std::string method_name;
    std::string signature;
    NativeHandler handler;
    NativeImplType impl_type;
    std::string description;
};

class JNIBridge {
public:
    static JNIBridge& instance() {
        static JNIBridge inst;
        return inst;
    }

    void register_native(
        const std::string& class_desc,
        const std::string& method_name,
        const std::string& signature,
        NativeHandler handler,
        NativeImplType impl_type = NativeImplType::HOST_COMPATIBILITY_STUB,
        const std::string& description = ""
    ) {
        std::string key = make_key(class_desc, method_name);
        methods_[key] = {class_desc, method_name, signature, handler, impl_type, description};
    }

    bool has_handler(const std::string& class_desc, const std::string& method_name) const {
        return methods_.find(make_key(class_desc, method_name)) != methods_.end();
    }

    bool invoke(const NativeCallContext& ctx, int32_t& int_ret, int64_t& long_ret,
                float& float_ret, double& double_ret, std::string& string_ret,
                uint32_t& obj_ret, bool& is_obj_ret) {
        std::string key = make_key(ctx.class_desc, ctx.method_name);
        auto it = methods_.find(key);
        if (it == methods_.end()) {
            log_unsupported(ctx);
            int_ret = 0;
            long_ret = 0;
            float_ret = 0.0f;
            double_ret = 0.0;
            is_obj_ret = false;
            return false;
        }
        log_native_call(it->second, ctx);
        it->second.handler(ctx, int_ret, long_ret, float_ret, double_ret, string_ret, obj_ret, is_obj_ret);
        return true;
    }

    void register_default_stubs() {
        // ConnectionsManager.native_getCurrentTime(I)I
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_getCurrentTime", "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                auto now = std::chrono::system_clock::now();
                ir = static_cast<int32_t>(std::chrono::duration_cast<std::chrono::seconds>(
                    now.time_since_epoch()).count());
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns real Unix timestamp");

        // ConnectionsManager.native_getCurrentTimeMillis()J
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_getCurrentTimeMillis", "()J",
            [](const NativeCallContext&, int32_t&, int64_t& lr, float&, double&, std::string&, uint32_t&, bool&) {
                auto now = std::chrono::system_clock::now();
                lr = std::chrono::duration_cast<std::chrono::milliseconds>(
                    now.time_since_epoch()).count();
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns real Unix time in ms");

        // ConnectionsManager.native_getTimeDifference(I)I
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_getTimeDifference", "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                ir = 0;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns 0 (no NTP sync)");

        // ConnectionsManager.native_getCurrentPingTime(I)I
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_getCurrentPingTime", "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                ir = 0;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns 0 (no connection)");

        // ConnectionsManager.native_getCurrentDatacenterId(I)I
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_getCurrentDatacenterId", "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                ir = -1;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns -1 (not connected)");

        // ConnectionsManager.native_getConnectionState(I)I
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_getConnectionState", "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                ir = 0;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns 0 (DISCONNECTED)");

        // ConnectionsManager.native_init(I)I
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_init", "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                ir = 0;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns 0 (stub init)");

        // ConnectionsManager.native_setJava(Z)V
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_setJava", "(Z)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB, "No-op");

        // ConnectionsManager.native_isTestBackend(I)Z
        register_native("Lorg/telegram/tgnet/ConnectionsManager;", "native_isTestBackend", "(I)Z",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                ir = 0;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns false");

        // NativeLoader.init(Ljava/lang/String;Z)V
        register_native("Lorg/telegram/messenger/NativeLoader;", "init", "(Ljava/lang/String;Z)V",
            [](const NativeCallContext& ctx, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                std::string lib = ctx.string_args.empty() ? "" : ctx.string_args[0];
                std::cerr << "[JNI] NativeLoader.init(\"" << lib << "\") — stub success" << std::endl;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Library 'loaded' as host stub");

        // NativeByteBuffer.native_free(I)V
        register_native("Lorg/telegram/tgnet/NativeByteBuffer;", "native_free", "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB, "No-op");

        // NativeByteBuffer.native_limit(I)I
        register_native("Lorg/telegram/tgnet/NativeByteBuffer;", "native_limit", "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {
                ir = 0;
            }, NativeImplType::HOST_COMPATIBILITY_STUB, "Returns 0");
    }

    size_t registered_count() const { return methods_.size(); }

private:
    std::map<std::string, NativeMethodEntry> methods_;
    size_t unsupported_count_ = 0;

    static std::string make_key(const std::string& cls, const std::string& mth) {
        return cls + "." + mth;
    }

    void log_native_call(const NativeMethodEntry& entry, const NativeCallContext& ctx) {
        static thread_local uint64_t count = 0;
        if (count < 50) {
            std::cerr << "[JNI-CALL] " << entry.class_desc << "." << entry.method_name
                      << " args=" << ctx.int_args.size() << "/" << ctx.string_args.size()
                      << " type=" << (entry.impl_type == NativeImplType::HOST_COMPATIBILITY_STUB ? "HOST_STUB" : "OTHER")
                      << std::endl;
            count++;
        }
    }

    void log_unsupported(const NativeCallContext& ctx) {
        static thread_local uint64_t count = 0;
        unsupported_count_++;
        if (count < 20) {
            std::cerr << "[JNI-UNSUPPORTED] " << ctx.class_desc << "." << ctx.method_name
                      << " — no handler registered" << std::endl;
            count++;
        }
    }
};

} // namespace jni
} // namespace miniandroid

#endif
