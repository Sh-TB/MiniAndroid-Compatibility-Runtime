package com.probe.fnew253;

import android.app.Activity;
import android.os.Bundle;
import android.os.Parcel;
import android.os.Parcelable;
import android.util.SparseArray;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.Serializable;
import java.lang.reflect.Field;

/**
 * CONT-7 W3 F-NEW-253 directive probe — the required synthetic contracts,
 * independent of Dooz (directive sections 4/5/6):
 *
 *   §4  Bundle contract:  putParcelable / getParcelable / containsKey /
 *       key+type preservation / Class.isInstance on retrieved values,
 *       with a REAL app-implemented Parcelable; positives AND honest
 *       negatives; verifies actual value/type identity, not just "no crash".
 *   §5  SaveableStateRegistry decision contract: the platform canBeSaved
 *       shape — walk the acceptable-classes array with Class.isInstance.
 *       Positive / negative / boundary (runtime class differs from the
 *       static reference type). Rows record input runtime class,
 *       expected, actual, reason.
 *   §6  Class.isInstance direct matrix: Object/Parcelable/Parent/Child/
 *       Unrelated/null — runtime-type assignability, never name matching.
 *
 * Every row is a generic platform contract. No app-specific conditions,
 * no class-name hacks. Visual verdict bands render through the view tree.
 */
public class MainActivity extends Activity {

    private static String report = "";

    private static void row(String id, boolean pass, String detail) {
        report += id + "|" + (pass ? "PASS" : "FAIL") + "|" + detail + "\n";
    }

    /** A REAL app-owned Parcelable implementation (AOSP contract). */
    public static final class PointParcelable implements Parcelable {
        public final int x;
        public final int y;
        public PointParcelable(int x, int y) { this.x = x; this.y = y; }
        @Override public int describeContents() { return 0; }
        @Override public void writeToParcel(Parcel out, int flags) {
            out.writeInt(x); out.writeInt(y);
        }
        public static final Parcelable.Creator<PointParcelable> CREATOR =
                new Parcelable.Creator<PointParcelable>() {
            @Override public PointParcelable createFromParcel(Parcel in) {
                return new PointParcelable(in.readInt(), in.readInt());
            }
            @Override public PointParcelable[] newArray(int size) {
                return new PointParcelable[size];
            }
        };
    }

    /** App-owned Serializable (second saveable family). */
    public static final class AppData implements Serializable {
        public final String tag;
        public AppData(String tag) { this.tag = tag; }
    }

    /** §6 hierarchy: Parent/Child/Unrelated app-owned classes. */
    public static class Parent { }
    public static class Child extends Parent { }
    public static class Unrelated { }

    /**
     * §5: the platform canBeSaved decision shape (dooz R8-trimmed 7-class
     * acceptable array; androidx DisposableSaveableStateRegistry walks it
     * with Class.isInstance). Generic re-implementation — no app names.
     */
    private static boolean canBeSavedShape(Object value) {
        Class<?>[] accept = { Serializable.class, Parcelable.class,
                              String.class, SparseArray.class,
                              android.os.Binder.class,
                              android.util.Size.class,
                              android.util.SizeF.class };
        for (Class<?> c : accept) if (c.isInstance(value)) return true;
        return false;
    }

    /** Runtime class name of a value, for evidence rows. */
    private static String rt(Object o) {
        return o == null ? "null" : o.getClass().getName();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // ── §6 Class.isInstance direct matrix (M-01..M-06) ─────────────
        Object plainObject = new Object();
        try {
            boolean r = Object.class.isInstance(plainObject);
            row("M-01", r, "Object.isInstance(Object)=" + r + " expected=true");
        } catch (Throwable t) { row("M-01", false, "threw " + t); }

        PointParcelable pp = new PointParcelable(3, 4);
        try {
            boolean r = Parcelable.class.isInstance(pp);
            row("M-02", r, "Parcelable.isInstance(PointParcelable)=" + r
                + " expected=true runtime=" + rt(pp));
        } catch (Throwable t) { row("M-02", false, "threw " + t); }

        Child child = new Child();
        try {
            boolean r = Parent.class.isInstance(child);
            row("M-03", r, "Parent.isInstance(Child)=" + r + " expected=true");
        } catch (Throwable t) { row("M-03", false, "threw " + t); }

        Parent parent = new Parent();
        try {
            boolean r = Child.class.isInstance(parent);
            row("M-04", !r, "Child.isInstance(Parent)=" + r + " expected=false");
        } catch (Throwable t) { row("M-04", false, "threw " + t); }

        try {
            boolean r = Unrelated.class.isInstance(plainObject);
            row("M-05", !r, "Unrelated.isInstance(Object)=" + r + " expected=false");
        } catch (Throwable t) { row("M-05", false, "threw " + t); }

        try {
            boolean r = Parcelable.class.isInstance(null);
            row("M-06", !r, "Parcelable.isInstance(null)=" + r + " expected=false (OpenJDK)");
        } catch (Throwable t) { row("M-06", false, "threw " + t); }

        // ── §4 Bundle contract (B-01..B-08) ────────────────────────────
        Bundle b = new Bundle();
        try {
            b.putParcelable("k1", pp);
            boolean r = b.containsKey("k1");
            row("B-01", r, "putParcelable->containsKey(k1)=" + r + " expected=true");
        } catch (Throwable t) { row("B-01", false, "threw " + t); }

        Object got1 = null;
        try {
            got1 = b.getParcelable("k1");
            boolean r = (got1 == pp);
            row("B-02", r, "getParcelable(k1)==same reference=" + r
                + " expected=true retrieved=" + rt(got1));
        } catch (Throwable t) { row("B-02", false, "threw " + t); }

        try {
            boolean r = got1 != null && PointParcelable.class == got1.getClass();
            row("B-03", r, "retrieved runtime class preserved=" + r
                + " expected=true class=" + rt(got1));
        } catch (Throwable t) { row("B-03", false, "threw " + t); }

        try {
            boolean r = Parcelable.class.isInstance(got1);
            row("B-04", r, "Parcelable.isInstance(retrieved)=" + r
                + " expected=true (canBeSaved decisive shape)");
        } catch (Throwable t) { row("B-04", false, "threw " + t); }

        try {
            Object absent = b.getParcelable("no-such-key");
            row("B-05", absent == null, "getParcelable(missing)=" + rt(absent)
                + " expected=null (Android semantics)");
        } catch (Throwable t) { row("B-05", false, "threw " + t); }

        try {
            boolean r = b.containsKey("no-such-key");
            row("B-06", !r, "containsKey(missing)=" + r + " expected=false");
        } catch (Throwable t) { row("B-06", false, "threw " + t); }

        try {
            b.putString("k2", "plain-string");
            Object raw = b.get("k2");
            boolean isParcel = Parcelable.class.isInstance(raw);
            // Android: a String stored in a Bundle stays a String; it must
            // NOT become Parcelable merely because Bundle accepts Objects.
            row("B-07", !isParcel && (raw instanceof String),
                "String stays String: raw=" + rt(raw)
                + " Parcelable.isInstance(raw)=" + isParcel + " expected=false");
        } catch (Throwable t) { row("B-07", false, "threw " + t); }

        try {
            // Key/type preservation: both entries coexist without crosstalk.
            String s = b.getString("k2");
            Object p = b.getParcelable("k1");
            boolean r = "plain-string".equals(s) && (p == pp);
            row("B-08", r, "type preservation: getString(k2)=" + s
                + " getParcelable(k1) identity=" + (p == pp) + " expected=true");
        } catch (Throwable t) { row("B-08", false, "threw " + t); }

        // ── §5 SaveableStateRegistry decision contract (S-01..S-06) ────
        // Positive: Bundle (the exact dooz face).
        try {
            boolean exp = true, act = canBeSavedShape(new Bundle());
            row("S-01", act == exp, "input=Landroid/os/Bundle; expected=" + exp
                + " actual=" + act + " reason=AOSP Bundle implements Parcelable");
        } catch (Throwable t) { row("S-01", false, "threw " + t); }

        // Positive: app Serializable.
        try {
            boolean exp = true, act = canBeSavedShape(new AppData("ad"));
            row("S-02", act == exp, "input=" + rt(new AppData("ad"))
                + " expected=" + exp + " actual=" + act
                + " reason=app class implements Serializable");
        } catch (Throwable t) { row("S-02", false, "threw " + t); }

        // Positive: String.
        try {
            boolean exp = true, act = canBeSavedShape("text");
            row("S-03", act == exp, "input=java.lang.String expected=" + exp
                + " actual=" + act + " reason=String is in the accept array");
        } catch (Throwable t) { row("S-03", false, "threw " + t); }

        // Negative: plain Object (registerValue must reject with IAE shape).
        try {
            boolean exp = false, act = canBeSavedShape(new Object());
            row("S-04", act == exp, "input=java.lang.Object expected=" + exp
                + " actual=" + act + " reason=no accept-class isInstance");
        } catch (Throwable t) { row("S-04", false, "threw " + t); }

        // Boundary: static Object reference holding a runtime Bundle —
        // the decision must consult the RUNTIME class.
        try {
            Object staticTyped = new Bundle();
            boolean exp = true, act = canBeSavedShape(staticTyped);
            row("S-05", act == exp, "input(static=Object,runtime="
                + rt(staticTyped) + ") expected=" + exp + " actual=" + act
                + " reason=runtime-type assignability, not static type");
        } catch (Throwable t) { row("S-05", false, "threw " + t); }

        // Boundary: app-implemented Parcelable is saveable via the parcel
        // family + the app DEX interface edge composed together.
        try {
            boolean exp = true, act = canBeSavedShape(pp);
            row("S-06", act == exp, "input=" + rt(pp) + " expected=" + exp
                + " actual=" + act + " reason=app Parcelable implements the family");
        } catch (Throwable t) { row("S-06", false, "threw " + t); }

        // Completeness (F-NEW-253 law): AOSP Bundle extends BaseBundle —
        // assignability against the BASE class must hold too. Probed via
        // the documented getGenericSuperclass surface (Class.forName
        // cannot name shadow framework classes — no DEX def — recorded
        // honestly; the generic-superclass law composes the AOSP table).
        try {
            Object gs = Bundle.class.getGenericSuperclass();
            boolean hasBase = gs instanceof Class;
            boolean accepts = hasBase && ((Class<?>) gs).isInstance(new Bundle());
            row("S-07", hasBase && accepts,
                "Bundle.getGenericSuperclass()=" + (hasBase ? rt(gs) : "null")
                + " isInstance(Bundle)=" + accepts
                + " expected=BaseBundle/true (AOSP: Bundle extends BaseBundle)");
        } catch (Throwable t) { row("S-07", false, "threw " + t); }

        // Visual verdict band.
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        TextView tv = new TextView(this);
        int pass = 0, total = 0;
        for (String line : report.split("\n")) {
            if (line.isEmpty()) continue;
            total++;
            if (line.contains("|PASS|")) pass++;
        }
        tv.setText("F253PROBE " + pass + "/" + total + "\n" + report);
        root.addView(tv);
        setContentView(root);
    }
}
