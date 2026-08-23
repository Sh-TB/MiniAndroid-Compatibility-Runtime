# EXP-067 Mission

**Goal:** Turn the proven Telegram Login path into a real, rendered, interactive Login screen while building generic Android compatibility infrastructure.

**Exit criteria (summarized):**
- VM: no generic interpreter corruption, exception semantics classified, arrays/fields/wide ops pass
- Resources: strings/colors/dimens/drawables/references resolve correctly with deterministic config selection
- UI: AXML parsing, LayoutInflater, setContentView, measure/layout, View inheritance, EditText, click dispatch, screenshot from generic tree
- Telegram: LoginActivity→PhoneView→phone label→country field→phone EditText→Next button→synthetic input→mock auth→SMS screen
- Genericity: at least one non-Telegram XML-heavy APK + one persistence APK + one JNI app reach first screen
- Evidence: 3-run reproducibility, screenshot SHA256, complete EXP report, GitHub commit/push

**Stop conditions:**
- All exit criteria met, OR
- A hard external dependency is proven (record evidence)

**Autonomous policy:** Do not stop after one fix. Identify next blocker, investigate, fix, test, continue.
