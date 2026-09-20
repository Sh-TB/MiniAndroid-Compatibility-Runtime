package com.miniandroid.f53str;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
import android.content.res.Resources;
public class MainActivity extends Activity {
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        setContentView(R.layout.activity_main);
        // F-136 law path 1: Context.getString(resId) — the FINAL Context
        // method every Activity/Application inherits (AOSP Context.java:959).
        String plain = getString(R.string.f53_plain);
        TextView tvCtx = (TextView) findViewById(R.id.tv_ctx);
        if (tvCtx != null) tvCtx.setText(plain);
        // F-136 law path 2: formatted overload — getString(resId, formatArgs)
        // (AOSP Context.java:976 → Resources.java:588 == String.format(raw,args)).
        String fmt = getString(R.string.f53_fmt, "S70", 136);
        TextView tvFmt = (TextView) findViewById(R.id.tv_fmt);
        if (tvFmt != null) tvFmt.setText(fmt);
        // F-136 law path 3: Resources direct — the resolution target itself
        // (AOSP Resources.java:564 getText→toString; ARSC-first per F-080).
        Resources res = getResources();
        String direct = res.getString(R.string.f53_direct);
        TextView tvRes = (TextView) findViewById(R.id.tv_res);
        if (tvRes != null) tvRes.setText(direct);
    }
}
