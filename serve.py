"""Local-only, single-game HTTP server; client never adjudicates moves."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import os
from semantic import Game
from session import Session, StaleState
from opponent import computer_move, engine_path

ROOT=Path(__file__).parent
session=None

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, kind="application/json", download=None):
        body=json.dumps(data).encode() if kind=="application/json" else data
        self.send_response(status)
        self.send_header("Content-Type",kind)
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        if download:
            self.send_header("Content-Disposition",f'attachment; filename="{download}"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path=="/api/state":
            self.reply(200,session.state())
        elif self.path=="/api/export/json":
            data=json.dumps(session.game.record(),indent=2).encode()
            self.reply(200,data,"application/json; charset=utf-8","semantic-chess.json")
        elif self.path=="/api/export/pgn":
            self.reply(200,session.game.pgn().encode(),"application/x-chess-pgn","semantic-chess.pgn")
        elif self.path in ("/","/web/board3d.js"):
            name,kind=("index.html","text/html; charset=utf-8") if self.path=="/" else ("board3d.js","text/javascript; charset=utf-8")
            self.reply(200,(ROOT/"web"/name).read_bytes(),kind)
        else:
            self.reply(404,{"error":"Not found"})

    def do_POST(self):
        try:
            if self.headers.get("Origin") not in (None,"http://127.0.0.1:8766"):
                raise ValueError("Invalid origin")
            n=int(self.headers.get("Content-Length","0"))
            if not 0<n<=1024:
                raise ValueError("Invalid body size")
            data=json.loads(self.rfile.read(n))
            if not isinstance(data,dict):
                raise ValueError("Expected JSON object")
            def operation(game):
                if self.path=="/api/reset":
                    opponent=data.get("opponent","human")
                    if opponent=="stockfish" and not engine_path():
                        raise ValueError("Install Stockfish first (brew install stockfish)")
                    return Game(seed=data.get("seed"),opponent=opponent,difficulty=data.get("difficulty","standard"))
                if self.path=="/api/undo":
                    return game.undo()
                if self.path=="/api/move":
                    if game.opponent=="stockfish" and not game.board.turn:
                        raise ValueError("It is the computer's turn")
                    game.move(data["uci"])
                elif self.path=="/api/computer":
                    if game.opponent!="stockfish" or game.board.turn or game.board.is_game_over():
                        raise ValueError("No computer move due")
                    game.move(computer_move(game.board,game.difficulty))
                return game
            if self.path not in ("/api/reset","/api/undo","/api/move","/api/computer"):
                self.reply(404,{"error":"Not found"})
                return
            self.reply(200,session.transact(data.get("revision"),operation))
        except StaleState as e:
            self.reply(409,{"error":str(e),"state":session.state()})
        except (ValueError,KeyError,TypeError) as e:
            self.reply(400,{"error":str(e)})
        except OSError:
            self.reply(500,{"error":"Could not save game; previous state retained."})

if __name__=="__main__":
    session=Session(os.environ.get("SEMANTIC_SAVE_PATH") or ROOT/".semantic-chess"/"session.json")
    print("Semantic Chess: http://127.0.0.1:8766")
    HTTPServer(("127.0.0.1",8766),Handler).serve_forever()
