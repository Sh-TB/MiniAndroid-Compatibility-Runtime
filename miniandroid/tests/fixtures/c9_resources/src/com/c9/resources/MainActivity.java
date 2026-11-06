package com.c9.resources;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.content.res.Resources;
import android.util.Log;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.util.Arrays;

/**
 * CODER 9 — synthetic resources/assets pipeline harness (§5/§6).
 *
 * Every case logs one `CASE..` line; scripts/c9/validate_c9_resources.sh
 * greps these lines and asserts the documented expectations per device
 * config (density/locale set by the RUNTIME env, not by the app — the app
 * only measures and reports what the platform answered).
 */
public class MainActivity extends Activity {

    private static void report(String line) {
        Log.i("C9HARNESS", line);
        System.out.println(line);
    }

    private static byte[] readAll(InputStream in) throws Exception {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
        in.close();
        return bos.toByteArray();
    }

    private static String headHex(byte[] b, int count) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < count && i < b.length; i++)
            sb.append(String.format("%02x", b[i]));
        return sb.toString();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Resources res = getResources();
        AssetManager am = getAssets();
        int dpi = res.getDisplayMetrics().densityDpi;

        // ── CASE01: PNG drawable decode (density law, decode-time half) ──
        Bitmap photo = BitmapFactory.decodeResource(res, R.drawable.c9_photo);
        if (photo != null) {
            report("CASE01 natural=" + photo.getWidth() + "x" + photo.getHeight()
                    + " density=" + dpi);
        } else {
            report("CASE01 natural=null density=" + dpi);
        }

        // ── CASE02: WebP bounds pass + full decode ───────────────────────
        BitmapFactory.Options bo = new BitmapFactory.Options();
        bo.inJustDecodeBounds = true;
        BitmapFactory.decodeResource(res, R.drawable.c9_webp, bo);
        Bitmap webpFull = BitmapFactory.decodeResource(res, R.drawable.c9_webp);
        report("CASE02 bounds=" + bo.outWidth + "x" + bo.outHeight
                + " mime=" + bo.outMimeType
                + " natural=" + (webpFull != null
                    ? webpFull.getWidth() + "x" + webpFull.getHeight() : "null"));

        // ── CASE03: nested asset list + byte-exact read ──────────────────
        try {
            String[] deep = am.list("sub");
            byte[] nested = readAll(am.open("sub/deep/c9_nested.bin"));
            report("CASE03 list=" + Arrays.toString(deep)
                    + "; " + nested.length + " bytes; head=" + headHex(nested, 8));
        } catch (Exception e) {
            report("CASE03 ERROR " + e.getClass().getSimpleName());
        }

        // ── CASE04: compressed asset — open serves bytes, openFd refuses ─
        try {
            byte[] comp = readAll(am.open("c9_compressed.txt"));
            String afdResult;
            try {
                am.openFd("c9_compressed.txt");
                afdResult = "UNEXPECTED-OPENED";
            } catch (FileNotFoundException e) {
                afdResult = "FileNotFoundException";
            }
            report("CASE04 open=" + comp.length + " bytes; openFd=" + afdResult);
        } catch (Exception e) {
            report("CASE04 ERROR " + e.getClass().getSimpleName());
        }

        // ── CASE05: uncompressed asset — AFD data-offset law ─────────────
        try {
            AssetFileDescriptor afd = am.openFd("c9_stored.bin");
            byte[] viaOpen = readAll(am.open("c9_stored.bin"));
            byte[] viaStream = readAll(afd.createInputStream());
            boolean match = Arrays.equals(viaOpen, viaStream);
            report("CASE05 afd startOffset=" + afd.getStartOffset()
                    + " length=" + afd.getLength()
                    + " declared=" + afd.getDeclaredLength()
                    + " openBytes=" + viaOpen.length
                    + " stream==open=" + match);
            afd.close();
        } catch (Exception e) {
            report("CASE05 ERROR " + e.getClass().getSimpleName());
        }

        // ── CASE06: VectorDrawable intrinsic law (C9-3) ──────────────────
        try {
            Drawable v = res.getDrawable(R.drawable.c9_vector);
            report("CASE06 intrinsic=" + v.getIntrinsicWidth() + "x"
                    + v.getIntrinsicHeight());
        } catch (Exception e) {
            report("CASE06 ERROR " + e.getClass().getSimpleName());
        }

        // ── CASE07: density-qualified bucket selection ───────────────────
        report("CASE07 photo=" + (photo != null
                    ? photo.getWidth() + "x" + photo.getHeight() : "null")
                + " at=" + dpi);

        // ── CASE08: locale-qualified string ──────────────────────────────
        report("CASE08 string=" + res.getString(R.string.c9_hello) + " locale=" + dpi);

        // ── CASE09: custom font from assets ──────────────────────────────
        try {
            Typeface tf = Typeface.createFromAsset(am, "fonts/c9_font.ttf");
            report("CASE09 typeface=" + (tf != null ? "loaded" : "null"));
        } catch (Exception e) {
            report("CASE09 ERROR " + e.getClass().getSimpleName());
        }

        // ── CASE10: missing resource laws ────────────────────────────────
        Bitmap missing = BitmapFactory.decodeResource(res, R.raw.c9_invalid);
        String missingString;
        try {
            // AOSP NotFoundException law: a WELL-FORMED but ABSENT resid
            // (no R field can exist for a missing resource — raw id used).
            missingString = String.valueOf(res.getString(0x7f0b0069));
        } catch (Resources.NotFoundException e) {
            missingString = "NotFoundException";
        } catch (Exception e) {
            missingString = e.getClass().getSimpleName();
        }
        report("CASE10 decode_null=" + (missing == null)
                + "; string_error=" + missingString);

        // ── CASE11: missing asset ────────────────────────────────────────
        try {
            am.open("missing.bin");
            report("CASE11 asset_error=UNEXPECTED-OPENED");
        } catch (FileNotFoundException e) {
            report("CASE11 asset_error=FileNotFoundException");
        } catch (Exception e) {
            report("CASE11 asset_error=" + e.getClass().getSimpleName());
        }

        // ── CASE12: invalid image data → null (no fake pixels) ───────────
        Bitmap invalid = BitmapFactory.decodeResource(res, R.raw.c9_invalid);
        report("CASE12 invalid_null=" + (invalid == null));

        // ── CASE13: nodpi → never density-scaled ─────────────────────────
        Bitmap nodpi = BitmapFactory.decodeResource(res, R.drawable.c9_nodpi);
        report("CASE13 nodpi=" + (nodpi != null
                    ? nodpi.getWidth() + "x" + nodpi.getHeight() : "null")
                + " at=" + dpi);

        // ── CASE14: §6 View chain — real views, real texts ───────────────
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        tv.setText(res.getString(R.string.c9_hello));
        ImageView ivPhoto = new ImageView(this);
        ivPhoto.setImageResource(R.drawable.c9_photo);
        ImageView ivVector = new ImageView(this);
        ivVector.setImageResource(R.drawable.c9_vector);
        root.addView(tv);
        root.addView(ivPhoto);
        root.addView(ivVector);
        setContentView(root);

        int children = root.getChildCount();
        StringBuilder texts = new StringBuilder();
        for (int i = 0; i < children; i++) {
            if (root.getChildAt(i) instanceof TextView)
                texts.append(((TextView) root.getChildAt(i)).getText());
        }
        report("CASE14 children=" + children + " texts=" + texts);
    }
}
