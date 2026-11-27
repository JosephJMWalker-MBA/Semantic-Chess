import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import chess
from semantic import Game
from session import Session, StaleState

def move(uci):
    def apply(game):
        game.move(uci)
        return game
    return apply

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)/"save.json"
        self.session=Session(self.path)

    def play(self,*moves):
        for uci in moves:
            self.session.transact(self.session.revision,move(uci))

    def test_round_trip_capture(self):
        self.play("e2e4","d7d5","e4d5")
        loaded=Session(self.path)
        self.assertEqual(loaded.game.state(),self.session.game.state())
        self.assertEqual(loaded.game.ids[chess.D5]["name"],"Eva")
        self.assertEqual(loaded.game.history[-1]["captured"]["name"],"Sam")

    def test_stale_rejected(self):
        old=self.session.revision
        self.play("e2e4")
        before=self.path.read_bytes()
        with self.assertRaises(StaleState):
            self.session.transact(old,move("d7d5"))
        self.assertEqual(self.path.read_bytes(),before)

    def test_failed_save_retains_state(self):
        before=self.session.state()
        disk=self.path.read_bytes()
        with patch("session.os.replace",side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.play("e2e4")
        self.assertEqual(self.session.state(),before)
        self.assertEqual(self.path.read_bytes(),disk)

    def test_invalid_save_preserved(self):
        self.path.write_text("bad json")
        with self.assertRaises(RuntimeError):
            Session(self.path)
        self.assertEqual(self.path.read_text(),"bad json")

    def test_undo_restores_captured_identity(self):
        self.play("e2e4","d7d5","e4d5")
        g=self.session.game.undo()
        self.assertEqual(g.ids[chess.D5]["name"],"Sam")
        self.assertEqual(g.ids[chess.E4]["name"],"Eva")
        self.assertEqual(g.locations,self.session.game.locations)

    def test_stockfish_undo_pair(self):
        g=Game(seed=42,opponent="stockfish",difficulty="casual")
        g.move("e2e4")
        self.assertFalse(g.undo().history)
        g.move("e7e5")
        self.assertFalse(g.undo().history)

    def test_saved_layout_validation(self):
        r=self.session.game.record()
        r["layout"]["a1"]=r["layout"]["b1"]
        with self.assertRaises(ValueError):
            Game.from_record(r)

    def test_pgn_and_export(self):
        self.play("e2e4","e7e5")
        g=self.session.game
        self.assertIn("1. e4 e5",g.pgn())
        self.assertEqual(Game.from_record(json.loads(json.dumps(g.record()))).state(),g.state())
