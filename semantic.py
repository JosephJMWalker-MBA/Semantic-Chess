"""Authoritative chess state and persistent semantic identities."""
import chess
import chess.pgn
import random
import secrets

ROWS = [
"US:America CA:Canada MX:Mexico BR:Brazil GB-ENG:England FR:France DE:Germany IT:Italy",
"ES:Spain PT:Portugal NL:Netherlands BE:Belgium CH:Switzerland SE:Sweden NO:Norway FI:Finland",
"PL:Poland UA:Ukraine RU:Russia TR:Turkey GR:Greece EG:Egypt DZ:Algeria MA:Morocco",
"TN:Tunisia LY:Libya KE:Kenya ET:Ethiopia NG:Nigeria ZA:South_Africa SA:Saudi_Arabia IR:Iran",
"IL:Israel IQ:Iraq IN:India CN:China JP:Japan KR:South_Korea ID:Indonesia PH:Philippines",
"VN:Vietnam TH:Thailand MY:Malaysia SG:Singapore AU:Australia NZ:New_Zealand PG:Papua_New_Guinea FJ:Fiji",
"AR:Argentina CL:Chile PE:Peru CO:Colombia VE:Venezuela BO:Bolivia UY:Uruguay PY:Paraguay",
"IE:Ireland GB-WLS:Wales GB-SCT:Scotland DK:Denmark IS:Iceland AT:Austria HU:Hungary RO:Romania"]
LOCATIONS = {}
for row, line in enumerate(ROWS):
    for col, item in enumerate(line.split()):
        code, name = item.split(":")
        LOCATIONS[chess.square(col, 7-row)] = dict(code=code.lower(), name=name.replace("_"," "))

# Curated visual-confusion groups; avoid edge AND corner adjacency.
SIMILAR = [
    {"au","nz","fj"}, {"co","ve","ec"}, {"id","pl","sg"},
    {"ro","td"}, {"ie","it","mx"}, {"nl","ru","py"},
    {"hu","ir","bg"}, {"no","is","dk","fi","se"},
    {"eg","iq","sy"}, {"ma","tr","tn"}, {"jp","bd"},
]
def lottery(seed):
    rng = random.Random(seed)
    entries = list(LOCATIONS.values())
    for _ in range(10000):
        rng.shuffle(entries)
        layout = dict(zip(chess.SQUARES, entries))
        positions = {value["code"]: sq for sq,value in layout.items()}
        groups = [[positions[c] for c in sorted(group) if c in positions] for group in SIMILAR]
        if all(chess.square_distance(a,b) > 1 for group in groups
               for i,a in enumerate(group) for b in group[i+1:]):
            return {sq: dict(value) for sq,value in layout.items()}
    raise RuntimeError("Unable to produce separated flag layout")

NAMES = {7:"Rex Blake Carter Diana Arthur Elliot Graham Harris",
         6:"Jack Doug Fred Sam Luke Owen Max Ben",
         1:"Alice Beth Clara Daisy Eva Flora Grace Hope",
         0:"Miles Noah Caleb Eliza Henry Victor Ethan Leo"}

class Game:
    def __init__(self, seed=None, opponent="human", difficulty="standard"):
        if seed is not None and (type(seed) is not int or not 0 <= seed < 2**32):
            raise ValueError("Invalid lottery seed")
        if opponent not in ("human", "stockfish"):
            raise ValueError("Invalid opponent")
        if difficulty not in ("casual", "standard", "challenge"):
            raise ValueError("Invalid difficulty")
        self.difficulty = difficulty
        self.seed = secrets.randbits(32) if seed is None else seed
        self.locations = lottery(self.seed)
        self.opponent = opponent
        self.board = chess.Board()
        self.ids = {sq: {"id": chess.square_name(sq), "name": NAMES[chess.square_rank(sq)].split()[chess.square_file(sq)]}
                    for sq in self.board.piece_map()}
        self.history = []

    def move(self, uci):
        if not isinstance(uci, str):
            raise ValueError('Expected move notation')
        m = chess.Move.from_uci(uci)
        b = self.board
        if b.is_game_over() or m not in b.legal_moves:
            raise ValueError("Illegal move or game over")
        src, dst = m.from_square, m.to_square
        actor = self.ids[src]
        capture_sq = dst
        if b.is_en_passant(m):
            capture_sq = dst - 8 if b.turn else dst + 8
        captured = self.ids.get(capture_sq) if b.is_capture(m) else None
        event = dict(uci=uci, san=b.san(m), actor=actor.copy(),
                     origin=self.locations[src]["name"], destination=self.locations[dst]["name"],
                     captured=captured.copy() if captured else None,
                     promotion=chess.piece_name(m.promotion) if m.promotion else None)
        if b.is_castling(m):
            rank = chess.square_rank(src)
            kingside = b.is_kingside_castling(m)
            rook_src = chess.square(7 if kingside else 0,rank)
            rook_dst = chess.square(5 if kingside else 3,rank)
            rook = self.ids.pop(rook_src)
            self.ids[rook_dst] = rook
            event["rook"] = dict(actor=rook.copy(), origin=self.locations[rook_src]["name"], destination=self.locations[rook_dst]["name"])
        if captured:
            self.ids.pop(capture_sq)
        self.ids.pop(src)
        self.ids[dst] = actor
        b.push(m)
        self.history.append(event)
        assert set(self.ids) == set(b.piece_map())
        return event

    def record(self):
        """Portable versioned record; history is derived by legal replay."""
        return dict(version=1, seed=self.seed, opponent=self.opponent,
                    difficulty=self.difficulty,
                    layout={chess.square_name(s): v["code"] for s,v in self.locations.items()},
                    moves=[e["uci"] for e in self.history])

    @classmethod
    def from_record(cls, record):
        if not isinstance(record, dict) or type(record.get("version")) is not int or record["version"] != 1:
            raise ValueError("Unsupported game record")
        seed = record["seed"]
        if type(seed) is not int or not 0 <= seed < 2**32:
            raise ValueError("Invalid saved seed")
        game = cls(seed, record["opponent"], record["difficulty"])
        layout = record["layout"]
        by_code = {v["code"]:v for v in LOCATIONS.values()}
        if (not isinstance(layout, dict) or set(layout) != set(chess.SQUARE_NAMES)
                or any(not isinstance(v,str) for v in layout.values())
                or set(layout.values()) != set(by_code)):
            raise ValueError("Invalid saved layout")
        game.locations = {chess.parse_square(s):dict(by_code[c]) for s,c in layout.items()}
        moves = record["moves"]
        if not isinstance(moves, list) or len(moves)>18000:
            raise ValueError("Invalid move history")
        for move in moves:
            game.move(move)
        return game

    def undo(self):
        if not self.history:
            raise ValueError("No moves to undo")
        record = self.record()
        # Against Stockfish return to the previous human decision.
        count = 2 if self.opponent == "stockfish" and self.board.turn and len(self.history)>1 else 1
        record["moves"] = record["moves"][:-count]
        return self.from_record(record)

    def pgn(self):
        game = chess.pgn.Game.from_board(self.board)
        game.headers["Event"] = "Semantic Chess"
        game.headers["White"] = "Human / White"
        game.headers["Black"] = "Stockfish" if self.opponent=="stockfish" else "Human / Black"
        game.headers["SemanticSeed"] = str(self.seed)
        return str(game) + "\n"

    def state(self):
        b = self.board
        outcome = b.outcome()
        return dict(seed=self.seed, opponent=self.opponent, difficulty=self.difficulty, fen=b.fen(), turn="white" if b.turn else "black",
                    check=b.is_check(), result=outcome.result() if outcome else None,
                    termination=outcome.termination.name.lower().replace("_"," ") if outcome else None,
                    legal=[m.uci() for m in b.legal_moves] if not outcome else [],
                    squares=[dict(square=chess.square_name(s), **self.locations[s],
                                  piece=dict(**self.ids[s], symbol=b.piece_at(s).symbol(),
                                             capability=chess.piece_name(b.piece_type_at(s)),
                                             self_actualized=bool(b.promoted & chess.BB_SQUARES[s]))
                                  if s in self.ids else None)
                             for s in sorted(self.locations, key=lambda s: (-chess.square_rank(s),chess.square_file(s)))],
                    history=self.history)
