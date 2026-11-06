import java.lang.reflect.*;
import java.net.*;
import java.io.*;
import java.util.*;

/** Dump R$color name->id map from an android.jar (reflection, the coder's method). */
public class Rdump {
    public static void main(String[] a) throws Exception {
        URL url = new File(a[0]).toURI().toURL();
        URLClassLoader cl = new URLClassLoader(new URL[]{url});
        Class<?> c = Class.forName("android.content.res.R$color", true, cl);
        Field[] fs = c.getDeclaredFields();
        List<String> rows = new ArrayList<>();
        for (Field f : fs) {
            if (f.getType() == int.class) rows.add(f.getName() + " 0x" + Integer.toHexString(f.getInt(null)));
        }
        Collections.sort(rows);
        for (String r : rows) System.out.println(r);
        System.err.println("TOTAL " + rows.size());
    }
}
