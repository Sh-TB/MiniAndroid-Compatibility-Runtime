package com.probe.c7runtime;

import android.app.Activity;

/** CODER7 WAVE-3: implicit-resolution candidate whose filter DECLARES
 *  android.intent.category.DEFAULT — the MATCH_DEFAULT_ONLY law picks
 *  THIS one over ResDefB (whose filter lacks the category). Never
 *  launched by the resolution probe. */
public class ResDefA extends Activity {}
