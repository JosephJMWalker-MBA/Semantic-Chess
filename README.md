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
