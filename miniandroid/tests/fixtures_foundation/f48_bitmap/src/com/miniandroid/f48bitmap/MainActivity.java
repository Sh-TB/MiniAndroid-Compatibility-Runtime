package com.miniandroid.f48bitmap;
import android.app.Activity; import android.content.Context; import android.os.Bundle;
import android.graphics.Bitmap; import android.graphics.BitmapFactory; import android.graphics.Canvas;
import android.graphics.Color; import android.graphics.Paint; import android.view.View;

// S68 FOUNDATION (§12/§13): Bitmap + BitmapFactory + Canvas.drawBitmap family.
// Every block is drawn from KNOWN pixels so the independent PIL verifier can
// check the full chain: decodeResource → BitmapStore → drawBitmap → fb → PNG.
public class MainActivity extends Activity {
    public static class ProbeView extends View {
        private final Bitmap decoded, made, scaled, cropped;
        private final Paint p = new Paint();

        public ProbeView(Context c) {
            super(c);
            // decodeResource: red 60x40 PNG through the BitmapStore.
            decoded = BitmapFactory.decodeResource(c.getResources(), com.miniandroid.f48bitmap.R.drawable.ic_red);
            // createBitmap: zero-filled (transparent) then erased green.
            made = Bitmap.createBitmap(120, 90, Bitmap.Config.ARGB_8888);
            made.eraseColor(Color.rgb(0, 200, 0));
            scaled = Bitmap.createScaledBitmap(made, 240, 45, false);
            cropped = Bitmap.createBitmap(made, 10, 10, 50, 50);
        }

        @Override public void onDraw(Canvas canvas) {
            canvas.drawColor(Color.WHITE);
            if (decoded != null) canvas.drawBitmap(decoded, 40, 40, p);      // red 60x40 @ (40,40)
            if (made != null)    canvas.drawBitmap(made, 200, 40, p);        // green 120x90 @ (200,40)
            if (scaled != null)  canvas.drawBitmap(scaled, 200, 200, p);     // green 240x45 @ (200,200)
            if (cropped != null) canvas.drawBitmap(cropped, 40, 200, p);     // green 50x50 @ (40,200)
            p.setColor(Color.BLACK);
            p.setTextSize(36);
            String m = "BM=" + (decoded != null ? decoded.getWidth() : -1) + "x"
                     + (decoded != null ? decoded.getHeight() : -1)
                     + " MK=" + (made != null ? made.getWidth() : -1)
                     + "px @" + (made != null ? Integer.toHexString(made.getPixel(5, 5)) : "null");
            canvas.drawText(m, 40, 380, p);
        }
    }

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(new ProbeView(this));
    }
}
