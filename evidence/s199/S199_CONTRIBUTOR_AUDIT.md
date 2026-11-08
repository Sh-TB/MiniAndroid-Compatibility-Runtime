# S199 CONTRIBUTOR AUDIT (Coders 2–9) — verified integration states

Recorded: 2026-11-08 20:03 UTC. Statuses use the S199 evidence-state vocabulary. "Independent
reproduction" = behavior observed on the S199 canonical binary 97628b00d237f9eb.

## Coder 3 (UI execution / ViewTree / adapter / native GL) — the P0 chain
| Contribution | Original claim | Independent reproduction on 97628b00d237f9eb | Integration state | App impact |
|---|---|---|---|---|
| S196 F-NEW-580/580b String-boundary | AssetManager.load NPE dies at desc.fileName.equals(null) after replaceAll stub | Ported verbatim; `npe_asset_load` count went 1 → 0 on tictactoe | **INTEGRATED + BUILD-VERIFIED + APP-OBSERVED** | tictactoe passes AssetDescriptor/I18NBundle ladder |
| S196 F-NEW-588 replace family | replaceAll("\\\\","/") answered null → null fileName | 6 live replaceAll calls logged; `i18n/TicTacToe` path built correctly | INTEGRATED, UNIT-OBSERVED | the named NPE chain closed |
| S196 F-NEW-589 Stack LIFO | Stack.size answered 0 → AssetManager.update believed queue empty | 19–22 live Stack.push/pop/size calls driving the async loader | INTEGRATED | font asset task actually runs |
| S196 F-NEW-582/582b direct-buffer family | copyJni faulted on NULL addresses | copyJni 5-arg live (font bytes stream into REAL memory, chunks 0..+28672) | INTEGRATED | FreeType font parses from REAL registered memory |
| S196 F-NEW-581 loadLibrary NOT-EXTRACTED | host-native not found when APK lib unextracted | SUPERSEDED: this line's S183/B1 host-native-first law already covers the shape (current code attempts host-native before any APK .so attempt) | SUPERSEDED (recorded in #557 reply) | — |
| S198a/b GLES raster + marshal | GL calls execute but nothing rasterizes | draws dispatch (GL_TRIANGLES 66/30/6/12), attribs coherent after F-NEW-616 | INTEGRATED (with the S199 parent-first fix) | font glyphs rasterize end-to-end |
| S198c F-NEW-610 typed-view setters | floatBuffer.position(3) lost → texcoord pointer at 0 | ported from the truncated tail; position/limit setters live | INTEGRATED | attribute offsets correct (attrib2 = base+12) |

## S199 additions the audit surfaced as REQUIRED for the chain
| Law | First divergence it closes |
|---|---|
| F-NEW-615 | Gdx2DPixmap.<init> "Error loading pixmap." on the SPACE glyph (empty outline → 0-cap NewDirectByteBuffer) |
| F-NEW-616/616b/616c/616d | three zeroed attribute pointers (typed views resolved through the view snapshot instead of the parent's real memory); shader COMPILE_STATUS read back 0 |
| F-NEW-617 | mesh vertex data never written (4-arg copyJni missing; Mesh.setVertices path dead) |
| F-NEW-618 | u_projTrans m33 = 1.06535e9 (F-028 raw-bits element read numerically cast) |

## Coder 4 (framework laws) — W17/F-C4-631
- F-C4-631 (provider authority via resource reference): verified ABSENT from
  origin/main in S195 (#566 6725597661 intake). Not touched this wave;
  remains intake (PENDING) — no caller in the current cohort failed on it
  this wave, so no independent reproduction exists yet.
- W17 F-NEW-601..604 remain INTEGRATED/REGRESSION-VERIFIED (goldens hold).

## Coder 9 (resources) — S195/S192 npTc
- npTc patch verified TRUE for origin/main but SUPERSEDED-by-f053 on this
  line (#521 6725597895). No regression: floor 11/11 holds. State stays
  SUPERSEDED; the C9 asset/ARSC chain is INTEGRATED (ARSC label + drawable
  resolution live in the tictactoe run).

## Coder 7 (components/SQLite), Coder 8 (concurrency), Coder 6 (native EGL),
## Coder 2 (corpus), Coder 5 (research)
- C8 W11+W12 97/97 probe: NOT rerun this wave (P0 consumed the budget) —
  PENDING on the S199 binary; the W11/W12 regression surface is covered by
  the floor battery (all HOLD).
- C7 SQLite impact audit: see S199_SQLITE_IMPACT.md (semantic coverage
  audit only — no cross-app claim made).
- C6 Mindustry composite gap: stays OPEN by law (mission §2 C6) — no new
  GL system was created; the S199 identity work advances the shared chain.


## NOTE — identity refresh (S199 close)
The S199 wave made two further source commits after the baseline was
written (F-NEW-619 typed-view parent chase at the f590 hook; F-NEW-620/
620b GL_ACTIVE_ATTRIBUTES=3 + glGetActiveAttrib canonical-name law).
The FINAL canonical S199 binary is 97628b00d237f9eb — goldens 3/3 ALL
HOLD and floor 11/11 CLEAN re-verified on it (this is the identity all
future waves compare against). The 619/620 laws did NOT yet move the
shape-attrib needle (glGetActiveAttrib never dispatched — the
fetchAttributes loop is gated deeper, at the AndroidGL20 real-native
path); that remains the named Coder-3 frontier with the evidence above.
