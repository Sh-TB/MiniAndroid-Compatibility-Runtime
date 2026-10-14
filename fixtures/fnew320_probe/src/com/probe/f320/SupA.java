package com.probe.f320;

/**
 * F-NEW-321 probe shape — the EXACT R8-shadowing family solitaire carries
 * (RecyclerView$Adapter ay$a.a = mObservable ay$b, shadowed by the subclass
 * NavigationMenuPresenter$Adapter c$b.a = outer presenter):
 *   SupA.a  — superclass instance field, initialized in the SUPER ctor to
 *             a fresh Inner (the mObservable shape)
 *   SubA.a  — subclass instance field of a DIFFERENT type, assigned in the
 *             SUB ctor from its own parameter (the outer-presenter shape)
 * ART law: the two fields are DISTINCT slots. The subclass slot must keep
 * the value the sub ctor wrote; the superclass slot must keep the Inner
 * the super ctor wrote. The engine's dual-write bare mirror (F-NEW-160)
 * must not let the super ctor's mirror land in the sub's qualified slot.
 */
public class SupA {
    public Inner a;

    public SupA() {
        a = new Inner("super-slot");
    }

    /** Super-slot accessor (the mObservable read face). */
    public Inner superA() {
        return a;
    }

    /** Super-slot writer (round-trip face). */
    public void setSuperA(Inner v) {
        a = v;
    }
}
