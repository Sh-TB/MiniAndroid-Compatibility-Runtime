/*
 * MiniAndroid Runtime v0.1 - Android API Stubs
 * EXP-001: HelloWorld Loader
 * 
 * Minimal implementations of Android framework classes.
 * Every call is traced for diagnostics.
 */

#ifndef MINIANDROID_ANDROID_STUBS_H
#define MINIANDROID_ANDROID_STUBS_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <cstdint>
#include <functional>
#include <chrono>
#include <algorithm>

namespace miniandroid {
namespace api {

// Forward declarations
class Bundle;
class Context;
class Activity;
class View;
class ViewGroup;
class TextView;
class Canvas;
class Paint;

// Diagnostic callback type
using TraceCallback = std::function<void(const std::string& class_name, 
                                         const std::string& method_name,
                                         const std::vector<std::string>& args)>;

/**
 * Base class for all Android objects in MiniAndroid
 */
class AndroidObject {
public:
    virtual ~AndroidObject() = default;
    
    virtual std::string get_class_name() const = 0;
    
    void set_trace_callback(TraceCallback callback) { trace_callback_ = callback; }
    
protected:
    void trace(const std::string& method_name) const {
        std::vector<std::string> empty_args;
        trace(method_name, empty_args);
    }
    
    void trace(const std::string& method_name, const std::vector<std::string>& args) const {
        if (trace_callback_) {
            trace_callback_(get_class_name(), method_name, args);
        }
    }
    
    void trace(const std::string& method_name, const std::string& arg) const {
        std::vector<std::string> args = {arg};
        trace(method_name, args);
    }
    
private:
    TraceCallback trace_callback_;
};

// ==================== android.os.Bundle ====================

class Bundle : public AndroidObject {
public:
    std::string get_class_name() const override { return "android.os.Bundle"; }
    
    // Core methods
    bool isEmpty() const { trace("isEmpty"); return string_data_.empty() && int_data_.empty(); }
    
    std::string getString(const std::string& key) {
        trace("getString", key);
        auto it = string_data_.find(key);
        return (it != string_data_.end()) ? it->second : "";
    }
    
    int getInt(const std::string& key, int default_value = 0) {
        trace("getInt", key + "," + std::to_string(default_value));
        auto it = int_data_.find(key);
        return (it != int_data_.end()) ? it->second : default_value;
    }
    
    bool getBoolean(const std::string& key, bool default_value = false) {
        trace("getBoolean", key);
        auto it = bool_data_.find(key);
        return (it != bool_data_.end()) ? it->second : default_value;
    }
    
    void putString(const std::string& key, const std::string& value) {
        trace("putString", key);
        string_data_[key] = value;
    }
    
    void putInt(const std::string& key, int value) {
        trace("putInt", key);
        int_data_[key] = value;
    }
    
    void putBoolean(const std::string& key, bool value) {
        trace("putBoolean", key);
        bool_data_[key] = value;
    }
    
    bool containsKey(const std::string& key) {
        trace("containsKey", key);
        return (string_data_.count(key) > 0 || int_data_.count(key) > 0 || 
                bool_data_.count(key) > 0);
    }

private:
    std::map<std::string, std::string> string_data_;
    std::map<std::string, int> int_data_;
    std::map<std::string, bool> bool_data_;
};

// ==================== android.content.Context ====================

class Context : public AndroidObject {
public:
    std::string get_class_name() const override { return "android.content.Context"; }
    
    virtual std::string getPackageName() { trace("getPackageName"); return package_name_; }
    virtual std::string getResources() { trace("getResources"); return ""; }
    
    void set_package_name(const std::string& name) { package_name_ = name; }
    
    // Resource access
    virtual int getResourceId(const std::string& name, const std::string& def_type) {
        trace("getResourceId", name);
        return resource_ids_.count(name) ? resource_ids_.at(name) : 0;
    }
    
    void register_resource(int id, const std::string& name) {
        resource_ids_[name] = id;
    }

private:
    std::string package_name_;
    std::map<std::string, int> resource_ids_;
};

// ==================== android.graphics.Paint ====================

class Paint : public AndroidObject {
public:
    enum class Style {
        FILL,
        STROKE,
        FILL_AND_STROKE
    };
    
    std::string get_class_name() const override { return "android.graphics.Paint"; }
    
    Paint() {
        color_ = 0xFF000000;  // Black
        text_size_ = 16.0f;
        style_ = Style::FILL;
        anti_alias_ = true;
    }
    
    uint32_t getColor() const { return color_; }
    void setColor(uint32_t color) {
        trace("setColor", "#" + int_to_hex(color));
        color_ = color;
    }
    
    float getTextSize() const { return text_size_; }
    void setTextSize(float size) {
        trace("setTextSize", std::to_string(size));
        text_size_ = size;
    }
    
    Style getStyle() const { return style_; }
    void setStyle(Style style) {
        trace("setStyle", std::to_string(static_cast<int>(style)));
        style_ = style;
    }
    
    bool isAntiAlias() const { return anti_alias_; }
    void setAntiAlias(bool aa) {
        trace("setAntiAlias", aa ? "true" : "false");
        anti_alias_ = aa;
    }
    
private:
    uint32_t color_;
    float text_size_;
    Style style_;
    bool anti_alias_;
    
    static std::string int_to_hex(uint32_t value) {
        const char* hex_digits = "0123456789ABCDEF";
        std::string result(8, '0');
        for (int i = 7; i >= 0; i--) {
            result[i] = hex_digits[value & 0xF];
            value >>= 4;
        }
        return result;
    }
};

// ==================== android.graphics.Canvas ====================

class Canvas : public AndroidObject {
public:
    std::string get_class_name() const override { return "android.graphics.Canvas"; }
    
    Canvas(uint8_t* buffer, int width, int height)
        : buffer_(buffer), width_(width), height_(height) {}
    
    void drawColor(uint32_t color) {
        trace("drawColor", "#" + int_to_hex(color));
        
        // Fill entire buffer with color
        if (buffer_) {
            uint8_t r = (color >> 16) & 0xFF;
            uint8_t g = (color >> 8) & 0xFF;
            uint8_t b = color & 0xFF;
            uint8_t a = (color >> 24) & 0xFF;
            
            for (int y = 0; y < height_; y++) {
                for (int x = 0; x < width_; x++) {
                    int offset = (y * width_ + x) * 4;
                    buffer_[offset + 0] = r;
                    buffer_[offset + 1] = g;
                    buffer_[offset + 2] = b;
                    buffer_[offset + 3] = a;
                }
            }
        }
    }
    
    void drawText(const std::string& text, float x, float y, const Paint& paint) {
        trace("drawText", text);
        
        // Simple bitmap font rendering (placeholder - draws rect for now)
        if (buffer_) {
            uint32_t color = paint.getColor();
            uint8_t r = (color >> 16) & 0xFF;
            uint8_t g = (color >> 8) & 0xFF;
            uint8_t b = color & 0xFF;
            
            int text_width = static_cast<int>(text.length() * paint.getTextSize() * 0.6f);
            int text_height = static_cast<int>(paint.getTextSize());
            
            int start_x = static_cast<int>(x);
            int start_y = static_cast<int>(y) - text_height;
            
            // Draw text background rectangle as placeholder
            for (int py = start_y; py < start_y + text_height && py < height_; py++) {
                for (int px = start_x; px < start_x + text_width && px < width_; px++) {
                    if (px >= 0 && py >= 0) {
                        int offset = (py * width_ + px) * 4;
                        buffer_[offset + 0] = r;
                        buffer_[offset + 1] = g;
                        buffer_[offset + 2] = b;
                        buffer_[offset + 3] = 255;
                    }
                }
            }
        }
    }
    
    void drawRect(float left, float top, float right, float bottom, const Paint& paint) {
        trace("drawRect");
        
        if (buffer_) {
            uint32_t color = paint.getColor();
            uint8_t r = (color >> 16) & 0xFF;
            uint8_t g = (color >> 8) & 0xFF;
            uint8_t b = color & 0xFF;
            
            int l = static_cast<int>(left);
            int t = static_cast<int>(top);
            int ri = static_cast<int>(right);
            int bo = static_cast<int>(bottom);
            
            for (int y = t; y < bo && y < height_; y++) {
                for (int x = l; x < ri && x < width_; x++) {
                    if (x >= 0 && y >= 0) {
                        int offset = (y * width_ + x) * 4;
                        buffer_[offset + 0] = r;
                        buffer_[offset + 1] = g;
                        buffer_[offset + 2] = b;
                        buffer_[offset + 3] = 255;
                    }
                }
            }
        }
    }
    
    int getWidth() const { return width_; }
    int getHeight() const { return height_; }

private:
    uint8_t* buffer_;
    int width_;
    int height_;
    
    static std::string int_to_hex(uint32_t value) {
        const char* hex_digits = "0123456789ABCDEF";
        std::string result(8, '0');
        for (int i = 7; i >= 0; i--) {
            result[i] = hex_digits[value & 0xF];
            value >>= 4;
        }
        return result;
    }
};

// ==================== android.view.View ====================

enum class ViewVisibility {
    VISIBLE,
    INVISIBLE,
    GONE
};

class View : public AndroidObject, public std::enable_shared_from_this<View> {
public:
    std::string get_class_name() const override { return "android.view.View"; }
    
    View() : id_(0), left_(0), top_(0), width_(0), height_(0),
             visibility_(ViewVisibility::VISIBLE) {}
    
    virtual void draw(Canvas& /*canvas*/) {
        trace("draw");
        // Default: do nothing
    }
    
    virtual void measure(int width_spec, int height_spec) {
        trace("measure");
        // Default: use measured dimensions
    }
    
    virtual void layout(int l, int t, int r, int b) {
        trace("layout");
        left_ = l;
        top_ = t;
        width_ = r - l;
        height_ = b - t;
    }
    
    void invalidate() { trace("invalidate"); }
    
    // Getters/Setters
    int getId() const { return id_; }
    void setId(int id) { id_ = id; }
    
    int getLeft() const { return left_; }
    int getTop() const { return top_; }
    int getWidth() const { return width_; }
    int getHeight() const { return height_; }
    
    ViewVisibility getVisibility() const { return visibility_; }
    void setVisibility(ViewVisibility v) {
        trace("setVisibility");
        visibility_ = v;
    }
    
    std::shared_ptr<ViewGroup> getParent() const { return parent_.lock(); }
    void setParent(std::shared_ptr<ViewGroup> p) { parent_ = p; }

protected:
    int id_;
    int left_, top_, width_, height_;
    ViewVisibility visibility_;
    std::weak_ptr<ViewGroup> parent_;
};

// ==================== android.view.ViewGroup ====================

class ViewGroup : public View {
public:
    std::string get_class_name() const override { return "android.view.ViewGroup"; }
    
    ViewGroup() : View() {}
    
    void addView(std::shared_ptr<View> child) {
        trace("addView");
        if (child) {
            child->setParent(std::static_pointer_cast<ViewGroup>(shared_from_this()));
            children_.push_back(child);
        }
    }
    
    void removeView(std::shared_ptr<View> child) {
        trace("removeView");
        children_.erase(
            std::remove(children_.begin(), children_.end(), child),
            children_.end()
        );
    }
    
    int getChildCount() const { return static_cast<int>(children_.size()); }
    std::shared_ptr<View> getChildAt(int index) {
        if (index >= 0 && index < static_cast<int>(children_.size())) {
            return children_[index];
        }
        return nullptr;
    }
    
    void draw(Canvas& canvas) override {
        trace("draw");
        // Draw all children
        for (auto& child : children_) {
            if (child && child->getVisibility() == ViewVisibility::VISIBLE) {
                child->draw(canvas);
            }
        }
    }
    
    void measure(int width_spec, int height_spec) override {
        View::measure(width_spec, height_spec);
        
        // Measure all children
        for (auto& child : children_) {
            if (child) {
                child->measure(width_spec, height_spec);
            }
        }
    }
    
    void layout(int l, int t, int r, int b) override {
        View::layout(l, t, r, b);
        
        // Layout children (simple full-size for now)
        for (auto& child : children_) {
            if (child) {
                child->layout(l, t, r, b);
            }
        }
    }

private:
    std::vector<std::shared_ptr<View>> children_;
};

// ==================== android.widget.TextView ====================

class TextView : public View {
public:
    std::string get_class_name() const override { return "android.widget.TextView"; }
    
    TextView() : View(), text_color_(0xFF000000), text_size_(16.0f) {}
    
    void setText(const std::string& text) {
        trace("setText", text);
        text_ = text;
    }
    
    std::string getText() const {
        trace("getText");
        return text_;
    }
    
    void setTextColor(uint32_t color) {
        trace("setTextColor");
        text_color_ = color;
    }
    
    void setTextSize(float size) {
        trace("setTextSize");
        text_size_ = size;
    }
    
    void draw(Canvas& canvas) override {
        trace("draw");
        
        Paint paint;
        paint.setColor(text_color_);
        paint.setTextSize(text_size_);
        
        canvas.drawText(text_, static_cast<float>(left_), 
                       static_cast<float>(top_ + text_size_), paint);
    }

private:
    std::string text_;
    uint32_t text_color_;
    float text_size_;
};

// ==================== android.app.Activity ====================

enum class ActivityState {
    CREATED,
    STARTED,
    RESUMED,
    PAUSED,
    STOPPED,
    DESTROYED
};

class Activity : public Context {
public:
    std::string get_class_name() const override { return "android.app.Activity"; }
    
    Activity() : state_(ActivityState::CREATED) {}
    
    // Lifecycle methods
    virtual void onCreate(Bundle* saved_instance_state) {
        std::string arg = saved_instance_state ? "bundle:non-null" : "null";
        trace("onCreate", arg);
        state_ = ActivityState::CREATED;
    }
    
    virtual void onStart() {
        trace("onStart");
        state_ = ActivityState::STARTED;
    }
    
    virtual void onResume() {
        trace("onResume");
        state_ = ActivityState::RESUMED;
    }
    
    virtual void onPause() {
        trace("onPause");
        state_ = ActivityState::PAUSED;
    }
    
    virtual void onStop() {
        trace("onStop");
        state_ = ActivityState::STOPPED;
    }
    
    virtual void onDestroy() {
        trace("onDestroy");
        state_ = ActivityState::DESTROYED;
    }
    
    // Content management
    virtual void setContentView(std::shared_ptr<View> view) {
        trace("setContentView");
        content_view_ = view;
    }
    
    virtual void setContentView(int layout_id) {
        trace("setContentView", "R.layout." + std::to_string(layout_id));
        // Would inflate layout here
    }
    
    std::shared_ptr<View> getContentView() const { return content_view_; }
    
    // View lookup
    template<typename T = View>
    std::shared_ptr<T> findViewById(int id) {
        trace("findViewById", std::to_string(id));
        return find_view_by_id<T>(content_view_, id);
    }
    
    ActivityState getState() const { return state_; }

private:
    std::shared_ptr<View> content_view_;
    ActivityState state_;
    
    template<typename T>
    std::shared_ptr<T> find_view_by_id(std::shared_ptr<View> root, int id) {
        if (!root) return nullptr;
        
        if (root->getId() == id) {
            return std::dynamic_pointer_cast<T>(root);
        }
        
        // Check if it's a ViewGroup and search children
        auto vg = std::dynamic_pointer_cast<ViewGroup>(root);
        if (vg) {
            for (int i = 0; i < vg->getChildCount(); i++) {
                auto found = find_view_by_id<T>(vg->getChildAt(i), id);
                if (found) return found;
            }
        }
        
        return nullptr;
    }
};

// ==================== API Registry ====================

/**
 * Registry for managing API stubs and tracking unimplemented calls
 */
struct ApiCallRecord {
    uint64_t timestamp;
    std::string thread_id;
    std::string class_name;
    std::string method_name;
    std::vector<std::string> args;
    std::string return_value;
    int call_depth;
};

class ApiRegistry {
public:
    ApiRegistry() : call_depth_(0) {}
    
    void register_call(const std::string& class_name, const std::string& method_name,
                       const std::vector<std::string>& args = {}) {
        ApiCallRecord record;
        record.timestamp = get_timestamp();
        record.thread_id = "main";
        record.class_name = class_name;
        record.method_name = method_name;
        record.args = args;
        record.call_depth = call_depth_;
        
        call_log_.push_back(record);
    }
    
    const std::vector<ApiCallRecord>& get_call_log() const { return call_log_; }
    size_t get_call_count() const { return call_log_.size(); }
    
    void push_depth() { call_depth_++; }
    void pop_depth() { if (call_depth_ > 0) call_depth_--; }
    
    void clear() {
        call_log_.clear();
        call_depth_ = 0;
    }
    
    // Generate summary by class
    std::map<std::string, size_t> get_calls_by_class() const {
        std::map<std::string, size_t> summary;
        for (const auto& call : call_log_) {
            summary[call.class_name]++;
        }
        return summary;
    }
    
    // Generate summary by method
    std::map<std::string, size_t> get_calls_by_method() const {
        std::map<std::string, size_t> summary;
        for (const auto& call : call_log_) {
            std::string full_method = call.class_name + "." + call.method_name;
            summary[full_method]++;
        }
        return summary;
    }

private:
    std::vector<ApiCallRecord> call_log_;
    int call_depth_;
    
    static uint64_t get_timestamp() {
        return static_cast<uint64_t>(
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()
            ).count()
        );
    }
};

} // namespace api
} // namespace miniandroid

#endif // MINIANDROID_ANDROID_STUBS_H
