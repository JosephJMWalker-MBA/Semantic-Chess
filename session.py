"""Transactional local session persistence. Never overwrite unreadable saves."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4
from semantic import Game

class StaleState(ValueError):
    pass

class Session:
    def __init__(self, path):
        self.path = Path(path)
        self.revision = uuid4().hex
        if self.path.exists():
            try:
                self.game = Game.from_record(json.loads(self.path.read_text(encoding="utf-8")))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                raise RuntimeError(f"Cannot load {self.path}; original save preserved: {exc}") from exc
        else:
            self.game = Game()
            self._save(self.game)

    def _save(self, game):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent, delete=False) as f:
                temporary = Path(f.name)
                json.dump(game.record(), f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def state(self):
        return dict(self.game.state(), revision=self.revision)

    def transact(self, revision, operation):
        if revision != self.revision:
            raise StaleState("Game changed in another request; refreshed state. Retry your move.")
        candidate = operation(deepcopy(self.game))
        self._save(candidate)
        self.game = candidate
        self.revision = uuid4().hex
        return self.state()
