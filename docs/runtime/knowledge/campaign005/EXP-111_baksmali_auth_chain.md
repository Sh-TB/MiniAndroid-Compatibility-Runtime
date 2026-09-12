# EXP-111 — Independent baksmali/dexlib2 verification of the SMS auth chain (Campaign 004)

Date: 2026-08-28. Tool: baksmali 2.5.2 (org.jf.dexlib2 2.5.2, fat classpath assembled from Maven
Central thin jars because GitHub release assets are network-blocked). Input: real Telegram
12.10.1 (vc70389, org.telegram.messenger.web, sha256 f5e11927…, 5 DEX).

## What was done
- Extracted classes1-5.dex + resources.arsc from the APK (unzip).
- baksmali disassemble ALL 5 DEX: 12,543 + 572 + 8,931 + 8,884 + 10,216 = 41,146 smali files, exit 0.
  NOTE: 41,146 total smali classes == androguard EXP-105 census (41,146 classes) — independent count MATCH.
- Located auth-chain classes and cross-checked them against the runtime-PROVEN chain from EXP-100/EXP-103.

## Evidence found (DEX#3 tgnet, DEX#4 UI)
1. org/telegram/tgnet/TLRPC$TL_auth_sendCode.smali — fields: api_hash:String, api_id:I,
   phone_number:String, settings:TL_codeSettings. Serializes constructor number 0xa6775c47
   (const v0, -0x5988dbb1 == 0xa6775c47). Deserialization target: TLRPC$auth_SentCode.TLdeserialize.
   → MATCHES runtime trace: TL_auth_sendCode obj#5104 constructed during onNextPressed (EXP-100).
2. org/telegram/ui/IntroActivity$4.smali — extends android/widget/TextView, enclosing method
   IntroActivity.createView, holds CellFlickerDrawable (the flickering start-messaging button).
   → MATCHES runtime click#3 record: class=IntroActivity$4 ("StartMessaging" text view).
3. org/telegram/ui/LoginActivity$LoginActivitySmsView.smali — setParams(Landroid/os/Bundle;Z)V
   exists at line 8175 (method), 2 call sites incl. line 7996.
   → MATCHES runtime trace SmsView.setParams(1486 insns) from EXP-103: the class the runtime
   observed is LoginActivity$LoginActivitySmsView (nested), not a top-level SmsView.
4. org/telegram/tgnet/TLRPC$TL_auth_signIn.smali — fields: phone_number, phone_code,
   phone_code_hash, flags, email_verification.
   → MATCHES runtime TL_auth_signIn obj#5170 intercept (EXP-103).
5. TL_auth_sentCode family present: TL_auth_sentCode, sentCodePaymentRequired, sentCodeTypeSmsPhrase,
   sentCodeSuccess (DEX#3).

## Verdict
- Independent tool (dexlib2) confirms the runtime's DEX-level claims about the SMS auth chain:
  PROVEN (chain classes, fields, and constructor number verified at bytecode level).
- Correction recorded: runtime docs referred to "SmsView"; real v12.10.1 symbol is
  LoginActivity$LoginActivitySmsView (alias documented here). No runtime claim invalidated.
- jadx 1.5.1 (full decompile) + apktool 2.9.3 (--no-src resource decode) launched on same APK;
  results appended in EXP-112/113.

## Environment note
GitHub release asset downloads 404 at network level in this environment (bitbucket: bot-wall).
Both baksmali and apktool were obtained from Maven Central instead. ReDex build attempt: see EXP-114.
