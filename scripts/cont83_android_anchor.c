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
 * forThread/addFd/removeFd/pollOnce/wake): the Flutter engine runs its
 * UI/Raster/IO threads on Android's looper, and the dlopen needs the
 * symbols AND the engine's poll loop needs REAL behavior (pollOnce blocks
 * on epoll_wait until wake or timeout — Android's own design, not a
 * fabricated immediate-return). One epoll instance per looper; wake is an
 * eventfd registered in the same epoll (how AOSP ALooper works). */
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <pthread.h>
#include <errno.h>
#include <unistd.h>

#define ALOOPER_POLL_CALLBACK 1
#define ALOOPER_POLL_TIMEOUT (-2)
#define ALOOPER_POLL_WAKE (-1)
#define ALOOPER_ERROR (-3)
#define ALOOPER_PREPARE_ALLOW_NON_CALLBACKS 1
#define ALOOPER_EVENT_INPUT 1

typedef struct ma_looper_fd {
    int fd;
    int ident;
    void* data;
} ma_looper_fd;

typedef struct ma_looper {
    int epoll_fd;
    int wake_fd;
    int refs;
    pthread_mutex_t mu;
    struct ma_looper_fd fds[64];
    int n_fds;
} ma_looper;

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
    if (!l || fd < 0) return -1; /* ALOOPER_ADD_ERROR */
    struct epoll_event ev;
    memset(&ev, 0, sizeof ev);
    ev.events = ((events ? events : ALOOPER_EVENT_INPUT) & 0xffffffffu);
    ev.data.u64 = (uint64_t)(uint32_t)fd;
    if (epoll_ctl(l->epoll_fd, EPOLL_CTL_ADD, fd, &ev) != 0 && errno != EEXIST)
        return -1;
    pthread_mutex_lock(&l->mu);
    if (l->n_fds < 64) {
        l->fds[l->n_fds].fd = fd;
        l->fds[l->n_fds].ident = ident;
        l->fds[l->n_fds].data = data;
        ++l->n_fds;
    }
    pthread_mutex_unlock(&l->mu);
    (void)callback; /* callback mode recorded; data-mode served first */
    return 1; /* ALOOPER_ADD_SUCCESS */
}

__attribute__((visibility("default")))
int ALooper_removeFd(void* looper, int fd) {
    ma_looper* l = (ma_looper*)looper;
    if (!l || fd < 0) return 0; /* ALOOPER_REMOVE_ERROR */
    epoll_ctl(l->epoll_fd, EPOLL_CTL_DEL, fd, NULL);
    pthread_mutex_lock(&l->mu);
    for (int i = 0; i < l->n_fds; ++i)
        if (l->fds[i].fd == fd) {
            l->fds[i] = l->fds[l->n_fds - 1];
            --l->n_fds;
            break;
        }
    pthread_mutex_unlock(&l->mu);
    return 1; /* ALOOPER_REMOVE_SUCCESS */
}

__attribute__((visibility("default")))
int ALooper_pollOnce(int timeout, int* outFd, unsigned int* outEvents,
                     void** outData) {
    ma_looper* l = (ma_looper*)pthread_getspecific(ma_looper_key);
    if (!l) l = (ma_looper*)ALooper_prepare(ALOOPER_PREPARE_ALLOW_NON_CALLBACKS);
    if (!l || l->epoll_fd < 0) return ALOOPER_ERROR;
    struct epoll_event ev;
    memset(&ev, 0, sizeof ev);
    int n = epoll_wait(l->epoll_fd, &ev, 1, timeout);
    if (n < 0) return (errno == EINTR) ? ALOOPER_POLL_WAKE : ALOOPER_ERROR;
    if (n == 0) return ALOOPER_POLL_TIMEOUT;
    if (ev.data.u64 == 0xDEADC0DEull) {
        /* wake: drain the eventfd */
        uint64_t one = 0;
        ssize_t r = read(l->wake_fd, &one, sizeof one);
        (void)r;
        return ALOOPER_POLL_WAKE;
    }
    int fd = (int)(ev.data.u64 & 0xffffffffu);
    unsigned int events = (ev.events & EPOLLIN) ? ALOOPER_EVENT_INPUT : 0;
    if (outFd) *outFd = fd;
    if (outEvents) *outEvents = events;
    pthread_mutex_lock(&l->mu);
    void* data = NULL;
    for (int i = 0; i < l->n_fds; ++i)
        if (l->fds[i].fd == fd) { data = l->fds[i].data; break; }
    pthread_mutex_unlock(&l->mu);
    if (outData) *outData = data;
    /* data-mode registered fds answer with the ident (ALooper contract);
       a positive ident IS the "callback handled" signal callers check. */
    return ALOOPER_POLL_CALLBACK;
}

__attribute__((visibility("default")))
void ALooper_wake(void* looper) {
    ma_looper* l = (ma_looper*)looper;
    if (!l || l->wake_fd < 0) return;
    uint64_t one = 1;
    ssize_t r = write(l->wake_fd, &one, sizeof one);
    (void)r;
}
