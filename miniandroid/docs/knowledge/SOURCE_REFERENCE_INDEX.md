# Source Reference Index

**Last Updated:** 2026-08-26
**Primary Branch HEAD:** `cdfd8fc`

This is the permanent navigation map for all open-source reference source
used by the MiniAndroid project. It maps Android APIs to their authoritative
source locations.

## Telegram Android Source

- **Repository:** https://github.com/DrKLO/Telegram
- **Local Path:** `third_party/telegram-android/`
- **Commit:** `62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c`
- **Version:** v12.10.1 (versionCode 7038)

### Key Files

| API / Concept | Source File | Location |
|--------------|------------|----------|
| LoginActivity | LoginActivity.java | `TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java` |
| PhoneView.onNextPressed | LoginActivity.java:4688 | Same file, line 4688 |
| fillNextCodeParams | LoginActivity.java:1757 | Same file, line 1757 |
| setPage | LoginActivity.java (DEX 0x56052c) | Compiled in classes4.dex |
| Page constants (VIEW_CODE_SMS=2) | LoginActivity.java:243-246 | Same file |
| SmsView | LoginActivity.java:3554 | Inner class LoginActivitySmsView |
| SmsView.setParams | LoginActivity.java:4298 | Same file |
| ConnectionsManager.sendRequest | (Telegram source) | `TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java` |
| TL_auth_sendCode / TL_auth_sentCode | TLRPC.java | `TMessagesProj/src/main/java/org/telegram/tgnet/TLRPC.java` |

## AOSP Reference (Web-Based)

AOSP source is NOT cloned locally (too large). Use web-based reference:

- **AOSP Source:** https://cs.android.com/android/platform/superproject/main
- **GitHub Mirror:** https://github.com/aosp-mirror

### Key AOSP Classes (Referenced via Web)

| API / Concept | AOSP Source File | URL |
|--------------|-----------------|-----|
| Application | `frameworks/base/core/java/android/app/Application.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/app/Application.java |
| Activity | `frameworks/base/core/java/android/app/Activity.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/app/Activity.java |
| Context | `frameworks/base/core/java/android/content/Context.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/content/Context.java |
| ContextImpl | `frameworks/base/core/java/android/app/ContextImpl.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/app/ContextImpl.java |
| View | `frameworks/base/core/java/android/view/View.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/view/View.java |
| ViewGroup | `frameworks/base/core/java/android/view/ViewGroup.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/view/ViewGroup.java |
| TextView | `frameworks/base/core/java/android/widget/TextView.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/widget/TextView.java |
| EditText | `frameworks/base/core/java/android/widget/EditText.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/widget/EditText.java |
| LayoutInflater | `frameworks/base/core/java/android/view/LayoutInflater.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/view/LayoutInflater.java |
| Handler | `frameworks/base/core/java/android/os/Handler.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/os/Handler.java |
| Looper | `frameworks/base/core/java/android/os/Looper.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/os/Looper.java |
| MessageQueue | `frameworks/base/core/java/android/os/MessageQueue.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/os/MessageQueue.java |
| Bundle | `frameworks/base/core/java/android/os/Bundle.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/os/Bundle.java |
| Intent | `frameworks/base/core/java/android/content/Intent.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/content/Intent.java |
| Uri | `frameworks/base/core/java/android/net/Uri.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/net/Uri.java |
| Resources | `frameworks/base/core/java/android/content/res/Resources.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/content/res/Resources.java |
| AssetManager | `frameworks/base/core/java/android/content/res/AssetManager.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/content/res/AssetManager.java |
| PackageManager | `frameworks/base/core/java/android/content/pm/PackageManager.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/content/pm/PackageManager.java |
| SystemClock | `frameworks/base/core/java/android/os/SystemClock.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/os/SystemClock.java |
| Build.VERSION | `frameworks/base/core/java/android/os/Build.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/os/Build.java |
| MotionEvent | `frameworks/base/core/java/android/view/MotionEvent.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/view/MotionEvent.java |
| Canvas | `frameworks/base/graphics/java/android/graphics/Canvas.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/graphics/java/android/graphics/Canvas.java |
| Paint | `frameworks/base/graphics/java/android/graphics/Paint.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/graphics/java/android/graphics/Paint.java |
| DisplayMetrics | `frameworks/base/core/java/android/util/DisplayMetrics.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/util/DisplayMetrics.java |
| TextUtils | `frameworks/base/core/java/android/text/TextUtils.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/text/TextUtils.java |
| SparseArray | `frameworks/base/core/java/android/util/SparseArray.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/util/SparseArray.java |
| ArrayMap | `frameworks/base/core/java/android/util/ArrayMap.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/util/ArrayMap.java |
| Base64 | `frameworks/base/core/java/android/util/Base64.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/util/Base64.java |
| ClipboardManager | `frameworks/base/core/java/android/content/ClipboardManager.java` | https://cs.android.com/android/platform/superproject/main/+/main:frameworks/base/core/java/android/content/ClipboardManager.java |

## AndroidX Reference (Web-Based)

- **AndroidX Source:** https://cs.android.com/androidx/platform/frameworks/support
- **GitHub:** https://github.com/androidx/androidx

### Key AndroidX Classes

| API / Concept | Source | URL |
|--------------|--------|-----|
| AppCompatActivity | androidx.appcompat | https://cs.android.com/androidx/platform/frameworks/support/+/refs/heads/main:appcompat/appcompat/src/main/java/androidx/appcompat/app/AppCompatActivity.java |
| Fragment | androidx.fragment | https://cs.android.com/androidx/platform/frameworks/support/+/refs/heads/main:fragment/fragment/src/main/java/androidx/fragment/app/Fragment.java |
| FragmentActivity | androidx.fragment | https://cs.android.com/androidx/platform/frameworks/support/+/refs/heads/main:fragment/fragment/src/main/java/androidx/fragment/app/FragmentActivity.java |
| ViewModel | androidx.lifecycle | https://cs.android.com/androidx/platform/frameworks/support/+/refs/heads/main:lifecycle/lifecycle-viewmodel/src/main/java/androidx/lifecycle/ViewModel.java |
| ViewPager | androidx.viewpager | https://cs.android.com/androidx/platform/frameworks/support/+/refs/heads/main:viewpager/viewpager/src/main/java/androidx/viewpager/widget/ViewPager.java |

## OpenJDK / Android libcore (Web-Based)

- **Android libcore:** https://cs.android.com/android/platform/superproject/main/+/main:libcore/
- **OpenJDK:** https://github.com/openjdk/jdk

### Key Java Classes

| API / Concept | Source | URL |
|--------------|--------|-----|
| String | OpenJDK | https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/lang/String.java |
| HashMap | OpenJDK | https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/HashMap.java |
| ArrayList | OpenJDK | https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/ArrayList.java |
| ByteBuffer / NIO | OpenJDK | https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/nio/ByteBuffer.java |

## LibGDX Reference (Web-Based)

- **LibGDX Source:** https://github.com/libgdx/libgdx

### Key LibGDX Classes

| API / Concept | Source File | URL |
|--------------|------------|-----|
| ShapeRenderer | ShapeRenderer.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/graphics/glutils/ShapeRenderer.java |
| SpriteBatch | SpriteBatch.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/graphics/g2d/SpriteBatch.java |
| Stage | Stage.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/scenes/scene2d/Stage.java |
| Actor | Actor.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/scenes/scene2d/Actor.java |
| BitmapFont | BitmapFont.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/graphics/g2d/BitmapFont.java |
| BitmapFontData | BitmapFontData.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/graphics/g2d/BitmapFontData.java |
| Mesh | Mesh.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/graphics/Mesh.java |
| GL20 | GL20.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/graphics/GL20.java |
| Pools | Pools.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/utils/Pools.java |
| Pool | Pool.java | https://github.com/libgdx/libgdx/blob/master/gdx/src/com/badlogic/gdx/utils/Pool.java |
