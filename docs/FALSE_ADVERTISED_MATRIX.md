# FALSE_ADVERTISED_MATRIX (#375 §5)

| id | surface | was | now | verdict | law/evidence |
|---|---------|-----|-----|---------|--------------|
| FA-01 | Build.SUPPORTED_ABIS | was [arm64-v8a, armeabi-v7a, armeabi] (arm64 persona) | [x86_64] — the host-executable ABI | FALSE_ADVERTISED-FIXED | #375 §5 law: no non-executable ARM without translation; ENV-005 updated; install ABI law still extracts arm trees for provenance with honest dlopen refusal (NAT-05) |
| FA-02 | Build.SUPPORTED_64_BIT_ABIS / 32 / CPU_ABI / CPU_ABI2 | [arm64-v8a] / [armeabi-v7a, armeabi] / arm64-v8a / armeabi-v7a | [x86_64] / [] / x86_64 / "" | FALSE_ADVERTISED-FIXED | same law family as FA-01; CPU_ABI2 empty = AOSP API 21+ convention |
| FA-03 | Camera / GPS / telephony / BT / NFC / microphone | not advertised — no feature API fabrication, ENV-008 ABSENT | absent, honest | ABSENT-BY-PROFILE | ENVIRONMENT_PROFILE ENV-008; no hasSystemFeature fabrication path exists |
| FA-04 | Permissions | no universal grant; request->grant->AppOps->deny chain | denial semantics proven | HONEST | negatives 17/17 incl. permission rows; §26 contracts |
| FA-05 | System services (active set) | SVC-01..04 started-vs-bound laws; unimplemented services honest-absent | honest | HONEST | docs/EXECUTION_LEVEL_MATRIX; FA audit: no service returns fake success |
| FA-06 | Storage paths | data/data/<pkg> + external app dirs = real filesystem (file-IO JSONL provenance) | paths correspond to real storage | HONEST | INSTALL_TREE_PROOF.jsonl; persistence 32/32; MINIANDROID_FILE_IO |
| FA-07 | Native library execution | x86_64 dlopen/JNI real (NATX 10/10 x3); ARM extraction-only with real UnsatisfiedLinkError shapes | EXTRACTED is not EXECUTED — enforced | HONEST | NATX 10/10x3 results 4d7761f7; NAT-05 ULE shape; EggReturnsHome arm-only install-OK/fail-at-launch live proof |
| FA-08 | Graphics capability (GLES/Vulkan) | software renderer + JSR-239 EGL facade; GLSL recorded-not-executed; no Vulkan advertisement | documented limitation | DOCUMENTED-LIMITATION | F-144 PARTIAL; #374 §16/§77; EGL facade law closed checkGL20 honestly |
| FA-09 | Build.* device identity | miniandroid persona (DEVICE/PRODUCT/HARDWARE/FINGERPRINT) | consistent persona, no false hardware claims | HONEST | ENV-002; F-NEW-190 non-empty-ABI-list face preserved (WhatsApp utility) |
| FA-10 | Screen/density/keyboard/touch configuration | frozen profile documented; unreachable configs named (CFG-01..05) | documented | HONEST | #374 §13/§52; density matrix 11/11 |

## Verdict totals

- HONEST: 6
- FALSE_ADVERTISED-FIXED: 2
- ABSENT-BY-PROFILE: 1
- DOCUMENTED-LIMITATION: 1
