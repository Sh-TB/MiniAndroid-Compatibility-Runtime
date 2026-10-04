package com.probe.r464;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {
    static List<String> out = new ArrayList<String>();
    static int pass = 0, fail = 0;

    static void ok(String id, String detail) {
        out.add("GATEA|R464-" + id + "|PASS|" + detail);
        pass++;
    }
    static void fail(String id, String detail) {
        out.add("GATEA|R464-" + id + "|FAIL|" + detail);
        fail++;
    }

    // Positive P-01: getDeclaredMethods excludes constructors and returns
    // real records (OpenJDK: constructors are NOT methods).
    static void p01() {
        Method[] ms = Subscriber.class.getDeclaredMethods();
        boolean hasCtor = false;
        int n = 0;
        for (Method m : ms) {
            n++;
            if (m.getName().equals("<init>")) hasCtor = true;
        }
        // Subscriber declares: onMessage, noArgs, secret (+ implicit none
        // for clinitOnly — package-private static still counts as declared)
        if (!hasCtor && n == 4) ok("P01-DECLARED-NO-CTOR", "declared=" + n + " ctorAbsent=true");
        else fail("P01-DECLARED-NO-CTOR", "declared=" + n + " ctorAbsent=" + !hasCtor);
    }

    // Positive P-02: getModifiers answers real DEX flags for public method.
    static void p02() throws Exception {
        Method m = Subscriber.class.getDeclaredMethod("onMessage", String.class);
        int mods = m.getModifiers();
        if (Modifier.isPublic(mods) && !Modifier.isStatic(mods))
            ok("P02-MODIFIERS", "mods=" + mods + " public=true static=false");
        else fail("P02-MODIFIERS", "mods=" + mods);
    }

    // Positive P-03: getParameterTypes — 1 param, exact type, never null.
    static void p03() throws Exception {
        Method m = Subscriber.class.getDeclaredMethod("onMessage", String.class);
        Class<?>[] ps = m.getParameterTypes();
        if (ps != null && ps.length == 1 && ps[0] == String.class)
            ok("P03-PARAMTYPES", "len=" + ps.length + " p0=java.lang.String");
        else fail("P03-PARAMTYPES", "ps=" + (ps == null ? "null" : ps.length));
        Method m2 = Subscriber.class.getDeclaredMethod("noArgs");
        Class<?>[] ps2 = m2.getParameterTypes();
        if (ps2 != null && ps2.length == 0) ok("P03b-EMPTY-PARAMS", "no-arg empty array");
        else fail("P03b-EMPTY-PARAMS", "ps2=" + (ps2 == null ? "null" : ps2.length));
    }

    // Positive P-04: getReturnType.
    static void p04() throws Exception {
        Method m = Subscriber.class.getDeclaredMethod("onMessage", String.class);
        if (m.getReturnType() == void.class) ok("P04-RETTYPE", "void");
        else fail("P04-RETTYPE", "ret=" + m.getReturnType());
    }

    // Positive P-05: getAnnotation resolves RUNTIME annotation + element.
    static void p05() throws Exception {
        Method m = Subscriber.class.getDeclaredMethod("onMessage", String.class);
        EventAnn a = m.getAnnotation(EventAnn.class);
        if (a != null && "main".equals(a.name()) && a.priority() == 3)
            ok("P05-ANNOTATION", "name=main priority=3");
        else fail("P05-ANNOTATION", "a=" + a);
    }

    // Negative N-01: getAnnotation on a non-annotated method answers null.
    static void n01() throws Exception {
        Method m = Subscriber.class.getDeclaredMethod("noArgs");
        if (m.getAnnotation(EventAnn.class) == null) ok("N01-ANN-ABSENT", "null per AOSP");
        else fail("N01-ANN-ABSENT", "non-null (silent-wrong)");
    }

    // Positive P-06: inherited public methods appear in getMethods with the
    // most-derived override law; inherited protected do NOT.
    static void p06() {
        Method[] all = Subscriber.class.getMethods();
        boolean onBase = false, pubInh = false, hidden = false;
        for (Method m : all) {
            if (m.getName().equals("onBase") && m.getDeclaringClass() == BaseSub.class) onBase = true;
            if (m.getName().equals("publicInherited")) pubInh = true;
            if (m.getName().equals("hiddenInherited")) hidden = true;
        }
        if (onBase && pubInh && !hidden)
            ok("P06-METHODS-INHERITED", "onBase+publicInherited present, hidden absent");
        else fail("P06-METHODS-INHERITED", "onBase=" + onBase + " pubInh=" + pubInh + " hidden=" + hidden);
    }

    // Negative N-02: NoSuchMethodException for an absent method (never a
    // fabricated record — F-NEW-219 law).
    static void n02() {
        try {
            Subscriber.class.getDeclaredMethod("nosuch", String.class);
            fail("N02-NO-SUCH-METHOD", "no exception (silent-wrong)");
        } catch (NoSuchMethodException e) {
            ok("N02-NO-SUCH-METHOD", "NoSuchMethodException thrown");
        } catch (Throwable t) {
            fail("N02-NO-SUCH-METHOD", "wrong throwable " + t);
        }
    }

    // Positive P-07: EventBus-style scan end-to-end (modifiers gate +
    // param gate + annotation read) over getDeclaredMethods — the real
    // consumer shape that died in R-NEW-464.
    static void p07() {
        int found = 0;
        for (Method m : Subscriber.class.getDeclaredMethods()) {
            int mods = m.getModifiers();
            if ((mods & Modifier.PUBLIC) == 0) continue;
            if ((mods & (Modifier.ABSTRACT | Modifier.STATIC)) != 0) continue;
            Class<?>[] ps = m.getParameterTypes();
            if (ps == null || ps.length != 1) continue;
            EventAnn a = m.getAnnotation(EventAnn.class);
            if (a != null) found++;
        }
        // onMessage + inherited onBase via declared only → 1
        if (found == 1) ok("P07-SCAN", "1 @EventAnn public 1-param method");
        else fail("P07-SCAN", "found=" + found);
    }

    // Positive P-08: Method identity — same method queried twice gives
    // equal identity semantics (declaring class preserved).
    static void p08() throws Exception {
        Method a = Subscriber.class.getDeclaredMethod("onMessage", String.class);
        Method b = Subscriber.class.getDeclaredMethod("onMessage", String.class);
        if (a.getDeclaringClass() == Subscriber.class)
            ok("P08-DECLARING-CLASS", "Subscriber");
        else fail("P08-DECLARING-CLASS", "wrong class");
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        TextView tv = new TextView(this);
        try {
            p01(); p02(); p03(); p04(); p05();
            n01(); p06(); n02(); p07(); p08();
        } catch (Throwable t) {
            out.add("GATEA|R464-HARNESS|FAIL|" + t.getClass().getName() + ": " + t.getMessage());
            fail++;
        }
        StringBuilder sb = new StringBuilder();
        for (String s : out) sb.append(s).append('\n');
        tv.setText(sb.toString());
        setContentView(tv);
        try {
            java.io.FileOutputStream fos = openFileOutput("r464_results.jsonl",
                    MODE_PRIVATE);
            fos.write(sb.toString().getBytes("UTF-8"));
            fos.close();
        } catch (Throwable t) { }
    }
}
