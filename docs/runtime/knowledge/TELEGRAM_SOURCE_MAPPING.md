# Telegram APK ↔ Source Mapping

**Last Updated:** 2026-08-26
**Primary Branch HEAD:** `063c772`

## APK Information

- **APK Path:** `miniandroid/download/exp038_telegram/Telegram.apk`
- **APK SHA256:** `193ad551e2cbb745387f26370369f9cd0cf0353ecbc318398ada087ac2bf945e`
- **APK Size:** 82,680,854 bytes (~79 MB)
- **Package Name:** `org.telegram.messenger.web`
- **DEX Files:** 5 (classes.dex, classes2.dex, classes3.dex, classes4.dex, classes5.dex)
- **ZIP Entries:** 11,531
- **Total Classes (after multi-DEX injection):** 41,078
- **Total Methods:** 219,286 (211,802 with bytecode)

## Source Checkout

- **Repository:** https://github.com/DrKLO/Telegram
- **Local Path:** `third_party/telegram-android/`
- **Source Commit:** `62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c`
- **Source Version:** 12.10.1 (versionCode 7038)
- **Checkout Date:** 2026-08-26
- **Clone Method:** Shallow clone (`--depth 1`)

## Version Mapping

### Confidence: APPROXIMATE

The APK package name `org.telegram.messenger.web` indicates this is a Telegram
variant (the "web" suffix is used for the anti-censorship/web-variant build).
The exact APK version/build may differ from the checked-out source commit.

### Known Differences

1. **Package name:** APK uses `org.telegram.messenger.web` while source uses
   `org.telegram.messenger` (the `.web` suffix is added during the build
   process for specific distribution channels).
2. **Resource shrinking:** The APK has been processed by R8/resource shrinker,
   which remaps some resource IDs (e.g., `R.string.ChooseCountry` → ordinal 3).
3. **D8/R8 compilation:** All lambda methods have been renamed to
   `$r8$lambda$<hash>` format by the D8 compiler.
4. **Code obfuscation/minification:** Some class names may differ from source
   due to R8 minification, but the core `LoginActivity` and its inner classes
   appear to match the source.

## Key Source Files

- **LoginActivity.java:** `TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java`
  - `PhoneView.onNextPressed(String code)` — line 4688 (auth.sendCode construction)
  - `fillNextCodeParams(Bundle, TLRPC.auth_SentCode, boolean)` — line 1757
  - `setPage(int, boolean, Bundle, boolean)` — line 56052c (DEX)
  - Page constants: `VIEW_PHONE_INPUT=0, VIEW_CODE_CHECK=1, VIEW_CODE_SMS=2, ...`

## Page Constants (from Source)

```java
// LoginActivity.java line 243-246
private final static int VIEW_PHONE_INPUT = 0,
        VIEW_CODE_CHECK = 1,
        VIEW_CODE_SMS = 2,
        ...
```

## Key Method Mappings

| Source Method | DEX Method | DEX Location |
|--------------|------------|--------------|
| `PhoneView.onNextPressed` | `onNextPressed(Ljava/lang/String;)V` | classes4.dex, code_off=0x55a914 |
| `fillNextCodeParams(Bundle, auth_SentCode, Z)` | `fillNextCodeParams(...)V` | classes4.dex, code_off=0x55e148 |
| `setPage(IZLandroid/os/Bundle;Z)V` | `setPage(...)V` | classes4.dex, code_off=0x56052c |
| `lambda$onNextPressed$22` | `lambda$onNextPressed$22(...)V` | classes4.dex, code_off=0x55a024 |

## Response Class Mapping

| Source Class | DEX Class | Usage |
|------------|----------|-------|
| `TLRPC.TL_auth_sendCode` | `Lorg/telegram/tgnet/TLRPC$TL_auth_sendCode;` | Request class |
| `TLRPC.auth_SentCode` | `Lorg/telegram/tgnet/TLRPC$auth_SentCode;` | Response base class |
| `TLRPC.TL_auth_sentCode` | `Lorg/telegram/tgnet/TLRPC$TL_auth_sentCode;` | Concrete response |
| `TLRPC.TL_auth_sentCodeTypeSms` | `Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeTypeSms;` | SMS type marker |
| `TLRPC.TL_auth_sentCodeSuccess` | `Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeSuccess;` | Success response (not used in mock) |
