#!/usr/bin/env bash
# scripts/foundation/make_fixtures.sh — S67 WAVE 1 base micro-corpus generator.
# Creates deterministic fixture APK sources under miniandroid/tests/fixtures_foundation/.
# Each fixture isolates ONE base contract (user §17 numbering).
set -euo pipefail
ROOT=/home/z/my-project
FDST=$ROOT/miniandroid/tests/fixtures_foundation
mkdir -p "$FDST"

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

mk() { # mk <name> <pkg> <label>
  mkdir -p "$FDST/$1/src/com/miniandroid/$2"
  echo "$MAN" | sed "s/__PKG__/$2/g; s/__LABEL__/$3/g" > "$FDST/$1/AndroidManifest.xml"
}

# ---------- R01 color: 4 solid bands (red/green/blue/black) ----------
mk f01_color f01color "F01 Color"
mkdir -p "$FDST/f01_color/res/layout"
cat > "$FDST/f01_color/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical">
    <FrameLayout android:layout_width="match_parent" android:layout_height="480px" android:background="#FFFF0000"/>
    <FrameLayout android:layout_width="match_parent" android:layout_height="480px" android:background="#FF00FF00"/>
    <FrameLayout android:layout_width="match_parent" android:layout_height="480px" android:background="#FF0000FF"/>
    <FrameLayout android:layout_width="match_parent" android:layout_height="480px" android:background="#FF000000"/>
</LinearLayout>
EOF
cat > "$FDST/f01_color/src/com/miniandroid/f01color/MainActivity.java" <<'EOF'
package com.miniandroid.f01color;
import android.app.Activity; import android.os.Bundle;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main); }
}
EOF

# ---------- R03 alpha: white bg + 50% red overlay ----------
mk f03_alpha f03alpha "F03 Alpha"
mkdir -p "$FDST/f03_alpha/res/layout"
cat > "$FDST/f03_alpha/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#FFFFFFFF">
    <View android:layout_width="match_parent" android:layout_height="960px"
          android:background="#80FF0000"/>
</FrameLayout>
EOF
cp "$FDST/f01_color/src/com/miniandroid/f01color/MainActivity.java" "$FDST/f03_alpha/src/com/miniandroid/f03alpha/MainActivity.java" 2>/dev/null || true
sed -i 's/f01color/f03alpha/' "$FDST/f03_alpha/src/com/miniandroid/f03alpha/MainActivity.java"
cat > "$FDST/f03_alpha/src/com/miniandroid/f03alpha/MainActivity.java" <<'EOF'
package com.miniandroid.f03alpha;
import android.app.Activity; import android.os.Bundle;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main); }
}
EOF

# ---------- R04 text: ASCII TextView ----------
mk f04_text f04text "F04 Text"
mkdir -p "$FDST/f04_text/res/layout"
cat > "$FDST/f04_text/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#FFFFFFFF">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Hello 12345" android:textSize="40sp" android:textColor="#FF000000"/>
</LinearLayout>
EOF
cat > "$FDST/f04_text/src/com/miniandroid/f04text/MainActivity.java" <<'EOF'
package com.miniandroid.f04text;
import android.app.Activity; import android.os.Bundle;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main); }
}
EOF

# ---------- R05 persian: TextView "سلام دنیا" ----------
mk f05_persian f05persian "F05 Persian"
mkdir -p "$FDST/f05_persian/res/layout"
cat > "$FDST/f05_persian/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#FFFFFFFF">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="سلام دنیا" android:textSize="40sp" android:textColor="#FF000000"/>
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Hello سلام 123" android:textSize="40sp" android:textColor="#FF000000"/>
</LinearLayout>
EOF
sed 's/f04text/f05persian/' "$FDST/f04_text/src/com/miniandroid/f04text/MainActivity.java" > "$FDST/f05_persian/src/com/miniandroid/f05persian/MainActivity.java"

# ---------- L11 linear weights: 3 equal 1:1:1 ----------
mk f11_linear f11linear "F11 Linear"
mkdir -p "$FDST/f11_linear/res/layout"
cat > "$FDST/f11_linear/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical">
    <FrameLayout android:layout_width="match_parent" android:layout_height="0dp"
        android:layout_weight="1" android:background="#FFAA0000"/>
    <FrameLayout android:layout_width="match_parent" android:layout_height="0dp"
        android:layout_weight="1" android:background="#FF00AA00"/>
    <FrameLayout android:layout_width="match_parent" android:layout_height="0dp"
        android:layout_weight="1" android:background="#FF0000AA"/>
</LinearLayout>
EOF
sed 's/f01color/f11linear/' "$FDST/f01_color/src/com/miniandroid/f01color/MainActivity.java" > "$FDST/f11_linear/src/com/miniandroid/f11linear/MainActivity.java"

# ---------- L13 frame gravity: top-left / center / bottom-right ----------
mk f13_frame f13frame "F13 Frame"
mkdir -p "$FDST/f13_frame/res/layout"
cat > "$FDST/f13_frame/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#FF202020">
    <View android:layout_width="200px" android:layout_height="200px"
        android:background="#FFFF0000"/>
    <View android:layout_width="200px" android:layout_height="200px"
        android:layout_gravity="center" android:background="#FF00FF00"/>
    <View android:layout_width="200px" android:layout_height="200px"
        android:layout_gravity="bottom|right" android:background="#FF0000FF"/>
</FrameLayout>
EOF
sed 's/f01color/f13frame/' "$FDST/f01_color/src/com/miniandroid/f01color/MainActivity.java" > "$FDST/f13_frame/src/com/miniandroid/f13frame/MainActivity.java"

# ---------- L14 relative: alignParent / below / toRightOf / center ----------
mk f14_relative f14relative "F14 Relative"
mkdir -p "$FDST/f14_relative/res/layout"
cat > "$FDST/f14_relative/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:background="#FFFFFFFF">
    <View android:id="@+id/anchor" android:layout_width="300px" android:layout_height="300px"
        android:layout_alignParentTop="true" android:layout_alignParentRight="true"
        android:background="#FFFF0000"/>
    <View android:id="@+id/belowv" android:layout_width="300px" android:layout_height="300px"
        android:layout_below="@id/anchor" android:layout_alignParentLeft="true"
        android:background="#FF00FF00"/>
    <View android:id="@+id/rightof" android:layout_width="200px" android:layout_height="200px"
        android:layout_toRightOf="@id/belowv" android:layout_alignTop="@id/belowv"
        android:background="#FF0000FF"/>
    <View android:layout_width="400px" android:layout_height="400px"
        android:layout_centerInParent="true" android:background="#FF00FFFF"/>
</RelativeLayout>
EOF
sed 's/f01color/f14relative/' "$FDST/f01_color/src/com/miniandroid/f01color/MainActivity.java" > "$FDST/f14_relative/src/com/miniandroid/f14relative/MainActivity.java"

# ---------- RES31 string + RES32 color from resources ----------
mk f31_resources f31res "F31 Resources"
mkdir -p "$FDST/f31_resources/res/layout" "$FDST/f31_resources/res/values"
cat > "$FDST/f31_resources/res/values/strings.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="greeting">Resource String Works</string>
</resources>
EOF
cat > "$FDST/f31_resources/res/values/colors.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="brand">#FF00695C</color>
    <color name="accent">#FFF9A825</color>
</resources>
EOF
cat > "$FDST/f31_resources/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="@color/brand">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="@string/greeting" android:textSize="40sp" android:textColor="@color/accent"/>
</LinearLayout>
EOF
cat > "$FDST/f31_resources/src/com/miniandroid/f31res/MainActivity.java" <<'EOF'
package com.miniandroid.f31res;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        // API-path cross-check: same string via getResources()
        TextView tv = (TextView) findViewById(R.id.res_tv);
        if (tv != null) tv.setText(R.string.greeting);
    }
}
EOF
sed -i 's|<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n        android:text="@string/greeting"|<TextView android:id="@+id/res_tv" android:layout_width="wrap_content" android:layout_height="wrap_content"\n        android:text="@string/greeting"|' "$FDST/f31_resources/res/layout/activity_main.xml"
python3 - <<'PYEOF'
import re
p="/home/z/my-project/miniandroid/tests/fixtures_foundation/f31_resources/res/layout/activity_main.xml"
s=open(p).read().replace('<TextView android:layout_width="wrap_content" android:layout_height="wrap_content"\n        android:text="@string/greeting"',
 '<TextView android:id="@+id/res_tv" android:layout_width="wrap_content" android:layout_height="wrap_content"\n        android:text="@string/greeting"')
open(p,"w").write(s)
PYEOF

# ---------- I21 button: click → state → text change ----------
mk f21_button f21button "F21 Button"
mkdir -p "$FDST/f21_button/res/layout"
cat > "$FDST/f21_button/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:gravity="center" android:background="#FFFFFFFF">
    <Button android:id="@+id/btn" android:layout_width="400px" android:layout_height="160px"
        android:text="TAP ME"/>
    <TextView android:id="@+id/state" android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="STATE=0" android:textSize="40sp" android:textColor="#FF000000"/>
</LinearLayout>
EOF
cat > "$FDST/f21_button/src/com/miniandroid/f21button/MainActivity.java" <<'EOF'
package com.miniandroid.f21button;
import android.app.Activity; import android.os.Bundle; import android.view.View;
import android.widget.Button; import android.widget.TextView;
public class MainActivity extends Activity {
    private int count = 0;
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        Button btn = (Button) findViewById(R.id.btn);
        final TextView state = (TextView) findViewById(R.id.state);
        btn.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                count++;
                state.setText("STATE=" + count);
            }
        });
    }
}
EOF

# ---------- LC27 startActivity: two activities ----------
mk f27_nav f27nav "F27 Nav"
mkdir -p "$FDST/f27_nav/res/layout"
cat > "$FDST/f27_nav/res/layout/activity_main.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#FFFFEECC" android:gravity="center">
    <Button android:id="@+id/go" android:layout_width="400px" android:layout_height="160px"
        android:text="GO SECOND"/>
</LinearLayout>
EOF
cat > "$FDST/f27_nav/res/layout/activity_second.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:background="#FFCCEEFF" android:gravity="center">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="SECOND ACTIVITY" android:textSize="40sp"/>
</LinearLayout>
EOF
cat > "$FDST/f27_nav/src/com/miniandroid/f27nav/MainActivity.java" <<'EOF'
package com.miniandroid.f27nav;
import android.app.Activity; import android.content.Intent; import android.os.Bundle;
import android.view.View; import android.widget.Button;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        Button go = (Button) findViewById(R.id.go);
        go.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivity(new Intent(MainActivity.this, SecondActivity.class));
            }
        });
    }
}
EOF
cat > "$FDST/f27_nav/src/com/miniandroid/f27nav/SecondActivity.java" <<'EOF'
package com.miniandroid.f27nav;
import android.app.Activity; import android.os.Bundle;
public class SecondActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_second); }
}
EOF
python3 - <<'PYEOF'
p="/home/z/my-project/miniandroid/tests/fixtures_foundation/f27_nav/AndroidManifest.xml"
s=open(p).read()
s=s.replace('</application>','        <activity android:name="com.miniandroid.f27nav.SecondActivity" android:label="F27 Second"/>\n    </application>')
open(p,"w").write(s)
PYEOF

# ---------- RT38-45 runtime micro probes (no UI: trace-verified) ----------
for name in f38_identity f45_exceptions; do
  mk "$name" "${name}_pkg" "$name"
done
cat > "$FDST/f38_identity/src/com/miniandroid/f38_identity_pkg/MainActivity.java" <<'EOF'
package com.miniandroid.f38_identity_pkg;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    public static class Box { public int v; }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        Box a = new Box(); a.v = 7;
        Box c = a;                 // identity: same reference
        c.v = 42;                  // mutates a.v too
        Box d = new Box(); d.v = 42;
        boolean same = (a == c);       // true
        boolean diff = (a == d);       // false (equal fields, different identity)
        tv.setText("IDENT=" + same + "," + diff + ",v=" + a.v);
        setContentView(tv);
    }
}
EOF
cat > "$FDST/f45_exceptions/src/com/miniandroid/f45_exceptions_pkg/MainActivity.java" <<'EOF'
package com.miniandroid.f45_exceptions_pkg;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        String result;
        try {
            int[] arr = new int[3];
            arr[5] = 1;                      // AIOOBE
            result = "NO_THROW";
        } catch (ArrayIndexOutOfBoundsException e) {
            result = "CAUGHT_AIOOBE";
        } finally {
            // finally path
        }
        setContentView(tv);
        tv.setText("EXC=" + result);
    }
}
EOF
echo "FIXTURES CREATED:" && ls "$FDST"
