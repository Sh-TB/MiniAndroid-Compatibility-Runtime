/* F-NEW-387 first-party liblog anchor: the core Android liblog surface,
   implemented faithfully onto bounded stderr rows. Priorities mirror
   <android/log.h> (ANDROID_LOG_* values are the same constants). */
#include <stdarg.h>
#include <stdio.h>
typedef int android_LogPriority;
__attribute__((visibility("default")))
int __android_log_print(int prio, const char* tag, const char* fmt, ...) {
    va_list ap; va_start(ap, fmt);
    fprintf(stderr, "[LOG:%d] %s: ", prio, tag ? tag : "-");
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    va_end(ap);
    return 1;
}
__attribute__((visibility("default")))
int __android_log_write(int prio, const char* tag, const char* text) {
    return __android_log_print(prio, tag, "%s", text ? text : "");
}
__attribute__((visibility("default")))
int __android_log_vprint(int prio, const char* tag, const char* fmt, va_list ap) {
    fprintf(stderr, "[LOG:%d] %s: ", prio, tag ? tag : "-");
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    return 1;
}
__attribute__((visibility("default")))
int __android_log_buf_print(int bufID, int prio, const char* tag,
                            const char* fmt, ...) {
    va_list ap; va_start(ap, fmt);
    int r = __android_log_vprint(prio, tag, fmt, ap);
    va_end(ap);
    (void)bufID;
    return r;
}
