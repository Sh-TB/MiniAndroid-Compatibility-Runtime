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

    // ── S108 ROOT-017: positional typed args ────────────────────────────
    // The legacy vectors above are UNPOSITIONED (int/string/object each go
    // to their own list, positions are lost) and INT64 args were TRUNCATED
    // to int32 at the marshalling site — impossible to pass a JNI pointer
    // handle through. `pos` preserves the original argument order + full
    // 64-bit precision; new handlers should read this one.
    struct Arg {
        enum class Kind { INT, LONG, FLOAT, DOUBLE, STRING, OBJECT, NULLREF, BOOLEAN } kind;
        int32_t int_val = 0;
        int64_t long_val = 0;
        float float_val = 0.0f;
        double double_val = 0.0;
        bool bool_val = false;
        std::string string_val;
        uint32_t object_id = 0;

        static Arg of_int(int32_t v) { Arg a; a.kind = Kind::INT; a.int_val = v; return a; }
        static Arg of_long(int64_t v) { Arg a; a.kind = Kind::LONG; a.long_val = v; return a; }
        static Arg of_bool(bool v) { Arg a; a.kind = Kind::BOOLEAN; a.bool_val = v; a.int_val = v ? 1 : 0; return a; }
        static Arg of_float(float v) { Arg a; a.kind = Kind::FLOAT; a.float_val = v; a.double_val = v; return a; }
        static Arg of_double(double v) { Arg a; a.kind = Kind::DOUBLE; a.double_val = v; return a; }
        static Arg of_string(std::string v) { Arg a; a.kind = Kind::STRING; a.string_val = std::move(v); return a; }
        static Arg of_object(uint32_t oid) { Arg a; a.kind = Kind::OBJECT; a.object_id = oid; return a; }
        static Arg null() { Arg a; a.kind = Kind::NULLREF; return a; }
    };
    std::vector<Arg> pos;

    const Arg& arg(size_t i) const {
        static const Arg k_default = Arg::of_int(0);
        return i < pos.size() ? pos[i] : k_default;
    }
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

// S108 ROOT-017: string-result channel. A handler that produces a real
// java.lang.String return calls mark_string_result(); invoke() RESETS the
// flag before dispatch and the marshalling site reads it after — no
// signature change needed (all existing handlers stay source-compatible).
namespace detail {
inline thread_local bool g_string_result_flag = false;
}
inline void mark_string_result() { detail::g_string_result_flag = true; }
inline bool consume_string_result() {
    bool v = detail::g_string_result_flag;
    detail::g_string_result_flag = false;
    return v;
}

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
        detail::g_string_result_flag = false;  // S108: reset string channel
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

        // ── F-NEW-627 (S209): SDL BOOTSTRAP FAMILY REGISTRATIONS ──────
        // The org.libsdl.app Java bootstrap native surface (the union
        // of every ACC_NATIVE declared by the SDL2 (gomoku, com.
        // traffar.gomoku 4) and SDL3 (rttt, org.kirkezz.rttt 3) Java
        // bootstraps — 71 natives over 6 classes, generated from the
        // two dexes). Semantics: honest fail-soft defaults (void no-op,
        // I/Z -> 0) EXCEPT nativeAllowRecreateActivity()Z -> true (the
        // SDL3 C default before the native main starts; a 0 answer
        // drives the app's own System.exit(0) path) and the two
        // ()Ljava/lang/String; natives (empty string over the S108
        // string channel — a NULL from the fail-soft path would NPE the
        // version handshake). The THREE load-bearing natives
        // (nativeGetVersion, nativeRunMain, nativeInit) are answered
        // engine-side BEFORE this registry (dalvik_engine.cpp F-NEW-627
        // route); these registrations are their honest fallbacks AND
        // make the GATE A S143 bridge-satisfied load law fire for SDL
        // libs the host dlopen refuses (32-bit ELF, missing GL deps).
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceConnected",
            "(ILjava/lang/String;IILjava/lang/String;ILjava/lang/String;Ljava/lang/String;IIIIZ)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceDisconnected",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceInputReport",
            "(I[B)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceOpenPending",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceOpenResult",
            "(IZ)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceRegisterCallback",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceReleaseCallback",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/HIDDeviceManager;", "HIDDeviceReportResponse",
            "(I[B)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeAddJoystick",
            "(ILjava/lang/String;IIIII)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeAddTouch",
            "(ILjava/lang/String;)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeAllowRecreateActivity",
            "()Z",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 1; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns true (SDL3 pre-main default)");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeCheckSDLThreadCounter",
            "()I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeCleanupMainThread",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeFlipBuffers",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeFocusChanged",
            "(Z)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeGetHint",
            "(Ljava/lang/String;)Ljava/lang/String;",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string& sr, uint32_t&, bool&) { sr.clear(); mark_string_result(); },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns "" (string channel)");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeGetHintBoolean",
            "(Ljava/lang/String;Z)Z",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeGetVersion",
            "()Ljava/lang/String;",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string& sr, uint32_t&, bool&) { sr.clear(); mark_string_result(); },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns "" (string channel)");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeInit",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeInitMainThread",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeLowMemory",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativePause",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativePermissionResult",
            "(IZ)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeQuit",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeRemoveJoystick",
            "(I)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeResume",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeRunMain",
            "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Object;)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeSendQuit",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeSetNaturalOrientation",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeSetScreenResolution",
            "(IIIIFF)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeSetenv",
            "(Ljava/lang/String;Ljava/lang/String;)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "nativeSetupJNI",
            "()I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeAccel",
            "(FFF)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeClipboardChanged",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeDarkModeChanged",
            "(Z)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeDropFile",
            "(Ljava/lang/String;)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeFileDialog",
            "(I[Ljava/lang/String;I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeHat",
            "(IIII)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeInsetsChanged",
            "(IIII)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeJoy",
            "(IIF)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeKeyDown",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeKeyUp",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeKeyboardFocusLost",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeLocaleChanged",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeMouse",
            "(IIFFZ)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativePadDown",
            "(II)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativePadUp",
            "(II)I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativePen",
            "(IIIFFF)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeResize",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeResize",
            "(III)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeRotationChanged",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeSoftReturnKey",
            "()Z",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeSurfaceChanged",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeSurfaceCreated",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeSurfaceDestroyed",
            "()V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLActivity;", "onNativeTouch",
            "(IIIFFF)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLAudioManager;", "addAudioDevice",
            "(ZLjava/lang/String;I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLAudioManager;", "nativeSetupJNI",
            "()I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLAudioManager;", "removeAudioDevice",
            "(ZI)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "nativeAddHaptic",
            "(ILjava/lang/String;)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "nativeAddJoystick",
            "(ILjava/lang/String;Ljava/lang/String;IIIIIIZ)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "nativeRemoveHaptic",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "nativeRemoveJoystick",
            "(I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "nativeSetupJNI",
            "()I",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "onNativeHat",
            "(IIII)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "onNativeJoy",
            "(IIF)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "onNativePadDown",
            "(II)Z",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLControllerManager;", "onNativePadUp",
            "(II)Z",
            [](const NativeCallContext&, int32_t& ir, int64_t&, float&, double&, std::string&, uint32_t&, bool&) { ir = 0; },
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "Returns 0");
        register_native("Lorg/libsdl/app/SDLInputConnection;", "nativeCommitText",
            "(Ljava/lang/String;I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLInputConnection;", "nativeGenerateScancodeForUnichar",
            "(C)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
        register_native("Lorg/libsdl/app/SDLInputConnection;", "nativeSetComposingText",
            "(Ljava/lang/String;I)V",
            [](const NativeCallContext&, int32_t&, int64_t&, float&, double&, std::string&, uint32_t&, bool&) {},
            NativeImplType::HOST_COMPATIBILITY_STUB,
            "No-op");
    }

    size_t registered_count() const { return methods_.size(); }

    // S143: count registered natives whose declaring class starts with the
    // given class-desc prefix (e.g. "Lorg/telegram/"). The GATE A
    // loadLibrary path uses this to decide whether the loading app's
    // native surface is already satisfied by the runtime's registered
    // REAL implementations (e.g. org.telegram.SQLite natives over REAL
    // sqlite3 — S108 ROOT-017) when a host dlopen is architecturally
    // impossible (AArch64 .so on the x86_64 host).
    size_t count_natives_for_class_prefix(const std::string& prefix) const {
        size_t n = 0;
        for (const auto& kv : methods_) {
            if (kv.second.class_desc.rfind(prefix, 0) == 0) ++n;
        }
        return n;
    }

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
