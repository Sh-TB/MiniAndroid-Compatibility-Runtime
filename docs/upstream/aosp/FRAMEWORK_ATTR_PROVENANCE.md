# Framework theme-attr defaults — provenance (S68 W2)

Source: aosp-mirror/platform_frameworks_base @ oreo-release

- `public.xml` sha256=`aae0d8b5addc7a844314e1159385c9913d1f1dcc072609b9c954527610c28b27`
- `themes_material.xml` sha256=`9cb656535492fc807f9f6cfaebe9eea1a41abbb86c3d7825fe2e804f0ece9629`
- `colors_material.xml` sha256=`0c39ceffa7fd34729d52d9d9d6c62f1cc71624972d30bb156e63a70e7d0ff051`
- `colors.xml` sha256=`9e1529faa7e064e5318f48b9f8966f36ef97cc9585257c0ce1f5b801f5b90a45`
- `colors_holo.xml` sha256=`97a208e98f34590f9ba12419fcf1f29b08f098a190731dd656d0d9c34ca550f1`
- `colors_legacy.xml` sha256=`b490ae2fd08aca079d934c8f19e3f7d315c378fb881c07f47a2bd8092af0ba50`

## Resolved (22 attrs)

| attr | id | Theme.Material | Theme.Material.Light |
|---|---|---|---|
| colorPrimary | 0x01010433 | 0xff212121 | 0xfff5f5f5 |
| colorPrimaryDark | 0x01010434 | 0xff000000 | 0xff757575 |
| colorAccent | 0x01010435 | 0xff80cbc4 | 0xff009688 |
| textColorPrimary | 0x01010036 | 0xffffffff | 0xde000000 |
| textColorSecondary | 0x01010038 | 0xb2ffffff | 0x8a000000 |
| textColorTertiary | 0x01010212 | 0xb3ffffff | 0x8a000000 |
| textColorPrimaryInverse | 0x01010039 | 0xde000000 | 0xffffffff |
| textColorSecondaryInverse | 0x0101003a | 0x8a000000 | 0xb3ffffff |
| textColorTertiaryInverse | 0x01010213 | 0x8a000000 | 0xb3ffffff |
| textColorHintInverse | 0x0101003f | 0xff000000 | 0xffffffff |
| textColorHint | 0x0101009a | 0xffffffff | 0xff000000 |
| colorForeground | 0x01010030 | 0xffffffff | 0xff000000 |
| colorForegroundInverse | 0x01010206 | 0xff000000 | 0xffffffff |
| colorBackground | 0x01010031 | 0xff303030 | 0xfffafafa |
| windowBackground | 0x01010054 | 0xff303030 | 0xfffafafa |
| windowFullscreen | 0x0101020d | 0x00000000 | 0x00000000 |
| navigationBarColor | 0x01010452 | 0xff000000 | 0xff000000 |
| statusBarColor | 0x01010451 | 0xff000000 | 0xff757575 |
| colorControlNormal | 0x01010429 | 0xb2ffffff | 0x8a000000 |
| colorControlActivated | 0x0101042a | 0xff80cbc4 | 0xff009688 |
| colorControlHighlight | 0x0101042c | 0xffffffff | 0xff000000 |
| disabledAlpha | 0x01010033 | 0x00002666 | 0x00002148 |

## Deferred (5)

| attr | reason |
|---|---|
| backgroundTint | dark=None→None light=None→None |
| windowActionBar | dark='@bool/config_windowActionBarSupported'→None light='@bool/config_windowActionBarSupported'→None |
| windowNoTitle | dark='@bool/config_windowNoTitleDefault'→None light='@bool/config_windowNoTitleDefault'→None |
| colorButtonNormal | dark='@color/btn_default_material_dark'→None light='@color/btn_default_material_light'→None |
| colorSwitchThumbNormal | no public id |
