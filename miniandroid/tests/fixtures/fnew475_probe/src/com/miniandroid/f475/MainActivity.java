package com.miniandroid.f475;

import android.app.Activity;
import android.os.Bundle;
import android.os.Parcel;

/**
 * R-NEW-018/019 probe (CONT-138): android.os.Parcel typed-record
 * marshalling law — obtain, write Int/Long/String/Float, dataSize,
 * setDataPosition(0), read back in order, dataPosition advance,
 * past-end readInt answers 0 (native JNI behavior), recycle no-op.
 */
public class MainActivity extends Activity {
    static void expect(String tag, boolean ok, String detail) {
        System.out.println("F475-" + tag + (ok ? "-OK " : "-FAIL ") + detail);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Parcel p = Parcel.obtain();
        p.writeInt(42);
        p.writeLong(1234567890123L);
        p.writeString("parcel-law");
        p.writeFloat(2.5f);
        expect("SIZE", p.dataSize() == 4, "dataSize=" + p.dataSize());
        p.setDataPosition(0);
        expect("POS0", p.dataPosition() == 0, "dataPosition=" + p.dataPosition());
        int i = p.readInt();
        expect("INT", i == 42, "readInt=" + i);
        long l = p.readLong();
        expect("LONG", l == 1234567890123L, "readLong=" + l);
        String s = p.readString();
        expect("STRING", "parcel-law".equals(s), "readString=" + s);
        float f = p.readFloat();
        expect("FLOAT", f == 2.5f, "readFloat=" + f);
        expect("POS4", p.dataPosition() == 4, "dataPosition=" + p.dataPosition());
        int past = p.readInt();
        expect("PASTEND", past == 0, "readInt=" + past);
        p.recycle();
        System.out.println("F475-DONE");
    }
}
