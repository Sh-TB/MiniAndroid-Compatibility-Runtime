package com.google.example.games.basegameutils;

import android.app.Activity;
import com.google.android.gms.common.api.GoogleApiClient;

/**
 * Build-time stub replacing the BaseGameUtils parent class: a plain Activity
 * whose sign-in callbacks are no-ops; the game's own overrides are preserved.
 */
public class BaseGameActivity extends Activity {
    protected GameHelper mHelper = new GameHelper();

    protected void onCreate(android.os.Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }

    public void onSignInSucceeded() {
    }

    public void onSignInFailed() {
    }

    public GoogleApiClient getApiClient() {
        return null;
    }

    protected void beginUserInitiatedSignIn() {
    }

    protected void signOut() {
    }
}
