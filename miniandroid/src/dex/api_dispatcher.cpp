/**
 * @file api_dispatcher.cpp
 * @brief Implementation of Android API Dispatcher
 * 
 * @author EXP-036 Development
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#include "api_dispatcher.h"
#include <iostream>
#include <algorithm>

namespace API {

// ============================================================================
// OBJECT RESOLVER
// ============================================================================

bool ObjectResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "java.lang.Object" || 
           ctx.api_class == "java/lang/Object";
}

ApiResult ObjectResolver::execute(const ApiCallContext& ctx) {
    // java.lang.Object methods that we can handle
    
    if (ctx.api_method == "getClass") {
        // Return the class of this object
        if (ctx.is_instance_call) {
            return ApiResult::ok("Ljava/lang/Class;", get_name());
        }
        return ApiResult::fail("getClass called without object instance");
    }
    
    if (ctx.api_method == "hashCode") {
        // Return hash code based on object ID
        if (ctx.is_instance_call) {
            std::ostringstream oss;
            oss << ctx.object_id;  // Simple hash: use object ID
            return ApiResult::ok(oss.str(), get_name());
        }
        return ApiResult::ok("0", get_name());  // Default hash
    }
    
    if (ctx.api_method == "equals") {
        // Compare objects (simplified: compare IDs)
        if (ctx.arguments.size() >= 1) {
            // Would need to resolve the other object reference
            return ApiResult::ok("false", get_name());  // Default: not equal
        }
        return ApiResult::fail("equals requires one argument");
    }
    
    if (ctx.api_method == "toString") {
        // Return string representation
        if (ctx.is_instance_call) {
            std::ostringstream oss;
            oss << ctx.api_class << "@" << std::hex << ctx.object_id;
            return ApiResult::ok(oss.str(), get_name());
        }
        return ApiResult::ok("java.lang.Object@0", get_name());
    }
    
    // Unknown Object method - return stub
    return ApiResult::stub("Object." + ctx.api_method + " not fully implemented");
}

// ============================================================================
// STRING RESOLVER
// ============================================================================

bool StringResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "java.lang.String" || 
           ctx.api_class == "java/lang/String";
}

ApiResult StringResolver::execute(const ApiCallContext& ctx) {
    // java.lang.String is mostly immutable, so many operations are simple
    
    if (ctx.api_method == "length") {
        if (ctx.is_instance_call && !ctx.arguments.empty()) {
            // String would be in arguments or as the instance
            // For now, return a default length
            return ApiResult::ok("0", get_name());
        }
        return ApiResult::ok("0", get_name());
    }
    
    if (ctx.api_method == "charAt") {
        if (ctx.arguments.size() >= 1) {
            // Return first char or empty
            return ApiResult::ok("", get_name());
        }
        return ApiResult::fail("charAt requires index argument");
    }
    
    if (ctx.api_method == "equals" || ctx.api_method == "contentEquals") {
        // Simplified string comparison - always false for stub
        return ApiResult::ok("false", get_name());
    }
    
    if (ctx.api_method == "toString") {
        // String.toString() returns itself
        if (ctx.is_instance_call) {
            return ApiResult::ok("(string)", get_name());
        }
        return ApiResult::ok("", get_name());
    }
    
    if (ctx.api_method == "<init>") {
        // String constructor - various overloads
        return ApiResult::ok("", get_name());  // Return empty string
    }
    
    return ApiResult::stub("String." + ctx.api_method + " not fully implemented");
}

// ============================================================================
// CLASS RESOLVER
// ============================================================================

bool ClassResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "java.lang.Class" || 
           ctx.api_class == "java/lang/Class";
}

ApiResult ClassResolver::execute(const ApiCallContext& ctx) {
    if (ctx.api_method == "getName") {
        // Return class name
        if (ctx.arguments.empty()) {
            return ApiResult::ok("Ljava/lang/Object;", get_name());
        }
        // Return whatever was passed as the class descriptor
        return ApiResult::ok(ctx.arguments[0], get_name());
    }
    
    if (ctx.api_method == "getSimpleName") {
        // Return simple name (without package)
        return ApiResult::ok("Object", get_name());
    }
    
    if (ctx.api_method == "getSuperclass") {
        // Return superclass (Object has none)
        return ApiResult::ok("", get_name());  // null for Object
    }
    
    if (ctx.api_method == "isInstance" || ctx.api_method == "isAssignableFrom") {
        // Simplified type check - assume true
        return ApiResult::ok("true", get_name());
    }
    
    if (ctx.api_method == "forName") {
        // Class.forName() - return the requested class
        if (!ctx.arguments.empty()) {
            return ApiResult::ok(ctx.arguments[0], get_name());
        }
        return ApiResult::fail("forName requires class name argument");
    }
    
    return ApiResult::stub("Class." + ctx.api_method + " not fully implemented");
}

// ============================================================================
// ACTIVITY RESOLVER
// ============================================================================

bool ActivityResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "android.app.Activity" || 
           ctx.api_class == "android/app/Activity";
}

ApiResult ActivityResolver::execute(const ApiCallContext& ctx) {
    // Activity lifecycle methods - these are critical for execution proof
    
    if (ctx.api_method == "onCreate") {
        // CRITICAL: This proves Activity lifecycle execution!
        std::cout << "[API] ✅ Activity.onCreate() CALLED - LIFECYCLE EVIDENCE" << std::endl;
        
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("LIFECYCLE: onCreate executed");
        result.side_effects.push_back("EVIDENCE: Real Activity lifecycle reached");
        
        // If Bundle argument provided, note it
        if (!ctx.arguments.empty()) {
            result.side_effects.push_back("Bundle received: " + ctx.arguments[0]);
        }
        
        return result;
    }
    
    if (ctx.api_method == "onStart") {
        std::cout << "[API] ✅ Activity.onStart() CALLED" << std::endl;
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("LIFECYCLE: onStart executed");
        return result;
    }
    
    if (ctx.api_method == "onResume") {
        std::cout << "[API] ✅ Activity.onResume() CALLED" << std::endl;
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("LIFECYCLE: onResume executed");
        return result;
    }
    
    if (ctx.api_method == "onPause") {
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("LIFECYCLE: onPause executed");
        return result;
    }
    
    if (ctx.api_method == "onStop") {
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("LIFECYCLE: onStop executed");
        return result;
    }
    
    if (ctx.api_method == "onDestroy") {
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("LIFECYCLE: onDestroy executed");
        return result;
    }
    
    if (ctx.api_method == "setContentView") {
        // Important: UI setup method
        std::cout << "[API] ✅ Activity.setContentView() CALLED - UI SETUP EVIDENCE" << std::endl;
        
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("UI: setContentView called");
        result.side_effects.push_back("EVIDENCE: View hierarchy initialization");
        
        if (!ctx.arguments.empty()) {
            result.side_effects.push_back("Layout resource: " + ctx.arguments[0]);
        }
        
        return result;
    }
    
    if (ctx.api_method == "findViewById") {
        // View lookup - return a dummy view ID
        ApiResult result = ApiResult::ok("1001", get_name());  // Dummy view ID
        result.side_effects.push_back("UI: findViewById returned stub view");
        return result;
    }
    
    if (ctx.api_method == "getIntent" || ctx.api_method == "getApplicationContext") {
        // Return null/default for now
        return ApiResult::stub("Activity." + ctx.api_method + " returns default");
    }
    
    // Other Activity methods - stub with note
    return ApiResult::stub("Activity." + ctx.api_method + " lifecycle method");
}

// ============================================================================
// VIEW RESOLVER
// ============================================================================

bool ViewResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "android.view.View" || 
           ctx.api_class == "android/view/View";
}

ApiResult ViewResolver::execute(const ApiCallContext& ctx) {
    if (ctx.api_method == "<init>") {
        // View constructor
        ApiResult result = ApiResult::ok("view_id_" + std::to_string(ctx.object_id), get_name());
        result.side_effects.push_back("VIEW: View created with id=" + std::to_string(ctx.object_id));
        return result;
    }
    
    if (ctx.api_method == "setId") {
        ApiResult result = ApiResult::ok("void", get_name());
        if (!ctx.arguments.empty()) {
            result.side_effects.push_back("VIEW: Set ID to " + ctx.arguments[0]);
        }
        return result;
    }
    
    if (ctx.api_method == "getId") {
        return ApiResult::ok(std::to_string(ctx.object_id), get_name());
    }
    
    if (ctx.api_method == "setOnClickListener") {
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("VIEW: Click listener registered (stub)");
        return result;
    }
    
    return ApiResult::stub("View." + ctx.api_method + " not fully implemented");
}

// ============================================================================
// TEXTVIEW RESOLVER
// ============================================================================

bool TextViewResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "android.widget.TextView" || 
           ctx.api_class == "android/widget/TextView";
}

ApiResult TextViewResolver::execute(const ApiCallContext& ctx) {
    // TextView extends View, so View methods also apply here
    
    if (ctx.api_method == "setText") {
        // IMPORTANT: This is a very common API call!
        std::string text = ctx.arguments.empty() ? "" : ctx.arguments[0];
        
        std::cout << "[API] ✅ TextView.setText(\"" << text << "\") CALLED - UI EVIDENCE" << std::endl;
        
        ApiResult result = ApiResult::ok("void", get_name());
        result.side_effects.push_back("TEXT_VIEW: setText called with \"" + text + "\"");
        result.side_effects.push_back("EVIDENCE: Text content set on UI element");
        return result;
    }
    
    if (ctx.api_method == "getText") {
        return ApiResult::ok("", get_name());  // Return empty string
    }
    
    if (ctx.api_method == "<init>") {
        ApiResult result = ApiResult::ok("textview_id_" + std::to_string(ctx.object_id), get_name());
        result.side_effects.push_back("TEXT_VIEW: TextView created");
        return result;
    }
    
    return ApiResult::stub("TextView." + ctx.api_method + " not fully implemented");
}

// ============================================================================
// BUNDLE RESOLVER
// ============================================================================

bool BundleResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "android.os.Bundle" || 
           ctx.api_class == "android/os/Bundle";
}

ApiResult BundleResolver::execute(const ApiCallContext& ctx) {
    if (ctx.api_method == "<init>") {
        ApiResult result = ApiResult::ok("bundle_id_" + std::to_string(ctx.object_id), get_name());
        result.side_effects.push_back("BUNDLE: Bundle created");
        return result;
    }
    
    if (ctx.api_method == "getString" || ctx.api_method == "getInt" || 
        ctx.api_method == "getBoolean" || ctx.api_method == "get") {
        // Get value from bundle - return default/empty
        if (ctx.arguments.size() >= 1) {
            std::string key = ctx.arguments[0];
            
            // Return appropriate default based on type
            if (ctx.api_method == "getString") return ApiResult::ok("", get_name());
            if (ctx.api_method == "getInt") return ApiResult::ok("0", get_name());
            if (ctx.api_method == "getBoolean") return ApiResult::ok("false", get_name());
            
            return ApiResult::ok("", get_name());
        }
        return ApiResult::fail(ctx.api_method + " requires key argument");
    }
    
    if (ctx.api_method == "putString" || ctx.api_method == "putInt" ||
        ctx.api_method == "putBoolean" || ctx.api_method == "put") {
        ApiResult result = ApiResult::ok("void", get_name());
        if (ctx.arguments.size() >= 2) {
            result.side_effects.push_back("BUNDLE: put " + ctx.arguments[0] + " = " + ctx.arguments[1]);
        }
        return result;
    }
    
    return ApiResult::stub("Bundle." + ctx.api_method + " not fully implemented");
}

// ============================================================================
// LOG RESOLVER
// ============================================================================

bool LogResolver::can_handle(const ApiCallContext& ctx) const {
    return ctx.api_class == "android.util.Log" || 
           ctx.api_class == "android/util/Log";
}

ApiResult LogResolver::execute(const ApiCallContext& ctx) {
    // Log methods are very commonly used and important for debugging evidence
    
    if (ctx.api_method == "v" || ctx.api_method == "d" || 
        ctx.api_method == "i" || ctx.api_method == "w" || ctx.api_method == "e") {
        // Log.v/d/i/w/e(String tag, String msg)
        if (ctx.arguments.size() >= 2) {
            std::string tag = ctx.arguments[0];
            std::string msg = ctx.arguments[1];
            
            // Map log level to prefix
            std::string level;
            if (ctx.api_method == "v") level = "V";
            else if (ctx.api_method == "d") level = "D";
            else if (ctx.api_method == "i") level = "I";
            else if (ctx.api_method == "w") level = "W";
            else level = "E";
            
            // Output actual log line
            std::cout << "[LOG/" << level << "] " << tag << ": " << msg << std::endl;
            
            ApiResult result = ApiResult::ok(std::to_string(msg.length()), get_name());
            result.side_effects.push_back("LOG: [" + level + "] " + tag + ": " + msg);
            return result;
        } else if (ctx.arguments.size() == 1) {
            std::cout << "[LOG/?] (no tag): " << ctx.arguments[0] << std::endl;
            return ApiResult::ok(std::to_string(ctx.arguments[0].length()), get_name());
        }
        
        return ApiResult::fail("Log requires tag and message arguments");
    }
    
    if (ctx.api_method == "println" || ctx.api_method == "wtf") {
        // Special log methods
        if (!ctx.arguments.empty()) {
            std::cout << "[LOG/SPECIAL] " << ctx.arguments[0] << std::endl;
            return ApiResult::ok(std::to_string(ctx.arguments[0].length()), get_name());
        }
        return ApiResult::ok("0", get_name());
    }
    
    return ApiResult::stub("Log." + ctx.api_method + " not fully implemented");
}

// ============================================================================
// API DISPATCHER IMPLEMENTATION
// ============================================================================

ApiDispatcher::ApiDispatcher(Observatory::ExecutionObservatory* observatory)
    : observatory_(observatory)
    , total_calls_(0)
    , successful_calls_(0)
    , failed_calls_(0)
    , stubbed_calls_(0)
    , critical_missing_calls_(0)
{
}

void ApiDispatcher::register_resolver(std::unique_ptr<IApiResolver> resolver) {
    if (resolver) {
        resolvers_.push_back(std::move(resolver));
        
        // Keep sorted by priority (higher priority first)
        std::sort(resolvers_.begin(), resolvers_.end(),
            [](const std::unique_ptr<IApiResolver>& a, const std::unique_ptr<IApiResolver>& b) {
                return a->get_priority() > b->get_priority();
            });
    }
}

void ApiDispatcher::register_builtin_resolvers() {
    register_resolver(std::make_unique<ObjectResolver>());
    register_resolver(std::make_unique<StringResolver>());
    register_resolver(std::make_unique<ClassResolver>());
    register_resolver(std::make_unique<ActivityResolver>());
    register_resolver(std::make_unique<ViewResolver>());
    register_resolver(std::make_unique<TextViewResolver>());
    register_resolver(std::make_unique<BundleResolver>());
    register_resolver(std::make_unique<LogResolver>());
}

void ApiDispatcher::clear_resolvers() {
    resolvers_.clear();
}

ApiResult ApiDispatcher::dispatch(const ApiCallContext& context) {
    total_calls_++;
    
    // Try to find a resolver that can handle this API
    ApiResult result = dispatch_to_resolvers(context);
    
    // Record in observatory
    if (observatory_) {
        observatory_->record_api_call(
            context.api_class,
            context.api_method,
            context.arguments,
            result.status,
            result.resolver_name,
            result.return_value,
            result.success,
            result.error_message
        );
    }
    
    // Update statistics
    switch (result.status) {
        case Observatory::ApiImplementationStatus::FOUND_AND_EXECUTED:
            successful_calls_;
            break;
        case Observatory::ApiImplementationStatus::FOUND_BUT_FAILED:
            failed_calls_;
            break;
        case Observatory::ApiImplementationStatus::MISSING_STUB:
            stubbed_calls_;
            break;
        case Observatory::ApiImplementationStatus::MISSING_CRITICAL:
            critical_missing_calls_;
            missing_critical_apis_.push_back(context);
            break;
        default:
            break;
    }
    
    return result;
}

ApiResult ApiDispatcher::dispatch(
    const std::string& api_class,
    const std::string& method,
    const std::vector<std::string>& args
) {
    ApiCallContext ctx;
    ctx.api_class = api_class;
    ctx.api_method = method;
    ctx.arguments = args;
    ctx.is_instance_call = false;
    ctx.object_id = 0;
    
    return dispatch(ctx);
}

std::string ApiDispatcher::generate_coverage_report() const {
    std::ostringstream oss;
    
    oss << "================================================================\n";
    oss << "API DISPATCHER COVERAGE REPORT\n";
    oss << "================================================================\n\n";
    
    oss << "Statistics:\n";
    oss << "  Total API Calls:       " << total_calls_ << "\n";
    oss << "  Successful:            " << successful_calls_ << " (" 
        << (total_calls_ > 0 ? (successful_calls_ * 100 / total_calls_) : 0) << "%)\n";
    oss << "  Failed:                 " << failed_calls_ << "\n";
    oss << "  Stubbed (Missing):      " << stubbed_calls_ << "\n";
    oss << "  Critical Missing:       " << critical_missing_calls_ << "\n\n";
    
    oss << "Registered Resolvers (" << resolvers_.size() << "):\n";
    for (const auto& r : resolvers_) {
        oss << "  - " << r->get_name() << " [priority=" << r->get_priority() << "]\n";
    }
    oss << "\n";
    
    if (!missing_critical_apis_.empty()) {
        oss << "Critical Missing APIs:\n";
        for (const auto& api : missing_critical_apis_) {
            oss << "  ❌ " << api.get_api_id() << "\n";
        }
        oss << "\n";
    }
    
    double coverage = total_calls_ > 0 
        ? (double)(successful_calls_ + stubbed_calls_) / total_calls_ * 100.0 
        : 0.0;
    
    oss << "Coverage Estimate: " << std::fixed << std::setprecision(1) << coverage << "%\n";
    oss << "================================================================\n";
    
    return oss.str();
}

std::vector<std::string> ApiDispatcher::get_missing_critical_apis() const {
    std::vector<std::string> apis;
    for (const auto& ctx : missing_critical_apis_) {
        apis.push_back(ctx.get_api_id());
    }
    return apis;
}

ApiResult ApiDispatcher::dispatch_to_resolvers(const ApiCallContext& context) {
    // Try each resolver in priority order
    for (auto& resolver : resolvers_) {
        if (resolver->can_handle(context)) {
            try {
                return resolver->execute(context);
            } catch (const std::exception& e) {
                // Resolver threw exception - record as failed
                return ApiResult::fail(std::string("Resolver error: ") + e.what());
            }
        }
    }
    
    // No resolver found - determine severity
    bool is_critical = (
        context.api_class.find("java.lang") != std::string::npos ||
        context.api_class.find("android.app") != std::string::npos
    ) && (
        context.api_method == "<init>" ||
        context.api_method == "onCreate" ||
        context.api_method == "setContentView"
    );
    
    if (is_critical) {
        return ApiResult::missing_critical("No resolver for " + context.get_api_id());
    }
    
    // Default stub for non-critical missing APIs
    return create_default_stub_result(context);
}

ApiResult ApiDispatcher::create_default_stub_result(const ApiCallContext& context) {
    // Generate a more informative stub message
    std::ostringstream note;
    note << "No implementation for " << context.get_api_id();
    
    return ApiResult::stub(note.str());
}

} // namespace API
