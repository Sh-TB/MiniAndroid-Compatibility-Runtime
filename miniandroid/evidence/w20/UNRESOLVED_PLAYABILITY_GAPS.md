# UNRESOLVED PLAYABILITY GAPS — W20 (cODER-ohc transfer + corpus)

Status vocabulary: LAUNCH RENDER / COMPLETE RENDER / INPUT DISPATCH /
LOGICAL MUTATION / VISIBLE MUTATION / DETERMINISTIC ×N / FULL GAMEPLAY.

## 1. 2048 (com.uberspot.a2048) — WS4/WS4B frontier
| Stage | State |
|---|---|
| Launch render | ✅ complete (board paints, 438 colors) |
| Input dispatch | ✅ WITH the two env gates: touchstart×2 → touchmove×12 → touchend, 0 JS errors (was 16 TypeErrors) |
| Logical mutation | ✅ emit("move") → GameManager.move → grid `0200|0000|0000|2200` (coder's live trace) |
| Visible mutation | ❌ **BLOCKED — WS4B** |
Determinism: ✅ (screens byte-identical on/off gates).
**Gap**: HTMLActuator DOM writes → computed layout → paint invalidation →
surface blit never happens: the WebView DOM mutates but the raster is not
re-derived. Also secondary: `position:absolute` grid-container computes
106×1741 instead of 500×500 (block-sizing law for absolutely-positioned
containers). **2048 must NOT be claimed playable until a real swipe visibly
changes the board.** Both gates default-OFF (byte-identical pristine).

## 2. TicTacToe Classic (com.emmanuelmess.tictactoe) — GAME-011
| Stage | State |
|---|---|
| Launch render | ✅ real libGDX board (5 glDrawArrays, 4 tex uploads) |
| Input dispatch | ❌ tap path throws `FileNotFoundException: assets/i18n/TicTacToe_en_US.properties` → GdxRuntimeException → DEFAULT_BACKGROUND_ONLY |
Deterministic ×3 (7354c1b2…).
**Gap**: AssetManager.open for i18n properties INSIDE the libGDX Natives
jar (the assets live in the APK + a nested jar face — asset resolver must
fall back to the libGDX classpath convention). Blocks tap-to-play.

## 3. SolitaireCG (net.sourceforge.solitaire_cg) — GAME-090
| Stage | State |
|---|---|
| Launch render | ✅ (splash by-design; WS2.02) |
| Board | coder's later PLAY-wave run hit createBitmap(w=0,h=-1) IAE at DrawMaster.DrawPortraitCards |
| This wave | bitmap-dims fallback integrated (getIntrinsic → __dr_bitmap__ → __bmp_width__/__bmp_height__); re-verification run queued |
**Remaining**: if the fallback resolves the card drawables, the board must
be re-proven (tap → board sha, 3× deterministic) before any status upgrade.

## 4. uNote (app.varlorg.unote) — APP-002
Launch render ✅ (full list chrome, 3 real buttons) · ListView EMPTY
(children=0) · editor unverified. **Gap**: no persisted note rows exist in
a fresh data-root and no CreateNote flow driven; needs a real tap-driven
note-creation pass (Add note → editor → save → list rebind via the WS6/
Adapter laws this wave fixed).

## 5. Notes/billthefarmer (org.billthefarmer.notes) — APP-006
Launch render: near-blank (only an ImageButton icon; MarkdownView draws
nothing despite 183/187 census). **Gap**: MarkdownView is a WebView-family
custom view — its content pipeline (loadData with markdown → DOM → paint)
needs the WS4B paint path too; clicks dispatched but no frame change.

## 6. Frozen Bubble (org.jfedor.frozenbubble) — bonus
Real GL content ✅ (37,988 distinct colors) · inScaled NSFE absorbed by the
app's own handler; NOW the Options fields are registered (deferred-exception
honesty gap removed — run should reach cleaner exit status). **Remaining**:
gameplay interaction (tap/aim/shoot) unvalidated; status upgrade only after
a visible state-change run ×3.

## 7. Corpus apps with in-app exceptions (7 APKs, W20 census)
janken, itsfrz tictactoe, authsrng, minos, chess, tallybook, gaskell dicer —
each renders a screenshot but carries 2 uncaught in-flight exceptions
(first-divergence logs in evidence/w20/corpus/<name>/run.log). These stay
investigation subjects; correctness recovery must NOT replace the runtime
performance objective.

## Highest-leverage next workstreams
1. **WS4B — DOM mutation → repaint** (unblocks 2048 visible play + Notes
   MarkdownView + any WebView-content app): one shared paint-invalidation
   path.
2. **libGDX asset resolver fallback** (unblocks TicTacToe tap-to-play and
   other libGDX titles).
3. **Adapter rebind on real data** (uNote list rows ride the WS6 contract
   now integrated).
