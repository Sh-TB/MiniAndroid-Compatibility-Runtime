package com.probe.font;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;

/**
 * cont70 ANT-6 probe: Typeface.createFromAsset -> Paint.setTypeface ->
 * Canvas.drawText must rasterize with the APK-shipped face (FreeSerif),
 * NOT the system family (DejaVu Sans). Two rows are drawn: the top with
 * the app face, the bottom with the default face — the faces differ
 * visibly (serif vs sans serifs on 'Sample 123'), and the engine logs
 * FONT_RESOLUTION source=APK_ASSETS when the app face is used.
 */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Typeface appFace = null;
        try {
            appFace = Typeface.createFromAsset(getAssets(),
                                               "fonts/FreeSerif.ttf");
        } catch (RuntimeException e) {
            // AOSP failure law surfaces here if the asset is missing —
            // the probe then renders the marker row honestly.
        }
        final Typeface face = appFace;
        setContentView(new View(this) {
            @Override
            protected void onDraw(Canvas c) {
                c.drawColor(Color.WHITE);
                Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
                p.setTextSize(64f);
                // Row 1: the app face (createFromAsset product).
                p.setColor(Color.rgb(10, 10, 120));
                if (face != null) {
                    p.setTypeface(face);
                    c.drawText("R123 Sample", 40, 200, p);
                } else {
                    c.drawText("NOFACE", 40, 200, p);
                }
                // Row 2: the system default (control) — SAME string, so any
                // pixel delta between the rows is a FACE delta, not a glyph
                // delta.
                p.setTypeface(null);
                p.setColor(Color.rgb(120, 10, 10));
                c.drawText("R123 Sample", 40, 400, p);
            }
        });
    }
}
