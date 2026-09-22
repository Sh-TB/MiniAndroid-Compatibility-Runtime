package com.s81probe;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * S81 VISUAL PROBE — one APK, four timed phases, each isolating one
 * visual-compatibility API family (S81 spec §21-§26):
 *   P0 (frames 0-3)   XML resources: ImageView android:src (raster PNG),
 *                     TextView textColor=@color ref, Button background=shape
 *                     drawable, programmatic setImageResource.
 *   P1 (frames 4-7)   AlertDialog: title + message + 3 list items.
 *   P2 (frames 8-11)  ListView + ArrayAdapter (5 rows).
 *   P3 (frames 12-15) Toast (LONG).
 * Phase switching uses the proven main-looper postDelayed ticker pattern
 * (S80 Thread law: Runnable-target never runs; lambda run() does).
 */
public class MainActivity extends Activity {
    private final Handler h = new Handler(Looper.getMainLooper());

    private void phase(final int p) {
        if (p == 0) {
            setContentView(R.layout.probe);
            ImageView iv = (ImageView) findViewById(R.id.prog_image);
            iv.setImageResource(R.drawable.picon2);
        } else if (p == 1) {
            AlertDialog.Builder b = new AlertDialog.Builder(this);
            b.setTitle("S81-TITLE");
            b.setMessage("S81 message body");
            b.setItems(new String[]{"ITEM-A", "ITEM-B", "ITEM-C"}, null);
            b.show();
        } else if (p == 2) {
            ListView lv = new ListView(this);
            String[] rows = {"ROW-0", "ROW-1", "ROW-2", "ROW-3", "ROW-4"};
            lv.setAdapter(new ArrayAdapter<String>(this,
                    android.R.layout.simple_list_item_1, rows));
            setContentView(lv);
        } else if (p == 3) {
            LinearLayout root = new LinearLayout(this);
            root.setOrientation(LinearLayout.VERTICAL);
            TextView tv = new TextView(this);
            tv.setText("PHASE-3-TOAST-NEXT");
            tv.setTextSize(28f);
            root.addView(tv);
            setContentView(root);
            Toast t = Toast.makeText(this, "S81-TOAST-BODY", Toast.LENGTH_LONG);
            t.show();
        }
        if (p < 3) {
            h.postDelayed(new Runnable() {
                public void run() { phase(p + 1); }
            }, 1000);
        }
    }

    protected void onCreate(Bundle b) {
        super.onCreate(b);
        phase(0);
    }
}
