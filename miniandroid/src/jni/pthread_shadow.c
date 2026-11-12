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

/* GP S225-M §6 (#585 findings 6+7): LOCKED-SECTION LAW.
 *
 * The old helpers released g_slots_mu and returned a live ShadowSlot*;
 * a concurrent shadow_close() swap-removed that slot, so every caller
 * that touched fields after unlock could hit ANOTHER key's slot or a
 * freed heap attr (the close-vs-use window). Every registry operation
 * is now atomic under g_slots_mu: lookup + state write + real-attr call
 * run inside ONE critical section, and the passthrough consumers
 * (mutex/cond/thread init, attr_getstack) hold the lock while they
 * borrow s->real. Nothing inside a critical section re-enters this
 * module (the real glibc attr functions never take g_slots_mu), so the
 * lock is deadlock-free; the only cost is that pthread_create holds the
 * registry lock for its spawn window — bounded by the real call.
 */
static struct ShadowSlot* find_locked(void* key, int kind) {
    /* caller holds g_slots_mu */
    for (int i = 0; i < g_slots_n; ++i)
        if (g_slots[i].key == key && g_slots[i].kind == kind)
            return &g_slots[i];
    return NULL;
}
static struct ShadowSlot* open_locked(void* key, int kind) {
    /* caller holds g_slots_mu */
    struct ShadowSlot* s = find_locked(key, kind);
    if (s) return s;
    if (g_slots_n >= SHADOW_CAP) return NULL;
    struct ShadowSlot* s2 = &g_slots[g_slots_n++];
    memset(s2, 0, sizeof(*s2));
    s2->key = key; s2->kind = kind; s2->clock = -1; s2->type = -1;
    return s2;
}
static void close_locked(void* key, int kind) {
    /* caller holds g_slots_mu */
    for (int i = 0; i < g_slots_n; ++i)
        if (g_slots[i].key == key && g_slots[i].kind == kind) {
            free(g_slots[i].real);
            g_slots[i] = g_slots[g_slots_n - 1];
            --g_slots_n;
            break;
        }
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
/* GP S225-M §6 finding 7: POSIX error semantics. init returns ENOMEM when
 * the registry is exhausted or the heap attr cannot be minted (it used to
 * report success while silently skipping the real init — every setter then
 * degraded to a no-op with wrong synchronization semantics). Setters/getters
 * on an UNKNOWN key answer EINVAL (the only legal ways to see one are
 * use-before-init, use-after-destroy, or a failed init). */
int pthread_mutexattr_init(pthread_mutexattr_t* key) {
    DEF_REAL(pthread_mutexattr_init);
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = open_locked(key, 0);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return ENOMEM; }
    if (!s->real) {
        s->real = malloc(sizeof(pthread_mutexattr_t));
        if (!s->real) { pthread_mutex_unlock(&g_slots_mu); return ENOMEM; }
        if (r_pthread_mutexattr_init((pthread_mutexattr_t*)s->real) != 0) {
            free(s->real); s->real = NULL;
            pthread_mutex_unlock(&g_slots_mu);
            return ENOMEM;
        }
    }
    pthread_mutex_unlock(&g_slots_mu);
    return 0;
}
int pthread_mutexattr_destroy(pthread_mutexattr_t* key) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 0);
    if (s) shadow_free_obj(s, 0);
    close_locked(key, 0);
    pthread_mutex_unlock(&g_slots_mu);
    return 0;
}
int pthread_mutexattr_settype(pthread_mutexattr_t* key, int type) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 0);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return EINVAL; }
    s->type = type;
    int rc = 0;
    if (s->real) {
        DEF_REAL(pthread_mutexattr_settype);
        rc = r_pthread_mutexattr_settype((pthread_mutexattr_t*)s->real, type);
    }
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
}
int pthread_mutexattr_gettype(const pthread_mutexattr_t* key, int* type) {
    if (type == NULL) return EINVAL;
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked((void*)key, 0);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return EINVAL; }
    *type = (s->type < 0) ? PTHREAD_MUTEX_DEFAULT : s->type;
    pthread_mutex_unlock(&g_slots_mu);
    return 0;
}
int pthread_mutexattr_setpshared(pthread_mutexattr_t* key, int pshared) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 0);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return EINVAL; }
    s->pshared = pshared;
    int rc = 0;
    if (s->real) {
        DEF_REAL(pthread_mutexattr_setpshared);
        rc = r_pthread_mutexattr_setpshared((pthread_mutexattr_t*)s->real, pshared);
    }
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
}

/* ── mutex objects (layout-compatible x86_64: 40 bytes both ABIs) ────── */
int pthread_mutex_init(pthread_mutex_t* m, const pthread_mutexattr_t* key) {
    DEF_REAL(pthread_mutex_init);
    if (!key) return r_pthread_mutex_init(m, NULL);
    /* GP S225-M §6: borrow the real attr UNDER the lock — a concurrent
     * attr destroy can no longer free it between find and use. */
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked((void*)key, 0);
    const pthread_mutexattr_t* use =
        (s && s->real) ? (const pthread_mutexattr_t*)s->real : key;
    /* the shadow's REAL attr carries the exact caller state (type etc.);
       a caller that never called attr_init gets the glibc default */
    int rc = r_pthread_mutex_init(m, use);
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
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
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = open_locked(key, 1);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return ENOMEM; }
    if (!s->real) {
        s->real = malloc(sizeof(pthread_condattr_t));
        if (!s->real) { pthread_mutex_unlock(&g_slots_mu); return ENOMEM; }
        if (r_pthread_condattr_init((pthread_condattr_t*)s->real) != 0) {
            free(s->real); s->real = NULL;
            pthread_mutex_unlock(&g_slots_mu);
            return ENOMEM;
        }
    }
    pthread_mutex_unlock(&g_slots_mu);
    return 0;
}
int pthread_condattr_destroy(pthread_condattr_t* key) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 1);
    if (s) shadow_free_obj(s, 1);
    close_locked(key, 1);
    pthread_mutex_unlock(&g_slots_mu);
    return 0;
}
int pthread_condattr_setclock(pthread_condattr_t* key, clockid_t clock) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 1);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return EINVAL; }
    s->clock = (long)clock;
    int rc = 0;
    if (s->real) {
        DEF_REAL(pthread_condattr_setclock);
        rc = r_pthread_condattr_setclock((pthread_condattr_t*)s->real, clock);
    }
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
}

/* ── cond objects (layout-compatible x86_64: 48 bytes both ABIs) ─────── */
int pthread_cond_init(pthread_cond_t* c, const pthread_condattr_t* key) {
    DEF_REAL(pthread_cond_init);
    if (!key) return r_pthread_cond_init(c, NULL);
    /* GP S225-M §6: borrow the real attr under the lock (see mutex_init). */
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked((void*)key, 1);
    const pthread_condattr_t* use =
        (s && s->real) ? (const pthread_condattr_t*)s->real : key;
    int rc = r_pthread_cond_init(c, use);
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
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
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = open_locked(key, 2);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return ENOMEM; }
    if (!s->real) {
        s->real = malloc(sizeof(pthread_attr_t));
        if (!s->real) { pthread_mutex_unlock(&g_slots_mu); return ENOMEM; }
        if (r_pthread_attr_init((pthread_attr_t*)s->real) != 0) {
            free(s->real); s->real = NULL;
            pthread_mutex_unlock(&g_slots_mu);
            return ENOMEM;
        }
    }
    pthread_mutex_unlock(&g_slots_mu);
    return 0;
}
int pthread_attr_destroy(pthread_attr_t* key) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 2);
    if (s) shadow_free_obj(s, 2);
    close_locked(key, 2);
    pthread_mutex_unlock(&g_slots_mu);
    return 0;
}
int pthread_attr_setstacksize(pthread_attr_t* key, size_t stacksize) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 2);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return EINVAL; }
    s->stacksize = (unsigned long)stacksize;
    int rc = 0;
    if (s->real) {
        DEF_REAL(pthread_attr_setstacksize);
        rc = r_pthread_attr_setstacksize((pthread_attr_t*)s->real, stacksize);
    }
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
}
int pthread_attr_setdetachstate(pthread_attr_t* key, int detachstate) {
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked(key, 2);
    if (!s) { pthread_mutex_unlock(&g_slots_mu); return EINVAL; }
    s->detachstate = detachstate;
    int rc = 0;
    if (s->real) {
        DEF_REAL(pthread_attr_setdetachstate);
        rc = r_pthread_attr_setdetachstate((pthread_attr_t*)s->real, detachstate);
    }
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
}
int pthread_attr_getstack(const pthread_attr_t* key, void** stackaddr,
                          size_t* stacksize) {
    DEF_REAL(pthread_attr_getstack);
    /* registered attrs carry our default-real object (honest defaults);
       unregistered pointers are genuine glibc attrs — pass through (with
       the borrow held under the lock, same as the init consumers). */
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked((void*)key, 2);
    int rc;
    if (!s || !s->real)
        rc = r_pthread_attr_getstack(key, stackaddr, stacksize);
    else
        rc = r_pthread_attr_getstack((pthread_attr_t*)s->real, stackaddr,
                                     stacksize);
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
}
int pthread_create(pthread_t* t, const pthread_attr_t* key,
                   void* (*fn)(void*), void* arg) {
    DEF_REAL(pthread_create);
    if (!key) return r_pthread_create(t, NULL, fn, arg);
    /* GP S225-M §6: the real attr borrow is under the lock; the spawn
     * window holds g_slots_mu — bounded by the real pthread_create. */
    pthread_mutex_lock(&g_slots_mu);
    struct ShadowSlot* s = find_locked((void*)key, 2);
    const pthread_attr_t* use =
        (s && s->real) ? (const pthread_attr_t*)s->real : key;
    int rc = r_pthread_create(t, use, fn, arg);
    pthread_mutex_unlock(&g_slots_mu);
    return rc;
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
