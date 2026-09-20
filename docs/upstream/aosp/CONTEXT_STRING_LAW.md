# UPSTREAM LAW — Context/Resources.getString (F-136 oracle)

Pinned upstream: AOSP frameworks/base main (fetched 2026-09-20, googlesource).

## Context.java (core/java/android/content/Context.java)

```java
945:    public final CharSequence getText(@StringRes int resId) {
946:        return getResources().getText(resId);
947:    }
...
959:    public final String getString(@StringRes int resId) {
960:        return getResources().getString(resId);
961:    }
...
976:    public final String getString(@StringRes int resId, Object... formatArgs) {
977:        return getResources().getString(resId, formatArgs);
978:    }
```

LAW: Context (and every subclass — Application/Activity/ContextWrapper since
getString is FINAL on Context) NEVER resolves itself; it ALWAYS delegates to
getResources(). Any implementation that resolves Context.getString through a
different table than Resources.getString violates the single-resolution-path
law (two tables = two answers for the same resid).

## Resources.java (core/java/android/content/res/Resources.java)

```java
464:    @NonNull public CharSequence getText(@StringRes int id) throws NotFoundException {
465:        CharSequence res = mResourcesImpl.getAssets().getResourceText(id);
466:        if (res != null) {
467:            return res;
468:        }
469:        throw new NotFoundException("String resource ID #0x"
470:                + Integer.toHexString(id));
471:    }
...
564:    public String getString(@StringRes int id) throws NotFoundException {
565:        return getText(id).toString();
566:    }
...
588:    public String getString(@StringRes int id, Object... formatArgs) throws NotFoundException {
589:        final String raw = getString(id);
590:        return String.format(mResourcesImpl.getConfiguration().getLocales().get(0), raw,
591:                formatArgs);
592:    }
```

LAWS:
1. Resolution goes through the ASSET MANAGER (the resource table = ARSC) —
   the authoritative source for ANY resid, any package. Not a name-keyed
   side cache.
2. Formatted overload == String.format(raw, formatArgs) — the raw string is
   ALWAYS fetched first; args format the fetched value.
3. Unresolved resid raises NotFoundException (AOSP fails LOUD). MiniAndroid
   documented deviation (mirrors M3 FIX-M3-007b for colors): unresolved
   keeps the historical "" default with a stderr flag instead of throwing,
   to avoid crashing consumers that today survive a failed lookup. Recorded
   in code at the resolution site.

MiniAndroid implementation sites: dalvik_engine.cpp Resources block (EXP-052
line ~24250) and Context family block (EXT-01 gate G25 line ~29026).
F-136 upgrades BOTH to ARSC-first via ResourceRuntime::arsc().resolve_string
(the same canonical path F-080 already mandated for colors), keeps the legacy
name-map strictly as fallback, and adds java_format_walk to the Resources
formatted overload (Context side already formats per EXT-01 G25).
