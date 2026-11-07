/* pthread_shadow.c — S188-W8 F-NEW-585: bionic pthread-attr shadow family.
 *
 * ROOT (live queens W8 evidence, evidence/s188_w8/QUEENS_SLOT_CENSUS.json +
 * queens_slot_census.console.log): libflutter's Dart runtime aborts at
 * synchronization_posix.cc:87 "pthread error: 22 (Invalid argument)" —
 * [BIONIC-ABORT] guarded, runtime survived. The library is compiled for
 * bionic, where pthread_mutexattr_t/pthread_condattr_t/pthread_attr_t are
 * 4-byte opaque objects; the host glibc's are 56-byte structs. Dart's
 * Mutex() allocates a 4-byte attr on ITS stack and calls glibc's
 * pthread_mutexattr_init, which writes 56 bytes — stack corruption, then
 * the next pthread call reads a garbage attr and answers EINVAL (22).
 *
 * LAW (same precedent as the FORTIFY _chk family in bionic_compat.c: the
 * exe is -rdynamic, so its exported symbols interpose for libraries loaded
 * later by the runtime's own loader — the Android linker-namespace analog):
 * the attr-family functions are shadowed with a side registry keyed by the
 * CALLER's attr pointer; the real glibc attr objects live on the heap.
 * The caller's object is NEVER dereferenced, so bionic-sized (4-byte) and
 * glibc-sized (56-byte) callers get identical, correct behavior. Every
 * consumer of the attr also goes through the shadow (attrs are opaque —
 * no code touches their fields directly), so the design is
 * behavior-preserving for glibc-compiled callers too (libgdx64.so etc.).
 * Mutex/cond objects themselves are layout-compatible on x86_64 (bionic
 * pthread_mutex_t = glibc pthread_mutex_t = 40 bytes; pthread_cond_t = 48
 * bytes) and pass straight through to the real functions.
 *
 * Real functions resolve via RTLD_NEXT once and are cached. The
 * hot-path functions (lock/unlock/trylock) never touch the registry.
 */
#define _GNU_SOURCE
#include <pthread.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <errno.h>

/* ── real-function cache (RTLD_NEXT, resolved lazily once) ───────────── */
#define DEF_REAL(name)                                                        \
    static typeof(name)* r_##name = NULL;                                     \
    if (!r_##name) {                                                          \
        r_##name = (typeof(name)*)dlsym(RTLD_NEXT, #name);                    \
        if (!r_##name) {                                                      \
            fprintf(stderr, "[PTHREAD-SHADOW] missing real " #name "\n");     \
            abort();                                                          \
        }                                                                     \
    }

/* ── side registry: caller's attr pointer -> real heap attr + state ──── */
#define SHADOW_CAP 1024
struct ShadowSlot {
    void* key;
    void* real;      /* heap-allocated REAL glibc attr object   */
    int kind;        /* 0 mutexattr, 1 condattr, 2 threadattr   */
    int type;        /* mutexattr type (default normal)         */
    int pshared;     /* PTHREAD_PROCESS_PRIVATE default         */
    long clock;      /* condattr clock, -1 = unset              */
    unsigned long stacksize;   /* threadattr                    */
    int detachstate;           /* threadattr                    */
};
static struct ShadowSlot g_slots[SHADOW_CAP];
static int g_slots_n = 0;
static pthread_mutex_t g_slots_mu = PTHREAD_MUTEX_INITIALIZER;

static struct ShadowSlot* shadow_open(void* key, int kind) {
    pthread_mutex_lock(&g_slots_mu);
    for (int i = 0; i < g_slots_n; ++i)
        if (g_slots[i].key == key && g_slots[i].kind == kind) {
            pthread_mutex_unlock(&g_slots_mu);
            return &g_slots[i];
        }
    if (g_slots_n >= SHADOW_CAP) { pthread_mutex_unlock(&g_slots_mu); return NULL; }
    struct ShadowSlot* s = &g_slots[g_slots_n++];
    memset(s, 0, sizeof(*s));
    s->key = key; s->kind = kind; s->clock = -1; s->type = -1;
    pthread_mutex_unlock(&g_slots_mu);
    return s;
}
static struct ShadowSlot* shadow_find(void* key, int kind) {
    pthread_mutex_lock(&g_slots_mu);
    for (int i = 0; i < g_slots_n; ++i)
        if (g_slots[i].key == key && g_slots[i].kind == kind) {
            pthread_mutex_unlock(&g_slots_mu);
            return &g_slots[i];
        }
    pthread_mutex_unlock(&g_slots_mu);
    return NULL;
}
static void shadow_close(void* key, int kind) {
    pthread_mutex_lock(&g_slots_mu);
    for (int i = 0; i < g_slots_n; ++i)
        if (g_slots[i].key == key && g_slots[i].kind == kind) {
            free(g_slots[i].real);
            g_slots[i] = g_slots[g_slots_n - 1];
            --g_slots_n;
            break;
        }
    pthread_mutex_unlock(&g_slots_mu);
}
static void shadow_free_obj(struct ShadowSlot* s, int kind) {
    if (!s || !s->real) return;
    if (kind == 0) {
        DEF_REAL(pthread_mutexattr_destroy);
        r_pthread_mutexattr_destroy((pthread_mutexattr_t*)s->real);
    } else if (kind == 1) {
        DEF_REAL(pthread_condattr_destroy);
        r_pthread_condattr_destroy((pthread_condattr_t*)s->real);
    } else {
        DEF_REAL(pthread_attr_destroy);
        r_pthread_attr_destroy((pthread_attr_t*)s->real);
    }
    free(s->real);
    s->real = NULL;
}

/* ── mutexattr family ────────────────────────────────────────────────── */
int pthread_mutexattr_init(pthread_mutexattr_t* key) {
    DEF_REAL(pthread_mutexattr_init);
    struct ShadowSlot* s = shadow_open(key, 0);
    if (s && !s->real) {
        s->real = malloc(sizeof(pthread_mutexattr_t));
        if (s->real) r_pthread_mutexattr_init((pthread_mutexattr_t*)s->real);
    }
    return 0;
}
int pthread_mutexattr_destroy(pthread_mutexattr_t* key) {
    struct ShadowSlot* s = shadow_find(key, 0);
    if (s) shadow_free_obj(s, 0);
    shadow_close(key, 0);
    return 0;
}
int pthread_mutexattr_settype(pthread_mutexattr_t* key, int type) {
    struct ShadowSlot* s = shadow_find(key, 0);
    if (!s) return 0;  /* never crash the library for an attr we missed */
    s->type = type;
    if (s->real) {
        DEF_REAL(pthread_mutexattr_settype);
        return r_pthread_mutexattr_settype((pthread_mutexattr_t*)s->real, type);
    }
    return 0;
}
int pthread_mutexattr_gettype(const pthread_mutexattr_t* key, int* type) {
    struct ShadowSlot* s = shadow_find((void*)key, 0);
    if (!s || type == NULL) return 0;
    *type = (s->type < 0) ? PTHREAD_MUTEX_DEFAULT : s->type;
    return 0;
}
int pthread_mutexattr_setpshared(pthread_mutexattr_t* key, int pshared) {
    struct ShadowSlot* s = shadow_find(key, 0);
    if (!s) return 0;
    s->pshared = pshared;
    if (s->real) {
        DEF_REAL(pthread_mutexattr_setpshared);
        return r_pthread_mutexattr_setpshared((pthread_mutexattr_t*)s->real, pshared);
    }
    return 0;
}

/* ── mutex objects (layout-compatible x86_64: 40 bytes both ABIs) ────── */
int pthread_mutex_init(pthread_mutex_t* m, const pthread_mutexattr_t* key) {
    DEF_REAL(pthread_mutex_init);
    struct ShadowSlot* s = key ? shadow_find((void*)key, 0) : NULL;
    /* the shadow's REAL attr carries the exact caller state (type etc.);
       a caller that never called attr_init gets the glibc default */
    return r_pthread_mutex_init(
        m, (const pthread_mutexattr_t*)(s && s->real ? s->real : key));
}
int pthread_mutex_destroy(pthread_mutex_t* m) {
    DEF_REAL(pthread_mutex_destroy); return r_pthread_mutex_destroy(m);
}
int pthread_mutex_lock(pthread_mutex_t* m) {
    DEF_REAL(pthread_mutex_lock); return r_pthread_mutex_lock(m);
}
int pthread_mutex_unlock(pthread_mutex_t* m) {
    DEF_REAL(pthread_mutex_unlock); return r_pthread_mutex_unlock(m);
}
int pthread_mutex_trylock(pthread_mutex_t* m) {
    DEF_REAL(pthread_mutex_trylock); return r_pthread_mutex_trylock(m);
}

/* ── condattr family ─────────────────────────────────────────────────── */
int pthread_condattr_init(pthread_condattr_t* key) {
    DEF_REAL(pthread_condattr_init);
    struct ShadowSlot* s = shadow_open(key, 1);
    if (s && !s->real) {
        s->real = malloc(sizeof(pthread_condattr_t));
        if (s->real) r_pthread_condattr_init((pthread_condattr_t*)s->real);
    }
    return 0;
}
int pthread_condattr_destroy(pthread_condattr_t* key) {
    struct ShadowSlot* s = shadow_find(key, 1);
    if (s) shadow_free_obj(s, 1);
    shadow_close(key, 1);
    return 0;
}
int pthread_condattr_setclock(pthread_condattr_t* key, clockid_t clock) {
    struct ShadowSlot* s = shadow_find(key, 1);
    if (!s) return 0;
    s->clock = (long)clock;
    if (s->real) {
        DEF_REAL(pthread_condattr_setclock);
        return r_pthread_condattr_setclock((pthread_condattr_t*)s->real, clock);
    }
    return 0;
}

/* ── cond objects (layout-compatible x86_64: 48 bytes both ABIs) ─────── */
int pthread_cond_init(pthread_cond_t* c, const pthread_condattr_t* key) {
    DEF_REAL(pthread_cond_init);
    struct ShadowSlot* s = key ? shadow_find((void*)key, 1) : NULL;
    return r_pthread_cond_init(
        c, (const pthread_condattr_t*)(s && s->real ? s->real : key));
}
int pthread_cond_destroy(pthread_cond_t* c) {
    DEF_REAL(pthread_cond_destroy); return r_pthread_cond_destroy(c);
}
int pthread_cond_signal(pthread_cond_t* c) {
    DEF_REAL(pthread_cond_signal); return r_pthread_cond_signal(c);
}
int pthread_cond_broadcast(pthread_cond_t* c) {
    DEF_REAL(pthread_cond_broadcast); return r_pthread_cond_broadcast(c);
}
int pthread_cond_wait(pthread_cond_t* c, pthread_mutex_t* m) {
    DEF_REAL(pthread_cond_wait); return r_pthread_cond_wait(c, m);
}
int pthread_cond_timedwait(pthread_cond_t* c, pthread_mutex_t* m,
                           const struct timespec* t) {
    DEF_REAL(pthread_cond_timedwait); return r_pthread_cond_timedwait(c, m, t);
}

/* ── threadattr family + create ──────────────────────────────────────── */
int pthread_attr_init(pthread_attr_t* key) {
    DEF_REAL(pthread_attr_init);
    struct ShadowSlot* s = shadow_open(key, 2);
    if (s && !s->real) {
        s->real = malloc(sizeof(pthread_attr_t));
        if (s->real) r_pthread_attr_init((pthread_attr_t*)s->real);
    }
    return 0;
}
int pthread_attr_destroy(pthread_attr_t* key) {
    struct ShadowSlot* s = shadow_find(key, 2);
    if (s) shadow_free_obj(s, 2);
    shadow_close(key, 2);
    return 0;
}
int pthread_attr_setstacksize(pthread_attr_t* key, size_t stacksize) {
    struct ShadowSlot* s = shadow_find(key, 2);
    if (!s) return 0;
    s->stacksize = (unsigned long)stacksize;
    if (s->real) {
        DEF_REAL(pthread_attr_setstacksize);
        return r_pthread_attr_setstacksize((pthread_attr_t*)s->real, stacksize);
    }
    return 0;
}
int pthread_attr_setdetachstate(pthread_attr_t* key, int detachstate) {
    struct ShadowSlot* s = shadow_find(key, 2);
    if (!s) return 0;
    s->detachstate = detachstate;
    if (s->real) {
        DEF_REAL(pthread_attr_setdetachstate);
        return r_pthread_attr_setdetachstate((pthread_attr_t*)s->real, detachstate);
    }
    return 0;
}
int pthread_attr_getstack(const pthread_attr_t* key, void** stackaddr,
                          size_t* stacksize) {
    DEF_REAL(pthread_attr_getstack);
    /* registered attrs carry our default-real object (honest defaults);
       unregistered pointers are genuine glibc attrs — pass through */
    struct ShadowSlot* s = shadow_find((void*)key, 2);
    if (!s || !s->real) return r_pthread_attr_getstack(key, stackaddr, stacksize);
    return r_pthread_attr_getstack((pthread_attr_t*)s->real, stackaddr, stacksize);
}
int pthread_create(pthread_t* t, const pthread_attr_t* key,
                   void* (*fn)(void*), void* arg) {
    DEF_REAL(pthread_create);
    struct ShadowSlot* s = key ? shadow_find((void*)key, 2) : NULL;
    return r_pthread_create(
        t, (const pthread_attr_t*)(s && s->real ? s->real : key), fn, arg);
}

/* ── TLS keys (pthread_key_t: unsigned on both ABIs) — pass through ──── */
int pthread_key_create(pthread_key_t* k, void (*dtor)(void*)) {
    DEF_REAL(pthread_key_create); return r_pthread_key_create(k, dtor);
}
int pthread_key_delete(pthread_key_t k) {
    DEF_REAL(pthread_key_delete); return r_pthread_key_delete(k);
}
void* pthread_getspecific(pthread_key_t k) {
    DEF_REAL(pthread_getspecific); return r_pthread_getspecific(k);
}
int pthread_setspecific(pthread_key_t k, const void* v) {
    DEF_REAL(pthread_setspecific); return r_pthread_setspecific(k, v);
}
