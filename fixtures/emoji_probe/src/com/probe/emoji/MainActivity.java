package com.probe.emoji;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

/** cont70 ANT-13: emoji rendering evidence (audit item 25). A color-emoji
 * glyph (U+1F600 GRINNING FACE) drawn at 128px on a custom view; a second
 * row draws the CJK glyph 好 as a wide-coverage control. Verdict is taken
 * from the pixels: a CBDT color strike yields MANY distinct colors in the
 * emoji band; a tofu/blank band yields ~1. */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(new View(this) {
            @Override
            protected void onDraw(Canvas c) {
                c.drawColor(Color.WHITE);
                Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
                p.setTextSize(128f);
                p.setColor(Color.BLACK);
                c.drawText("\uD83D\uDE00", 80, 300, p);   // 😀
                c.drawText("好", 80, 600, p);              // CJK control
            }
        });
    }
}
