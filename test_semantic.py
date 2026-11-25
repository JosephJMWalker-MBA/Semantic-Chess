import unittest
import chess
from semantic import Game, LOCATIONS, SIMILAR, lottery

class SemanticTests(unittest.TestCase):
    def fixture(self, fen, identities):
        g=Game()
        g.board=chess.Board(fen)
        g.ids={chess.parse_square(s):dict(id=s,name=n) for s,n in identities.items()}
        return g
    def test_lottery(self):
        for seed in range(20):
            a=lottery(seed)
            self.assertEqual(a,lottery(seed))
            self.assertEqual(len({x["code"] for x in a.values()}),64)
            positions={v["code"]:s for s,v in a.items()}
            for group in SIMILAR:
                present=[positions[c] for c in group if c in positions]
                for i,x in enumerate(present):
                    for y in present[i+1:]:
                        self.assertGreater(chess.square_distance(x,y),1)
        self.assertNotEqual(lottery(1),lottery(2))
    def test_mapping_history(self):
        g=Game(seed=42)
        layout=g.locations.copy()
        event=g.move("e2e4")
        self.assertEqual(event["origin"],layout[chess.E2]["name"])
        self.assertEqual(event["destination"],layout[chess.E4]["name"])
        self.assertEqual(g.locations,layout)
    def test_initial(self):
        g=Game()
        self.assertEqual(len(LOCATIONS),64)
        self.assertEqual(len(set(x["name"] for x in LOCATIONS.values())),64)
        self.assertEqual(len(set(x["name"] for x in g.ids.values())),32)
        self.assertEqual(len(g.state()["legal"]),20)
    def test_capture(self):
        g=Game()
        g.move("e2e4");g.move("d7d5");e=g.move("e4d5")
        self.assertEqual(e["captured"]["name"],"Sam")
        self.assertEqual(g.ids[chess.D5]["name"],"Eva")
    def test_promotion(self):
        for choice in "qrbn":
            g=self.fixture("7k/8/8/8/8/8/p7/7K b - - 0 1",{"h8":"Arthur","a2":"Jack","h1":"Henry"})
            original=g.ids[chess.A2].copy()
            g.move("a2a1"+choice)
            self.assertEqual(g.ids[chess.A1],original)
            self.assertTrue(next(s for s in g.state()["squares"] if s["square"]=="a1")["piece"]["self_actualized"])
    def test_castling(self):
        g=self.fixture("4k3/8/8/8/8/8/8/4K2R w K - 0 1",{"e8":"Arthur","e1":"Henry","h1":"Leo"})
        g.move("e1g1")
        self.assertEqual(g.ids[chess.F1]["name"],"Leo")
        self.assertEqual(g.ids[chess.G1]["name"],"Henry")
    def test_en_passant(self):
        g=Game()
        for m in ("e2e4","a7a6","e4e5","d7d5"):g.move(m)
        e=g.move("e5d6")
        self.assertEqual(e["captured"]["name"],"Sam")
        self.assertNotIn(chess.D5,g.ids)
    def test_illegal(self):
        g=Game();before=g.state()
        with self.assertRaises(ValueError):g.move("e2e5")
        self.assertEqual(before,g.state())

if __name__=="__main__":unittest.main()
