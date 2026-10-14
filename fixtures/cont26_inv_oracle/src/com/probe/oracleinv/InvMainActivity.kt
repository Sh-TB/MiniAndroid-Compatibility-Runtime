package com.probe.oracleinv

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import kotlinx.coroutines.flow.MutableStateFlow

/**
 * CONT-26 TRACK A — invalidation-delivery oracle (TEST-ONLY, un-renamed
 * real Compose 1.11.4 + real deps, NO R8, NO navigation).
 *
 * Mirrors the dooz-blocked chain WITHOUT navigation machinery:
 *
 *   composition #1 renders           L1=A  L2=A!  L3=S0
 *   LaunchedEffect coroutine starts  (effectCoroutineContext dispatch)
 *   coroutine writes x = "B"         (global snapshot write)
 *   GlobalSnapshotManager monitor    (sendApplyNotifications)
 *   Recomposer apply-observer        (snapshotInvalidations)
 *   runner wakes -> recomposition #2 -> applyChanges -> LayoutNode update
 *   measure/layout/draw              L1=B  L2=B!  L3=S1
 *
 * Three arms (each an upstream-generic invalidation shape):
 *   L1  LaunchedEffect(Unit) { x = "B" }       plain state write from a
 *                                              composition effect coroutine
 *   L2  derivedStateOf { x + "!" }             derived-state invalidation
 *   L3  MutableStateFlow + collectAsState      StateFlow first-emit-on-
 *       + LaunchedEffect { flow.value="S1" }   subscribe chain (the dooz
 *                                              visibleEntries shape)
 *
 * If the delivery chain works end-to-end the screen shows
 *   L1=B  L2=B!  L3=S1
 * If it stalls where dooz stalls, the screen keeps composition #1's
 *   L1=A  L2=A!  L3=S0
 * Either way the un-renamed names give the exact first failing link.
 */
class InvMainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    Column {
                        var x by remember { mutableStateOf("A") }
                        LaunchedEffect(Unit) { x = "B" }
                        Text("L1=$x")

                        val d by remember { derivedStateOf { x + "!" } }
                        Text("L2=$d")

                        val flow = remember { MutableStateFlow("S0") }
                        val pv by flow.collectAsState()
                        Text("L3=$pv")
                        LaunchedEffect(Unit) { flow.value = "S1" }
                    }
                }
            }
        }
    }
}
