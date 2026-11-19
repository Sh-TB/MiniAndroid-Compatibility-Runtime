# CROSS-CODER INTEGRATION MATRIX (W20-K2)

Chain: DEX execution -> Framework contract -> Shadow state -> ViewTree ->
Layout -> Rendering -> Input -> State mutation -> Visible output.

| Chain stage | Cross-coder findings now ON HEAD | Test |
|---|---|---|
| DEX execution | E-02 arithmetic law (unsigned-width + MIN/-1) | battery |
| Framework contract | WS5 cursor law; WS6 adapter position law; E-02/H-04 | s248, s249 |
| Shadow state | WS7 dialog tokens; WS8 result default; WS9 flags; W14 F-NEW-722 | s250, s251, s252 |
| ViewTree | WS9 ViewNode activated/hovered | s252 |
| Rendering | WS9 pick_state_list first-match + real flag forwarding; drawRoundRect law | s252 + battery |
| Input | WS4A/B env-gated browser gesture forward | gated runs |
| State mutation | W14 result chain + WS8 default | s249/s251 |
| Visible output | SolCG bitmap-dims fallback; Frozen Options seeds; B-CORPUS laws | APK re-runs pending |

Integration risk legend: every ACCEPT/ALREADY_INTEGRATED row above has a
focused regression test on this lineage; source SHAs are in the CSV.

Highest-leverage shared-runtime improvements DELIVERED (multi-APK):
1. WS7 dialog lifecycle (every dialog app: first-paint setup + release hooks).
2. WS9 state-flag family (selected/activated UIs: openlauncher 17 call sites,
   stopwatch, opensudoku, tictactoe...).
3. WS8+WS14 result chain (every startActivityForResult app).
