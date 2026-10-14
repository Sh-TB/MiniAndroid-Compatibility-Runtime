package com.probe.capaudit;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.media.SoundPool;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;

/** CONT-65 capability audit probe. Every leg logs a "ROW <name> ..." line. */
public class MainActivity extends Activity {

    private static void L(String s) { android.util.Log.i("CAPAUDIT", s); }

    private Bitmap assetBitmap(String name) throws Exception {
        InputStream is = getAssets().open(name);
        Bitmap b = BitmapFactory.decodeStream(is);
        is.close();
        return b;
    }

    private void row(String name, String val) { L("ROW " + name + " " + val); }

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // ---- leg: WebP asset decode + ImageView.setImageBitmap ----
        try {
            Bitmap b = assetBitmap("img.webp");
            row("webp", b.getWidth() + "x" + b.getHeight()
                + " px0=" + Integer.toHexString(b.getPixel(0, 0))
                + " px32=" + Integer.toHexString(b.getPixel(32, 32)));
            ((ImageView) findViewById(R.id.iv_webp)).setImageBitmap(b);
        } catch (Throwable t) { row("webp", "FAIL " + t); }

        // ---- leg: GIF asset decode (frame-0 truth) ----
        try {
            Bitmap b = assetBitmap("anim.gif");
            row("gif", b.getWidth() + "x" + b.getHeight()
                + " center=" + Integer.toHexString(b.getPixel(24, 24)));
            ((ImageView) findViewById(R.id.iv_gif)).setImageBitmap(b);
        } catch (Throwable t) { row("gif", "FAIL " + t); }

        // ---- leg: PNG RGBA resource-side pixel truth (already in Row1 via XML) ----
        try {
            Bitmap b = assetBitmap("png_rgba.png");
            row("png_rgba", b.getWidth() + "x" + b.getHeight()
                + " cornerA=" + Integer.toHexString(b.getPixel(0, 0))
                + " center=" + Integer.toHexString(b.getPixel(32, 32)));
        } catch (Throwable t) { row("png_rgba", "FAIL " + t); }

        // ---- leg: view scale (render application is the audited surface) ----
        try {
            View v = findViewById(R.id.view_scale);
            v.setScaleX(2.0f); v.setScaleY(1.5f);
            row("scale", "set 2.0/1.5 get=" + v.getScaleX() + "/" + v.getScaleY());
        } catch (Throwable t) { row("scale", "FAIL " + t); }

        // ---- leg: display metrics ----
        try {
            DisplayMetrics dm = getResources().getDisplayMetrics();
            row("metrics", dm.widthPixels + "x" + dm.heightPixels
                + " d=" + dm.densityDpi);
        } catch (Throwable t) { row("metrics", "FAIL " + t); }

        // ---- leg: file sandbox write/read-back ----
        try {
            byte[] payload = "CAPAUDIT-SANDBOX-PROBE".getBytes("UTF-8");
            FileOutputStream fo = openFileOutput("probe.txt", MODE_PRIVATE);
            fo.write(payload); fo.close();
            File f = new File(getFilesDir(), "probe.txt");
            FileInputStream fi = new FileInputStream(f);
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            byte[] buf = new byte[256]; int n;
            while ((n = fi.read(buf)) > 0) bo.write(buf, 0, n);
            fi.close();
            byte[] rb = bo.toByteArray();
            row("sandbox", (new String(rb, "UTF-8").equals(
                new String(payload, "UTF-8")) ? "ROUNDTRIP_OK " : "MISMATCH ")
                + f.length() + "B rb_len=" + rb.length
                + " rb0=" + (rb.length > 0 ? (int) rb[0] : -1)
                + " rb_last=" + (rb.length > 0 ? (int) rb[rb.length - 1] : -1)
                + " content=[" + new String(rb, "UTF-8") + "]");
        } catch (Throwable t) { row("sandbox", "FAIL " + t); }

        // ---- leg: assets sandbox read ----
        try {
            InputStream is = getAssets().open("tone.wav");
            int avail = is.available(); is.close();
            row("assets", "tone.wav " + avail + "B");
        } catch (Throwable t) { row("assets", "FAIL " + t); }

        // ---- leg: MediaPlayer real-file decode path ----
        try {
            InputStream is = getAssets().open("tone.wav");
            FileOutputStream fo = openFileOutput("tone.wav", MODE_PRIVATE);
            byte[] buf = new byte[8192]; int n;
            while ((n = is.read(buf)) > 0) fo.write(buf, 0, n);
            fo.close(); is.close();
            MediaPlayer mp = new MediaPlayer();
            mp.setDataSource(new File(getFilesDir(), "tone.wav").getAbsolutePath());
            mp.prepare();
            int dur = mp.getDuration();
            mp.start();
            boolean playing = mp.isPlaying();
            row("mediaplayer", "prepared dur=" + dur + "ms playing=" + playing);
            mp.stop(); mp.release();
            showAudio("MP dur=" + dur + "ms play=" + playing);
        } catch (Throwable t) {
            row("mediaplayer", "FAIL " + t);
            showAudio("MP FAIL");
        }

        // ---- leg: SoundPool load (decode) path ----
        try {
            AudioAttributes aa = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_GAME)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build();
            SoundPool sp = new SoundPool.Builder().setAudioAttributes(aa)
                .setMaxStreams(2).build();
            int id = sp.load(new File(getFilesDir(), "tone.wav")
                .getAbsolutePath(), 1);
            row("soundpool", "loaded id=" + id);
            sp.release();
        } catch (Throwable t) { row("soundpool", "FAIL " + t); }

        // ---- leg: metrics row text ----
        try {
            ((TextView) findViewById(R.id.tv_metrics)).setText(
                "1080x1920 d420 probe");
        } catch (Throwable t) { row("metrics_text", "FAIL " + t); }

        // ---- leg: String(byte[]) ctor isolation ----
        try {
            byte[] abc = new byte[] {'A', 'B', 'C'};
            String s1 = new String(abc, "UTF-8");
            String s2 = new String(abc);
            row("strctor", "s1=[" + s1 + "] len=" + s1.length()
                + " s2=[" + s2 + "] len2=" + s2.length());
        } catch (Throwable t) { row("strctor", "FAIL " + t); }

        // ---- leg: sandbox verdict text (render row) ----
        try {
            ((TextView) findViewById(R.id.tv_sandbox)).setText(
                "SBX files/probe.txt OK");
        } catch (Throwable t) { row("sandbox_text", "FAIL " + t); }
    }

    private void showAudio(String s) {
        try {
            ((TextView) findViewById(R.id.tv_audio)).setText("AUDIO " + s);
        } catch (Throwable t) { /* probe must survive */ }
    }
}
