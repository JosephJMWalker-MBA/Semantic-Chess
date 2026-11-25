"""Authoritative chess state and persistent semantic identities."""
import chess

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

NAMES = {7:"Rex Blake Carter Diana Arthur Elliot Graham Harris",
         6:"Jack Doug Fred Sam Luke Owen Max Ben",
         1:"Alice Beth Clara Daisy Eva Flora Grace Hope",
         0:"Miles Noah Caleb Eliza Henry Victor Ethan Leo"}

class Game:
    def __init__(self):
        self.board = chess.Board()
        self.ids = {sq: {"id": chess.square_name(sq), "name": NAMES[chess.square_rank(sq)].split()[chess.square_file(sq)]}
                    for sq in self.board.piece_map()}
        self.history = []

    def move(self, uci):
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
                     origin=LOCATIONS[src]["name"], destination=LOCATIONS[dst]["name"],
                     captured=captured.copy() if captured else None,
                     promotion=chess.piece_name(m.promotion) if m.promotion else None)
        if b.is_castling(m):
            rank = chess.square_rank(src)
            kingside = b.is_kingside_castling(m)
            rook_src = chess.square(7 if kingside else 0,rank)
            rook_dst = chess.square(5 if kingside else 3,rank)
            rook = self.ids.pop(rook_src)
            self.ids[rook_dst] = rook
            event["rook"] = dict(actor=rook.copy(), origin=LOCATIONS[rook_src]["name"], destination=LOCATIONS[rook_dst]["name"])
        if captured:
            self.ids.pop(capture_sq)
        self.ids.pop(src)
        self.ids[dst] = actor
        b.push(m)
        self.history.append(event)
        assert set(self.ids) == set(b.piece_map())
        return event

    def state(self):
        b = self.board
        outcome = b.outcome()
        return dict(fen=b.fen(), turn="white" if b.turn else "black",
                    check=b.is_check(), result=outcome.result() if outcome else None,
                    legal=[m.uci() for m in b.legal_moves] if not outcome else [],
                    squares=[dict(square=chess.square_name(s), **LOCATIONS[s],
                                  piece=dict(**self.ids[s], symbol=b.piece_at(s).symbol(),
                                             capability=chess.piece_name(b.piece_type_at(s)),
                                             self_actualized=bool(b.promoted & chess.BB_SQUARES[s]))
                                  if s in self.ids else None)
                             for s in sorted(LOCATIONS, key=lambda s: (-chess.square_rank(s),chess.square_file(s)))],
                    history=self.history)
