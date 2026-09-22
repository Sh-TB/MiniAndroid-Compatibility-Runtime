// locale_insets_shadow.cpp — S83-GFX-BASE §32: F-NEW-159 semantic shadows.
#include "locale_insets_shadow.h"

#include <sstream>

namespace miniandroid { namespace framework {

void LocaleInsetsShadow::init(HeapAllocator* heap) {
    heap_ = heap;
}

uint32_t LocaleInsetsShadow::ensure_list(const std::string& tags) {
    if (!heap_) return 0;
    // One canonical LocaleList per tag string (getDefault == getAdjustedDefault
    // == the same list for the single-locale software profile).
    const std::string key = tags.empty() ? kDefaultLanguageTags : tags;
    uint32_t obj = heap_->get_or_create("Landroid/os/LocaleList;");
    heap_->set_object_string_field(obj, "languageTags", key);
    heap_->set_object_int_field(obj, "size", 1);
    // Materialize locale[0] lazily-consistently: the primary locale.
    const uint32_t loc = ensure_locale(key.substr(0, key.find(',')));
    heap_->set_object_ref_field(obj, "primaryLocale", loc,
                                "Ljava/util/Locale;", "", false);
    return obj;
}

uint32_t LocaleInsetsShadow::ensure_locale(const std::string& tag) {
    if (!heap_) return 0;
    const std::string t = tag.empty() ? kDefaultLanguageTags : tag;
    uint32_t obj = heap_->get_or_create("Ljava/util/Locale;");
    heap_->set_object_string_field(obj, "languageTag", t);
    // AOSP Locale decomposition: language = prefix before '-'/_.
    const size_t sep = t.find_first_of("-_");
    heap_->set_object_string_field(
        obj, "language", sep == std::string::npos ? t : t.substr(0, sep));
    return obj;
}

uint32_t LocaleInsetsShadow::ensure_controller() {
    if (!heap_) return 0;
    // AOSP Window.getInsetsController(): a real controller per window.
    // State fields follow android.view.WindowInsetsController laws:
    //   appearance  — APPEARANCE_* bits last set via setSystemBarsAppearance
    //   behavior    — BEHAVIOR_* bits (showBarsByDefault / bypass / transient)
    //   visibleMask — WindowInsets.Type bars last requested via show()/hide()
    uint32_t obj = heap_->get_or_create("Landroid/view/WindowInsetsController;");
    int32_t v = 0;
    if (!heap_->get_object_int_field(obj, "appearance", v)) {
        heap_->set_object_int_field(obj, "appearance", 0);
        heap_->set_object_int_field(obj, "behavior", 0);   // BEHAVIOR_SHOW_BARS_BY_TOUCH default
        heap_->set_object_int_field(obj, "visibleMask", 0);
    }
    return obj;
}

CallResult LocaleInsetsShadow::dispatch(const CallContext& ctx) {
    if (!heap_) return CallResult{};
    const std::string& cls = ctx.class_name;
    const std::string& m = ctx.method;

    // ── LocaleList ───────────────────────────────────────────────────────
    if (cls.find("os/LocaleList;") != std::string::npos) {
        // Static factories first (no receiver state).
        if (m == "getDefault" || m == "getAdjustedDefault") {
            return CallResult::handled_object(ensure_list(kDefaultLanguageTags),
                                              "Landroid/os/LocaleList;");
        }
        if (m == "wrap") {
            // wrap(Locale) → singleton list of that locale.
            std::string tag = kDefaultLanguageTags;
            const uint32_t loc = ctx.arg_as_object(0, 0);
            std::string t;
            if (loc != 0 && heap_->get_object_string_field(loc, "languageTag", t))
                tag = t;
            return CallResult::handled_object(ensure_list(tag),
                                              "Landroid/os/LocaleList;");
        }
        const uint32_t self = ctx.receiver_id;
        if (m == "toLanguageTags") {
            std::string tags;
            if (self != 0)
                heap_->get_object_string_field(self, "languageTags", tags);
            if (tags.empty()) tags = kDefaultLanguageTags;
            return CallResult::handled_string(tags);
        }
        if (m == "isEmpty") return CallResult::handled_bool(false);
        if (m == "size") return CallResult::handled_int(1);
        if (m == "get") {
            return CallResult::handled_object(ensure_locale(kDefaultLanguageTags),
                                              "Ljava/util/Locale;");
        }
        if (m == "indexOf") return CallResult::handled_int(0);
    }

    // ── Locale ───────────────────────────────────────────────────────────
    if (cls == "Ljava/util/Locale;" || cls.find("util/Locale;") != std::string::npos) {
        if (m == "getDefault") {   // static Locale.getDefault()
            return CallResult::handled_object(ensure_locale(kDefaultLanguageTags),
                                              "Ljava/util/Locale;");
        }
        const uint32_t self = ctx.receiver_id;
        std::string tag = kDefaultLanguageTags;
        if (self != 0) heap_->get_object_string_field(self, "languageTag", tag);
        if (m == "toLanguageTag" || m == "toString") {
            return CallResult::handled_string(tag);
        }
        if (m == "getLanguage") {
            const size_t sep = tag.find_first_of("-_");
            return CallResult::handled_string(
                sep == std::string::npos ? tag : tag.substr(0, sep));
        }
        if (m == "getCountry") return CallResult::handled_string("");
        if (m == "getDisplayName") return CallResult::handled_string(tag);
    }

    // ── WindowInsetsController (platform interface object) ──────────────
    if (cls.find("view/WindowInsetsController") != std::string::npos) {
        const uint32_t self = ctx.receiver_id != 0
                                  ? ctx.receiver_id
                                  : ensure_controller();
        auto set_i = [&](const char* f, int32_t v) {
            heap_->set_object_int_field(self, f, v);
        };
        if (m == "setSystemBarsAppearance" && ctx.args.size() >= 2) {
            // AOSP: appearance = (appearance & ~mask) | (values & mask).
            const int32_t values = ctx.arg_as_int(0, 0);
            const int32_t mask = ctx.arg_as_int(1, 0);
            int32_t cur = 0;
            heap_->get_object_int_field(self, "appearance", cur);
            set_i("appearance", (cur & ~mask) | (values & mask));
            return CallResult::handled_void();
        }
        if (m == "setSystemBarsBehavior" && ctx.args.size() >= 1) {
            set_i("behavior", ctx.arg_as_int(0, 0));
            return CallResult::handled_void();
        }
        if (m == "show" || m == "hide") {
            // WindowInsets.Type masks: record the requested visibility.
            const int32_t mask = ctx.args.size() >= 1 ? ctx.arg_as_int(0, 0) : 0;
            int32_t cur = 0;
            heap_->get_object_int_field(self, "visibleMask", cur);
            set_i("visibleMask", m == "show" ? (cur | mask) : (cur & ~mask));
            return CallResult::handled_void();
        }
        if (m == "getSystemBarsAppearance") {
            int32_t cur = 0;
            heap_->get_object_int_field(self, "appearance", cur);
            return CallResult::handled_int(cur);
        }
        if (m == "setDecorFitsSystemWindows") {
            int32_t v = ctx.args.size() >= 1 && ctx.arg_as_bool(0, true) ? 1 : 0;
            set_i("decorFits", v);
            return CallResult::handled_void();
        }
        // Lifecycle/unused callbacks: honest accept with state.
        if (m == "controlInsets" || m == "addOnControllableInsetsChangedListener" ||
            m == "removeOnControllableInsetsChangedListener") {
            return CallResult::handled_void();
        }
    }

    return CallResult{};
}

} } // namespace miniandroid::framework
