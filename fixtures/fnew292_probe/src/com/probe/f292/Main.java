package com.probe.f292;

import android.app.Activity;
import android.os.Bundle;
import android.os.Parcelable;
import android.widget.TextView;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * F-NEW-292 probe — LIBCORE UUID HIERARCHY LAW (framework interface table).
 *
 * AOSP libcore java/util/UUID.java:
 *   public final class UUID implements Serializable, Comparable<UUID>
 *
 * The androidx compose DisposableSaveableStateRegistry whitelist walk
 * (DisposableSaveableStateRegistry.android.kt, Compose 1.11.4 — decoded from
 * the upstream AAR in this campaign) accepts a rememberSaveable value iff
 * canBeSavedToBundle(value): NOT (Function AND Serializable), and
 * Class[] {Serializable, Parcelable, String, SparseArray, Binder, Size,
 * SizeF}.isInstance(value) is true. java.util.UUID passes on ART through
 * the Serializable arm. With no framework-table row for UUID the engine's
 * Class.isInstance/instance-of answered FALSE for the Serializable edge →
 * the registry threw IAE "…cannot be saved using the current
 * SaveableStateRegistry…" (composeStopwatch ground truth: IAE x51/run,
 * Lh4;.onMeasure catch-all aborted the measure pass → ops=0 →
 * DEFAULT_BACKGROUND_ONLY).
 *
 * Rows (positives = the law; negatives guard against over-acceptance):
 *   UUID-SER      Serializable.class.isInstance(uuid) == true   (THE law)
 *   UUID-INSTOF   (Object) uuid instanceof Serializable == true
 *   UUID-CMP      Comparable.class.isInstance(uuid) == true
 *   ENUM-SER      Serializable.class.isInstance(appEnum) == true
 *                 (the Ll71; shape: app enum, edge via the platform hop
 *                  java.lang.Enum implements Serializable, Comparable)
 *   ENUM-INSTOF   (Object) appEnum instanceof Serializable == true
 *   NEG-PARCEL    Parcelable.class.isInstance(uuid)   == false
 *   NEG-STR       String.class.isInstance(uuid)       == false
 *   NEG-CHARSEQ   CharSequence.class.isInstance(uuid) == false
 *   NEG-ENUMSTR   String.class.isInstance(appEnum)    == false
 *   SUMMARY       PASS iff all rows pass
 *
 * Hygiene: activity class "Main" — no name-gated arm substrings.
 */
public class Main extends Activity {

    /** An app enum — the Ll71; shape (R8-minified, extends java.lang.Enum). */
    enum Tick { T0, T1 }

    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static synchronized void row(String id, boolean ok, String detail) {
        out.add("F292|" + id + "|" + (ok ? "PASS" : "FAIL") + "|" + detail);
        if (ok) pass++; else fail++;
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        out.clear(); pass = 0; fail = 0;
        TextView tv = new TextView(this);
        setContentView(tv);

        // The F-090g law mints the runtime UUID (deterministic bits, same
        // heap shape the target app receives from UUID.randomUUID()).
        UUID uuid = UUID.randomUUID();

        // UUID-SER — THE law row (the whitelist arm ART uses).
        boolean ser = Serializable.class.isInstance(uuid);
        row("UUID-SER", ser, "Serializable.isInstance(uuid)=" + ser);

        // UUID-INSTOF — the DEX instanceof opcode path (same tables).
        boolean iof = ((Object) uuid) instanceof Serializable;
        row("UUID-INSTOF", iof, "uuid instanceof Serializable=" + iof);

        // UUID-CMP — the second libcore edge.
        boolean cmp = Comparable.class.isInstance(uuid);
        row("UUID-CMP", cmp, "Comparable.isInstance(uuid)=" + cmp);

        // ENUM-SER — the Ll71; shape (app enum; the Serializable edge lives
        // on the platform hop java.lang.Enum, not on the app class_def).
        boolean eser = Serializable.class.isInstance(Tick.T0);
        row("ENUM-SER", eser, "Serializable.isInstance(Tick.T0)=" + eser);

        // ENUM-INSTOF — DEX instanceof opcode on the same edge.
        boolean eiof = ((Object) Tick.T0) instanceof Serializable;
        row("ENUM-INSTOF", eiof, "Tick.T0 instanceof Serializable=" + eiof);

        // NEG-PARCEL — UUID is NOT Parcelable (over-acceptance guard).
        boolean par = Parcelable.class.isInstance(uuid);
        row("NEG-PARCEL", !par, "Parcelable.isInstance(uuid)=" + par);

        // NEG-STR — UUID is not a String.
        boolean str = String.class.isInstance(uuid);
        row("NEG-STR", !str, "String.isInstance(uuid)=" + str);

        // NEG-CHARSEQ — UUID is not a CharSequence.
        boolean chs = CharSequence.class.isInstance(uuid);
        row("NEG-CHARSEQ", !chs, "CharSequence.isInstance(uuid)=" + chs);

        // NEG-ENUMSTR — an enum is not a String (over-acceptance guard).
        boolean estr = String.class.isInstance(Tick.T0);
        row("NEG-ENUMSTR", !estr, "String.isInstance(Tick.T0)=" + estr);

        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        String summary = "F292|SUMMARY|"
                + (fail == 0 && pass >= 9 ? "PASS" : "FAIL")
                + "| " + pass + " pass, " + fail + " fail";
        sb.append(summary);
        tv.setText(sb.toString());
        try {
            java.io.FileOutputStream fos =
                openFileOutput("f292_results.txt", MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t2) { }
    }
}
