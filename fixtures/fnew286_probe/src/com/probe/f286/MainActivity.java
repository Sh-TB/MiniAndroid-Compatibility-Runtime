package com.probe.f286;

import java.lang.annotation.Annotation;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.reflect.Method;

/**
 * CONT-30 synthetic probe — F-NEW-286 (zero-payload re-entrant dispatch) +
 * F-NEW-287 (Method.getAnnotations never-null).
 *
 * R1/R2/R6  — a zero-arg instance method legally RE-ENTERS on the same
 *             receiver through a cross-class dispatch hop, each nesting
 *             distinguished only by INTERNAL state (the depth field) — the
 *             exact upstream shape of GapComposer.recomposeToGroupEnd
 *             (skipToGroupEnd/skipCurrentGroup → scope.compose → nested
 *             skip). Pre-F-NEW-286 the M3-19 active-cycle stub fabricated a
 *             void for the nested call: the counter stops, the return value
 *             is void. Post-fix every nesting executes real DEX.
 * R3/R4     — Method.getAnnotations never-null (ART law): annotated method
 *             answers its runtime annotations; plain method answers an EMPTY
 *             array — never null (the LocalSavedStateRegistryOwnerKt.<clinit>
 *             face shape: Intrinsics.checkNotNullExpressionValue(
 *             getAnnotations(...), "getAnnotations(...)")).
 * R5        — payload-distinct same-key re-entry still terminates (the
 *             guard/backstop path stays armed for payload-distinct keys).
 */
public class MainActivity extends android.app.Activity {

    // ── F-NEW-286: legal zero-payload re-entrant dispatch ──────────────
    static class Dispatcher {
        int depth = 0;
        int visits = 0;
        StringBuilder trace = new StringBuilder();

        // zero-arg instance method: key = class.method()I + receiver only
        int visit() {
            visits++;
            depth++;
            trace.append("v").append(depth);
            if (depth < 3) {
                Walker.hop(this, depth);    // cross-class dispatch hop,
                                            // payload-distinct per level
            }
            int at = depth;
            depth--;
            return at;                       // 3, 2 at nesting levels
        }
    }

    static class Walker {
        static void hop(Dispatcher d, int level) {
            d.visit();                       // RE-ENTRY, same receiver,
                                             // zero-payload visit() re-enters
        }
    }

    // ── F-NEW-287: reflective annotation probe surface ─────────────────
    @Retention(RetentionPolicy.RUNTIME)
    @interface Mark {}

    static class Anno {
        @Mark
        int annotated() { return 1; }

        int plain() { return 2; }
    }

    static int fails = 0;

    static void row(String name, boolean ok) {
        System.out.println("PROBE-ROW " + name + " "
            + (ok ? "|PASS|" : "|FAIL|"));
        if (!ok) fails++;
    }

    @Override
    protected void onCreate(android.os.Bundle b) {
        super.onCreate(b);

        // R1: nested zero-payload re-entries all execute (3 visits)
        Dispatcher d = new Dispatcher();
        int top = d.visit();
        row("R1-nested-zero-payload-executes(d.visits==3)", d.visits == 3);

        // R2: the re-entrant calls return REAL values (3 then 2), not the
        // stub's void: the outer visit's nested hop returns 2 observed via
        // the trace order v1v2v3 and the top return == 1 (outermost).
        row("R2-nested-returns-real(trace==v1v2v3,top==1)",
            d.trace.toString().equals("v1v2v3") && top == 1);

        // R6: per-level internal state distinguished the nestings — the
        // depth counter unwound cleanly (back to 0).
        row("R6-depth-unwind(depth==0)", d.depth == 0);

        // R3: annotated method → non-null array, exact runtime annotation
        try {
            Method m = Anno.class.getDeclaredMethod("annotated");
            Annotation[] a = m.getAnnotations();
            row("R3-getAnnotations-annotated(len==1,type==Mark)",
                a != null && a.length == 1
                    && a[0].annotationType() == Mark.class);
            // R3b: the F-191 consumer on the same method — isolates a
            // table-population gap (R3b FAIL) from a getAnnotations lookup
            // gap (R3b PASS but R3 FAIL).
            Object one = m.getAnnotation(Mark.class);
            row("R3b-getAnnotation-F191(nonNull)", one != null);
            // R3c/R3d: decompose the composite R3 check.
            row("R3c-getAnnotations-nonNull", a != null);
            row("R3d-getAnnotations-len1", a != null && a.length == 1);
            row("R3e-getAnnotations-typeMatch",
                a != null && a.length == 1
                    && a[0].annotationType() == Mark.class);
        } catch (Throwable t) {
            row("R3-getAnnotations-annotated(len==1,type==Mark)", false);
            row("R3b-getAnnotation-F191(nonNull)", false);
            row("R3c-getAnnotations-nonNull", false);
            row("R3d-getAnnotations-len1", false);
            row("R3e-getAnnotations-typeMatch", false);
        }

        // R4: plain method → non-null EMPTY array (never null)
        try {
            Method m2 = Anno.class.getDeclaredMethod("plain");
            Annotation[] a2 = m2.getAnnotations();
            row("R4-getAnnotations-plain(nonNull,empty)",
                a2 != null && a2.length == 0);
        } catch (Throwable t) {
            row("R4-getAnnotations-plain(nonNull,empty)", false);
        }

        // R5: payload-distinct re-entry (int arg → =v key part) still
        // terminates: bounded recursion through the guard path completes.
        row("R5-payload-distinct-terminates(sum==6)", sumDown(3) == 6);

        System.out.println("PROBE-DONE fails=" + fails);
    }

    static int sumDown(int n) {
        if (n <= 0) return 0;
        return n + sumDown(n - 1);   // same receiver(static)=none + payload =n
    }
}
