package com.probe.r464;

public class BaseSub {
    @EventAnn(name = "base", priority = 7)
    public void onBase(String event) { }
    public void publicInherited() { }
    protected void hiddenInherited() { }
}
