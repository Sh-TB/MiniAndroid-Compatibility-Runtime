#!/usr/bin/env python3
"""S82-GFX-REVOLUTION P3 — golden fixture ladder generator (LEVEL 0..6).

Creates one minimal Android app per graphics level under
fixtures/s82gfx/<lvl>_<name>/ with real aapt2-compilable res/ trees.

LEVEL law (S82-GFX §5): every level must isolate exactly one graphics
capability so a fixture failure pins the family without execution noise:

  L0 solid ColorDrawable + TextView + Button          (baseline)
  L1 PNG ImageView — quadrant test image (RGBA + transparent checker)
  L2 PNG color types 0/2/3/4/6 (palette ct=3 + tRNS)  (decoder law)
  L3 density buckets mdpi..xxxhdpi (marker colors)    (selection law)
  L4 XML drawables: shape/gradient/layer-list/selector(inflation law)
  L5 custom View onDraw: rect/path/text/bitmap/clip   (Canvas law)
  L6 GLSurfaceView + GL10 renderer                    (surface law, F-NEW-157)
"""
import os
import sys
from PIL import Image

ROOT = "/home/z/my-project/fixtures/s82gfx"

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
        if isinstance(content, bytes):
            with open(p, "wb") as f:
                f.write(content)
        else:
            with open(p, "w") as f:
                f.write(content)
    return d


def pkg_of(name):
    return "org.miniandroid.gfx." + name


def manifest_for(name, label):
    return MANIFEST.format(pkg=pkg_of(name), label=label)


# ---------------------------------------------------------------- L0
l0_src = """package org.miniandroid.gfx.l0_solid;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundDrawable(new ColorDrawable(Color.rgb(20, 40, 60)));
        TextView tv = new TextView(this);
        tv.setText("L0 SOLID BASELINE");
        tv.setTextColor(Color.WHITE);
        Button btn = new Button(this);
        btn.setText("TAP");
        root.addView(tv);
        root.addView(btn);
        setContentView(root);
    }
}
"""
write("l0_solid", {
    "AndroidManifest.xml": manifest_for("l0_solid", "L0"),
    "src/org/miniandroid/gfx/l0_solid/MainActivity.java": l0_src,
})

# ---------------------------------------------------------------- L1
img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
for y in range(32):
    for x in range(32):
        img.putpixel((x, y), (255, 0, 0, 255))
        img.putpixel((x + 32, y), (0, 255, 0, 255))
        img.putpixel((x, y + 32), (0, 0, 255, 255))
        img.putpixel((x + 32, y + 32), (0, 0, 0, 255))
# 8x8 checkerboard center: white/transparent alternating 4px cells
for cy in range(4):
    for cx in range(4):
        if (cx + cy) % 2 == 0:
            for yy in range(8):
                for xx in range(8):
                    img.putpixel((16 + cx * 8 + xx, 24 + cy * 8 + yy), (255, 255, 255, 255))
import io
buf = io.BytesIO(); img.save(buf, "PNG")
quadrant_png = buf.getvalue()

l1_src = """package org.miniandroid.gfx.l1_quadrant;

import android.app.Activity;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        ImageView iv = new ImageView(this);
        iv.setImageResource(R.drawable.quadrant);
        root.addView(iv);
        setContentView(root);
    }
}
"""
write("l1_quadrant", {
    "AndroidManifest.xml": manifest_for("l1_quadrant", "L1"),
    "src/org/miniandroid/gfx/l1_quadrant/MainActivity.java": l1_src,
    "res/drawable/quadrant.png": quadrant_png,
})

# ---------------------------------------------------------------- L2
def pmode_png(colors, transparent_idx=None):
    im = Image.new("P", (16 * len(colors), 16))
    px = im.load()
    for i, c in enumerate(colors):
        for y in range(16):
            for x in range(16):
                px[i * 16 + x, y] = i
    pal = []
    for c in colors:
        pal.extend(c)
    im.putpalette(pal)
    if transparent_idx is not None:
        im.info["transparency"] = transparent_idx
    b = io.BytesIO()
    im.save(b, "PNG", transparency=im.info.get("transparency"))
    return b.getvalue()

# ct=3 palette with 16 colors + tRNS on index 0
pal_colors = [(i * 16, 255 - i * 16, (i * 7) % 256) for i in range(16)]
palette_png = pmode_png(pal_colors, transparent_idx=0)
# ct=0 grayscale
gray_png = Image.new("L", (32, 32))
for y in range(32):
    for x in range(32):
        gray_png.putpixel((x, y), (x * 8) % 256)
b = io.BytesIO(); gray_png.save(b, "PNG"); gray_png = b.getvalue()
# ct=2 RGB truecolor
rgb_png = Image.new("RGB", (32, 32))
for y in range(32):
    for x in range(32):
        rgb_png.putpixel((x, y), (255, x * 8 % 256, y * 8 % 256))
b = io.BytesIO(); rgb_png.save(b, "PNG"); rgb_png = b.getvalue()
# ct=4 gray+alpha
ga_png = Image.new("LA", (32, 32))
for y in range(32):
    for x in range(32):
        ga_png.putpixel((x, y), (128, x * 8 % 256))
b = io.BytesIO(); ga_png.save(b, "PNG"); ga_png = b.getvalue()

l2_src = """package org.miniandroid.gfx.l2_colortypes;

import android.app.Activity;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        ImageView a = new ImageView(this);
        a.setImageResource(R.drawable.pal);
        ImageView g = new ImageView(this);
        g.setImageResource(R.drawable.gray);
        ImageView r = new ImageView(this);
        r.setImageResource(R.drawable.rgb);
        ImageView ga = new ImageView(this);
        ga.setImageResource(R.drawable.ga);
        root.addView(a);
        root.addView(g);
        root.addView(r);
        root.addView(ga);
        setContentView(root);
    }
}
"""
write("l2_colortypes", {
    "AndroidManifest.xml": manifest_for("l2_colortypes", "L2"),
    "src/org/miniandroid/gfx/l2_colortypes/MainActivity.java": l2_src,
    "res/drawable/pal.png": palette_png,
    "res/drawable/gray.png": gray_png,
    "res/drawable/rgb.png": rgb_png,
    "res/drawable/ga.png": ga_png,
})

# ---------------------------------------------------------------- L3
# Density markers: solid colors + canonical launcher sizes (mdpi=48 …)
densities = [
    ("m", (255, 0, 0), 48, "drawable-mdpi"),
    ("h", (0, 160, 0), 72, "drawable-hdpi"),
    ("x", (0, 0, 255), 96, "drawable-xhdpi"),
    ("xx", (255, 220, 0), 144, "drawable-xxhdpi"),
    ("xxx", (200, 0, 200), 192, "drawable-xxxhdpi"),
]
l3_res = {}
for name, color, side, folder in densities:
    im = Image.new("RGBA", (side, side), color + (255,))
    # 25% corner notch to make per-variant geometry measurable
    for y in range(side // 4):
        for x in range(side // 4):
            im.putpixel((x, y), (255, 255, 255, 0))
    b = io.BytesIO(); im.save(b, "PNG")
    l3_res[f"res/{folder}/marker.png"] = b.getvalue()

l3_src = """package org.miniandroid.gfx.l3_density;

import android.app.Activity;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        ImageView iv = new ImageView(this);
        iv.setImageResource(R.drawable.marker);
        root.addView(iv);
        setContentView(root);
    }
}
"""
l3_res["AndroidManifest.xml"] = manifest_for("l3_density", "L3")
l3_res["src/org/miniandroid/gfx/l3_density/MainActivity.java"] = l3_src
write("l3_density", l3_res)

# ---------------------------------------------------------------- L4
l4_res = {
    "AndroidManifest.xml": manifest_for("l4_xmldrawables", "L4"),
    "res/drawable/shape_round.xml": """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#FF6633"/>
    <corners android:radius="12dp"/>
    <stroke android:width="2dp" android:color="#003366"/>
</shape>""",
    "res/drawable/gradient_bar.xml": """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient android:startColor="#FF0000" android:endColor="#0000FF"
              android:angle="0"/>
</shape>""",
    "res/drawable/layer_card.xml": """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@drawable/shape_round"/>
    <item android:top="8dp" android:left="8dp" android:right="8dp" android:bottom="8dp">
        <shape android:shape="rectangle">
            <solid android:color="#FFFFFF"/>
        </shape>
    </item>
</layer-list>""",
    "res/drawable/btn_state.xml": """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true"><shape android:shape="rectangle">
        <solid android:color="#00CC66"/></shape></item>
    <item><shape android:shape="rectangle">
        <solid android:color="#333333"/></shape></item>
</selector>""",
}
l4_src = """package org.miniandroid.gfx.l4_xmldrawables;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        Button a = new Button(this);
        a.setText("SHAPE");
        a.setBackgroundResource(R.drawable.shape_round);
        Button g = new Button(this);
        g.setText("GRADIENT");
        g.setBackgroundResource(R.drawable.gradient_bar);
        Button l = new Button(this);
        l.setText("LAYER");
        l.setBackgroundResource(R.drawable.layer_card);
        Button s = new Button(this);
        s.setText("SELECTOR");
        s.setBackgroundResource(R.drawable.btn_state);
        root.addView(a);
        root.addView(g);
        root.addView(l);
        root.addView(s);
        setContentView(root);
    }
}
"""
l4_res["src/org/miniandroid/gfx/l4_xmldrawables/MainActivity.java"] = l4_src
write("l4_xmldrawables", l4_res)

# ---------------------------------------------------------------- L5
l5_src = """package org.miniandroid.gfx.l5_canvas;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    static class DrawView extends View {
        Paint fill = new Paint();
        Paint thin = new Paint();
        DrawView(Context c) {
            super(c);
            fill.setColor(Color.rgb(200, 30, 30));
            fill.setStyle(Paint.Style.FILL);
            thin.setColor(Color.rgb(0, 90, 200));
            thin.setStyle(Paint.Style.STROKE);
            thin.setStrokeWidth(4f);
        }
        @Override
        protected void onDraw(Canvas canvas) {
            canvas.drawColor(Color.rgb(245, 240, 220));
            canvas.drawRect(40, 40, 400, 200, fill);
            Path tri = new Path();
            tri.moveTo(60, 480);
            tri.lineTo(300, 480);
            tri.lineTo(180, 260);
            tri.close();
            Paint green = new Paint();
            green.setColor(Color.rgb(0, 160, 60));
            green.setStyle(Paint.Style.FILL);
            canvas.drawPath(tri, green);
            Paint text = new Paint();
            text.setColor(Color.BLACK);
            text.setTextSize(48f);
            canvas.drawText("GFX-CANVAS", 40, 560, text);
            canvas.save();
            canvas.clipRect(420, 40, 700, 300);
            canvas.drawRect(430, 50, 690, 290, thin);
            canvas.restore();
        }
    }
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.addView(new DrawView(this));
        setContentView(root);
    }
}
"""
write("l5_canvas", {
    "AndroidManifest.xml": manifest_for("l5_canvas", "L5"),
    "src/org/miniandroid/gfx/l5_canvas/MainActivity.java": l5_src,
})

# ---------------------------------------------------------------- L6
l6_src = """package org.miniandroid.gfx.l6_glsurface;

import android.app.Activity;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class MainActivity extends Activity {
    static class ClearRenderer implements GLSurfaceView.Renderer {
        public void onSurfaceCreated(GL10 gl, EGLConfig config) {}
        public void onSurfaceChanged(GL10 gl, int w, int h) {}
        public void onDrawFrame(GL10 gl) {
            gl.glClearColor(0.1f, 0.6f, 0.9f, 1f);
            gl.glClear(GL10.GL_COLOR_BUFFER_BIT);
        }
    }
    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        GLSurfaceView v = new GLSurfaceView(this);
        v.setRenderer(new ClearRenderer());
        setContentView(v);
    }
}
"""
write("l6_glsurface", {
    "AndroidManifest.xml": manifest_for("l6_glsurface", "L6"),
    "src/org/miniandroid/gfx/l6_glsurface/MainActivity.java": l6_src,
})

print("fixtures generated under", ROOT)
for d in sorted(os.listdir(ROOT)):
    print(" ", d)
