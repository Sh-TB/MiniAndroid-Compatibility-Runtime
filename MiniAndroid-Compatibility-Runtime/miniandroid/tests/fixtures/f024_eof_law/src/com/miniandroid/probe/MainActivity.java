/*
 * M3 F-024 micro reproducer — the InputStream EOF law family, executed as
 * real DEX inside a real APK, with a VISUAL verdict.
 *
 * The single law under proof (libcore/ojluni java.io.InputStream):
 *     read() returns the next byte 0..255, and -1 at end of stream —
 *     forever (repeated reads after EOF keep returning -1), and
 *     read(byte[],off,len) returns the count filled, -1 at EOF.
 * The historical defect class this guards against: a fail-soft read()
 * that returns 0 (spinning every `while ((b = read()) != -1)` loop
 * forever) or that renders 0xFF as a signed -1 (making EOF
 * indistinguishable from a data byte).
 *
 * Seven laws, one 150px verdict band each (green = holds, red = violated):
 *   L1 empty stream:        first read() == -1 immediately
 *   L2 single-byte stream:  read() == 0x41, next read() == -1
 *   L3 0xFF is DATA:        read() == 255 (not -1, not 0 — unsigned law)
 *   L4 EOF is sticky:       3 further reads after EOF all == -1
 *   L5 bulk read:           read(buf,0,64) == 11, bytes land, then -1
 *   L6 loop terminates:     while((b=read())!=-1) counts exactly 11
 *   L7 close() law:         available() 11→0 across drain; read-after-close
 *                           observes EOF (runtime law: closed = EOF)
 *
 * Determinism: no time, no randomness, no collections — the same 7 bands
 * every run, byte-identical framebuffer.
 */
package com.miniandroid.probe;

import android.app.Activity;
import android.content.res.AssetManager;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.View;
import java.io.InputStream;

public class MainActivity extends Activity {

    static boolean l1 = false, l2 = false, l3 = false,
                   l4 = false, l5 = false, l6 = false, l7 = false;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            AssetManager am = getAssets();

            // L1 — empty stream: EOF on the very first read.
            InputStream e = am.open("empty.bin");
            l1 = (e.read() == -1);
            e.close();

            // L2 — single-byte stream: exactly one data byte, then EOF.
            InputStream o = am.open("one.bin");
            int b1 = o.read();
            int b2 = o.read();
            l2 = (b1 == 0x41 && b2 == -1);
            o.close();

            // L3 — 0xFF is a DATA byte (255), never a signed -1.
            InputStream f = am.open("ff.bin");
            int ff = f.read();
            l3 = (ff == 255);
            // L4 — EOF is sticky: keep reading, keep getting -1.
            int r1 = f.read(), r2 = f.read(), r3 = f.read();
            l4 = (ff != -1) && (r1 == -1 && r2 == -1 && r3 == -1);
            f.close();

            // L5 — bulk read: count filled, bytes land at off, then EOF.
            InputStream t = am.open("text.bin");
            byte[] buf = new byte[64];
            int n = t.read(buf, 0, 64);
            boolean landed = (n == 11) && (buf[0] == 0x48 /*H*/)
                && (buf[10] == 0x21 /*!*/) && (buf[11] == 0);
            int after = t.read();
            l5 = landed && (after == -1);
            t.close();

            // L6 — the canonical drain loop terminates with the exact count.
            InputStream t2 = am.open("text.bin");
            int count = 0;
            int b;
            while ((b = t2.read()) != -1) {
                count++;
                if (count > 1000) break; // guard: never spin forever
            }
            l6 = (count == 11);
            // L7 — available() + close(): 11 pending before, 0 at EOF;
            // a read after close observes EOF (runtime law: closed = EOF).
            InputStream t3 = am.open("text.bin");
            int avail0 = t3.available();
            int drain = 0;
            while ((b = t3.read()) != -1) drain++;
            int availEnd = t3.available();
            t3.close();
            int closedRead = t3.read();
            l7 = (avail0 == 11) && (availEnd == 0) && (closedRead == -1);
        } catch (Throwable t) {
            // any throw = law chain violated; bands render red
        }
        setContentView(new ProbeView(this));
    }

    class ProbeView extends View {
        ProbeView(android.content.Context c) { super(c); }

        @Override
        public void onDraw(Canvas canvas) {
            canvas.drawColor(0xFFFFFFFF);
            Paint p = new Paint();
            p.setStyle(Paint.Style.FILL);
            boolean[] laws = { l1, l2, l3, l4, l5, l6, l7 };
            for (int i = 0; i < 7; i++) {
                p.setColor(laws[i] ? 0xFF00A000 : 0xFFD00000);
                int top = 100 + i * 250;
                canvas.drawRect(100, top, 980, top + 150, p);
            }
        }
    }
}
