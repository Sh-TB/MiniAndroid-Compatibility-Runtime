package com.probe.r464;

public class Subscriber extends BaseSub {
    @EventAnn(name = "main", priority = 3)
    public void onMessage(String event) { }
    public void noArgs() { }
    private void secret(int code) { }
    public Subscriber() { }
    static void clinitOnly() { }
}
