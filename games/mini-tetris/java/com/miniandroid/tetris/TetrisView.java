package com.miniandroid.tetris;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.os.Handler;
import android.os.Looper;
import android.view.View;

/**
 * Mini Tetris game surface — real Canvas.onDraw rendering: dark board,
 * glossy rounded tetromino blocks in the classic 7-color palette, NEXT
 * preview, SCORE/LINES/LEVEL panel.
 *
 * RUNTIME LAW NOTES (S80): static state + main-looper postDelayed ticker
 * (see Snake Deluxe GameView for the object-identity / thread rationale).
 */
public class TetrisView extends View {

    static final int COLS = 10;
    static final int ROWS = 20;
    static final int TICK_MS = 420;

    // piece ids 1..7: I O T S Z J L
    static final int[][][] SHAPES = {
        {{0, 1}, {1, 1}, {2, 1}, {3, 1}},   // I
        {{1, 0}, {2, 0}, {1, 1}, {2, 1}},   // O
        {{1, 0}, {0, 1}, {1, 1}, {2, 1}},   // T
        {{1, 1}, {2, 1}, {0, 2}, {1, 2}},   // S
        {{0, 1}, {1, 1}, {1, 2}, {2, 2}},   // Z
        {{0, 0}, {0, 1}, {1, 1}, {2, 1}},   // J
        {{2, 0}, {0, 1}, {1, 1}, {2, 1}},   // L
    };
    static final int[] COLORS = {
        0xFF06B6D4, 0xFFFACC15, 0xFFA855F7, 0xFF22C55E,
        0xFFEF4444, 0xFF3B82F6, 0xFFF97316,
    };

    static final int C_BG     = 0xFF0B1020;
    static final int C_BOARD  = 0xFF111834;
    static final int C_GRID   = 0xFF1A2140;
    static final int C_BORDER = 0xFF3B82F6;
    static final int C_TEXT   = 0xFFF1F5F9;
    static final int C_DIM    = 0xFF8FA3BF;

    static MainActivity host;
    static int[][] board = new int[ROWS][COLS];
    static int cur = 0, nxt = 3, rot = 0, px = 3, py = -1;
    static int score = 0, lines = 0, level = 1;
    static boolean started = false, over = false;
    static long seed = 0x9E3779B9L;
    static boolean tickScheduled = false;

    static Handler h;
    Paint p = new Paint();

    public TetrisView(Context c) {
        super(c);
        h = new Handler(Looper.getMainLooper());
    }

    static int nextRnd(int bound) {
        seed = (seed * 1103515245L + 12345L) & 0x7FFFFFFFL;
        return (int) (seed % (long) bound);
    }

    public void startTicker() {
        if (tickScheduled) return;
        tickScheduled = true;
        h.postDelayed(ticker, TICK_MS);
    }

    final Runnable ticker = new Runnable() {
        public void run() {
            if (started && !over) gravity();
            postInvalidate();
            h.postDelayed(this, TICK_MS);
        }
    };

    public static void resetAndStart() {
        board = new int[ROWS][COLS];
        score = 0; lines = 0; level = 1; over = false; started = true;
        seed = 0x9E3779B9L;
        nxt = nextRnd(7);
        spawn();
    }

    public static void toggleStart() {
        if (!started || over) resetAndStart();
        else started = false;
    }

    static int[] cellXY(int piece, int r, int i) {
        int x = SHAPES[piece][i][0], y = SHAPES[piece][i][1];
        for (int q = 0; q < r; q++) { int nx = 3 - y; int ny = x; x = nx; y = ny; }
        return new int[]{x, y};
    }

    static boolean collides(int nx, int ny, int nr) {
        for (int i = 0; i < 4; i++) {
            int[] c = cellXY(cur, nr, i);
            int bx = nx + c[0], by = ny + c[1];
            if (bx < 0 || bx >= COLS || by >= ROWS) return true;
            if (by >= 0 && board[by][bx] != 0) return true;
        }
        return false;
    }

    public static void move(int dx) {
        if (!started || over) return;
        if (!collides(px + dx, py, rot)) px += dx;
    }

    public static void rotate() {
        if (!started || over) return;
        int nr = (rot + 1) & 3;
        int[] kicks = {0, -1, 1, -2, 2};
        for (int k = 0; k < kicks.length; k++) {
            if (!collides(px + kicks[k], py, nr)) {
                px += kicks[k]; rot = nr; return;
            }
        }
    }

    public static void softDrop() {
        if (!started || over) return;
        gravity();
    }

    static void gravity() {
        if (!collides(px, py + 1, rot)) py++;
        else lock();
    }

    static void lock() {
        for (int i = 0; i < 4; i++) {
            int[] c = cellXY(cur, rot, i);
            int bx = px + c[0], by = py + c[1];
            if (by < 0) { die(); return; }
            board[by][bx] = cur + 1;
        }
        // line clears
        int cleared = 0;
        for (int r = ROWS - 1; r >= 0; r--) {
            boolean full = true;
            for (int cc = 0; cc < COLS; cc++) if (board[r][cc] == 0) { full = false; break; }
            if (full) {
                cleared++;
                for (int rr = r; rr > 0; rr--) board[rr] = board[rr - 1];
                board[0] = new int[COLS];
                r++;   // re-check this row index after shift
            }
        }
        if (cleared > 0) {
            lines += cleared;
            score += cleared == 1 ? 100 : cleared == 2 ? 300
                   : cleared == 3 ? 500 : 800;
            level = 1 + lines / 5;
        }
        spawn();
    }

    static void spawn() {
        cur = nxt;
        nxt = nextRnd(7);
        rot = 0; px = 3; py = -2;
        if (collides(px, py + 2, rot)) { die(); return; }
        py += 2;
    }

    static void die() {
        started = false; over = true;
        if (host != null) host.showGameOver(score, lines);
    }

    // ---- rendering ---------------------------------------------------------
    @Override
    protected void onDraw(Canvas cv) {
        int w = cv.getWidth();
        int hgt = cv.getHeight();
        cv.drawColor(C_BG);

        int cell = Math.min((w - 430) / COLS, (hgt - 150) / ROWS);
        int bwd = cell * COLS, bht = cell * ROWS;
        int bxl = 30, byt = 130;

        // board base + grid
        p.setStyle(Paint.Style.FILL);
        p.setColor(C_BOARD);
        cv.drawRoundRect(bxl - 8, byt - 8, bxl + bwd + 8, byt + bht + 8, 18, 18, p);
        p.setColor(C_GRID);
        for (int r = 1; r < ROWS; r++)
            cv.drawRect(bxl, byt + r * cell - 1, bxl + bwd, byt + r * cell, p);
        for (int c = 1; c < COLS; c++)
            cv.drawRect(bxl + c * cell - 1, byt, bxl + c * cell, byt + bht, p);

        // settled blocks
        for (int r = 0; r < ROWS; r++) {
            for (int c2 = 0; c2 < COLS; c2++) {
                if (board[r][c2] != 0) {
                    drawBlock(cv, bxl + c2 * cell, byt + r * cell, cell,
                              COLORS[board[r][c2] - 1]);
                }
            }
        }

        // current piece
        for (int i = 0; i < 4; i++) {
            int[] c = cellXY(cur, rot, i);
            int bx = px + c[0], by = py + c[1];
            if (by >= 0) {
                drawBlock(cv, bxl + bx * cell, byt + by * cell, cell, COLORS[cur]);
            }
        }

        // border
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(5);
        p.setColor(C_BORDER);
        cv.drawRoundRect(bxl - 8, byt - 8, bxl + bwd + 8, byt + bht + 8, 18, 18, p);
        p.setStyle(Paint.Style.FILL);

        // ---- right panel ----
        int pnl = bxl + bwd + 56;
        p.setColor(C_TEXT);
        p.setTextSize(44);
        p.setFakeBoldText(true);
        cv.drawText("NEXT", pnl, 150, p);

        int pvx = pnl, pvy = 180, pvs = cell - 6;
        p.setColor(C_BOARD);
        cv.drawRoundRect(pvx - 10, pvy - 10, pvx + pvs * 4 + 10, pvy + pvs * 3 + 10, 14, 14, p);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(3);
        p.setColor(C_GRID);
        cv.drawRoundRect(pvx - 10, pvy - 10, pvx + pvs * 4 + 10, pvy + pvs * 3 + 10, 14, 14, p);
        p.setStyle(Paint.Style.FILL);
        // next piece centered-ish in the preview box
        int minx = 4, maxx = 0, miny = 4, maxy = 0;
        for (int i = 0; i < 4; i++) {
            int[] c = SHAPES[nxt][i];
            if (c[0] < minx) minx = c[0];
            if (c[0] > maxx) maxx = c[0];
            if (c[1] < miny) miny = c[1];
            if (c[1] > maxy) maxy = c[1];
        }
        int ox = pvx + (pvs * 4 - (maxx - minx + 1) * pvs) / 2 - minx * pvs;
        int oy = pvy + (pvs * 3 - (maxy - miny + 1) * pvs) / 2 - miny * pvs;
        for (int i = 0; i < 4; i++) {
            int[] c = SHAPES[nxt][i];
            drawBlock(cv, ox + c[0] * pvs, oy + c[1] * pvs, pvs, COLORS[nxt]);
        }

        p.setColor(C_DIM);
        p.setTextSize(38);
        p.setFakeBoldText(false);
        cv.drawText("SCORE", pnl, 520, p);
        p.setColor(C_TEXT);
        p.setTextSize(52);
        p.setFakeBoldText(true);
        cv.drawText(String.valueOf(score), pnl, 580, p);
        p.setColor(C_DIM);
        p.setTextSize(38);
        p.setFakeBoldText(false);
        cv.drawText("LINES", pnl, 680, p);
        p.setColor(C_TEXT);
        p.setTextSize(52);
        p.setFakeBoldText(true);
        cv.drawText(String.valueOf(lines), pnl, 740, p);
        p.setColor(C_DIM);
        p.setTextSize(38);
        p.setFakeBoldText(false);
        cv.drawText("LEVEL", pnl, 840, p);
        p.setColor(C_TEXT);
        p.setTextSize(52);
        p.setFakeBoldText(true);
        cv.drawText(String.valueOf(level), pnl, 900, p);

        if (!started && !over) {
            p.setColor(C_DIM);
            p.setTextSize(40);
            p.setFakeBoldText(false);
            cv.drawText("PRESS START TO PLAY", bxl + bwd / 2 - 260, byt + bht + 70, p);
        }
        if (over) {
            p.setColor(C_DIM);
            p.setTextSize(40);
            p.setFakeBoldText(false);
            cv.drawText("GAME OVER", bxl + bwd / 2 - 130, byt + bht + 70, p);
        }
    }

    void drawBlock(Canvas cv, float x, float y, float s, int color) {
        float in = s * 0.06f;
        p.setStyle(Paint.Style.FILL);
        p.setColor(color);
        cv.drawRoundRect(x + in, y + in, x + s - in, y + s - in,
                         s * 0.22f, s * 0.22f, p);
        // glossy top-left highlight
        p.setColor(0x66FFFFFF);
        cv.drawRoundRect(x + s * 0.16f, y + s * 0.16f, x + s * 0.52f, y + s * 0.42f,
                         s * 0.10f, s * 0.10f, p);
        // darker rim
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(Math.max(1.5f, s * 0.05f));
        p.setColor(0x33000000);
        cv.drawRoundRect(x + in, y + in, x + s - in, y + s - in,
                         s * 0.22f, s * 0.22f, p);
        p.setStyle(Paint.Style.FILL);
    }
}
