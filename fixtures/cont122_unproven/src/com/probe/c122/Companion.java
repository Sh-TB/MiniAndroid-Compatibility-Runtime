package com.probe.c122;

/**
 * CONT-122 U16 probe: lives in classes2.dex (the second DEX inside the
 * probe APK). If the engine's multi-dex enumeration reaches this class,
 * Class.forName("com.probe.c122.Companion") resolves — R-NEW-132 dynamic
 * DEX enumeration proven live.
 */
public class Companion implements MainActivity.Companion2Marker {
    public String tag() { return "companion-classes2"; }
}
