plugins {
    id("com.android.library")
    id("app.cash.paparazzi")
}

android {
    namespace = "oracle.paparazzi"
    compileSdk = 34

    defaultConfig {
        minSdk = 24
    }
}

// EXP-095 §23: Paparazzi renders through layoutlib — the SAME rendering
// pipeline Android Studio's preview uses. This is the pixel-level ORACLE
// for MiniAndroid's software renderer comparison.
