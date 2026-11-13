# S156-T5 — Tusky (com.keylesspalace.tusky_145) five-stage frontier

Engine chain: S155 rebuild `35cd06374f3c457b` (blocked boot) → S156 anchor
law `a9b58de1d4e56f01` (clean boot). APK pin `8154cabe67374f2e`, vc=145,
v33.1, minSdk 24, targetSdk 36, 1 dex, main
`com.keylesspalace.tusky.MainActivity`, app class `TuskyApplication`
(androguard-verified).

## Stage 1 — PIN

sha16 `8154cabe67374f2e`, zip magic OK. Classic-View stack (material=124,
lifecycle=61, sqlite, preference) + light Compose (58).

## Stage 2 — androguard profile

Families: material=124, androidx/lifecycle=61, compose/ui=54, javax/net/ssl=41,
glide=38, appcompat=27, work=19, android/database/sqlite=19, preference=16,
android/webkit=10, okhttp platform init expected (okhttp3 internals in dex).

## Stage 3 — BOOT at pre-anchor engine (35cd0637)

Face `31ddd4d5b8e6d18e` (the S151-recorded Compose-family generic face),
12/12 frames, wall 2.4 s, 26 uncaught, 25 NPE rows. Root exception:
`UnsatisfiedLinkError: "conscrypt_jni" dlopen failed: undefined symbol
__strchr_chk` from `org/conscrypt/NativeCrypto;.checkAvailability`, then
okhttp platform fallback → `IllegalArgumentException "At least one cipher
suite is required"` cascade (TLS stack dead).

## Stage 4 — FIX (the S156 anchor law) + Stage 5 — VERIFY

Law A (F-NEW-484, FIXED-VERIFIED): the bionic FORTIFY/anchor family — the
Coder-6 wave-5b/7 anchor block (C6-R9a..R9d, provenance
wip/coder-engine-postS154 branch, merge-path decision closed) transplanted
into `miniandroid/src/jni/bionic_compat.c` + S156 extension
(`__memset_chk`/`__vsnprintf_chk`/`__stack_chk_fail`). The engine links
-rdynamic so these definitions are the dlopen resolution surface for
app-native libs.

Verification (engine a9b58de1, RERUN_AFTER_ANCHORS.json):
- anchors dooz 11a38a5a ✓ / unote 3b8dcb0a ✓ (DEX-face-neutral law).
- Tusky boot: **uncaught 26→0, NPE 25→0**, wall 0.5 s, 12/12 frames, face
  `31ddd4d5b8e6d18e` — the boot is now exception-free end to end; conscrypt
  loads, TLS init passes, okhttp platform init completes.

## VERDICT

PARTIAL: clean boot (L0-L2 true), final frame is the HONEST generic
Compose-family face (keep-empty white) — Tusky's own content awaits the
generic Compose render-pipeline wave (the S151-pinned 31ddd4d5 family), not
a Tusky-specific blocker. Tusky-specific TLS/native blockers: SOLVED this
wave.

---
**S226 re-census (a4516511, S225-M):** the mainline anchor surface carries
12/15 FORTIFY symbols + the property API — the conscrypt dlopen boundary
holds without my block. Residue: __memset_chk/__vsnprintf_chk/__stack_chk_fail
still absent (F-NEW-484, transferred). Live battery: gates 4/4 vs the S225-M
pins; tusky clean-family boot, verdict SAFE + DEFAULT_BACKGROUND_ONLY.
