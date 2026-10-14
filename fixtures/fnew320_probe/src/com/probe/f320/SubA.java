package com.probe.f320;

/**
 * The subclass with the SHADOWING field (the c$b shape): its own field
 * {@code a} of type Outer, assigned in ITS ctor from the parameter, after
 * the super ctor has already stored the Inner into the super slot.
 */
public class SubA extends SupA {
    public Outer a;   // shadows SupA.a by NAME — distinct ART slot

    public SubA(Outer o) {
        super();      // super ctor writes SupA.a = Inner("super-slot")
        a = o;        // sub ctor writes SubA.a = o (the outer presenter)
    }

    /** The outer read face — c$b.f pc=27 `iget c$b.a`. */
    public Outer outer() {
        return a;
    }
}
