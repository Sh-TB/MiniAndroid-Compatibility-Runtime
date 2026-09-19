#!/usr/bin/env bash
# scripts/foundation/make_fixtures_wave2.sh — S67 wave 2 fixtures:
# canvas op probe (user §5) + proven-gap fixtures (INVISIBLE A4, setARGB A5,
# LL-top C3, dimen seeding A2, Persian shaping contrast, runtime RT39-44).
set -euo pipefail
ROOT=/home/z/my-project
FDST=$ROOT/miniandroid/tests/fixtures_foundation

MAN='<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.miniandroid.__PKG__"
    android:versionCode="1" android:versionName="1.0">
    <application android:label="__LABEL__">
        <activity android:name="com.miniandroid.__PKG__.MainActivity" android:label="__LABEL__">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>'

mk() { mkdir -p "$FDST/$1/src/com/miniandroid/$2"
  echo "$MAN" | sed "s/__PKG__/$2/g; s/__LABEL__/$3/g" > "$FDST/$1/AndroidManifest.xml"; }

plain_main() { cat > "$FDST/$1/src/com/miniandroid/$2/MainActivity.java"; }

# ---------- R08/R09 canvas op probe: every op in its own 180px row ----------
mk f08_canvasops f08canvasops "F08 CanvasOps"
cat > "$FDST/f08_canvasops/src/com/miniandroid/f08canvasops/MainActivity.java" <<'EOF'
package com.miniandroid.f08canvasops;
import android.app.Activity; import android.content.Context; import android.os.Bundle;
import android.graphics.Canvas; import android.graphics.Color; import android.graphics.Paint;
import android.view.View;

public class MainActivity extends Activity {
    public static class ProbeView extends View {
        public ProbeView(Context c) { super(c); }
        @Override public void onDraw(Canvas canvas) {
            // Row 1 (y 0..179): drawColor full-view is replaced by rows below;
            // start by filling background via drawColor then overdraw.
            Paint p = new Paint();
            // R1: drawColor (white base) + drawRect fill
            canvas.drawColor(Color.WHITE);
            p.setColor(Color.RED);
            canvas.drawRect(40, 20, 400, 140, p);              // R1 red rect
            // R2: drawCircle fill + stroke
            p.setColor(Color.BLUE);
            p.setStyle(Paint.Style.FILL);
            canvas.drawCircle(140, 280, 80, p);                // R2 blue disc
            p.setColor(Color.rgb(0,150,0));
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(12);
            canvas.drawCircle(420, 280, 80, p);                // R2 stroke ring
            // R3: drawLine (2x) + drawText
            p.setColor(Color.BLACK);
            p.setStyle(Paint.Style.FILL);
            p.setStrokeWidth(6);
            canvas.drawLine(40, 500, 700, 500, p);
            canvas.drawLine(40, 560, 700, 560, p);
            p.setTextSize(40);
            canvas.drawText("OK", 760, 540, p);                // R3 text
            // R4: translate + restore
            canvas.save();
            canvas.translate(300, 620);
            p.setColor(Color.rgb(128,0,128));
            canvas.drawRect(40, 640, 240, 740, p);             // R4 purple at 340,1260 (translated)
            canvas.restore();
            // R5: scale probe — scale(2,2) then small rect; if scale applied,
            // the rect appears 4x area at doubled coords.
            canvas.save();
            canvas.scale(2.0f, 2.0f);
            p.setColor(Color.rgb(255,140,0));
            canvas.drawRect(40, 820, 90, 845, p);              // R5 orange probe
            canvas.restore();
            // R6: clipRect probe — clip then draw outside; if clip enforced,
            // the outside part must not appear.
            canvas.save();
            p.setColor(Color.rgb(0,180,180));
            canvas.clipRect(40, 980, 300, 1080);
            canvas.drawRect(40, 980, 800, 1080, p);            // R6 teal (clipped?)
            canvas.restore();
            // R7: rotate probe — rotate 45 then axis-aligned rect; if rotation
            // applied the raster is a diamond, else a plain rect.
            canvas.save();
            canvas.rotate(45);
            p.setColor(Color.rgb(90,90,90));
            canvas.drawRect(600, 1150, 800, 1200, p);          // R7 gray probe
            canvas.restore();
            // R8: setARGB probe — engine gap census (A5): currently unhandled.
            Paint p2 = new Paint();
            p2.setARGB(255, 0, 0, 200);
            canvas.drawRect(40, 1300, 400, 1400, p2);          // R8 expect blue
            // R9: drawRoundRect probe (radius 40 — corners rounded?)
            p.setColor(Color.rgb(180,120,60));
            canvas.drawRoundRect(460, 1300, 860, 1400, 40, 40, p); // R9 brown
            // R10: drawText non-ASCII probe (A6): Persian via Canvas
            canvas.drawText("سلام", 40, 1520, p);
        }
    }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(new ProbeView(this)); }
}
EOF

# ---------- A4 invisible-view-drawn probe ----------
mk f06_invisible f06invisible "F06 Invisible"
mkdir -p "$FDST/f06_invisible/res/layout"
cat > "$FDST/f06_invisible/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#FFFFFFFF">
    <View android:layout_width="1080px" android:layout_height="800px"
        android:background="#FF000000" android:visibility="invisible"/>
</FrameLayout>
EOF
sed 's/f01color/f06invisible/' "$FDST/f01_color/src/com/miniandroid/f01color/MainActivity.java" > "$FDST/f06_invisible/src/com/miniandroid/f06invisible/MainActivity.java"

# ---------- C3 LL horizontal cross-axis TOP ----------
mk f18_lltop f18lltop "F18 LLTop"
mkdir -p "$FDST/f18_lltop/res/layout"
cat > "$FDST/f18_lltop/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="horizontal" android:background="#FFFFFFFF">
    <View android:layout_width="200px" android:layout_height="400px"
        android:layout_gravity="top" android:background="#FFFF0000"/>
</LinearLayout>
EOF
sed 's/f01color/f18lltop/' "$FDST/f01_color/src/com/miniandroid/f01color/MainActivity.java" > "$FDST/f18_lltop/src/com/miniandroid/f18lltop/MainActivity.java"

# ---------- A2 dimen seeding probe: getDimensionPixelSize ----------
mk f32_dimen f32dimen "F32 Dimen"
mkdir -p "$FDST/f32_dimen/res/layout" "$FDST/f32_dimen/res/values"
cat > "$FDST/f32_dimen/res/values/dimens.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <dimen name="probe">100dp</dimen>
</resources>
EOF
cat > "$FDST/f32_dimen/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#FFFFFFFF">
    <View android:id="@+id/probe" android:layout_width="1080px" android:layout_height="262px"
        android:background="#FF123456"/>
</LinearLayout>
EOF
cat > "$FDST/f32_dimen/src/com/miniandroid/f32dimen/MainActivity.java" <<'EOF'
package com.miniandroid.f32dimen;
import android.app.Activity; import android.os.Bundle; import android.view.View;
import android.widget.TextView; import android.widget.LinearLayout;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        // AOSP law: 100dp at density 2.625 (420dpi bucket) = 262px (262.5 floored).
        int px = getResources().getDimensionPixelSize(R.dimen.probe);
        TextView tv = new TextView(this);
        tv.setText("PX=" + px);
        ((LinearLayout) findViewById(R.id.dimroot)).addView(tv);
    }
}
EOF
python3 - <<'PYEOF'
p="/home/z/my-project/miniandroid/tests/fixtures_foundation/f32_dimen/res/layout/activity_main.xml"
s=open(p).read().replace('<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"\n    android:layout_width="match_parent"',
 '<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"\n    android:id="@+id/dimroot"\n    android:layout_width="match_parent"')
open(p,"w").write(s)
PYEOF

# ---------- Persian shaping contrast: joined vs spaced ----------
mk f05b_persian2 f05bpersian2 "F05b Persian2"
mkdir -p "$FDST/f05b_persian2/res/layout"
cat > "$FDST/f05b_persian2/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#FFFFFFFF">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="سلام" android:textSize="60sp" android:textColor="#FF000000"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="س ل ا م" android:textSize="60sp" android:textColor="#FF000000"/>
</LinearLayout>
EOF
sed 's/f04text/f05bpersian2/' "$FDST/f04_text/src/com/miniandroid/f04text/MainActivity.java" > "$FDST/f05b_persian2/src/com/miniandroid/f05bpersian2/MainActivity.java"

# ---------- RT39-44 runtime probes (trace/text-verified) ----------
mk f39_44_runtime f3944 "F39-44 Runtime"
cat > "$FDST/f39_44_runtime/src/com/miniandroid/f3944/MainActivity.java" <<'EOF'
package com.miniandroid.f3944;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
import java.lang.reflect.Method;
public class MainActivity extends Activity {
    static int staticInit = 0;
    static { staticInit = 11; }
    int fieldInit = 22;
    public interface Shape { int area(); }
    public static class Sq implements Shape {
        public int area() { return 9; }
    }
    public static class Base { public String name() { return "BASE"; } }
    public static class Sub extends Base { @Override public String name() { return "SUB"; } }
    public static class Box { public int v; public long w; public Box(int a, long c) { v = a; w = c; } }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        // RT39 null
        String s = null; String nullOk = (s == null) ? "NULLOK" : "BAD";
        // RT40/RT41 arrays + primitive arrays + multi-dim
        int[] arr = new int[3]; arr[0] = 5; arr[2] = 7;
        int[][] grid = new int[2][3]; grid[1][2] = 9;
        long[] larr = new long[2]; larr[1] = 123456789L;
        // RT42 reflection
        String refl;
        try {
            Method m = MainActivity.class.getMethod("hashCode");
            refl = "REFL" + (m != null ? "OK" : "BAD");
        } catch (NoSuchMethodException e) { refl = "REFLMISS"; }
        // RT43 superclass dispatch
        String sup = new Sub().name();
        // RT44 interface dispatch
        int area = ((Shape) new Sq()).area();
        // RT45 wide values
        Box bx = new Box(3, 4000000000L);
        long wide = bx.w + 1;
        tv.setText(nullOk + "," + arr[0] + "," + arr[2] + "," + grid[1][2] + "," +
                   larr[1] + "," + refl + "," + sup + "," + area + "," +
                   staticInit + "," + fieldInit + "," + wide);
        setContentView(tv);
    }
}
EOF

# ---------- LC26-30 lifecycle/constructor probes (text-verified) ----------
mk f26_lifecycle f26lifecycle "F26 Lifecycle"
cat > "$FDST/f26_lifecycle/src/com/miniandroid/f26lifecycle/MainActivity.java" <<'EOF'
package com.miniandroid.f26lifecycle;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    private int ctor = 0;
    private int field = 5;
    public MainActivity() { ctor = 6; }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        // LC28/LC29: constructor + field initializers ran before onCreate (F-118)
        tv.setText("INIT=" + ctor + "," + field);
        setContentView(tv);
    }
}
EOF
echo done && ls "$FDST" | wc -l
