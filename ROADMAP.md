# Semantic Chess — development stewardship

## Invariants
- Canonical legal chess; labels never change movement or results.
- Stable character identity through capability changes.
- Seeded flag topology fixed per game.
- Python remains authoritative; 2D, 3D, and speech are clients.
- Research claims require measured, reproducible evidence.

## Sequence
1. Reliability: persistence, undo, exports, stale-state rejection and automated regression coverage (v0.4 implementation).
2. Playability: verify real browser/GPU and voice interactions; optimize name placement and capture/last-move feedback; improve keyboard and mobile controls.
3. Learning modes: optional flag recall exercises, progressive concealment and location search.
4. Research: versioned experimental protocols contrasting entity and location semantics; preserve null results; no alteration of chess rules without explicit new research scope.

## Admission
Committed code is not evidence of runtime correctness. Record test results and browser playtest observations before declaring releases validated. No telemetry or external publication by default.
