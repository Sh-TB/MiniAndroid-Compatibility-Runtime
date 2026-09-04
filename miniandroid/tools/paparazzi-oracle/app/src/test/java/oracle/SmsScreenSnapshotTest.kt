package oracle

import app.cash.paparazzi.DeviceConfig
import app.cash.paparazzi.Paparazzi
import org.junit.Rule
import org.junit.Test

/**
 * EXP-095 §23: Paparazzi renders the SmsView layout structure through
 * LAYOUTLIB — the real Android rendering pipeline (same as Android Studio
 * preview). Output PNG = pixel-level reference for MiniAndroid's renderer.
 */
class SmsScreenSnapshotTest {

    @get:Rule
    val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_6.copy(
            screenHeight = 1920, screenWidth = 1080, density = 160.0
        ),
    )

    @Test
    fun smsScreen() {
        val view = paparazzi.inflate(R.layout.sms_screen)
        paparazzi.snapshot(view)
    }
}
