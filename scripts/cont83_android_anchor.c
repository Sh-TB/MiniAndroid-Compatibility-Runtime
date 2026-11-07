/* T22 (F-NEW-564 support): libandroid anchor — honest first-party surface
 * for the symbols libtmessages binds (T18's "honest surfaces" design,
 * reconstructed from the tracked spec text).
 *
 * Laws (software runtime, no display/audio hardware):
 *  - IDENTITY: ANativeWindow_fromSurface / AAssetManager_fromJava return a
 *    NON-NULL opaque token derived from the passed jobject (0 = input null)
 *    so app null-checks behave like a real device.
 *  - OPERATIONS: window lock/unlockAndPost/setBuffersGeometry honestly
 *    report no window buffers (AOSP negative/0 semantics, documented
 *    deviation: no pixels are served — the GL/EGL software path is the
 *    render surface); asset open returns NULL (asset absent = legal state
 *    apps must handle), asset read serves nothing.
 *  - No app special-casing: the surface is the platform primitive. */
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

/* ── ANativeWindow family ──────────────────────────────────────────────── */
typedef struct ANativeWindow ANativeWindow;
typedef struct ANativeWindow_Buffer {
    int32_t width, height, stride;  /* stride in pixels */
    int32_t format;
    void* bits;
} ANativeWindow_Buffer;

static void* ma_window_token(void* jsurface) {
    /* jobject/surface marshaling law: 0x500000000 | heap_id; 0 stays 0 */
    uint64_t v = (uint64_t)(uintptr_t)jsurface;
    if (!v) return NULL;
    return (void*)(uintptr_t)(0x600000000ull | (v & 0xffffffffull));
}

__attribute__((visibility("default")))
ANativeWindow* ANativeWindow_fromSurface(void* env, void* surface) {
    (void)env;
    return (ANativeWindow*)ma_window_token(surface);
}

__attribute__((visibility("default")))
void ANativeWindow_release(ANativeWindow* window) { (void)window; }

__attribute__((visibility("default")))
int ANativeWindow_lock(ANativeWindow* window, ANativeWindow_Buffer* outBuffer,
                       void* outRectangle) {
    /* honest: the software runtime's window has no lockable CPU buffer */
    (void)window; (void)outBuffer; (void)outRectangle;
    return -1; /* AOSP: nonzero = failure */
}

__attribute__((visibility("default")))
int ANativeWindow_unlockAndPost(ANativeWindow* window) {
    (void)window;
    return 0; /* nothing locked -> nothing to post (honest no-op) */
}

__attribute__((visibility("default")))
int32_t ANativeWindow_setBuffersGeometry(ANativeWindow* window, int32_t width,
                                         int32_t height, int32_t format) {
    /* accept the request (identity window keeps no geometry state) */
    (void)window; (void)width; (void)height; (void)format;
    return 0;
}

__attribute__((visibility("default")))
int32_t ANativeWindow_getWidth(ANativeWindow* window) {
    (void)window; return 0;
}

__attribute__((visibility("default")))
int32_t ANativeWindow_getHeight(ANativeWindow* window) {
    (void)window; return 0;
}

/* ── AAsset family (honest: engine-side assets are served by the DEX
 *    AssetManager shadow; the NDK AAsset surface has no file descriptors
 *    to hand out in this runtime) ──────────────────────────────────────── */
typedef struct AAssetManager AAssetManager;
typedef struct AAsset AAsset;

__attribute__((visibility("default")))
AAssetManager* AAssetManager_fromJava(void* env, void* assetManager) {
    (void)env;
    return (AAssetManager*)ma_window_token(assetManager);
}

__attribute__((visibility("default")))
AAsset* AAssetManager_open(AAssetManager* mgr, const char* filename, int mode) {
    (void)mgr; (void)filename; (void)mode;
    return NULL; /* asset absent — a legal state apps must handle */
}

__attribute__((visibility("default")))
void AAsset_close(AAsset* asset) { (void)asset; }

__attribute__((visibility("default")))
int AAsset_read(AAsset* asset, void* buf, size_t count) {
    (void)asset; (void)buf; (void)count;
    return 0; /* EOF on a NULL/absent asset */
}

/* ── S188-W2: the rest of the AAsset/ANativeWindow face libflutter.so
 * binds. NULL-asset law flows through: Flutter only reads an asset AFTER
 * AAssetManager_open returned non-NULL, and that stays NULL (asset absent
 * = legal state) — these exist so the DLOPEN proceeds and the absent-asset
 * branch is the one that runs. */
__attribute__((visibility("default")))
void* AAsset_getBuffer(AAsset* asset) { (void)asset; return NULL; }

__attribute__((visibility("default")))
long AAsset_getLength(AAsset* asset) { (void)asset; return 0; }

__attribute__((visibility("default")))
int AAsset_isAllocated(AAsset* asset) { (void)asset; return 0; }

/* WINDOW_FORMAT_RGBA_8888 = 1 (the software framebuffer's format) */
#define MA_WINDOW_FORMAT_RGBA8888 1
__attribute__((visibility("default")))
int32_t ANativeWindow_getFormat(ANativeWindow* window) {
    (void)window;
    return MA_WINDOW_FORMAT_RGBA8888;
}

/* ── S188-W2: ALooper — REAL epoll-backed event loop ────────────────────
 * libflutter.so binds the full ALooper face (prepare/acquire/release/
 * forThread/addFd/removeFd/pollOnce/pollAll/wake): the Flutter engine runs
 * its UI/Raster/IO threads on Android's looper, and the dlopen needs the
 * symbols AND the engine's poll loop needs REAL behavior (pollOnce blocks
 * on epoll_wait until wake or timeout — Android's own design, not a
 * fabricated immediate-return). One epoll instance per looper; wake is an
 * eventfd registered in the same epoll (how AOSP ALooper works).
 *
 * S188-W9 F-NEW-588 — AOSP CALLBACK-MODE CONTRACT (the hot-loop fix):
 * live queens evidence (evidence/s188_w9/W9E_FD_PROBE.json + W9F_FDSTATE.json
 * + the 1.raster/1.io stack walks) pinned the Dart-VM-init stall to this
 * file's W2 implementation: ALooper_addFd DISCARDED the callback
 * (`(void)callback`), so the engine's CALLBACK-mode-registered timerfd was
 * never drained. A fired timerfd stays EPOLLIN-ready (level-triggered)
 * forever -> epoll_wait returns instantly, forever -> the raster/io
 * MessageLoopAndroid threads burn 100% CPU and the Shell::Create latch on
 * the platform thread never closes (the W8 "two threads spin" stall).
 * AOSP contract restored, verified against frameworks/native/libutils/
 * Looper.cpp semantics:
 *   - return constants EXACT: POLL_WAKE(-1) POLL_CALLBACK(-2) TIMEOUT(-3)
 *     ERROR(-4)
 *   - addFd ident == ALOOPER_POLL_CALLBACK(-2) -> CALLBACK mode (callback
 *     required, invoked by pollOnce/pollAll, its return value returned);
 *     ident >= 0 -> data mode (outFd/outEvents/outData filled, ident
 *     returned); other negative -> ALOOPER_ADD_ERROR
 *   - pollOnce: dispatch ONE event (callback result or data ident)
 *   - pollAll: dispatch callback events CONTINUOUSLY until a data event,
 *     wake, timeout or error (AOSP pollAll semantics — dartjni's poll face)
 *   - ALOOPER_EVENT_* <-> EPOLL* translation incl. ERROR/HANGUP
 *   - EINTR: retry the wait (AOSP pollInner behavior), not a spurious WAKE
 *                                                                       */
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <pthread.h>
#include <errno.h>
#include <unistd.h>

#define ALOOPER_POLL_CALLBACK (-2)   /* AOSP Looper.h exact */
#define ALOOPER_POLL_TIMEOUT (-3)
#define ALOOPER_POLL_WAKE (-1)
#define ALOOPER_ERROR (-4)
#define ALOOPER_ADD_SUCCESS 1
#define ALOOPER_ADD_ERROR (-1)
#define ALOOPER_REMOVE_SUCCESS 1
#define ALOOPER_REMOVE_ERROR (-1)
#define ALOOPER_PREPARE_ALLOW_NON_CALLBACKS 1
#define ALOOPER_EVENT_INPUT 1u
#define ALOOPER_EVENT_OUTPUT 2u
#define ALOOPER_EVENT_ERROR 4u
#define ALOOPER_EVENT_HANGUP 8u
#define ALOOPER_EVENT_INVALID 0u

typedef int (*ma_alooper_cb)(int fd, int events, void* data);

typedef struct ma_looper_fd {
    int fd;
    int ident;             /* >=0 data mode; ALOOPER_POLL_CALLBACK cb mode */
    ma_alooper_cb cb;      /* callback mode only */
    void* data;
} ma_looper_fd;

typedef struct ma_looper {
    int epoll_fd;
    int wake_fd;
    int refs;
    pthread_mutex_t mu;
    struct ma_looper_fd fds[256];
    int n_fds;
} ma_looper;

static unsigned int ma_events_to_epoll(unsigned int alooper) {
    unsigned int e = 0;
    if (alooper & ALOOPER_EVENT_INPUT) e |= EPOLLIN;
    if (alooper & ALOOPER_EVENT_OUTPUT) e |= EPOLLOUT;
    if (alooper & ALOOPER_EVENT_ERROR) e |= EPOLLERR;
    if (alooper & ALOOPER_EVENT_HANGUP) e |= EPOLLHUP;
    return e;
}

static unsigned int ma_epoll_to_events(unsigned int epoll_ev) {
    unsigned int e = 0;
    if (epoll_ev & EPOLLIN) e |= ALOOPER_EVENT_INPUT;
    if (epoll_ev & EPOLLOUT) e |= ALOOPER_EVENT_OUTPUT;
    if (epoll_ev & EPOLLERR) e |= ALOOPER_EVENT_ERROR;
    if (epoll_ev & EPOLLHUP) e |= ALOOPER_EVENT_HANGUP;
    return e;
}

static pthread_key_t ma_looper_key;
static pthread_once_t ma_looper_once = PTHREAD_ONCE_INIT;

static void ma_looper_key_init(void) { pthread_key_create(&ma_looper_key, NULL); }

static ma_looper* ma_looper_new(void) {
    ma_looper* l = (ma_looper*)calloc(1, sizeof(ma_looper));
    if (!l) return NULL;
    l->epoll_fd = epoll_create1(0);
    l->wake_fd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
    pthread_mutex_init(&l->mu, NULL);
    if (l->epoll_fd >= 0 && l->wake_fd >= 0) {
        struct epoll_event ev;
        memset(&ev, 0, sizeof ev);
        ev.events = EPOLLIN;
        ev.data.u64 = 0xDEADC0DEull; /* wake marker */
        epoll_ctl(l->epoll_fd, EPOLL_CTL_ADD, l->wake_fd, &ev);
    }
    l->refs = 1;
    return l;
}

__attribute__((visibility("default")))
void* ALooper_prepare(int opts) {
    (void)opts;  /* ALLOW_NON_CALLBACKS is the only mode we serve */
    pthread_once(&ma_looper_once, ma_looper_key_init);
    ma_looper* l = (ma_looper*)pthread_getspecific(ma_looper_key);
    if (l) return l;
    l = ma_looper_new();
    if (l) pthread_setspecific(ma_looper_key, l);
    return l;
}

__attribute__((visibility("default")))
void ALooper_acquire(void* looper) {
    ma_looper* l = (ma_looper*)looper;
    if (!l) return;
    pthread_mutex_lock(&l->mu);
    ++l->refs;
    pthread_mutex_unlock(&l->mu);
}

__attribute__((visibility("default")))
void ALooper_release(void* looper) {
    ma_looper* l = (ma_looper*)looper;
    if (!l) return;
    pthread_mutex_lock(&l->mu);
    int last = (--l->refs == 0);
    pthread_mutex_unlock(&l->mu);
    if (last) {
        if (l->wake_fd >= 0) close(l->wake_fd);
        if (l->epoll_fd >= 0) close(l->epoll_fd);
        pthread_mutex_destroy(&l->mu);
        free(l);
    }
}

__attribute__((visibility("default")))
void* ALooper_forThread(void) {
    pthread_once(&ma_looper_once, ma_looper_key_init);
    return pthread_getspecific(ma_looper_key);
}

__attribute__((visibility("default")))
int ALooper_addFd(void* looper, int fd, int ident, unsigned int events,
                  void* callback, void* data) {
    ma_looper* l = (ma_looper*)looper;
    if (!l || fd < 0) return ALOOPER_ADD_ERROR;
    /* AOSP: ALOOPER_POLL_CALLBACK(-2) = callback mode (callback required);
       ident >= 0 = data mode; any other negative = invalid. */
    ma_alooper_cb cb = (ma_alooper_cb)callback;
    if (ident == ALOOPER_POLL_CALLBACK) {
        if (!cb) return ALOOPER_ADD_ERROR;
    } else if (ident < 0) {
        return ALOOPER_ADD_ERROR;
    }
    struct epoll_event ev;
    memset(&ev, 0, sizeof ev);
    ev.events = ma_events_to_epoll(events ? events : ALOOPER_EVENT_INPUT);
    /* EPOLLERR/EPOLLHUP are always reported by epoll regardless (AOSP). */
    ev.events |= EPOLLERR | EPOLLHUP;
    ev.data.u64 = (uint64_t)(uint32_t)fd;
    if (epoll_ctl(l->epoll_fd, EPOLL_CTL_ADD, fd, &ev) != 0 && errno != EEXIST)
        return ALOOPER_ADD_ERROR;
    pthread_mutex_lock(&l->mu);
    int slot = -1;
    for (int i = 0; i < l->n_fds; ++i)
        if (l->fds[i].fd == fd) { slot = i; break; }  /* re-add: update */
    if (slot < 0 && l->n_fds < 256) slot = l->n_fds++;
    if (slot >= 0) {
        l->fds[slot].fd = fd;
        l->fds[slot].ident = ident;
        l->fds[slot].cb = cb;
        l->fds[slot].data = data;
    }
    pthread_mutex_unlock(&l->mu);
    return ALOOPER_ADD_SUCCESS;
}

__attribute__((visibility("default")))
int ALooper_removeFd(void* looper, int fd) {
    ma_looper* l = (ma_looper*)looper;
    if (!l || fd < 0) return ALOOPER_REMOVE_ERROR;
    epoll_ctl(l->epoll_fd, EPOLL_CTL_DEL, fd, NULL);
    pthread_mutex_lock(&l->mu);
    int found = 0;
    for (int i = 0; i < l->n_fds; ++i)
        if (l->fds[i].fd == fd) {
            l->fds[i] = l->fds[l->n_fds - 1];
            --l->n_fds;
            found = 1;
            break;
        }
    pthread_mutex_unlock(&l->mu);
    return found ? ALOOPER_REMOVE_SUCCESS : ALOOPER_REMOVE_ERROR;
}

/* One epoll_wait dispatch, shared by pollOnce/pollAll (dispatch inline in
   ma_poll_inner below). */
static int ma_lookup_fd(ma_looper* l, int fd, int* ident, ma_alooper_cb* cb,
                        void** data) {
    *ident = 0; *cb = NULL; *data = NULL;
    pthread_mutex_lock(&l->mu);
    for (int i = 0; i < l->n_fds; ++i)
        if (l->fds[i].fd == fd) {
            *ident = l->fds[i].ident;
            *cb = l->fds[i].cb;
            *data = l->fds[i].data;
            pthread_mutex_unlock(&l->mu);
            return 1;
        }
    pthread_mutex_unlock(&l->mu);
    return 0;
}

static int ma_poll_inner(ma_looper* l, int timeout, int* outFd,
                         unsigned int* outEvents, void** outData,
                         int* was_callback) {
    *was_callback = 0;
    struct epoll_event ev;
    memset(&ev, 0, sizeof ev);
    int n;
    do {
        n = epoll_wait(l->epoll_fd, &ev, 1, timeout);
    } while (n < 0 && errno == EINTR);   /* AOSP: retry on EINTR */
    if (n < 0) return ALOOPER_ERROR;
    if (n == 0) return ALOOPER_POLL_TIMEOUT;
    if (ev.data.u64 == 0xDEADC0DEull) {
        /* wake: drain the eventfd (the level-triggered face must clear) */
        uint64_t one = 0;
        ssize_t r = read(l->wake_fd, &one, sizeof one);
        (void)r;
        return ALOOPER_POLL_WAKE;
    }
    int fd = (int)(ev.data.u64 & 0xffffffffu);
    int ident;
    ma_alooper_cb cb;
    void* data;
    unsigned int events = ma_epoll_to_events(ev.events);
    if (!ma_lookup_fd(l, fd, &ident, &cb, &data)) {
        /* fd removed between add and event: serve as a data event with 0 */
        if (outFd) *outFd = fd;
        if (outEvents) *outEvents = events;
        if (outData) *outData = NULL;
        return 0;
    }
    if (cb) {
        *was_callback = 1;
        if (outFd) *outFd = fd;
        if (outEvents) *outEvents = events;
        if (outData) *outData = data;
        return cb(fd, (int)events, data);  /* the callback drains its fd */
    }
    if (outFd) *outFd = fd;
    if (outEvents) *outEvents = events;
    if (outData) *outData = data;
    return ident;
}

__attribute__((visibility("default")))
int ALooper_pollOnce(int timeout, int* outFd, unsigned int* outEvents,
                     void** outData) {
    ma_looper* l = (ma_looper*)pthread_getspecific(ma_looper_key);
    if (!l) l = (ma_looper*)ALooper_prepare(ALOOPER_PREPARE_ALLOW_NON_CALLBACKS);
    if (!l || l->epoll_fd < 0) return ALOOPER_ERROR;
    int was_cb;
    return ma_poll_inner(l, timeout, outFd, outEvents, outData, &was_cb);
}

/* AOSP pollAll: callback-mode events are dispatched CONTINUOUSLY inside the
 * call (each callback drains its own fd — the engine's timerfd face); the
 * call returns only on wake / timeout / error / data event. The first wait
 * honors the caller timeout; pending-event waits afterwards are 0ms. This
 * is the poll face dartjni (jni_native_loop) uses. */
__attribute__((visibility("default")))
int ALooper_pollAll(int timeout, int* outFd, unsigned int* outEvents,
                    void** outData) {
    ma_looper* l = (ma_looper*)pthread_getspecific(ma_looper_key);
    if (!l) l = (ma_looper*)ALooper_prepare(ALOOPER_PREPARE_ALLOW_NON_CALLBACKS);
    if (!l || l->epoll_fd < 0) return ALOOPER_ERROR;
    int was_cb;
    for (;;) {
        int rc = ma_poll_inner(l, timeout, outFd, outEvents, outData, &was_cb);
        timeout = 0;  /* subsequent iterations drain pending events only */
        if (rc == ALOOPER_POLL_WAKE || rc == ALOOPER_POLL_TIMEOUT ||
            rc == ALOOPER_ERROR || !was_cb)
            return rc;
        /* callback result: dispatched inside, keep draining (AOSP) */
    }
}

__attribute__((visibility("default")))
void ALooper_wake(void* looper) {
    ma_looper* l = (ma_looper*)looper;
    if (!l || l->wake_fd < 0) return;
    uint64_t one = 1;
    ssize_t r = write(l->wake_fd, &one, sizeof one);
    (void)r;
}
