#!/usr/bin/env python3
"""gen_s92_fixtures.py — generate the S92 §25 false-positive-battery
fixture sources + assets under fixtures/s92battery/<case>/.

Each fixture is a REAL minimal Android app exercising one visual-contract
defect class, built with the real aapt2 toolchain (build_fixture_apk.sh).
Oracle outcomes are recorded in fixtures/s92battery/ORACLE.json — the
verifier MUST reject the defective ones and accept the good one (§40).
"""
import json
import os
import struct
import zlib

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "fixtures", "s92battery")

MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pkg}">
    <application android:label="{label}">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
"""


def png_bytes(w, h, rgba_fn):
    rows = b""
    for y in range(h):
        rows += b"\x00"
        for x in range(w):
            r, g, b, a = rgba_fn(x, y)
            rows += bytes((r, g, b, a))

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def icon_main(x, y):
    # 48x48 blue circle on transparent
    cx = cy = 24
    if (x - cx) ** 2 + (y - cy) ** 2 <= 400:
        return (30, 90, 220, 255)
    return (0, 0, 0, 0)


def icon_rect(x, y):
    # 48x48 orange rect with dark border
    if x in (0, 47) or y in (0, 47):
        return (60, 30, 10, 255)
    return (240, 140, 30, 255)


def corrupt_png():
    data = png_bytes(40, 40, lambda x, y: (200, 30, 30, 255))
    return data[: len(data) // 2]  # truncated -> decode failure


GOOD_JAVA = """package {pkg};

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends Activity {{
    private int count = 0;
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        final TextView tv = (TextView) findViewById(R.id.counter);
        Button b = (Button) findViewById(R.id.increment);
        b.setOnClickListener(new View.OnClickListener() {{
            public void onClick(View v) {{
                count++;
                tv.setText("counter: " + count);
            }}
        }});
    }}
}}
"""


def write_case(name, pkg, label, files):
    d = os.path.join(BASE, name)
    for rel, content in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(p, mode) as f:
            f.write(content)
    return d


def main():
    os.makedirs(BASE, exist_ok=True)
    cases = {}
    icon48 = png_bytes(48, 48, icon_main)
    icon48x = png_bytes(48, 48, icon_rect)
    icon144 = png_bytes(144, 144, icon_main)  # xxhdpi-density 48dp asset

    layout_good = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical" android:layout_width="match_parent"
    android:layout_height="match_parent">
    <ImageView android:id="@+id/icon" android:layout_width="48dp"
        android:layout_height="48dp" android:src="@drawable/ic_main"/>
    <TextView android:id="@+id/counter" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="counter: 0"
        android:textSize="28sp"/>
    <Button android:id="@+id/increment" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="increment"/>
</LinearLayout>
"""
    # ---- G: known-good control ------------------------------------------
    write_case("good", "org.miniandroid.s92.good", "S92G", {
        "AndroidManifest.xml": MANIFEST.format(
            pkg="org.miniandroid.s92.good", label="S92G"),
        "res/layout/activity_main.xml": layout_good,
        "res/drawable/ic_main.png": icon48,
        "src/org/miniandroid/s92/good/MainActivity.java":
            GOOD_JAVA.format(pkg="org.miniandroid.s92.good"),
    })
    cases["good"] = {
        "pkg": "org.miniandroid.s92.good",
        "required_verdict": "ACCEPT",
        "case": "control: real icon + working button + visible state change",
        "s92_case": "G(control)"}

    # ---- A: button covered by opaque overlay (hidden but clickable) -----
    layout_a = """<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
    <LinearLayout android:orientation="vertical"
        android:layout_width="match_parent"
        android:layout_height="match_parent">
        <ImageView android:id="@+id/icon" android:layout_width="48dp"
            android:layout_height="48dp" android:src="@drawable/ic_main"/>
        <Button android:id="@+id/hidden" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:text="hidden tap"/>
    </LinearLayout>
    <View android:layout_width="match_parent"
        android:layout_height="match_parent" android:background="#FFFFFFFF"/>
</FrameLayout>
"""
    write_case("casea_covered_button", "org.miniandroid.s92.casea", "S92A", {
        "AndroidManifest.xml": MANIFEST.format(
            pkg="org.miniandroid.s92.casea", label="S92A"),
        "res/layout/activity_main.xml": layout_a,
        "res/drawable/ic_main.png": icon48,
        "src/org/miniandroid/s92/casea/MainActivity.java":
            GOOD_JAVA.format(pkg="org.miniandroid.s92.casea"),
    })
    cases["casea_covered_button"] = {
        "pkg": "org.miniandroid.s92.casea",
        "required_verdict": "REJECT",
        "case": "button covered by opaque overlay; blind tap must NOT count",
        "s92_case": "A"}

    # ---- C: corrupt PNG (decode failure) --------------------------------
    write_case("casec_corrupt_png", "org.miniandroid.s92.casec", "S92C", {
        "AndroidManifest.xml": MANIFEST.format(
            pkg="org.miniandroid.s92.casec", label="S92C"),
        "res/layout/activity_main.xml": layout_good,
        "res/drawable/ic_main.png": icon48,
        "res/raw/corrupt.bin": corrupt_png(),
        "src/org/miniandroid/s92/casec/MainActivity.java":
            GOOD_JAVA.format(pkg="org.miniandroid.s92.casec"),
    })
    cases["casec_corrupt_png"] = {
        "pkg": "org.miniandroid.s92.casec",
        "required_verdict": "ACCEPT",
        "case": "control layout; corrupt asset lives in res/raw and is "
                "DECODED-BUT-NEVER-SHOWN (decode taxonomy probe fixture; "
                "verifier must list DECODE_FAILURE if it is ever required)",
        "s92_case": "C-asset"}

    # ---- D: splash-only (5s splash, short capture window) ---------------
    layout_splash = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical" android:layout_width="match_parent"
    android:layout_height="match_parent" android:background="#FF203050">
    <TextView android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="SPLASH"
        android:textSize="40sp"/>
</LinearLayout>
"""
    java_d = """package org.miniandroid.s92.cased;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.splash);
        new Handler().postDelayed(new Runnable() {
            public void run() {
                setContentView(R.layout.activity_main);
            }
        }, 5000);
    }
}
"""
    write_case("cased_splash", "org.miniandroid.s92.cased", "S92D", {
        "AndroidManifest.xml": MANIFEST.format(
            pkg="org.miniandroid.s92.cased", label="S92D"),
        "res/layout/activity_main.xml": layout_good,
        "res/layout/splash.xml": layout_splash,
        "res/drawable/ic_main.png": icon48,
        "src/org/miniandroid/s92/cased/MainActivity.java": java_d,
    })
    cases["cased_splash"] = {
        "pkg": "org.miniandroid.s92.cased",
        "required_verdict": "REJECT_SHORT_WINDOW",
        "case": "5s splash then main scene; short capture window must "
                "produce splash-only -> NOT fully verified (readiness law)",
        "s92_case": "D"}

    # ---- E: visible but NOT clickable ------------------------------------
    layout_e = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical" android:layout_width="match_parent"
    android:layout_height="match_parent">
    <ImageView android:id="@+id/icon" android:layout_width="48dp"
        android:layout_height="48dp" android:src="@drawable/ic_main"/>
</LinearLayout>
"""
    java_e = """package org.miniandroid.s92.casee;

import android.app.Activity;
import android.os.Bundle;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
    }
}
"""
    write_case("casee_not_clickable", "org.miniandroid.s92.casee", "S92E", {
        "AndroidManifest.xml": MANIFEST.format(
            pkg="org.miniandroid.s92.casee", label="S92E"),
        "res/layout/activity_main.xml": layout_e,
        "res/drawable/ic_main.png": icon48,
        "src/org/miniandroid/s92/casee/MainActivity.java": java_e,
    })
    cases["casee_not_clickable"] = {
        "pkg": "org.miniandroid.s92.casee",
        "required_verdict": "REJECT_INTERACTION",
        "case": "icon visible but no click listener; interaction stages "
                "must not pass",
        "s92_case": "E"}

    # ---- F: callback without visual change (the "2+2" class) -------------
    java_f = """package org.miniandroid.s92.casef;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

public class MainActivity extends Activity {
    private int hidden = 0;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Button b = (Button) findViewById(R.id.increment);
        b.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                hidden++;          // NO UI update on purpose (2+2 class)
            }
        });
    }
}
"""
    layout_f = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical" android:layout_width="match_parent"
    android:layout_height="match_parent">
    <ImageView android:id="@+id/icon" android:layout_width="48dp"
        android:layout_height="48dp" android:src="@drawable/ic_main"/>
    <Button android:id="@+id/increment" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="silent"/>
</LinearLayout>
"""
    write_case("casef_silent_callback", "org.miniandroid.s92.casef", "S92F", {
        "AndroidManifest.xml": MANIFEST.format(
            pkg="org.miniandroid.s92.casef", label="S92F"),
        "res/layout/activity_main.xml": layout_f,
        "res/drawable/ic_main.png": icon48,
        "src/org/miniandroid/s92/casef/MainActivity.java": java_f,
    })
    cases["casef_silent_callback"] = {
        "pkg": "org.miniandroid.s92.casef",
        "required_verdict": "REJECT_VISUAL_CHANGE",
        "case": "callback fires but NO visual change (S92 addendum 30: "
                "computation/state pass must NOT promote to FULL)",
        "s92_case": "F"}

    # ---- G: density law (xxhdpi-only asset) -------------------------------
    write_case("caseg_density", "org.miniandroid.s92.caseg", "S92G2", {
        "AndroidManifest.xml": MANIFEST.format(
            pkg="org.miniandroid.s92.caseg", label="S92G2"),
        "res/layout/activity_main.xml": """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:orientation="vertical" android:layout_width="match_parent"
    android:layout_height="match_parent">
    <ImageView android:id="@+id/icon" android:layout_width="48dp"
        android:layout_height="48dp" android:src="@mipmap/ic_dense"/>
</LinearLayout>
""",
        "res/mipmap-xxhdpi/ic_dense.png": icon144,
        "src/org/miniandroid/s92/caseg/MainActivity.java": java_e.replace(
            "org.miniandroid.s92.casee", "org.miniandroid.s92.caseg"),
    })
    cases["caseg_density"] = {
        "pkg": "org.miniandroid.s92.caseg",
        "required_verdict": "MEASURE",
        "case": "48dp slot fed ONLY by a 144px xxhdpi asset; measured "
                "displayed size must equal 48px at 160dpi runtime "
                "(density law); wrong size = DENSITY_MISMATCH",
        "s92_case": "G"}

    # ---- corrupt asset for the decode-taxonomy check (kept as info) ------
    with open(os.path.join(BASE, "corrupt_asset.bin"), "wb") as f:
        f.write(corrupt_png())

    oracle = {
        "schema": "s92.battery_oracle.v1",
        "note": "required_verdict: ACCEPT = verifier must not fail the "
                "title on its visual contract; REJECT* = verifier MUST "
                "fail the named stage; MEASURE = record real behavior, "
                "judge by density law 48px @160dpi",
        "cases": cases,
    }
    with open(os.path.join(BASE, "ORACLE.json"), "w") as f:
        json.dump(oracle, f, indent=1, sort_keys=True)
    print(json.dumps({"fixtures": sorted(cases.keys())}, indent=1))


if __name__ == "__main__":
    main()
