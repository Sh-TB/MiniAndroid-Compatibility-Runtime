package com.probe.swipe1;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.View;

// CONT-86 SWIPE fixture (CONT-84 T8 closure): drives the S129 (R-NEW-425/426)
// generic --swipe gesture law end-to-end through the REAL pipeline:
//   harness --swipe -> TouchDispatcher -> engine-materialized MotionEvent
//   stream (DOWN + 12 interpolated MOVEs + UP) -> app View.onTouchEvent ->
//   app GestureDetector (C++ shadow FSM) -> Listener callbacks.
// Evidence lives in the [SWIPE1-*] stderr rows + the verdict canvas band;
// NOT in the screenshot alone.
public class MainActivity extends Activity {
    private static int downs = 0, moves = 0, ups = 0;
    private static int scrolls = 0, flings = 0, taps = 0;
    private static float lastDx = Float.NaN, lastDy = Float.NaN;
    private static float flingVx = Float.NaN, flingVy = Float.NaN;
    private static long evTimeFirst = -1, evTimeLast = -1;
    private static String verdict = "PENDING";

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        System.out.println("[SWIPE1-VERSION] pkg=com.probe.swipe1 wave=CONT-86");
        setContentView(new ProbeView(this));
        System.out.println("[SWIPE1-DONE] setup complete");
    }

    static class ProbeView extends View {
        GestureDetector det;
        ProbeView(Context c) {
            super(c);
            det = new GestureDetector(c, new Listener());
        }
        @Override public boolean onTouchEvent(MotionEvent ev) {
            int a = ev.getAction();
            float x = ev.getX();
            float y = ev.getY();
            long t = ev.getEventTime();
            System.out.println("[SWIPE1-EV] action=" + a + " x=" + x + " y=" + y
                + " t=" + t);
            if (a == MotionEvent.ACTION_DOWN) { downs++; evTimeFirst = t; }
            if (a == MotionEvent.ACTION_MOVE) moves++;
            if (a == MotionEvent.ACTION_UP) { ups++; evTimeLast = t; }
            boolean handled = det.onTouchEvent(ev);
            System.out.println("[SWIPE1-DET] action=" + a + " handled=" + handled);
            return true;
        }
        @Override public void onDraw(Canvas cv) {
            cv.drawColor(Color.WHITE);
            Paint p = new Paint();
            p.setColor(Color.BLACK);
            p.setTextSize(30);
            cv.drawText("downs=" + downs + " moves=" + moves + " ups=" + ups,
                        20, 60, p);
            cv.drawText("scrolls=" + scrolls + " flings=" + flings
                        + " taps=" + taps, 20, 110, p);
            cv.drawText("lastDx=" + lastDx + " lastDy=" + lastDy, 20, 160, p);
            cv.drawText("flingVx=" + flingVx + " flingVy=" + flingVy, 20, 210, p);
            cv.drawText("evT=" + evTimeFirst + ".." + evTimeLast, 20, 260, p);
            p.setColor(verdict.startsWith("PASS") ? Color.rgb(0,128,0)
                                                  : Color.rgb(180,0,0));
            cv.drawText(verdict, 20, 320, p);
        }
        static class Listener extends GestureDetector.SimpleOnGestureListener {
            @Override public boolean onDown(MotionEvent e) {
                System.out.println("[SWIPE1-ONDOWN] x=" + e.getX()
                    + " y=" + e.getY());
                return true;
            }
            @Override public boolean onScroll(MotionEvent e1, MotionEvent e2,
                                              float dx, float dy) {
                scrolls++;
                lastDx = dx;
                lastDy = dy;
                int idx = (int) dx;
                int idy = (int) dy;
                System.out.println("[SWIPE1-SCROLL] n=" + scrolls
                    + " dx=" + dx + " dy=" + dy
                    + " idx=" + idx + " idy=" + idy
                    + " e1=" + e1.getX() + "," + e1.getY()
                    + " e2=" + e2.getX() + "," + e2.getY());
                verdict = "SCROLL-SEEN";
                return true;
            }
            @Override public boolean onFling(MotionEvent e1, MotionEvent e2,
                                             float vx, float vy) {
                flings++;
                flingVx = vx;
                flingVy = vy;
                System.out.println("[SWIPE1-FLING] n=" + flings
                    + " vx=" + vx + " vy=" + vy
                    + " ivx=" + (int) vx + " ivy=" + (int) vy
                    + " e1=" + e1.getX() + "," + e1.getY()
                    + " e2=" + e2.getX() + "," + e2.getY());
                verdict = "FLING-SEEN";
                return true;
            }
            @Override public boolean onSingleTapUp(MotionEvent e) {
                taps++;
                System.out.println("[SWIPE1-TAPUP] n=" + taps);
                return true;
            }
        }
    }
}
