# DOOZ_COMPOSE_DEPENDENCY_MATRIX (CONT-12 PHASE 1)

Source of versions: the dooz APK itself (`META-INF/*.version`, SHA
299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b).
Binaries: real Maven artifacts, KMP `-android` coordinates (the root
AAR on Google Maven is an empty stub since compose went multiplatform).
NO version mixing: every artifact matches the APK's own version file.

| artifact | dooz version-file entry | version | source | artifact SHA16 | classes.jar SHA16 | #classes |
|---|---|---|---|---|---|---|
| runtime-android | 1.11.4 | 1.11.4 | google-maven | 18fd863f42c06100 | 57a4a22728458b47 | 764 |
| runtime-saveable-android | 1.11.4 | 1.11.4 | google-maven | 75acd64c040fc768 | d67ea117111a273d | 22 |
| runtime-retain-android | 1.11.4 | 1.11.4 | google-maven | 48d960544c81e82b | 371131b73a22168c | 24 |
| ui-android | 1.11.4 | 1.11.4 | google-maven | 893c3b0a4f90631b | 82fa4d600cdbffdb | 1696 |
| ui-geometry-android | 1.11.4 | 1.11.4 | google-maven | 393066ecd102f8cd | 046abc42369640d5 | 19 |
| ui-graphics-android | 1.11.4 | 1.11.4 | google-maven | 4ccaf8e169c158f7 | e603bb9757cc3b91 | 314 |
| ui-text-android | 1.11.4 | 1.11.4 | google-maven | 01284212abb9ab6b | 59ea065159afc40a | 427 |
| ui-unit-android | 1.11.4 | 1.11.4 | google-maven | 8b778afa16102b89 | 8174d77f5b03ef00 | 50 |
| ui-util-android | 1.11.4 | 1.11.4 | google-maven | d6ca2aaed3f71455 | f3906c54d3fc415d | 9 |
| foundation-android | 1.11.4 | 1.11.4 | google-maven | a6aac6be46b77569 | d046555d433f34de | 1899 |
| foundation-layout-android | 1.11.4 | 1.11.4 | google-maven | 23ff32f548deccf4 | d2bb00a148d27c1e | 335 |
| animation-android | 1.11.4 | 1.11.4 | google-maven | 4a9534afa595551d | 17c18f1e179e7e91 | 297 |
| animation-core-android | 1.11.4 | 1.11.4 | google-maven | 66d489454bfcb123 | 96c268be093e2590 | 174 |
| material-ripple-android | 1.11.4 | 1.11.4 | google-maven | 38bd10db57ffd6f8 | afc96b3ea0b5a697 | 40 |
| material-icons-core-android | 1.7.8 | 1.7.8 | google-maven | 332c06b25e662cc4 | e433f64a31563fa6 | 293 |
| material3-android | 1.4.0 | 1.4.0 | google-maven | 3a37e8b36df3822f | 5293787ad0dcb97d | 1367 |
| material3-window-size-class-android | 1.4.0 | 1.4.0 | google-maven | 97b32a3a7d09c68c | 88545fa1283d7db3 | 9 |
| activity | 1.13.0 | 1.13.0 | google-maven | b5541dc5f74e3538 | 10b1ce80d96f5eba | 127 |
| activity-compose | 1.13.0 | 1.13.0 | google-maven | ab9dbab873fff677 | a72c61c30f76a71e | 35 |
| activity-ktx | 1.13.0 | 1.13.0 | google-maven | b5541dc5f74e3538 | 27f9d13cbb14946f | 0 |
| lifecycle-runtime-android | 2.11.0 | 2.11.0 | google-maven | 8711865f8d3603bc | d50215d553b73d1f | 33 |
| lifecycle-runtime-ktx-android | 2.11.0 | 2.11.0 | google-maven | 1fead96607f8b4eb | 24bd2f0eeebee7b4 | 0 |
| lifecycle-runtime-compose-android | 2.11.0 | 2.11.0 | google-maven | 7b31489e6e162143 | 044f3cd446c452ba | 24 |
| lifecycle-viewmodel-android | 2.11.0 | 2.11.0 | google-maven | 509aa5c0711e61a1 | 13467966db82d4e0 | 48 |
| lifecycle-viewmodel-compose-android | 2.11.0 | 2.11.0 | google-maven | 2bafd402807bd4af | d6b195a58347b617 | 15 |
| lifecycle-viewmodel-savedstate-android | 2.11.0 | 2.11.0 | google-maven | 1761707c1ddee002 | 7fb42d10ceee4b1d | 34 |
| lifecycle-livedata | 2.11.0 | 2.11.0 | google-maven | ab9dbab873fff677 | 9127ae7b51b3335e | 30 |
| lifecycle-livedata-core | 2.11.0 | 2.11.0 | google-maven | ab9dbab873fff677 | 6664ca188b60a6b4 | 9 |
| lifecycle-common (jvm coordinate) | n/a | 2.11.0 | google-maven | e6a66e67b9f63a0f | e6a66e67b9f63a0f | 42 |
| lifecycle-process | 2.11.0 | 2.11.0 | google-maven | ab9dbab873fff677 | 326c81a17a0d2def | 10 |
| navigation-compose-android | 2.9.8 | 2.9.8 | google-maven | 53dccc442276cde3 | cde8b0eaa877eb04 | 43 |
| navigation-runtime-android | 2.9.8 | 2.9.8 | google-maven | 7d741a3b0a299a8c | c34dc5c90b50e38e | 50 |
| navigation-common-android | 2.9.8 | 2.9.8 | google-maven | d43832772012afa0 | 30fe4b66ece1e33f | 140 |
| navigationevent-android | 1.0.0 | 1.0.0 | google-maven | cda4bb83d1c892a2 | 525d5f988236caa7 | 29 |
| navigationevent-compose-android | 1.0.0 | 1.0.0 | google-maven | 5cee018dbe130b53 | d87acddf8384f1c6 | 11 |
| core | 1.19.0 | 1.19.0 | google-maven | dc1b678d58ebcf2b | 9c84bdd11f6dcb98 | 1048 |
| core-ktx | 1.19.0 | 1.19.0 | google-maven | db1ae24b15c36358 | b08e0f7c85e373d3 | 0 |
| core-viewtree | 1.0.0 | 1.0.0 | google-maven | dc1b678d58ebcf2b | 0979a3d91da3a70d | 1 |
| savedstate-android | 1.4.0 | 1.4.0 | google-maven | 1656ce62cd233d48 | 70e718fd5b47a440 | 70 |
| savedstate-compose-android | 1.4.0 | 1.4.0 | google-maven | 0f0ae3032d6c6eea | 7dee122992fb8de2 | 7 |
| annotation-experimental | 1.4.1 | 1.4.1 | google-maven | 6bd4c7c7476f8260 | f97daae3e5fa1231 | 6 |
| customview-poolingcontainer | 1.0.0 | 1.0.0 | google-maven | 3584102fc49bf399 | 0690e2d3b17755c3 | 3 |
| emoji2 | 1.4.0 | 1.4.0 | google-maven | 433febd3434a4566 | 3754ea9040ac7b65 | 63 |
| startup-runtime | 1.1.1 | 1.1.1 | google-maven | e0a6329a371262fe | 7f90b874051d50d5 | 5 |
| tracing | 1.2.0 | 1.2.0 | google-maven | ab9dbab873fff677 | ba2884d7e9f4e315 | 3 |
| profileinstaller | 1.4.0 | 1.4.0 | google-maven | d502141fcce90243 | 4f5b02cc0ad1d103 | 26 |
| autofill | 1.0.0 | 1.0.0 | google-maven | c9468f56e05006ea | 88d069672dd02b16 | 1 |
| core-runtime | task ':arch:core:core-runtime:writeVersi | 2.2.0 | google-maven | a1be5e0caa2b0762 | c57bea6797743219 | 5 |
| core-common | n/a | 2.2.0 | google-maven | 65308a06b1c00ee1 | 65308a06b1c00ee1 | 9 |
| kotlinx-coroutines-core-jvm | 1.9.0 | 1.9.0 | maven-central | ad89c2892235e670 | ad89c2892235e670 | 826 |
| kotlinx-coroutines-android | 1.9.0 | 1.9.0 | maven-central | bd783acd2f973884 | bd783acd2f973884 | 8 |
| atomicfu-jvm | n/a | 0.23.2 | maven-central | 101ff43ff563fca1 | 101ff43ff563fca1 | 26 |
| kotlinx-collections-immutable-jvm | n/a | 0.3.7 | maven-central | 0c461865231ff825 | 0c461865231ff825 | 128 |
| collection-jvm | n/a | 1.5.0 | google-maven | 70b35924e4babcdf | 70b35924e4babcdf | 162 |
| kotlin-stdlib | n/a | 2.1.20 | maven-central | 65d12d85a3b865c1 | 1bcc74e8ce84e2c2 | 951 |

Total: 55 artifacts, 11767 real classes fetched.
Excluded: `androidx.annotation:annotation` (1.4.1 not published as binary;
annotations are compile-time metadata with no runtime behavior — R8 strips
their enforcement; dooz's own copy stays inside its DEX).

## Dooz APK version files (authoritative, verbatim)

```text
androidx.activity_activity = 1.13.0
androidx.activity_activity-compose = 1.13.0
androidx.activity_activity-ktx = 1.13.0
androidx.annotation_annotation-experimental = 1.4.1
androidx.arch.core_core-runtime = task ':arch:core:core-runtime:writeVersi
androidx.autofill_autofill = 1.0.0
androidx.compose.animation_animation = 1.11.4
androidx.compose.animation_animation-core = 1.11.4
androidx.compose.foundation_foundation = 1.11.4
androidx.compose.foundation_foundation-layout = 1.11.4
androidx.compose.material3_material3 = 1.4.0
androidx.compose.material3_material3-window-size-class = 1.4.0
androidx.compose.material_material-icons-core = 1.7.8
androidx.compose.material_material-icons-extended = 1.7.8
androidx.compose.material_material-ripple = 1.11.4
androidx.compose.runtime_runtime = 1.11.4
androidx.compose.runtime_runtime-annotation = 1.11.4
androidx.compose.runtime_runtime-retain = 1.11.4
androidx.compose.runtime_runtime-saveable = 1.11.4
androidx.compose.ui_ui = 1.11.4
androidx.compose.ui_ui-geometry = 1.11.4
androidx.compose.ui_ui-graphics = 1.11.4
androidx.compose.ui_ui-text = 1.11.4
androidx.compose.ui_ui-tooling-preview = 1.11.4
androidx.compose.ui_ui-unit = 1.11.4
androidx.compose.ui_ui-util = 1.11.4
androidx.core_core = 1.19.0
androidx.core_core-ktx = 1.19.0
androidx.core_core-viewtree = 1.0.0
androidx.customview_customview = 1.0.0
androidx.customview_customview-poolingcontainer = 1.0.0
androidx.datastore_datastore = 1.2.1
androidx.datastore_datastore-core = 1.2.1
androidx.datastore_datastore-preferences = 1.2.1
androidx.datastore_datastore-preferences-core = 1.2.1
androidx.documentfile_documentfile = 1.0.0
androidx.dynamicanimation_dynamicanimation = 1.0.0
androidx.emoji2_emoji2 = 1.4.0
androidx.fragment_fragment = 1.5.1
androidx.graphics_graphics-path = 1.0.1
androidx.hilt_hilt-lifecycle-viewmodel = 1.4.0
androidx.hilt_hilt-lifecycle-viewmodel-compose = 1.4.0
androidx.interpolator_interpolator = 1.0.0
androidx.legacy_legacy-support-core-utils = 1.0.0
androidx.lifecycle_lifecycle-livedata = 2.11.0
androidx.lifecycle_lifecycle-livedata-core = 2.11.0
androidx.lifecycle_lifecycle-livedata-core-ktx = 2.11.0
androidx.lifecycle_lifecycle-process = 2.11.0
androidx.lifecycle_lifecycle-runtime = 2.11.0
androidx.lifecycle_lifecycle-runtime-compose = 2.11.0
androidx.lifecycle_lifecycle-runtime-ktx = 2.11.0
androidx.lifecycle_lifecycle-viewmodel = 2.11.0
androidx.lifecycle_lifecycle-viewmodel-compose = 2.11.0
androidx.lifecycle_lifecycle-viewmodel-ktx = 2.11.0
androidx.lifecycle_lifecycle-viewmodel-savedstate = 2.11.0
androidx.loader_loader = 1.0.0
androidx.localbroadcastmanager_localbroadcastmanager = 1.0.0
androidx.navigation_navigation-common = 2.9.8
androidx.navigation_navigation-compose = 2.9.8
androidx.navigation_navigation-runtime = 2.9.8
androidx.navigationevent_navigationevent = 1.0.0
androidx.navigationevent_navigationevent-compose = 1.0.0
androidx.print_print = 1.0.0
androidx.profileinstaller_profileinstaller = 1.4.0
androidx.savedstate_savedstate = 1.4.0
androidx.savedstate_savedstate-compose = 1.4.0
androidx.savedstate_savedstate-ktx = 1.4.0
androidx.startup_startup-runtime = 1.1.1
androidx.tracing_tracing = 1.2.0
androidx.transition_transition = 1.6.0
androidx.versionedparcelable_versionedparcelable = 1.1.1
androidx.viewpager_viewpager = 1.0.0
androidx.window_window = 1.5.0
androidx.window_window-core = 1.5.0
com.google.dagger_dagger = 2.60.1
com.google.dagger_dagger-lint-aar = 2.60.1
com.google.dagger_hilt-android = 2.60.1
com.google.dagger_hilt-core = 2.60.1
kotlinx_coroutines_android = 1.9.0
kotlinx_coroutines_core = 1.9.0
```
