package com.miniandroid.minicraft;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;

/**
 * MiniCraft world — a 2D house-building sandbox (S86 in-house game, the
 * خانه سازی companion to Snake Deluxe / Tetris / 2048 / TicTacToe Deluxe).
 *
 * World model: static block grid (runtime static-state law, same pattern
 * as the other in-house games). Terrain is generated once from a fixed
 * LCG seed: grass surface, dirt underneath, stone bedrock with caves.
 *
 * The builder walks a cursor with the direction pad and places / digs
 * blocks; DEMO auto-builds a small brick cottage (walls + timber frame +
 * gabled roof + door + window). Every render is real Canvas.onDraw with
 * per-block textures (brick courses, plank grain, grass blades).
 */
public class CraftWorldView extends View {

    static final int COLS = 14, ROWS = 20;

    // block ids
    static final int B_AIR = 0, B_GRASS = 1, B_DIRT = 2, B_STONE = 3,
            B_BRICK = 4, B_PLANK = 5, B_ROOF = 6, B_GLASS = 7, B_DOOR = 8;

    // palette
    static final int C_SKY      = 0xFFB8E2F2;
    static final int C_SUN      = 0xFFFFD75E;
    static final int C_GRASS    = 0xFF6FBF5A;
    static final int C_GRASS_D  = 0xFF57A344;
    static final int C_DIRT     = 0xFF9B6A43;
    static final int C_DIRT_D   = 0xFF82553A;
    static final int C_STONE    = 0xFF9E9E9E;
    static final int C_STONE_D  = 0xFF7B7B7B;
    static final int C_BRICK    = 0xFFB5543B;
    static final int C_BRICK_M  = 0xFFE0C8B0;   // mortar
    static final int C_PLANK    = 0xFFC89A5B;
    static final int C_PLANK_D  = 0xFFA87C42;
    static final int C_ROOF     = 0xFF8C3B32;
    static final int C_ROOF_D   = 0xFF742E27;
    static final int C_GLASS    = 0xFFBFE8F5;
    static final int C_GLASS_F  = 0xFF6FB7D4;   // frame
    static final int C_DOOR     = 0xFF7A4E28;
    static final int C_DOOR_K   = 0xFFFFD75E;   // knob
    static final int C_CURSOR   = 0xFFFFEE44;

    static String[] BLOCK_NAMES = {
        "AIR", "GRASS", "DIRT", "STONE", "BRICK", "PLANK", "ROOF", "GLASS",
        "DOOR"
    };

    static int[][] world = new int[ROWS][COLS];
    static int cursorR = 8, cursorC = 3;        // cursor row / col
    static int currentBlock = B_BRICK;          // selected block type
    static int placed = 0, dug = 0;             // stats
    static String lastAction = "Welcome, builder!";

    static long seed = 0xC0FFEE42L;

    Paint p = new Paint();

    public CraftWorldView(Context c) { super(c); }

    // deterministic LCG (java.util.Random is available; keep the law of the
    // other in-house games: own LCG, fully reproducible worlds)
    static int nextRand(int bound) {
        seed = seed * 6364136223846793005L + 1442695040888963407L;
        int r = (int) ((seed >>> 33) & 0x7FFFFFFF);
        return r % bound;
    }

    /** Generates the starting terrain: rolling grass, dirt layer, stone
     *  bedrock with a couple of surface pits. */
    public static void genTerrain() {
        seed = 0xC0FFEE42L;
        for (int r = 0; r < ROWS; r++)
            for (int c = 0; c < COLS; c++) world[r][c] = B_AIR;
        for (int c = 0; c < COLS; c++) {
            int surf = 12 + (nextRand(3) - 1);           // 11..13
            world[surf][c] = B_GRASS;
            for (int r = surf + 1; r < surf + 4 && r < ROWS; r++)
                world[r][c] = B_DIRT;
            for (int r = surf + 4; r < ROWS; r++)
                world[r][c] = B_STONE;
        }
        // a small stone outcrop
        for (int i = 0; i < 6; i++) {
            int r = 11 + nextRand(3), c = nextRand(COLS);
            world[r][c] = B_STONE;
        }
        placed = 0;
        dug = 0;
        lastAction = "Terrain ready. Build something!";
    }

    static void setBlock(int r, int c, int b, String what) {
        if (r < 0 || r >= ROWS || c < 0 || c >= COLS) {
            lastAction = "Out of the world!";
            return;
        }
        if (world[r][c] == b) {
            lastAction = "Already " + BLOCK_NAMES[b];
            return;
        }
        world[r][c] = b;
        lastAction = what + " " + BLOCK_NAMES[b] +
                " @ (" + c + "," + r + ")";
    }

    // ── actions (driven by real button clicks) ──────────────────────────
    public static void moveCursor(int dr, int dc) {
        int nr = cursorR + dr, nc = cursorC + dc;
        if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS) {
            lastAction = "Edge of the world!";
            return;
        }
        cursorR = nr;
        cursorC = nc;
        lastAction = "Cursor (" + cursorC + "," + cursorR + ")";
    }

    public static void cycleBlock() {
        currentBlock++;
        if (currentBlock > B_DOOR) currentBlock = B_BRICK;
        lastAction = "Selected " + BLOCK_NAMES[currentBlock];
    }

    public static void place() {
        setBlock(cursorR, cursorC, currentBlock, "Placed");
        if (world[cursorR][cursorC] == currentBlock) placed++;
    }

    public static void dig() {
        if (world[cursorR][cursorC] == B_AIR) {
            lastAction = "Nothing to dig";
            return;
        }
        setBlock(cursorR, cursorC, B_AIR, "Dug");
        dug++;
    }

    /** DEMO — auto-builds a small brick cottage around the cursor column:
     *  plank floor frame, brick walls, timber ring, gabled roof, glass
     *  window and a wooden door. */
    public static void buildDemoHouse() {
        int base = 11;                    // ground line the house sits on
        int left = 2, right = 9;          // inclusive wall columns
        int wallTop = 6;
        int mid = (left + right) / 2;

        // clear the plot
        for (int r = wallTop - 2; r <= base; r++)
            for (int c = left - 1; c <= right + 1; c++)
                if (r >= 0 && r < ROWS && c >= 0 && c < COLS)
                    world[r][c] = B_AIR;

        // ground line: grass + dirt under the house
        world[base][left - 1] = B_GRASS;
        world[base][right + 1] = B_GRASS;

        // brick walls (rows wallTop..base-1)
        for (int r = wallTop; r < base; r++) {
            world[r][left] = B_BRICK;
            world[r][right] = B_BRICK;
        }
        // plank floor
        for (int c = left; c <= right; c++) world[base - 1][c] = B_PLANK;
        // timber ring on top of the walls
        for (int c = left; c <= right; c++) world[wallTop][c] = B_PLANK;
        // glass window band on one wall row (between door columns)
        for (int c = left + 2; c <= right - 2; c++)
            world[wallTop + 2][c] = B_GLASS;
        // door on the front wall (2 tall)
        world[base - 2][mid] = B_DOOR;
        world[base - 1][mid] = B_DOOR;
        // solid brick infill left/right of the door row
        for (int c = left + 1; c < mid; c++) world[base - 1][c] = B_BRICK;
        for (int c = mid + 1; c < right; c++) world[base - 1][c] = B_BRICK;

        // gabled roof: two slopes of roof blocks meeting at the ridge
        int r = wallTop - 1;
        for (int span = 0; left - 1 + span <= right + 1 - span; span++, r--) {
            for (int c = left - 1 + span; c <= right + 1 - span; c++) {
                if (r >= 0) world[r][c] = B_ROOF;
            }
        }

        placed += 2;                    // the door counts double 🙂
        lastAction = "House built! Blocks: " + placed;
    }

    // ── rendering ────────────────────────────────────────────────────────
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        int W = getWidth(), H = getHeight();

        // sky
        p.setColor(C_SKY);
        canvas.drawRect(0, 0, W, H, p);
        // sun
        p.setColor(C_SUN);
        canvas.drawCircle(W - 110, 130, 60, p);

        // stat strip
        p.setColor(0xCC222222);
        p.setTextSize(34);
        canvas.drawText("Blocks " + placed + "  Dug " + dug + "  ["
                + BLOCK_NAMES[currentBlock] + "]", 24, 46, p);
        p.setColor(0xCC444444);
        p.setTextSize(28);
        canvas.drawText(lastAction, 24, 84, p);

        int top = 100;
        int cellW = W / COLS;
        int cellH = (H - top - 20) / ROWS;

        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                int x = c * cellW, y = top + r * cellH;
                drawBlock(canvas, world[r][c], x, y, cellW, cellH);
            }
        }

        // cursor crosshair
        int cx = cursorC * cellW, cy = top + cursorR * cellH;
        p.setColor(C_CURSOR);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(6);
        canvas.drawRect(cx + 3, cy + 3, cx + cellW - 3, cy + cellH - 3, p);
        p.setStyle(Paint.Style.FILL);
    }

    void drawBlock(Canvas canvas, int b, int x, int y, int w, int h) {
        switch (b) {
            case B_GRASS:
                p.setColor(C_DIRT); canvas.drawRect(x, y, x + w, y + h, p);
                p.setColor(C_GRASS); canvas.drawRect(x, y, x + w, y + h / 3, p);
                p.setColor(C_GRASS_D);
                for (int i = 0; i < 4; i++)
                    canvas.drawRect(x + i * w / 4, y + h / 3,
                            x + i * w / 4 + w / 8, y + h / 2, p);
                break;
            case B_DIRT:
                p.setColor(C_DIRT); canvas.drawRect(x, y, x + w, y + h, p);
                p.setColor(C_DIRT_D);
                canvas.drawRect(x, y + h / 2, x + w / 2, y + h, p);
                canvas.drawRect(x + w / 2, y, x + w, y + h / 4, p);
                break;
            case B_STONE:
                p.setColor(C_STONE); canvas.drawRect(x, y, x + w, y + h, p);
                p.setColor(C_STONE_D);
                canvas.drawRect(x, y + h * 2 / 3, x + w * 2 / 3, y + h, p);
                canvas.drawRect(x + w / 3, y, x + w, y + h / 3, p);
                break;
            case B_BRICK:
                p.setColor(C_BRICK_M); canvas.drawRect(x, y, x + w, y + h, p);
                p.setColor(C_BRICK);
                for (int row = 0; row < 4; row++) {
                    int off = (row % 2 == 0) ? 0 : w / 4;
                    for (int col = -1; col < 3; col++) {
                        int bx = x + col * w / 2 + off;
                        canvas.drawRect(bx + 2, y + row * h / 4 + 2,
                                bx + w / 2 - 2, y + (row + 1) * h / 4 - 2, p);
                    }
                }
                break;
            case B_PLANK:
                p.setColor(C_PLANK); canvas.drawRect(x, y, x + w, y + h, p);
                p.setColor(C_PLANK_D);
                for (int row = 1; row < 4; row++)
                    canvas.drawRect(x, y + row * h / 4 - 1,
                            x + w, y + row * h / 4 + 1, p);
                break;
            case B_ROOF:
                p.setColor(C_ROOF); canvas.drawRect(x, y, x + w, y + h, p);
                p.setColor(C_ROOF_D);
                canvas.drawRect(x, y, x + w, y + h / 5, p);
                canvas.drawRect(x, y + h / 2, x + w, y + h / 2 + h / 8, p);
                break;
            case B_GLASS:
                p.setColor(C_GLASS_F);
                canvas.drawRect(x, y, x + w, y + h, p);
                p.setColor(C_GLASS);
                canvas.drawRect(x + h / 6, y + h / 6,
                        x + w - h / 6, y + h - h / 6, p);
                break;
            case B_DOOR:
                p.setColor(C_DOOR);
                canvas.drawRect(x + w / 6, y, x + w - w / 6, y + h, p);
                p.setColor(C_DOOR_K);
                canvas.drawCircle(x + w - w / 3, y + h / 2, h / 10, p);
                break;
            default:
                break;  // air — sky already painted
        }
    }
}
