"""Optional Stockfish UCI opponent, with explicit failure rather than silent substitution."""
import os
import shutil
import chess.engine

def engine_path():
    return os.environ.get("STOCKFISH_PATH") or shutil.which("stockfish")

PRESETS = {"casual": (2, .15), "standard": (10, .25), "challenge": (20, .75)}

def computer_move(board, difficulty="standard"):
    path = engine_path()
    if not path:
        raise ValueError("Stockfish not found. Install it or set STOCKFISH_PATH.")
    try:
        skill, seconds = PRESETS[difficulty]
        with chess.engine.SimpleEngine.popen_uci(path, timeout=5) as engine:
            if "Skill Level" not in engine.options:
                raise ValueError("Engine does not expose Stockfish Skill Level")
            engine.configure({"Skill Level":skill})
            result = engine.play(board, chess.engine.Limit(time=seconds))
        if result.move not in board.legal_moves:
            raise ValueError("Engine returned no legal move")
        return result.move.uci()
    except (OSError, chess.engine.EngineError, TimeoutError) as exc:
        raise ValueError("Stockfish unavailable: " + str(exc)) from exc
