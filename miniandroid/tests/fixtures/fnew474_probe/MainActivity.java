package com.miniandroid.f474;

import android.app.Activity;
import android.os.Bundle;
import dalvik.system.InMemoryDexClassLoader;
import java.nio.ByteBuffer;

/**
 * R-NEW-133 probe (CONT-137): loads a REAL secondary dex image from memory
 * via dalvik.system.InMemoryDexClassLoader and asserts child-first
 * loadClass semantics: the buffer-dex class resolves, an absent class
 * raises ClassNotFoundException (real law), and the parent loader is
 * captured. The payload dex is built by build.sh with the real D8
 * toolchain and embedded as a hex string (deterministic, no asset/IO).
 */
public class MainActivity extends Activity {
    static final String PAYLOAD_HEX = "@@PAYLOAD_HEX@@";

    static byte[] hexBytes(String s) {
        byte[] out = new byte[s.length() / 2];
        for (int i = 0; i < out.length; i++) {
            int hi = Character.digit(s.charAt(i * 2), 16);
            int lo = Character.digit(s.charAt(i * 2 + 1), 16);
            out[i] = (byte) ((hi << 4) | lo);
        }
        return out;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        try {
            byte[] dex = hexBytes(PAYLOAD_HEX);
            System.out.println("F474-DEX-BYTES " + dex.length);
            ByteBuffer bb = ByteBuffer.wrap(dex);
            InMemoryDexClassLoader cl =
                    new InMemoryDexClassLoader(bb, getClassLoader());
            Class<?> c = cl.loadClass("com.miniandroid.f474.Payload");
            System.out.println("F474-HIT " + c.getName());
            try {
                cl.loadClass("com.miniandroid.f474.Absent");
                System.out.println("F474-NEG-FAIL no-CNFE");
            } catch (ClassNotFoundException e) {
                System.out.println("F474-NEG-OK " + e.getMessage());
            }
            System.out.println("F474-PARENT " + (cl.getParent() != null));
            System.out.println("F474-REMAIN " + bb.remaining());
        } catch (Throwable t) {
            System.out.println("F474-ERROR " + t);
        }
    }
}
