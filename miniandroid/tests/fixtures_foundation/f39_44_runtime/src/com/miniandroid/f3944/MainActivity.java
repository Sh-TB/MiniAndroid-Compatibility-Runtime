package com.miniandroid.f3944;
import android.app.Activity; import android.os.Bundle; import android.widget.TextView;
import java.lang.reflect.Method;
public class MainActivity extends Activity {
    static int staticInit = 0;
    static { staticInit = 11; }
    int fieldInit = 22;
    public interface Shape { int area(); }
    public static class Sq implements Shape {
        public int area() { return 9; }
    }
    public static class Base { public String name() { return "BASE"; } }
    public static class Sub extends Base { @Override public String name() { return "SUB"; } }
    public static class Box { public int v; public long w; public Box(int a, long c) { v = a; w = c; } }
    @Override public void onCreate(Bundle b) { super.onCreate(b);
        TextView tv = new TextView(this);
        // RT39 null
        String s = null; String nullOk = (s == null) ? "NULLOK" : "BAD";
        // RT40/RT41 arrays + primitive arrays + multi-dim
        int[] arr = new int[3]; arr[0] = 5; arr[2] = 7;
        int[][] grid = new int[2][3]; grid[1][2] = 9;
        long[] larr = new long[2]; larr[1] = 123456789L;
        // RT42 reflection
        String refl;
        try {
            Method m = MainActivity.class.getMethod("hashCode");
            refl = "REFL" + (m != null ? "OK" : "BAD");
        } catch (NoSuchMethodException e) { refl = "REFLMISS"; }
        // RT43 superclass dispatch
        String sup = new Sub().name();
        // RT44 interface dispatch
        int area = ((Shape) new Sq()).area();
        // RT45 wide values
        Box bx = new Box(3, 4000000000L);
        long wide = bx.w + 1;
        tv.setText(nullOk + "," + arr[0] + "," + arr[2] + "," + grid[1][2] + "," +
                   larr[1] + "," + refl + "," + sup + "," + area + "," +
                   staticInit + "," + fieldInit + "," + wide);
        setContentView(tv);
    }
}
