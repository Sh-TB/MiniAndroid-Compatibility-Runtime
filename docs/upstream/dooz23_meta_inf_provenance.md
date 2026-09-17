# dooz23_extracted/META-INF — provenance record (compact knowledge)

Generated S51 finalization. The physical directory was REMOVED from Git (extraction residue, zero code/test/runtime consumers).
This file preserves the decisive provenance so no forensic knowledge is lost.

- Producer: unzip of Dooz v23 corpus APK (io.github.yamin8000.dooz v23, sha256 299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b, verified 2026-09-16 at miniandroid/download/exp076_corpus/io.github.yamin8000.dooz_23.apk; corpus fixture era S43/S44)
- Content: 93 files = AndroidX/Kotlin library '.version' pins + version-control-info.textproto (APK signing-era metadata)
- Purpose: pinned the upstream source versions consulted for R-NEW-361 forensics (compose runtime/ui 1.11.4)
- Runtime required: NO (dalvik_engine reads classes.dex/resources.arsc; never META-INF .version files)
- Test/script consumer: NO (rg dooz23_extracted → docs only)
- Reproduce: unzip -l miniandroid/download/io.github.yamin8000.dooz_23.apk 'META-INF/*'

## Version pins (verbatim from extracted META-INF)

androidx.activity_activity-compose = 1.13.0
androidx.activity_activity-ktx = 1.13.0
androidx.activity_activity = 1.13.0
androidx.annotation_annotation-experimental = 1.4.1
androidx.arch.core_core-runtime = task ':arch:core:core-runtime:writeVersionFile' property 'version'
androidx.autofill_autofill = 1.0.0
androidx.compose.animation_animation-core = 1.11.4
androidx.compose.animation_animation = 1.11.4
androidx.compose.foundation_foundation-layout = 1.11.4
androidx.compose.foundation_foundation = 1.11.4
androidx.compose.material3_material3-window-size-class = 1.4.0
androidx.compose.material3_material3 = 1.4.0
androidx.compose.material_material-icons-core = 1.7.8
androidx.compose.material_material-icons-extended = 1.7.8
androidx.compose.material_material-ripple = 1.11.4
androidx.compose.runtime_runtime-annotation = 1.11.4
androidx.compose.runtime_runtime-retain = 1.11.4
androidx.compose.runtime_runtime-saveable = 1.11.4
androidx.compose.runtime_runtime = 1.11.4
androidx.compose.ui_ui-geometry = 1.11.4
androidx.compose.ui_ui-graphics = 1.11.4
androidx.compose.ui_ui-text = 1.11.4
androidx.compose.ui_ui-tooling-preview = 1.11.4
androidx.compose.ui_ui-unit = 1.11.4
androidx.compose.ui_ui-util = 1.11.4
androidx.compose.ui_ui = 1.11.4
androidx.core_core-ktx = 1.19.0
androidx.core_core-viewtree = 1.0.0
androidx.core_core = 1.19.0
androidx.customview_customview-poolingcontainer = 1.0.0
androidx.customview_customview = 1.0.0
androidx.datastore_datastore-core = 1.2.1
androidx.datastore_datastore-preferences-core = 1.2.1
androidx.datastore_datastore-preferences = 1.2.1
androidx.datastore_datastore = 1.2.1
androidx.documentfile_documentfile = 1.0.0
androidx.dynamicanimation_dynamicanimation = 1.0.0
androidx.emoji2_emoji2 = 1.4.0
androidx.fragment_fragment = 1.5.1
androidx.graphics_graphics-path = 1.0.1
androidx.hilt_hilt-lifecycle-viewmodel-compose = 1.4.0
androidx.hilt_hilt-lifecycle-viewmodel = 1.4.0
androidx.interpolator_interpolator = 1.0.0
androidx.legacy_legacy-support-core-utils = 1.0.0
androidx.lifecycle_lifecycle-livedata-core-ktx = 2.11.0
androidx.lifecycle_lifecycle-livedata-core = 2.11.0
androidx.lifecycle_lifecycle-livedata = 2.11.0
androidx.lifecycle_lifecycle-process = 2.11.0
androidx.lifecycle_lifecycle-runtime-compose = 2.11.0
androidx.lifecycle_lifecycle-runtime-ktx = 2.11.0
androidx.lifecycle_lifecycle-runtime = 2.11.0
androidx.lifecycle_lifecycle-viewmodel-compose = 2.11.0
androidx.lifecycle_lifecycle-viewmodel-ktx = 2.11.0
androidx.lifecycle_lifecycle-viewmodel-savedstate = 2.11.0
androidx.lifecycle_lifecycle-viewmodel = 2.11.0
androidx.loader_loader = 1.0.0
androidx.localbroadcastmanager_localbroadcastmanager = 1.0.0
androidx.navigation_navigation-common = 2.9.8
androidx.navigation_navigation-compose = 2.9.8
androidx.navigation_navigation-runtime = 2.9.8
androidx.navigationevent_navigationevent-compose = 1.0.0
androidx.navigationevent_navigationevent = 1.0.0
androidx.print_print = 1.0.0
androidx.profileinstaller_profileinstaller = 1.4.0
androidx.savedstate_savedstate-compose = 1.4.0
androidx.savedstate_savedstate-ktx = 1.4.0
androidx.savedstate_savedstate = 1.4.0
androidx.startup_startup-runtime = 1.1.1
androidx.tracing_tracing = 1.2.0
androidx.transition_transition = 1.6.0
androidx.versionedparcelable_versionedparcelable = 1.1.1
androidx.viewpager_viewpager = 1.0.0
androidx.window_window-core = 1.5.0
androidx.window_window = 1.5.0
com.google.dagger_dagger-lint-aar = 2.60.1
com.google.dagger_dagger = 2.60.1
com.google.dagger_hilt-android = 2.60.1
com.google.dagger_hilt-core = 2.60.1
kotlinx_coroutines_android = 1.9.0
kotlinx_coroutines_core = 1.9.0
