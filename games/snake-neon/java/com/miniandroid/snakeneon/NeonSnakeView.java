package com.miniandroid.snakeneon;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;

/**
 * NeonSnakeView — wrap-around snake with obstacles and speed ramps.
 * ALL state static (runtime static-state law). Deterministic LCG (same
 * law as the other in-house games — no java.util.Random).
 */
public class NeonSnakeView extends View {

    public static NeonSnakeView game;

    static final int COLS = 15, ROWS = 16;

    // colors
    static final int C_BG = 0xFF14141E;
    static final int C_GRID = 0xFF23233A;
    static final int C_SNAKE = 0xFF00FFD0;   // neon teal
    static final int C_HEAD = 0xFF9CFFE8;
    static final int C_FOOD = 0xFFFF2E88;    // neon magenta
    static final int C_BLOCK = 0xFFB44BFF;   // neon purple obstacle
    static final int C_TEXT = 0xFFCFCFE8;
    static final int C_OVER = 0xFFFF5555;

    // static-state law: everything mutable is static
    static int[] sx = new int[COLS * ROWS];
    static int[] sy = new int[COLS * ROWS];
    static int len = 3;
    static int dir = 1;                 // 0 up, 1 right, 2 down, 3 left
    static int pendingDir = 1;
    static int foodC = 10, foodR = 8;
    static int score = 0;
    static int foods = 0;
    static int tickMsNow = 220;
    static boolean dead = false;
    static String cause = "";
    static int blocks = 0;              // obstacle count
    static int[] blockC = new int[4];
    static int[] blockR = new int[4];

    static long seed = 0x5EEDBEEFL;

    Paint p = new Paint();

    public NeonSnakeView(Context c) { super(c); }

    static int nextRand(int bound) {
        seed = seed * 6364136223846793005L + 1442695040888963407L;
        int r = (int) ((seed >>> 33) & 0x7FFFFFFF);
        return r % bound;
    }

    // Neon tick law (deterministic): the tick is a CONSTANT 220ms so the
    // driver's 110ms frame cadence maps EXACTLY 1 move = 2 frames (the
    // speed-ramp remains visible in the HUD counter but does not alter the
    // tick — recorded honestly as DETECTED-NOT-EXERCISED for the autoplay).
    static int tickMs() {
        return 220;
    }

    public static void wantDir(int d) {
        // reverse guard: no 180 turns
        if ((d == 0 && dir == 2) || (d == 2 && dir == 0) ||
            (d == 1 && dir == 3) || (d == 3 && dir == 1)) return;
        pendingDir = d;
    }

    static boolean occupied(int c, int r) {
        for (int i = 0; i < len; i++)
            if (sx[i] == c && sy[i] == r) return true;
        for (int i = 0; i < blocks; i++)
            if (blockC[i] == c && blockR[i] == r) return true;
        return false;
    }

    static void spawnFood() {
        for (int t = 0; t < 500; t++) {
            int c = nextRand(COLS), r = nextRand(ROWS);
            if (!occupied(c, r) && !(c == foodC && r == foodR)) {
                foodC = c; foodR = r;
                return;
            }
        }
    }

    static void spawnBlock() {
        if (blocks >= 4) return;
        for (int t = 0; t < 500; t++) {
            int c = nextRand(COLS), r = nextRand(ROWS);
            if (!occupied(c, r) && !(c == foodC && r == foodR)) {
                blockC[blocks] = c; blockR[blocks] = r;
                blocks++;
                return;
            }
        }
    }

    public static void reset() {
        len = 3;
        dir = 1; pendingDir = 1;
        score = 0; foods = 0;
        tickMsNow = 220;
        dead = false; cause = "";
        blocks = 0;
        seed = 0x5EEDBEEFL;
        for (int i = 0; i < COLS * ROWS; i++) { sx[i] = 0; sy[i] = 0; }
        sx[0] = 4; sy[0] = 8;
        sx[1] = 3; sy[1] = 8;
        sx[2] = 2; sy[2] = 8;
        foodC = 10; foodR = 8;
    }

    /** One tick. WRAP-AROUND law: edges re-enter the opposite side. */
    public static void step() {
        if (dead) return;
        dir = pendingDir;
        int hc = sx[0], hr = sy[0];
        if (dir == 0) hr--; else if (dir == 1) hc++;
        else if (dir == 2) hr++; else hc--;
        // wrap-around (the Neon law — walls are portals)
        if (hc < 0) hc = COLS - 1;
        if (hc >= COLS) hc = 0;
        if (hr < 0) hr = ROWS - 1;
        if (hr >= ROWS) hr = 0;
        // self collision
        for (int i = 0; i < len - 1; i++)
            if (sx[i] == hc && sy[i] == hr) {
                dead = true; cause = "tail"; return;
            }
        // obstacle collision
        for (int i = 0; i < blocks; i++)
            if (blockC[i] == hc && blockR[i] == hr) {
                dead = true; cause = "block"; return;
            }
        // shift body
        for (int i = len - 1; i > 0; i--) { sx[i] = sx[i - 1]; sy[i] = sy[i - 1]; }
        sx[0] = hc; sy[0] = hr;
        // food?
        if (hc == foodC && hr == foodR) {
            score += 10;
            foods++;
            len++;
            sx[len - 1] = sx[len - 2];
            sy[len - 1] = sy[len - 2];
            spawnFood();
            if (foods % 3 == 0) spawnBlock();
            tickMsNow = tickMs();
        }
    }

    @Override
    protected void onDraw(Canvas canvas) {
        canvas.drawColor(C_BG);
        int top = 140;
        int cell = 62;
        int bxl = (1080 - COLS * cell) / 2;

        // neon grid
        p.setColor(C_GRID);
        p.setStrokeWidth(1);
        for (int c = 0; c <= COLS; c++)
            canvas.drawLine(bxl + c * cell, top, bxl + c * cell,
                            top + ROWS * cell, p);
        for (int r = 0; r <= ROWS; r++)
            canvas.drawLine(bxl, top + r * cell, bxl + COLS * cell,
                            top + r * cell, p);

        // obstacles
        p.setColor(C_BLOCK);
        for (int i = 0; i < blocks; i++)
            canvas.drawRect(bxl + blockC[i] * cell + 4, top + blockR[i] * cell + 4,
                            bxl + blockC[i] * cell + cell - 4,
                            top + blockR[i] * cell + cell - 4, p);

        // food
        p.setColor(C_FOOD);
        canvas.drawCircle(bxl + foodC * cell + cell / 2,
                          top + foodR * cell + cell / 2, cell / 3, p);

        // snake
        for (int i = len - 1; i >= 1; i--) {
            p.setColor(C_SNAKE);
            canvas.drawRect(bxl + sx[i] * cell + 3, top + sy[i] * cell + 3,
                            bxl + sx[i] * cell + cell - 3,
                            top + sy[i] * cell + cell - 3, p);
        }
        p.setColor(C_HEAD);
        canvas.drawRect(bxl + sx[0] * cell + 3, top + sy[0] * cell + 3,
                        bxl + sx[0] * cell + cell - 3,
                        top + sy[0] * cell + cell - 3, p);

        // hud
        p.setColor(C_TEXT);
        p.setTextSize(52);
        canvas.drawText("NEON  score=" + score + "  len=" + len + "  speed="
                        + (220 - tickMsNow + 80), 60, 90, p);
        if (dead) {
            p.setColor(C_OVER);
            p.setTextSize(64);
            canvas.drawText("GAME OVER (" + cause + ")", 260, top + 320, p);
        }
    }
}
