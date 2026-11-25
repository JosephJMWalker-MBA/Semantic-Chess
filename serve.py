"""Local-only, single-game HTTP server; client never adjudicates moves."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
from semantic import Game

game = Game()
class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, kind="application/json"):
        body = json.dumps(data).encode() if kind == "application/json" else data
        self.send_response(status)
        self.send_header("Content-Type",kind)
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path == "/api/state":
            self.reply(200,game.state())
        elif self.path == "/":
            self.reply(200,(Path(__file__).parent/"web"/"index.html").read_bytes(),"text/html; charset=utf-8")
        else:
            self.reply(404,{"error":"Not found"})
    def do_POST(self):
        global game
        try:
            if self.headers.get("Origin") not in (None,"http://127.0.0.1:8766"):
                raise ValueError("Invalid origin")
            if self.path == "/api/reset":
                game = Game()
            elif self.path == "/api/move":
                n = int(self.headers.get("Content-Length","0"))
                if not 0 < n <= 1024:
                    raise ValueError("Invalid body size")
                data = json.loads(self.rfile.read(n))
                game.move(data["uci"])
            else:
                self.reply(404,{"error":"Not found"})
                return
            self.reply(200,game.state())
        except (ValueError, KeyError, TypeError) as e:
            self.reply(400,{"error":str(e)})
if __name__ == "__main__":
    print("Semantic Chess: http://127.0.0.1:8766")
    HTTPServer(("127.0.0.1",8766),Handler).serve_forever()
