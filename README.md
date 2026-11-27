# Semantic Chess

Same game. Same mathematics. Different ontology.

A standard chess environment with persistent named characters and 64 named flag locations. Inspired by Crownline's authoritative engine and evidence-driven development. Promotion changes capabilities, never identity.

Prototype v0.4: local two-player or Stockfish browser game; Python rules engine using python-chess. No AI strength or semantic-learning claims are established.

Run `python3 -m pip install -r requirements.txt`, then `python3 serve.py` and open http://127.0.0.1:8766. Run `python3 -m unittest discover -v` for tests.

See RULES.md for representation and research boundaries.

## v0.2
- New game draws a seeded flag lottery; similar flag groups cannot touch, even diagonally. Seed is visible and accepted by reset API for reproduction.
- Flag labels: always, hover/keyboard focus, or hidden. Responsive board uses viewport and container sizing.
- Voice: click Listen in a supporting browser, allow microphone, say "Eva to Japan" (choose an actually legal destination), review and confirm. Typed commands use the same parser. Browser speech recognition may use an external service; no continuous listening. For promotion say "Jack to America as queen" where legal.
- Stockfish: on macOS run `brew install stockfish`; select Stockfish (Black) and New game. Set STOCKFISH_PATH if not on PATH. The human plays White; engine moves use the selected difficulty preset. Engine failure is explicit and retryable; no silent fallback. 

## v0.3 — 3D tabletop
Choose Board view → 3D tabletop. The original 2D view remains available without resetting the game or lottery. Procedural Three.js meshes, lighting, shadows, flag textures, selectable pieces and legal destination rings are presentation-only. Drag to orbit; scroll or pinch to zoom; flip, overhead and reset-camera controls are available. Flag label visibility applies in both views. Use 2D for keyboard square selection. Three.js is loaded from a pinned CDN version (same version as Crownline); WebGL and internet are required for 3D. Failed initialization falls back to 2D. Restart the local Python server after updating to enable the JS route. Browser/GPU visual and interaction validation is pending.

## v0.4 — durable gameplay
- The local server autosaves the current game after every successful mutation and resumes it on restart. The default save is .semantic-chess/session.json (ignored by Git); SEMANTIC_SAVE_PATH overrides it. Do not run multiple servers against one save. An invalid save blocks startup without overwriting the file.
- Undo replays the prior legal history, preserving identities, promotions, captures and flag mapping. In Stockfish mode undo returns to the preceding human turn where possible.
- Export standard PGN for conventional analysis or versioned JSON for exact semantic replay (layout, seed and moves). JSON import UI is not implemented. Reset replaces the current save; export first to archive. Replay this layout starts a new game with the same seed.
- Stockfish presets: Casual skill 2 / 150 ms, Standard skill 10 / 250 ms, Challenge skill 20 / 750 ms. These are not calibrated Elo ratings. Settings apply on new game.
- Last move blue, selection gold, legal destination green, capture destination amber. Both views use authoritative state.
- Stale mutations from other tabs are rejected; the client refreshes state before retrying.
- Run tests locally with `python3 -m unittest discover -v`. Browser/GPU and microphone testing remain manual.
