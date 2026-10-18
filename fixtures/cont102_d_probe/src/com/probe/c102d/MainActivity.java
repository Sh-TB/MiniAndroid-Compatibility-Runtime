package com.probe.c102d;

import android.app.Activity;
import android.app.ListActivity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * CONT-102 Batch D — #364 CONT-99 T8 (ScrollView/list content geometry) +
 * T10 (final frame integrity: present-boundary freshness under tap).
 *
 * Scene (1080x1920 viewport):
 *   PHASE1: ScrollView (top 900px tall) with 8 rows x 200px = 1600px content;
 *           ListView (bottom, y=900..1920) with 5 distinct rows x 150px.
 *   PHASE2 (tap 100,100): ScrollView.scrollTo(0,300) — content moves up;
 *           pixel oracle: (50,10) shows ROW3 color 0xFF1166AA pre-scroll is
 *           ROW1; post-scroll it must be the row at y=310 => ROW2.
 *   PHASE3 (tap 500,1000): ListView row tap -> onItemClick position row.
 *   PHASE4 (tap 1000,1870): toggle button flips scene bg BLUE<->RED so the
 *           NEXT captured frame must differ from the previous one
 *           (present-boundary freshness law).
 */
public class MainActivity extends Activity {
    static final int[] ROW_COLORS = {
            0xFF1166AA, 0xFF22AA44, 0xFFAA4422, 0xFF4422AA, 0xFFAA2244,
            0xFF2244AA, 0xFF44AA22, 0xFFAA4444};
    static final int[] LV_COLORS = {
            0xFFCC8811, 0xFF1188CC, 0xFF88CC11, 0xFFCC1188, 0xFF1155CC};

    ScrollView sv;
    LinearLayout rows;
    ListView lv;
    FrameLayout scene;
    Button toggle;
    Button scroller;
    Button reporter;
    int lastClickPos = -1;
    int toggles = 0;

    void row(String tag, Object v) {
        System.err.println("[C102-" + tag + "] " + v);
    }

    View colorRow(final int idx, int h) {
        View v = new View(this);
        v.setBackgroundColor(ROW_COLORS[idx]);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, h);
        v.setLayoutParams(lp);
        v.setTag("row" + idx);
        return v;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            scene = new FrameLayout(this);
            scene.setBackgroundColor(0xFFEFEFEF);

            // ScrollView content: 8 rows x 200px = 1600px, viewport 900px.
            sv = new ScrollView(this);
            sv.setLayoutParams(new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 900));
            rows = new LinearLayout(this);
            rows.setOrientation(LinearLayout.VERTICAL);
            for (int i = 0; i < 8; i++) rows.addView(colorRow(i, 200));
            sv.addView(rows);
            scene.addView(sv);

            // ListView bottom half: 5 distinct rows.
            lv = new ListView(this);
            FrameLayout.LayoutParams llp = new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, 900);
            llp.topMargin = 900;
            lv.setLayoutParams(llp);
            lv.setAdapter(new BaseAdapter() {
                public int getCount() { return 5; }
                public Object getItem(int position) { return position; }
                public long getItemId(int position) { return position; }
                public View getView(int position, View convertView,
                                    ViewGroup parent) {
                    View v = new View(MainActivity.this);
                    v.setBackgroundColor(LV_COLORS[position]);
                    v.setLayoutParams(new AdapterView.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT, 150));
                    v.setTag("lv" + position);
                    return v;
                }
            });
            lv.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                public void onItemClick(AdapterView<?> parent, View view,
                                        int position, long id) {
                    lastClickPos = position;
                    System.err.println("[C102-LV-CLICK] pos=" + position);
                }
            });
            scene.addView(lv);

            // toggle button bottom-right corner (not overlapped by rows).
            toggle = new Button(this);
            toggle.setText("T");
            FrameLayout.LayoutParams tlp = new FrameLayout.LayoutParams(
                    80, 50);
            tlp.leftMargin = 1000;
            tlp.topMargin = 1870 - 50;
            toggle.setLayoutParams(tlp);
            toggle.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    toggles++;
                    scene.setBackgroundColor(
                            (toggles % 2 == 1) ? 0xFF30A030 : 0xFFEFEFEF);
                    System.err.println("[C102-TOGGLE] n=" + toggles);
                }
            });
            scene.addView(toggle);

            // SCROLL button (top-right of the scroll viewport): tap -> phase2
            scroller = new Button(this);
            scroller.setText("S");
            FrameLayout.LayoutParams slp = new FrameLayout.LayoutParams(
                    80, 50);
            slp.leftMargin = 900;
            slp.topMargin = 10;
            scroller.setLayoutParams(slp);
            scroller.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    System.err.println("[C102-SBTN] hit");
                    phase2();
                }
            });
            scene.addView(scroller);

            // REPORT button (bottom-left corner): tap -> phase4 rows
            reporter = new Button(this);
            reporter.setText("R");
            FrameLayout.LayoutParams rlp = new FrameLayout.LayoutParams(
                    80, 50);
            rlp.leftMargin = 10;
            rlp.topMargin = 1870 - 50;
            reporter.setLayoutParams(rlp);
            reporter.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    System.err.println("[C102-RBTN] hit");
                    phase4();
                }
            });
            scene.addView(reporter);
            setContentView(scene);

            row("SV-RANGE", 8 * 200);
            row("SV-VIEWPORT", 900);
            row("SV-SCROLLY-0", sv.getScrollY());
            row("LV-COUNT", lv.getCount());
            row("LV-CHILDREN", lv.getChildCount());
            row("D-PHASE1", "printed");
        } catch (Throwable t) {
            System.err.println("[C102-D-ERR] " + t);
        }
    }

    // phases driven by real taps on the S / R buttons.
    void phase2() {
        sv.scrollTo(0, 300);
        row("SV-SCROLLY-300", sv.getScrollY());
        row("SV-CONTENT-TOP", rows.getTop());
        row("D-PHASE2", "printed");
    }

    void phase4() {
        row("TOGGLES", toggles);
        row("LV-LAST-CLICK", lastClickPos);
        row("D-PHASE4", "printed");
    }
}
