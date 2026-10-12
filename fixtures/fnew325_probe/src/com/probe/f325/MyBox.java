package com.probe.f325;

import android.content.Context;
import android.widget.LinearLayout;

/**
 * The DEX-intermediate reader: the iget instructions inside readWidth/
 * readHeight/readTag carry a DEX REF CLASS (MyLP) — the shape whose key
 * construction fabricated a second identity for framework-owned fields.
 */
public class MyBox extends LinearLayout {
    public MyBox(Context c) {
        super(c);
    }

    /** iget ref class = MyLP (DEX), field width declared by the FRAMEWORK. */
    public int readWidth() {
        return ((MyLP) getLayoutParams()).width;
    }

    public int readHeight() {
        return ((MyLP) getLayoutParams()).height;
    }

    /** iget-object ref class = MyLP (DEX), field tag DECLARED by MyLP. */
    public String readTag() {
        return ((MyLP) getLayoutParams()).tag;
    }
}
