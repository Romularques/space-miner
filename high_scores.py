"""Persistência e ordenação do placar local."""

import json
from pathlib import Path
from time import time_ns


class HighScores:
    """Mantém os dez melhores resultados, inclusive entre execuções."""

    LIMIT = 10

    def __init__(self) -> None:
        # Junto ao jogo: funciona em uma instalação portátil sem depender do Windows.
        data_dir = Path(__file__).resolve().parent / "data"
        self.path = data_dir / "high_scores.json"
        self.scores = self._load()

    @staticmethod
    def _sort_key(entry: dict[str, object]) -> tuple[int, int, int]:
        # A ordenação reversa atende: mais pontos, fase mais alta e resultado mais recente.
        return (int(entry["score"]), int(entry["phase"]), int(entry["timestamp"]))

    def _load(self) -> list[dict[str, object]]:
        try:
            with self.path.open(encoding="utf-8") as file:
                entries = json.load(file)
            if not isinstance(entries, list):
                return []
            valid = [
                entry for entry in entries
                if isinstance(entry, dict)
                and isinstance(entry.get("initials"), str)
                and len(entry["initials"]) == 3
                and all(key in entry for key in ("score", "phase", "timestamp"))
            ]
            return sorted(valid, key=self._sort_key, reverse=True)[:self.LIMIT]
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []

    def qualifies(self, score: int, phase: int) -> bool:
        candidate = {"score": score, "phase": phase, "timestamp": time_ns()}
        ranked = sorted([*self.scores, candidate], key=self._sort_key, reverse=True)[:self.LIMIT]
        return candidate in ranked

    def add(self, initials: str, score: int, phase: int) -> None:
        entry = {
            "initials": initials.upper(),
            "score": score,
            "phase": phase,
            "timestamp": time_ns(),
        }
        self.scores = sorted([*self.scores, entry], key=self._sort_key, reverse=True)[:self.LIMIT]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(self.scores, file, ensure_ascii=False, indent=2)
        temporary_path.replace(self.path)
