# GP — issue #582 wave-2 pointer receipt — 2026-11-12

Wave-2 of this master audit ran against **issue #583** (the cross-lane integration + GLES/build-truth findings) and is reported in full there: https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/583#issuecomment-6805070652

Summary of the wave (12 findings actioned, commit `4d2c4b66`, binary `a76c8661dc96e195`):

- **#583 findings fixed:** GP583-BUILD-001/002/003, GP583-TEST-001/002 (+ the latent broken s130 law test the battery surfaced), GP583-GLES-001..010, GP583-LAYOUT-001.
- **Cross-cutting effects relevant to THIS issue's ledger:** the GLES compile/link/introspection false-success faces (the canned COMPILE_STATUS/LINK_STATUS/ACTIVE_ATTRIBUTES rows this issue's GP-GFX/GLES adjacents rely on) are now family-gated per-object; the DrawElements diagnostic OOB face is closed; the copy-allocation face is bounded; the GL composer consumes the View walk's accumulated geometry (no second GL-only model).
- **Regression:** `make test-all` 24/24 + manifest parity OK; new GLES law test 31/31; FULL 6-PIN GATE ALL HOLD byte-exact on `a76c8661dc96e195` (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 / microtimer `b39665f6` / ttt `7354c1b2` ×3 — the honest-status wave transiently broke the ttt pin and was diagnosed via the GLSL trace chain and restored byte-exact; the chain is documented in §5 of the #583 report as a worked example of the false-success family this issue indexes).
- **Remaining open on THIS issue (unchanged, queued):** GP-DEX-003 fuzz hardening, GP-INT-005/008..011 per-callsite classification, GP-EXC-005..009 injected-exception/class-init batteries, GP-APK-001/003/004/006 per-callsite, GP-JNI-004 fork-isolation architecture, GP-MEM teardown free-loop, GP-EXC-008 TextWatcher, fuzz corpus for the hardened parsers.
