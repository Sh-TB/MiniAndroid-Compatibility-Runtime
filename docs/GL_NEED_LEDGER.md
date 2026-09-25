# GL NEED LEDGER (S104)

Corpus demand for GLES APIs — raw `method_ids[]` scan of every
classes*.dex in the 54-APK census (a called API must appear there).
Implementation gate (S103 rule): implement only APIs with measured
demand; PGL already implements texture/framebuffer/shader at C level —
the frontier is the BRIDGE dispatch (which of these the engine never
routes to PGL).

- census APKs scanned: **54**
- APKs referencing ANY GLES/EGL/GLSurfaceView API: **6**

## VERDICT (measured)

Census GLES demand is **EGL10 setup only** (Khronos JSR-239:

```text
GLES20/30 method references corpus-wide: 0
EGL10/EGLContext references:            6 APKs (tictactoe, klooni,
    secuso solitaire, firestrike, halma, 2048)
```

The libGDX-family titles render through their bundled NATIVE libgdx.so
(JNI), not Java GLES calls — the Java GLES bridge is NOT the blocking
layer for them. Therefore:
1. GLES bridge dispatch stays demand-gated (measured demand = 0 —
   the S103 decision holds, now with a corpus-wide number).
2. The real frontier for the 6 GL titles is native-library loading
   (out of the Java-runtime scope this campaign targets).
3. EGL10 setup is shadow-surface territory (S103 ROOT-EGL-SHADOW).

## Demand by API (top 40)

| API | APK count |
|-----|----------:|
| `Ljavax/microedition/khronos/egl/EGL10;->eglChooseConfig` | 6 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglGetConfigAttrib` | 6 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglGetError` | 5 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglTerminate` | 5 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglDestroyContext` | 5 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglGetDisplay` | 5 |
| `Ljavax/microedition/khronos/egl/EGLContext;->getEGL` | 5 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglInitialize` | 5 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglCreateContext` | 5 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglGetCurrentContext` | 4 |
| `Ljavax/microedition/khronos/egl/EGLContext;->getGL` | 4 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglMakeCurrent` | 4 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglDestroySurface` | 4 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglSwapBuffers` | 4 |
| `Ljavax/microedition/khronos/egl/EGL10;->eglCreateWindowSurface` | 4 |

## Demand by family

| Family | APK count |
|--------|----------:|
| other:eglChooseConfig | 6 |
| other:eglGetConfigAttrib | 6 |
| other:eglGetError | 5 |
| other:eglTerminate | 5 |
| other:eglDestroyContext | 5 |
| other:eglGetDisplay | 5 |
| other:getEGL | 5 |
| other:eglInitialize | 5 |
| other:eglCreateContext | 5 |
| other:eglGetCurrentContext | 4 |
| other:getGL | 4 |
| other:eglMakeCurrent | 4 |
| other:eglDestroySurface | 4 |
| other:eglSwapBuffers | 4 |
| other:eglCreateWindowSurface | 4 |

## Titles using GLES

- app.halma.apk (10 API refs)
- com.eightsines.firestrike.opensource.apk (14 API refs)
- com.emmanuelmess.tictactoe.apk (15 API refs)
- dev.lonami.klooni.apk (15 API refs)
- org.andstatus.game2048.apk (2 API refs)
- org.secuso.privacyfriendlysolitaire.apk (15 API refs)
