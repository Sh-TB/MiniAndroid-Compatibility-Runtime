package com.miniandroid.f51themeattr;
import android.app.Activity; import android.os.Bundle;

// S68 W2 (A1/A10): ?attr resolution through the theme.
// Row 1: ?attr/customColor   — app attr from the theme bag   → #234567
// Row 2: ?android:attr/colorAccent — framework attr, LIGHT flavor (parent chain
//        "Theme.Material.Light") → #009688 per AOSP themes_material law
// Row 3: ?android:attr/textColorPrimary — framework state-list hand-expansion
//        (colorForeground × primaryContentAlpha, light) → 0xde000000 over white
public class MainActivity extends Activity {
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(com.miniandroid.f51themeattr.R.layout.activity_main);
    }
}
