/**
 * @file api_dispatcher.h
 * @brief Scalable Android API dispatcher foundation
 * 
 * @description
 * Provides a plugin-based architecture for Android API calls.
 * Instead of implementing the entire Android framework, this system:
 * 
 * 1. Resolves API calls to implementations
 * 2. Tracks implementation status (FOUND/MISSING)
 * 3. Provides default behaviors for missing APIs
 * 4. Supports incremental API coverage growth
 * 
 * Architecture:
 *   Dalvik invoke → API Resolver → Native C++ Implementation
 *                                   ↓
 *                              (or Default Stub)
 * 
 * @author EXP-036 Development
 * @date 2026-08-14
 * @version 1.0.0
 * 
 * @license MIT
 */

#ifndef API_DISPATCHER_H
#define API_DISPATCHER_H

#include <string>
#include <vector>
#include <map>
#include <functional>
#include <memory>
#include <sstream>
#include "execution_observatory.h"

/**
 * @namespace API
 * @brief Android API dispatching components
 */
namespace API {

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * @enum ApiPriority
 * @brief Priority level for API implementation
 */
enum class ApiPriority : uint8_t {
    P0_CRITICAL = 0,     ///< Must have for basic execution (Object, String, Class)
    P1_IMPORTANT = 1,    ///< Important for Activity lifecycle (Activity, Bundle)
    P2_USEFUL = 2,       ///< Useful for common apps (View, TextView, Button)
    P3_NICE_TO_HAVE = 3, ///< Enhances compatibility (advanced widgets)
    P4_FUTURE = 4         ///< Can defer indefinitely
};

/**
 * @enum ApiCategory
 * @brief Category of Android API
 */
enum class ApiCategory : uint8_t {
    CORE_JAVA,           ///< java.lang.*, java.util.*
    android_APP,          ///< android.app.*
    android_OS,           ///< android.os.*
    android_VIEW,         ///< android.view.*
    android_WIDGET,       ///< android.widget.*
    android_CONTENT,      ///< android.content.*
    CUSTOM                ///< User-defined or other
};

/**
 * @struct ApiCallContext
 * @brief Context information for an API call
 */
struct ApiCallContext {
    // Caller information
    std::string caller_class;
    std::string caller_method;
    uint32_t caller_pc;
    
    // Target information
    std::string api_class;
    std::string api_method;
    std::string api_signature;
    
    // Arguments (as strings for flexibility)
    std::vector<std::string> arguments;
    
    // Object context (for instance methods)
    bool is_instance_call;
    uint32_t object_id;  // Heap object ID if instance call
    
    /**
     * @brief Get full API identifier
     */
    std::string get_api_id() const {
        return api_class + "." + api_method + api_signature;
    }
};

/**
 * @struct ApiResult
 * @brief Result of an API call dispatch
 */
struct ApiResult {
    // Status
    Observatory::ApiImplementationStatus status;
    
    // Return value (as string representation)
    std::string return_value;
    
    // Success flag
    bool success;
    
    // Error information
    std::string error_message;
    
    // Side effects (for logging)
    std::vector<std::string> side_effects;
    
    // Implementation info
    std::string resolver_name;  // Which resolver handled this
    
    /**
     * @brief Create a successful result
     */
    static ApiResult ok(const std::string& value = "", const std::string& resolver = "implemented") {
        ApiResult result;
        result.status = Observatory::ApiImplementationStatus::FOUND_AND_EXECUTED;
        result.return_value = value;
        result.success = true;
        result.resolver_name = resolver;
        return result;
    }
    
    /**
     * @brief Create a failure result
     */
    static ApiResult fail(const std::string& error, const std::string& resolver = "error") {
        ApiResult result;
        result.status = Observatory::ApiImplementationStatus::FOUND_BUT_FAILED;
        result.success = false;
        result.error_message = error;
        result.resolver_name = resolver;
        return result;
    }
    
    /**
     * @brief Create a stub result (missing implementation)
     */
    static ApiResult stub(const std::string& note = "not implemented") {
        ApiResult result;
        result.status = Observatory::ApiImplementationStatus::MISSING_STUB;
        result.return_value = "";  // Default/null
        result.success = true;  // Stubs don't fail, they just do nothing
        result.resolver_name = "stub";
        result.side_effects.push_back("STUB: " + note);
        return result;
    }
    
    /**
     * @brief Create a critical missing result
     */
    static ApiResult missing_critical(const std::string& reason) {
        ApiResult result;
        result.status = Observatory::ApiImplementationStatus::MISSING_CRITICAL;
        result.success = false;
        result.error_message = "CRITICAL MISSING: " + reason;
        result.resolver_name = "missing";
        return result;
    }
};

// ============================================================================
// API RESOLVER INTERFACE
// ============================================================================

/**
 * @class IApiResolver
 * @brief Interface for API call resolvers
 * 
 * Implementations handle specific API calls or categories.
 */
class IApiResolver {
public:
    virtual ~IApiResolver() = default;
    
    /**
     * @brief Get resolver name (for logging)
     */
    virtual std::string get_name() const = 0;
    
    /**
     * @brief Check if this resolver can handle the given API
     * @param context The API call context
     * @return true if this resolver can handle it
     */
    virtual bool can_handle(const ApiCallContext& context) const = 0;
    
    /**
     * @brief Execute the API call
     * @param context The API call context
     * @return Result of the execution
     */
    virtual ApiResult execute(const ApiCallContext& context) = 0;
    
    /**
     * @brief Get priority of this resolver (higher = more specific)
     */
    virtual int get_priority() const { return 0; }
};

// ============================================================================
// BUILT-IN RESOLVERS
// ============================================================================

/**
 * @class ObjectResolver
 * @brief Handles java.lang.Object methods
 */
class ObjectResolver : public IApiResolver {
public:
    std::string get_name() const override { return "java.lang.Object"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 100; }  // High priority - core
};

/**
 * @class StringResolver
 * @brief Handles java.lang.String methods
 */
class StringResolver : public IApiResolver {
public:
    std::string get_name() const override { return "java.lang.String"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 100; }
};

/**
 * @class ClassResolver
 * @brief Handles java.lang.Class methods
 */
class ClassResolver : public IApiResolver {
public:
    std::string get_name() const override { return "java.lang.Class"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 100; }
};

/**
 * @class ActivityResolver
 * @brief Handles android.app.Activity methods (lifecycle)
 */
class ActivityResolver : public IApiResolver {
public:
    std::string get_name() const override { return "android.app.Activity"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 90; }
};

/**
 * @class ViewResolver
 * @brief Handles android.view.View methods
 */
class ViewResolver : public IApiResolver {
public:
    std::string get_name() const override { return "android.view.View"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 80; }
};

/**
 * @class TextViewResolver
 * @brief Handles android.widget.TextView methods
 */
class TextViewResolver : public IApiResolver {
public:
    std::string get_name() const override { return "android.widget.TextView"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 70; }
};

/**
 * @class BundleResolver
 * @brief Handles android.os.Bundle methods
 */
class BundleResolver : public IApiResolver {
public:
    std::string get_name() const override { return "android.os.Bundle"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 85; }
};

/**
 * @class LogResolver
 * @brief Handles android.util.Log methods
 */
class LogResolver : public IApiResolver {
public:
    std::string get_name() const override { return "android.util.Log"; }
    bool can_handle(const ApiCallContext& ctx) const override;
    ApiResult execute(const ApiCallContext& ctx) override;
    int get_priority() const override { return 95; }
};

// ============================================================================
// MAIN DISPATCHER
// ============================================================================

/**
 * @class ApiDispatcher
 * @brief Central dispatcher for all Android API calls
 * 
 * @description
 * Routes API calls to appropriate resolvers with fallback to stubs.
 * Provides complete observability and statistics.
 * 
 * Usage:
 * @code
 * API::ApiDispatcher dispatcher(&observatory);
 * dispatcher.register_resolver(std::make_unique<API::ActivityResolver>());
 * 
 * API::ApiCallContext ctx;
 * ctx.api_class = "android.app.Activity";
 * ctx.api_method = "onCreate";
 * 
 * API::ApiResult result = dispatcher.dispatch(ctx);
 * if (result.status == API::MISSING_CRITICAL) {
 *     // Handle critical missing API
 * }
 * @endcode
 */
class ApiDispatcher {
public:
    /**
     * @brief Constructor
     * @param observatory Observatory for recording events (can be null)
     */
    explicit ApiDispatcher(Observatory::ExecutionObservatory* observatory = nullptr);
    
    // =========================================================================
    // RESOLVER MANAGEMENT
    // =========================================================================
    
    /**
     * @brief Register a new resolver
     * @param resolver Unique pointer to resolver (takes ownership)
     */
    void register_resolver(std::unique_ptr<IApiResolver> resolver);
    
    /**
     * @brief Register all built-in resolvers
     */
    void register_builtin_resolvers();
    
    /**
     * @brief Remove all resolvers
     */
    void clear_resolvers();
    
    /**
     * @brief Get number of registered resolvers
     */
    size_t get_resolver_count() const { return resolvers_.size(); }
    
    // =========================================================================
    // DISPATCH
    // =========================================================================
    
    /**
     * @brief Dispatch an API call to appropriate resolver
     * @param context The API call context
     * @return Result of the dispatch
     */
    ApiResult dispatch(const ApiCallContext& context);
    
    /**
     * @brief Quick dispatch with minimal context setup
     */
    ApiResult dispatch(
        const std::string& api_class,
        const std::string& method,
        const std::vector<std::string>& args = {}
    );
    
    // =========================================================================
    // STATISTICS & QUERIES
    // =========================================================================
    
    /**
     * @brief Get total API calls dispatched
     */
    size_t get_total_calls() const { return total_calls_; }
    
    /**
     * @brief Get number of successful calls
     */
    size_t get_successful_calls() const { return successful_calls_; }
    
    /**
     * @brief Get number of failed calls
     */
    size_t get_failed_calls() const { return failed_calls_; }
    
    /**
     * @brief Get number of stubbed (missing) calls
     */
    size_t get_stubbed_calls() const { return stubbed_calls_; }
    
    /**
     * @brief Get number of critically missing calls
     */
    size_t get_critical_missing_calls() const { return critical_missing_calls_; }
    
    /**
     * @brief Check if any critical APIs are missing
     */
    bool has_critical_missing() const { return critical_missing_calls_ > 0; }
    
    /**
     * @brief Generate API coverage report
     */
    std::string generate_coverage_report() const;
    
    /**
     * @brief Get list of missing critical APIs
     */
    std::vector<std::string> get_missing_critical_apis() const;

private:
    // Resolvers (ordered by priority)
    std::vector<std::unique_ptr<IApiResolver>> resolvers_;
    
    // Observatory integration
    Observatory::ExecutionObservatory* observatory_;
    
    // Statistics
    size_t total_calls_;
    size_t successful_calls_;
    size_t failed_calls_;
    size_t stubbed_calls_;
    size_t critical_missing_calls_;
    
    // Missing API tracking
    std::vector<ApiCallContext> missing_critical_apis_;
    
    // Internal helper
    ApiResult dispatch_to_resolvers(const ApiCallContext& context);
    ApiResult create_default_stub_result(const ApiCallContext& context);
};

} // namespace API

#endif // API_DISPATCHER_H
