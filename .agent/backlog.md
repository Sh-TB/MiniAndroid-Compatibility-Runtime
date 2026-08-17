# Backlog

## P0 — Login Path
- [ ] Forensic PC trace of LaunchActivity.onCreate PC 678-730
- [ ] Determine why getFragmentStack() returns null
- [ ] Fix root cause (smallest generic fix)
- [ ] Reach getClientNotActivatedFragment()
- [ ] Reach LoginActivity construction
- [ ] Reach addFragmentToStack()

## P1 — Resources
- [ ] Cross-check R class values with androguard
- [ ] Implement resources.arsc parser if needed

## P2 — Exception
- [ ] Typed catch handler (class hierarchy walk)
- [ ] Exception propagation across method boundaries

## P3 — Fragment
- [ ] Minimal Fragment lifecycle (onCreate, onCreateView)
- [ ] INavigationLayout.addFragmentToStack dispatch
