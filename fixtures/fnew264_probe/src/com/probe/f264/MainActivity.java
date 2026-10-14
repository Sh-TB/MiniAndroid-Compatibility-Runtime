package com.probe.f264;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;

/**
 * F-NEW-264 probe — bitmap-target Canvas law (AOSP graphics/Canvas.java).
 *
 * Rows exercised (each independently pixel- or readback-verifiable):
 *   R1  Bitmap.createBitmap(64,64,ARGB_8888) + new Canvas(bmp) + drawColor:
 *       the bitmap MUST composite non-transparent onto the view canvas
 *       (pre-fix: drawBitmap RECORDED but 0 app-owned pixels — W4 ladder).
 *   R2  Canvas state persistence on a bitmap target: save → translate(30,20)
 *       → drawRect(0,0,10,10) → restore: the rect lands at bitmap
 *       (30..40, 20..30), NOT at (0..10, 0..10).
 *   R3  Readback law: bmp.getPixel sees the rasterized result
 *       (pre-fix: transparent zeros).
 */
public class MainActivity extends Activity {

    static class ProbeView extends View {
        final Bitmap bmp;
        final String read1, read2;

        ProbeView(Context c) {
            super(c);
            // R1: in-memory bitmap + bitmap-target canvas (onCreate-time —
            // OUTSIDE any view-draw capture window).
            bmp = Bitmap.createBitmap(64, 64, Bitmap.Config.ARGB_8888);
            Canvas bc = new Canvas(bmp);              // F-NEW-264 bind law
            bc.drawColor(0xFFCC2222);                 // red fill
            // R2: state persistence — translated rect into the SAME canvas.
            Paint green = new Paint();
            green.setColor(0xFF22AA44);
            bc.save();
            bc.translate(30, 20);
            bc.drawRect(0, 0, 10, 10, green);
            bc.restore();
            // R3: readback through Bitmap.getPixel (BitmapStore pixels).
            read1 = Integer.toHexString(bmp.getPixel(5, 5));
            read2 = Integer.toHexString(bmp.getPixel(35, 25));
        }

        @Override protected void onDraw(Canvas canvas) {
            // Background marker: dark slate so app-owned pixels are census-able.
            canvas.drawColor(0xFF303030);
            // R1+R2: composite the bitmap at (100,120); the translated green
            // rect must appear at framebuffer (130..140, 140..150).
            canvas.drawBitmap(bmp, 100, 120, null);
            // R3: print the readback values as REAL text pixels.
            Paint tp = new Paint();
            tp.setColor(0xFFFFFFFF);
            tp.setTextSize(34);
            canvas.drawText("F264R" + read1, 20, 260, tp);
            canvas.drawText("F264G" + read2, 20, 320, tp);
        }
    }

    @Override protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(new ProbeView(this));
    }
}
