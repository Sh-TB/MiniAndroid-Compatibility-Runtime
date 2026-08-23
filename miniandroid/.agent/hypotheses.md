# EXP-067 Hypotheses

Active hypotheses to verify or refute.

## H001: PhoneView's missing Next button is a FragmentFloatingButton sibling
**Status:** TO VERIFY
**Evidence needed:** Check if FragmentFloatingButton exists as a sibling of PhoneView in LoginActivity's view tree, OR if it's created by LoginActivity.presentFragment.

## H002: Real color resolution would fix the gray placeholder rectangles
**Status:** TO VERIFY
**Evidence needed:** Check if ImageView.setBackgroundResource is called with a color resource (not a drawable). If so, real color resolution would make the rectangles show the actual theme color.

## H003: AXML parser would unlock generic APK validation
**Status:** LIKELY TRUE
**Evidence needed:** Build a synthetic APK with a simple XML layout, verify MiniAndroid can inflate it.

## H004: Exception engine is needed for Telegram Login
**Status:** TO VERIFY
**Evidence needed:** Check if any Login-path method uses try/catch that affects control flow. If all try blocks are "catch (Exception e) { Log.e(...) }" (no-op), exception engine is not blocking Login.
