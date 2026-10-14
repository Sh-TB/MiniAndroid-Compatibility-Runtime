package com.probe.fragtx;

import android.app.Activity;
import android.app.Fragment;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

/**
 * The probe fragment: exercises the full platform lifecycle ladder the
 * F-NEW-304 drain must honor — onAttach → onCreate → onCreateView (REAL
 * inflater path, R.layout.frag_main) → onViewCreated → onActivityCreated →
 * onStart → onResume — and the state getters (isAdded/getView).
 */
public class ProbeFragment extends Fragment {
    View createdView;

    @Override
    public void onAttach(Activity activity) {
        super.onAttach(activity);
        MainActivity.row("FT-05", activity != null,
            "onAttach activity non-null=" + (activity != null));
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        MainActivity.row("FT-06", true, "onCreate fired");
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        View v = inflater.inflate(R.layout.frag_main, container, false);
        createdView = v;
        MainActivity.row("FT-07",
            v != null && container != null && inflater != null,
            "inflater=" + (inflater != null)
            + " container=" + (container != null)
            + " view=" + (v != null));
        return v;
    }

    @Override
    public void onViewCreated(View view, Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        MainActivity.row("FT-08", view == createdView,
            "onViewCreated identity=" + (view == createdView));
    }

    @Override
    public void onActivityCreated(Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
        MainActivity.row("FT-09a", true, "onActivityCreated fired");
    }

    @Override
    public void onStart() {
        super.onStart();
        MainActivity.row("FT-09b", isAdded() && getView() != null,
            "onStart isAdded=" + isAdded()
            + " getView non-null=" + (getView() != null));
    }

    @Override
    public void onResume() {
        super.onResume();
        MainActivity.row("FT-09c", true, "onResume fired");
    }
}
