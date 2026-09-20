package com.miniandroid.f49canstext;
import android.app.Activity; import android.content.Context; import android.os.Bundle;
import android.graphics.Canvas; import android.graphics.Color; import android.graphics.Paint;
import android.view.View;

// S68 FOUNDATION (A6, §14): Canvas.drawText through the REAL shaping engine.
// S67 proved Persian on the TextView path; the Canvas path was ASCII-only
// (BitmapFont) and rendered 0 px for Persian. This fixture pins the new law:
// Canvas.drawText with a paint textSize produces REAL joined Arabic-script
// ink via TextShaper (FreeType/HarfBuzz/FriBidi — the same engine TextView
// uses; one shaping engine, two consumers).
public class MainActivity extends Activity {
    public static class ProbeView extends View {
        public ProbeView(Context c) { super(c); }
        @Override public void onDraw(Canvas canvas) {
            canvas.drawColor(Color.WHITE);
            Paint p = new Paint();
            p.setColor(Color.rgb(200, 0, 0));
            p.setTextSize(64);
            canvas.drawText("سلام", 60, 140, p);          // joined Persian
            p.setColor(Color.rgb(0, 0, 200));
            canvas.drawText("م ا ل س", 60, 320, p);       // spaced Persian
            p.setColor(Color.rgb(0, 0, 0));
            p.setTextSize(40);
            canvas.drawText("ASCII OK 123", 60, 480, p);  // regression: ASCII still inked
        }
    }
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(new ProbeView(this));
    }
}
