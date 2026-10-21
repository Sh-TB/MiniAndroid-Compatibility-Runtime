package com.miniandroid.f474;

/** Payload class living ONLY in the in-memory dex (never in the primary APK dex). */
public final class Payload {
    public static final int MARK = 0x474;
    public static String tag() {
        return "f474-payload";
    }
}
