#!/usr/bin/env python3
"""S83-B2 foundation fixture generator — l4e_layerlist + l4f_codelayer.

Emits two golden-ladder fixtures that pin the S83-B2 foundation closures:
  * l4e_layerlist — <layer-list> XML law (color + inset shape + dashed
    stroke) and the GradientDrawable ring/line kinds (ratio law + dash).
  * l4f_codelayer — code-level LayerDrawable/GradientDrawable capture law
    (AOSP GradientState setters → setBackground materialization).
Every pixel assertion cites the AOSP law in the ladder runner (s83b_ladder).
"""
import os

ROOT = "/home/z/my-project/fixtures/s83gfx"

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


def write(name, files):
    d = os.path.join(ROOT, name)
    for rel, content in files.items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
    return d


def pkg_of(name):
    return "org.miniandroid.gfx." + name


def manifest_for(name, label):
    return MANIFEST.format(pkg=pkg_of(name), label=label)


LAYOUT = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#FF202020">

    <View
        android:layout_width="match_parent"
        android:layout_height="200px"
        android:background="@drawable/layer_bg"/>

    <View
        android:layout_width="match_parent"
        android:layout_height="200px"
        android:background="@drawable/ring_bg"/>

    <View
        android:layout_width="match_parent"
        android:layout_height="120px"
        android:background="@drawable/line_bg"/>

</LinearLayout>
"""

LAYER_BG = """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item>
        <color android:color="#FF1B5E20"/>
    </item>
    <item android:left="40px" android:top="40px"
          android:right="40px" android:bottom="60px">
        <shape android:shape="rectangle">
            <solid android:color="#FFD32F2F"/>
            <corners android:radius="24px"/>
            <stroke android:width="6px" android:color="#FF64B5F6"
                    android:dashWidth="16px" android:dashGap="10px"/>
        </shape>
    </item>
</layer-list>
"""

RING_BG = """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="ring"
    android:innerRadiusRatio="4"
    android:thicknessRatio="10">
    <solid android:color="#FFFFEB3B"/>
</shape>
"""

LINE_BG = """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="line">
    <stroke android:width="8px" android:color="#FF4CAF50"
            android:dashWidth="20px" android:dashGap="12px"/>
</shape>
"""

L4E_SRC = """package org.miniandroid.gfx.l4e_layerlist;

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

write("l4e_layerlist", {
    "AndroidManifest.xml": manifest_for("l4e_layerlist", "L4E"),
    "res/layout/activity_main.xml": LAYOUT,
    "res/drawable/layer_bg.xml": LAYER_BG,
    "res/drawable/ring_bg.xml": RING_BG,
    "res/drawable/line_bg.xml": LINE_BG,
    "src/org/miniandroid/gfx/l4e_layerlist/MainActivity.java": L4E_SRC,
})

L4F_SRC = """package org.miniandroid.gfx.l4f_codelayer;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.LayerDrawable;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackground(new ColorDrawable(Color.rgb(18, 18, 18)));

        // code-level LayerDrawable: indigo pad + inset orange RING
        GradientDrawable pad = new GradientDrawable();
        pad.setColor(Color.rgb(48, 63, 159));
        GradientDrawable ring = new GradientDrawable();
        ring.setShape(GradientDrawable.RING);
        ring.setColor(Color.rgb(255, 112, 67));
        ring.setInnerRadius(50);
        ring.setThickness(25);
        LayerDrawable ld = new LayerDrawable(new Drawable[]{pad, ring});
        ld.setLayerInset(1, 100, 50, 100, 50);
        View v1 = new View(this);
        v1.setBackground(ld);
        root.addView(v1, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 300));

        // code-level GradientDrawable: rounded green rect + red stroke
        GradientDrawable rr = new GradientDrawable();
        rr.setColor(Color.rgb(0, 200, 83));
        rr.setCornerRadius(30f);
        rr.setStroke(10, Color.rgb(229, 57, 53));
        View v2 = new View(this);
        v2.setBackground(rr);
        root.addView(v2, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 300));

        setContentView(root);
    }
}
"""

write("l4f_codelayer", {
    "AndroidManifest.xml": manifest_for("l4f_codelayer", "L4F"),
    "src/org/miniandroid/gfx/l4f_codelayer/MainActivity.java": L4F_SRC,
})

print("S83-B2 fixtures generated under", ROOT)
for d in sorted(os.listdir(ROOT)):
    print(" ", d)
