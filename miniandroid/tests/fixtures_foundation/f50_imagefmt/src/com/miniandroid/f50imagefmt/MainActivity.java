package com.miniandroid.f50imagefmt;
import android.app.Activity; import android.os.Bundle;

// S68 FOUNDATION (A3/§13): image FORMAT corpus through the ImageView inflate
// path. All sources are KNOWN solids: JPEG magenta, WebP cyan, palette PNG
// orange, grayscale PNG 128, GIF green (EXPLICIT-UNSUPPORTED — must show the
// labelled placeholder, never a silent drop).
public class MainActivity extends Activity {
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(com.miniandroid.f50imagefmt.R.layout.activity_main);
    }
}
