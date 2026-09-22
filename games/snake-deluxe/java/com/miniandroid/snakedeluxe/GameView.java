package com.miniandroid.snakedeluxe;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Handler;
import android.os.Looper;
import android.view.View;

/**
 * Snake Deluxe game surface — real Canvas.onDraw rendering:
 * dark board, checker cells, rounded striped snake body, directional head
 * eyes, apple food, score HUD.
 *
 * RUNTIME LAW NOTES (S80):
 * - All game state lives in STATIC fields. The engine's SGET/SPUT storage is
 *   class-global and shared across every dispatch context (click listeners,
 *   main-looper runnables, onDraw) — object-identity frontier (S79) makes
 *   cross-object instance-field mutation invisible to the render path.
 * - The game tick is a self-reposting Handler.postDelayed runnable on the
 *   main looper — the engine's canonical animation pattern (frame-stepped
 *   message queue), not a background thread.
 */
public class GameView extends View {

    // ---- board geometry ------------------------------------------------
    static final int COLS = 15;
    static final int ROWS = 16;
    static final int MAXLEN = COLS * ROWS;
    static final int TICK_MS = 190;

    // ---- palette --------------------------------------------------------
    static final int C_BG      = 0xFF0F172A;
    static final int C_BOARD   = 0xFF1E293B;
    static final int C_CHK_A   = 0xFF1B2841;
    static final int C_CHK_B   = 0xFF21304C;
    static final int C_BORDER  = 0xFF38BDF8;
    static final int C_HEAD    = 0xFF4ADE80;
    static final int C_BODY_A  = 0xFF22C55E;
    static final int C_BODY_B  = 0xFF18A54B;
    static final int C_TAIL    = 0xFF15803D;
    static final int C_APPLE   = 0xFFEF4444;
    static final int C_LEAF    = 0xFF4ADE80;
    static final int C_STEM    = 0xFF7C2D12;
    static final int C_SCORE   = 0xFFF8FAFC;
    static final int C_BEST    = 0xFF94A3B8;
    static final int C_HINT    = 0xFFCBD5E1;

    // ---- static game state ------------------------------------------------
    static MainActivity host;
    static int[] bx = new int[MAXLEN];
    static int[] by = new int[MAXLEN];
    static int headIdx = 0;
    static int len = 3;
    static int dx = 1, dy = 0;
    static int[] qdx = new int[4], qdy = new int[4];
    static int qlen = 0;
    static int fx = 8, fy = 6;
    static int score = 0, best = 0;
    static boolean started = false, alive = true, over = false;
    static long seed = 0x2F6E2B1L;
    static boolean tickScheduled = false;

    static Handler h;
    Paint p = new Paint();

    public GameView(Context c) {
        super(c);
        initSnake();
        h = new Handler(Looper.getMainLooper());
    }

    static void initSnake() {
        len = 3; headIdx = 0; dx = 1; dy = 0; qlen = 0;
        score = 0; alive = true; over = false; started = false;
        for (int i = 0; i < len; i++) {
            bx[(headIdx - i + MAXLEN) % MAXLEN] = 5 - i;
            by[(headIdx - i + MAXLEN) % MAXLEN] = 7;
        }
    }

    /** Main-looper self-reposting ticker — the runtime's frame-stepped
     *  animation law (postDelayed queue drained once per frame). */
    public void startTicker() {
        if (tickScheduled) return;
        tickScheduled = true;
        h.postDelayed(ticker, TICK_MS);
    }

    final Runnable ticker = new Runnable() {
        public void run() {
            if (started && alive) step();
            postInvalidate();
            h.postDelayed(this, TICK_MS);
        }
    };

    // ---- deterministic app-local PRNG (LCG, glibc constants) -------------
    static int nextRnd(int bound) {
        seed = (seed * 1103515245L + 12345L) & 0x7FFFFFFFL;
        return (int) (seed % (long) bound);
    }

    public static void toggleStart() {
        if (!alive || over) { resetAndStart(); return; }
        started = !started;
        postInv();
    }

    public static void resetAndStart() {
        initSnake();
        started = true;
        spawnFood();
        postInv();
    }

    public static void pushDir(int ndx, int ndy) {
        if (qlen >= 4) return;
        int lx = qlen == 0 ? dx : qdx[qlen - 1];
        int ly = qlen == 0 ? dy : qdy[qlen - 1];
        if (ndx == -lx && ndy == -ly) return;   // reverse guard
        if (ndx == lx && ndy == ly) return;     // duplicate no-op
        qdx[qlen] = ndx; qdy[qlen] = ndy; qlen++;
        postInv();
    }

    static void postInv() {
        // static context has no View — the engine re-renders every frame
        // regardless; nothing to do here.
    }

    static boolean bodyAt(int x, int y, int skipTail) {
        for (int i = 0; i < len - skipTail; i++) {
            int idx = (headIdx - i + MAXLEN) % MAXLEN;
            if (bx[idx] == x && by[idx] == y) return true;
        }
        return false;
    }

    static void spawnFood() {
        int empty = COLS * ROWS - len;
        if (empty <= 0) return;
        int pick = nextRnd(empty);
        int seen = 0;
        for (int y = 0; y < ROWS; y++) {
            for (int x = 0; x < COLS; x++) {
                if (!bodyAt(x, y, 0)) {
                    if (seen == pick) { fx = x; fy = y; return; }
                    seen++;
                }
            }
        }
    }

    static void step() {
        if (qlen > 0) {
            dx = qdx[0]; dy = qdy[0];
            for (int i = 1; i < qlen; i++) { qdx[i - 1] = qdx[i]; qdy[i - 1] = qdy[i]; }
            qlen--;
        }
        int nhx = bx[headIdx] + dx;
        int nhy = by[headIdx] + dy;
        if (nhx < 0 || nhy < 0 || nhx >= COLS || nhy >= ROWS) { die(); return; }
        if (bodyAt(nhx, nhy, 1)) { die(); return; }   // tail vacates this tick
        headIdx = (headIdx + 1) % MAXLEN;
        bx[headIdx] = nhx; by[headIdx] = nhy;
        if (nhx == fx && nhy == fy) {
            len++;
            score++;
            if (score > best) best = score;
            if (len >= MAXLEN) { started = false; return; }  // perfect win
            spawnFood();
        }
    }

    static void die() {
        alive = false; over = true; started = false;
        if (host != null) host.showGameOver(score, best);
    }

    // ---- rendering --------------------------------------------------------
    @Override
    protected void onDraw(Canvas cv) {
        int w = cv.getWidth();
        int hgt = cv.getHeight();
        p.setStyle(Paint.Style.FILL);
        cv.drawColor(C_BG);

        int pad = 24;
        int topStrip = 132;
        int cell = Math.min((w - 2 * pad) / COLS, (hgt - topStrip - pad) / ROWS);
        int bw = cell * COLS, bh = cell * ROWS;
        int bxl = (w - bw) / 2, byt = topStrip;

        // board base + checker
        p.setColor(C_BOARD);
        cv.drawRoundRect(bxl - 10, byt - 10, bxl + bw + 10, byt + bh + 10, 30, 30, p);
        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                p.setColor(((r + c) & 1) == 0 ? C_CHK_A : C_CHK_B);
                cv.drawRect(bxl + c * cell, byt + r * cell,
                            bxl + (c + 1) * cell, byt + (r + 1) * cell, p);
            }
        }

        // apple
        int acx = bxl + fx * cell + cell / 2;
        int acy = byt + fy * cell + cell / 2;
        int ar = (int) (cell * 0.36f);
        p.setColor(C_APPLE);
        cv.drawCircle(acx, acy, ar, p);
        p.setColor(C_LEAF);
        cv.drawCircle(acx + ar / 2, acy - ar - 2, ar / 3, p);
        p.setColor(C_STEM);
        cv.drawRect(acx - 2, acy - ar - 6, acx + 3, acy - ar + 6, p);
        p.setColor(0x99FFFFFF);
        cv.drawCircle(acx - ar / 3, acy - ar / 3, ar / 5, p);

        // snake (ring buffer: index 0 = head)
        float inset = cell * 0.07f;
        float rad = cell * 0.30f;
        for (int i = len - 1; i >= 0; i--) {
            int idx = (headIdx - i + MAXLEN) % MAXLEN;
            int col;
            if (i == 0) col = C_HEAD;
            else if (i == len - 1) col = C_TAIL;
            else col = (i & 1) == 0 ? C_BODY_A : C_BODY_B;
            p.setColor(col);
            cv.drawRoundRect(bxl + bx[idx] * cell + inset, byt + by[idx] * cell + inset,
                             bxl + (bx[idx] + 1) * cell - inset, byt + (by[idx] + 1) * cell - inset,
                             rad, rad, p);
        }
        // head eyes (direction-aware)
        int hx = bxl + bx[headIdx] * cell, hy = byt + by[headIdx] * cell;
        float er = cell * 0.13f, pr = cell * 0.065f;
        float ecx, ecy, e2x, e2y;
        if (dx != 0) {
            float fxo = dx > 0 ? cell * 0.62f : cell * 0.38f;
            ecx = hx + fxo; ecy = hy + cell * 0.32f;
            e2x = hx + fxo; e2y = hy + cell * 0.68f;
        } else {
            float fyo = dy > 0 ? cell * 0.62f : cell * 0.38f;
            ecx = hx + cell * 0.32f; ecy = hy + fyo;
            e2x = hx + cell * 0.68f; e2y = hy + fyo;
        }
        p.setColor(0xFFFFFFFF);
        cv.drawCircle(ecx, ecy, er, p);
        cv.drawCircle(e2x, e2y, er, p);
        p.setColor(0xFF0F172A);
        cv.drawCircle(ecx + dx * pr * 1.4f, ecy + dy * pr * 1.4f, pr, p);
        cv.drawCircle(e2x + dx * pr * 1.4f, e2y + dy * pr * 1.4f, pr, p);

        // border on top
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(6);
        p.setColor(C_BORDER);
        cv.drawRoundRect(bxl - 10, byt - 10, bxl + bw + 10, byt + bh + 10, 30, 30, p);
        p.setStyle(Paint.Style.FILL);

        // score HUD
        p.setColor(C_SCORE);
        p.setTextSize(58);
        p.setFakeBoldText(true);
        cv.drawText("SCORE " + score, bxl - 6, 92, p);
        p.setColor(C_BEST);
        p.setTextSize(44);
        p.setFakeBoldText(false);
        String bs = "BEST " + best;
        // Align.RIGHT is not reproduced by the runtime text path — place by
        // estimate instead.
        float bs_w = bs.length() * 27.0f;
        cv.drawText(bs, bxl + bw - bs_w, 92, p);

        if (!started && alive && !over) {
            p.setColor(C_HINT);
            p.setTextSize(40);
            cv.drawText("PRESS START TO PLAY", bxl + bw / 2 - 260, byt + bh + 74, p);
        }
        if (over) {
            p.setColor(C_HINT);
            p.setTextSize(40);
            cv.drawText("GAME OVER", bxl + bw / 2 - 130, byt + bh + 74, p);
        }
    }
}
