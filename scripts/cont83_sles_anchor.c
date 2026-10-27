/* T22 (F-NEW-564 support): libOpenSLES anchor — the OpenSLES SPEC surface.
 *
 * T18's named design, reconstructed: the anchor exports the OpenSL ES
 * interface-IID GUIDs (SL_IID_*) exactly as the Android NDK spec defines
 * them (each is an SLInterfaceID_ = a 16-byte GUID), plus slCreateEngine
 * with the honest FEATURE_UNSUPPORTED verdict — audio OUTPUT is a no-op
 * in this software runtime (no speaker), but the SYMBOL SURFACE must be
 * real so libtmessages' dlopen completes and JNI_OnLoad runs.
 *
 * GUIDs are verbatim from the OpenSL ES 1.0.1 spec (SLES/OpenSLES_IID). */
#include <stdint.h>

typedef struct { uint32_t a, b, c; uint16_t d0, d1; uint8_t e[6]; } SLInterfaceID_;

/* { engine: 0x8c1b5c80, ... } etc. — spec GUIDs */
static const SLInterfaceID_ iid_engine = {0x156199a2, 0x8b44, 0x11db, 0xa905, {0x00,0x02,0xa5,0xd5,0xc5,0x1b}};
static const SLInterfaceID_ iid_bufferqueue = {0x2b1368b0, 0x8b45, 0x11db, 0xa905, {0x00,0x02,0xa5,0xd5,0xc5,0x1b}};
static const SLInterfaceID_ iid_play = {0x2b136950, 0x8b45, 0x11db, 0xa905, {0x00,0x02,0xa5,0xd5,0xc5,0x1b}};
static const SLInterfaceID_ iid_record = {0xc5657aa0, 0x8b47, 0x11db, 0xa905, {0x00,0x02,0xa5,0xd5,0xc5,0x1b}};
static const SLInterfaceID_ iid_volume = {0x2b136a68, 0x8b45, 0x11db, 0xa905, {0x00,0x02,0xa5,0xd5,0xc5,0x1b}};
static const SLInterfaceID_ iid_androidconf = {0x6b5bd3f2, 0xb23c, 0x11e1, 0xa09c, {0x00,0x02,0xa5,0xd5,0xc5,0x1b}};
static const SLInterfaceID_ iid_androidsimplebq = {0x6b5bd446, 0xb23c, 0x11e1, 0xa09c, {0x00,0x02,0xa5,0xd5,0xc5,0x1b}};

__attribute__((visibility("default")))
const SLInterfaceID_* SL_IID_ENGINE = &iid_engine;
__attribute__((visibility("default")))
const SLInterfaceID_* SL_IID_BUFFERQUEUE = &iid_bufferqueue;
__attribute__((visibility("default")))
const SLInterfaceID_* SL_IID_PLAY = &iid_play;
__attribute__((visibility("default")))
const SLInterfaceID_* SL_IID_RECORD = &iid_record;
__attribute__((visibility("default")))
const SLInterfaceID_* SL_IID_VOLUME = &iid_volume;
__attribute__((visibility("default")))
const SLInterfaceID_* SL_IID_ANDROIDCONFIGURATION = &iid_androidconf;
__attribute__((visibility("default")))
const SLInterfaceID_* SL_IID_ANDROIDSIMPLEBUFFERQUEUE = &iid_androidsimplebq;

/* slCreateEngine: honest unsupported verdict (no audio device in a
 * software runtime) — returns SL_RESULT_FEATURE_UNSUPPORTED (12). */
__attribute__((visibility("default")))
int slCreateEngine(void** pEngine, uint32_t numOptions,
                   const void* pEngineOptions, uint32_t numInterfaces,
                   const void* pInterfaceIds, const void* pInterfaceRequired) {
    (void)pEngine; (void)numOptions; (void)pEngineOptions;
    (void)numInterfaces; (void)pInterfaceIds; (void)pInterfaceRequired;
    return 12; /* SL_RESULT_FEATURE_UNSUPPORTED — honest, spec value */
}
