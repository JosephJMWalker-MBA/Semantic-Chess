# Semantic Chess

Same game. Same mathematics. Different ontology.

A standard chess environment with persistent named characters and 64 named flag locations. Inspired by Crownline's authoritative engine and evidence-driven development. Promotion changes capabilities, never identity.

Prototype v0.2: local two-player or Stockfish browser game; Python rules engine using python-chess. No AI strength or semantic-learning claims are established.

Run `python3 -m pip install -r requirements.txt`, then `python3 serve.py` and open http://127.0.0.1:8766. Run `python3 -m unittest discover -v` for tests.

See RULES.md for representation and research boundaries.

## v0.2
- New game draws a seeded flag lottery; similar flag groups cannot touch, even diagonally. Seed is visible and accepted by reset API for reproduction.
- Flag labels: always, hover/keyboard focus, or hidden. Responsive board uses viewport and container sizing.
- Voice: click Listen in a supporting browser, allow microphone, say "Eva to Japan" (choose an actually legal destination), review and confirm. Typed commands use the same parser. Browser speech recognition may use an external service; no continuous listening. For promotion say "Jack to America as queen" where legal.
- Stockfish: on macOS run `brew install stockfish`; select Stockfish (Black) and New game. Set STOCKFISH_PATH if not on PATH. The human plays White; engine moves are limited to 250 ms search time. Engine failure is explicit and retryable; no silent fallback. 

## v0.3 — 3D tabletop
Choose Board view → 3D tabletop. The original 2D view remains available without resetting the game or lottery. Procedural Three.js meshes, lighting, shadows, flag textures, selectable pieces and legal destination rings are presentation-only. Drag to orbit; scroll or pinch to zoom; flip, overhead and reset-camera controls are available. Flag label visibility applies in both views. Use 2D for keyboard square selection. Three.js is loaded from a pinned CDN version (same version as Crownline); WebGL and internet are required for 3D. Failed initialization falls back to 2D. Restart the local Python server after updating to enable the JS route. Browser/GPU visual and interaction validation is pending.
