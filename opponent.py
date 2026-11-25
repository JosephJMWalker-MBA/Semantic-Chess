"""Optional Stockfish UCI opponent, with explicit failure rather than silent substitution."""
import os
import shutil
import chess.engine

def engine_path():
    return os.environ.get("STOCKFISH_PATH") or shutil.which("stockfish")

def computer_move(board):
    path = engine_path()
    if not path:
        raise ValueError("Stockfish not found. Install it or set STOCKFISH_PATH.")
    try:
        with chess.engine.SimpleEngine.popen_uci(path, timeout=5) as engine:
            result = engine.play(board, chess.engine.Limit(time=0.25))
        if result.move not in board.legal_moves:
            raise ValueError("Engine returned no legal move")
        return result.move.uci()
    except (OSError, chess.engine.EngineError, TimeoutError) as exc:
        raise ValueError("Stockfish unavailable: " + str(exc)) from exc
