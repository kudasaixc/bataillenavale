from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

Coordinate = Tuple[int, int]


@dataclass
class Ship:
    name: str
    length: int
    coordinates: Set[Coordinate]
    hits: Set[Coordinate] = field(default_factory=set)

    def register_hit(self, coord: Coordinate) -> str:
        self.hits.add(coord)
        if self.is_sunk:
            return "touché-coulé"
        return "touché"

    @property
    def is_sunk(self) -> bool:
        return len(self.hits) == len(self.coordinates)


class Board:
    def __init__(self, size: int = 10) -> None:
        self.size = size
        self.ships: List[Ship] = []
        self.misses: Set[Coordinate] = set()
        self.hits: Set[Coordinate] = set()

    def place_fleet_randomly(self, fleet: Iterable[Tuple[str, int]], rng: random.Random) -> None:
        for name, length in fleet:
            placed = False
            attempts = 0
            while not placed:
                attempts += 1
                if attempts > 500:
                    raise RuntimeError("Unable to place fleet with current constraints.")
                start_row = rng.randrange(self.size)
                start_col = rng.randrange(self.size)
                orientation = rng.choice(["horizontal", "vertical"])
                coords = self._compute_positions((start_row, start_col), length, orientation)
                if coords and self._can_place(coords):
                    ship = Ship(name=name, length=length, coordinates=coords)
                    self._add_ship(ship)
                    placed = True

    def _add_ship(self, ship: Ship) -> None:
        self.ships.append(ship)

    def _compute_positions(
        self, start: Coordinate, length: int, orientation: str
    ) -> Optional[Set[Coordinate]]:
        row, col = start
        coords: Set[Coordinate] = set()
        for step in range(length):
            r = row + (step if orientation == "vertical" else 0)
            c = col + (step if orientation == "horizontal" else 0)
            if r >= self.size or c >= self.size:
                return None
            coords.add((r, c))
        return coords

    def _can_place(self, coords: Set[Coordinate]) -> bool:
        for ship in self.ships:
            if not ship.coordinates.isdisjoint(coords):
                return False
            if not self._is_non_adjacent(ship.coordinates, coords):
                return False
        return True

    def _is_non_adjacent(self, existing: Set[Coordinate], new_coords: Set[Coordinate]) -> bool:
        for (row, col) in existing:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    neighbor = (row + dr, col + dc)
                    if neighbor in new_coords:
                        return False
        return True

    def shoot(self, coord: Coordinate) -> Tuple[str, Optional[str]]:
        if coord in self.hits or coord in self.misses:
            raise ValueError("Coordinate already targeted")
        for ship in self.ships:
            if coord in ship.coordinates:
                feedback = ship.register_hit(coord)
                self.hits.add(coord)
                return feedback, ship.name if ship.is_sunk else None
        self.misses.add(coord)
        return "plouf", None

    @property
    def all_sunk(self) -> bool:
        return all(ship.is_sunk for ship in self.ships)


@dataclass
class ShotResult:
    feedback: str
    coordinate: Coordinate
    sunk: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        payload = {
            "coordinate": format_coordinate(self.coordinate),
            "feedback": self.feedback,
        }
        if self.sunk:
            payload["sunk"] = self.sunk
        return payload


@dataclass
class Game:
    id: str
    player_board: Board
    bot_board: Board
    player_shots_remaining: int = 30
    bot_shots_remaining: int = 30
    status: str = "in_progress"  # in_progress | won | lost | draw
    player_shots: Set[Coordinate] = field(default_factory=set)
    bot_shots: Set[Coordinate] = field(default_factory=set)

    @classmethod
    def create(cls, fleet: Iterable[Tuple[str, int]], rng: Optional[random.Random] = None) -> "Game":
        rng = rng or random.Random()
        player_board = Board()
        bot_board = Board()
        player_board.place_fleet_randomly(fleet, rng)
        bot_board.place_fleet_randomly(fleet, rng)
        return cls(id=str(uuid.uuid4()), player_board=player_board, bot_board=bot_board)

    def fire(self, coord: Coordinate, rng: Optional[random.Random] = None) -> Dict[str, Optional[ShotResult]]:
        if self.status != "in_progress":
            raise ValueError("Game already finished")

        rng = rng or random.Random()

        if self.player_shots_remaining <= 0:
            raise ValueError("No shots remaining for player")

        if coord in self.player_shots:
            raise ValueError("Coordinate already targeted")

        player_feedback, sunk_name = self.bot_board.shoot(coord)
        self.player_shots_remaining -= 1
        self.player_shots.add(coord)

        player_result = ShotResult(feedback=player_feedback, coordinate=coord, sunk=sunk_name)

        if self.bot_board.all_sunk:
            self.status = "won"
            return {"player": player_result, "bot": None}

        bot_result: Optional[ShotResult] = None
        if self.bot_shots_remaining > 0:
            bot_coord = self._pick_bot_coordinate(rng)
            bot_feedback, bot_sunk_name = self.player_board.shoot(bot_coord)
            self.bot_shots_remaining -= 1
            self.bot_shots.add(bot_coord)
            bot_result = ShotResult(feedback=bot_feedback, coordinate=bot_coord, sunk=bot_sunk_name)
            if self.player_board.all_sunk:
                self.status = "lost"
        
        if self.status == "in_progress" and self.player_shots_remaining == 0 and self.bot_shots_remaining == 0:
            self.status = "draw"

        return {"player": player_result, "bot": bot_result}

    def _pick_bot_coordinate(self, rng: random.Random) -> Coordinate:
        available: List[Coordinate] = []
        for row in range(self.player_board.size):
            for col in range(self.player_board.size):
                coord = (row, col)
                if coord not in self.bot_shots:
                    available.append(coord)
        if not available:
            raise RuntimeError("Bot has no valid coordinates left")
        return rng.choice(available)

    def to_public_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "player_shots_remaining": self.player_shots_remaining,
            "bot_shots_remaining": self.bot_shots_remaining,
            "board_size": self.player_board.size,
            "fleet": DEFAULT_FLEET,
        }


DEFAULT_FLEET: List[Tuple[str, int]] = [
    ("Porte-avion", 5),
    ("Croiseur", 4),
    ("Contretorpilleur", 3),
    ("Contretorpilleur", 3),
    ("Torpilleur", 2),
]

COLUMN_LABELS = "ABCDEFGHIJ"


def parse_coordinate(label: str) -> Coordinate:
    if not label or len(label) < 2:
        raise ValueError("Invalid coordinate")
    label = label.strip().upper()
    column = label[0]
    row_part = label[1:]
    if column not in COLUMN_LABELS:
        raise ValueError("Invalid column")
    try:
        row_index = int(row_part) - 1
    except ValueError as exc:  # noqa: B904
        raise ValueError("Invalid row") from exc
    col_index = COLUMN_LABELS.index(column)
    if row_index < 0 or row_index >= 10:
        raise ValueError("Row out of bounds")
    return row_index, col_index


def format_coordinate(coord: Coordinate) -> str:
    row, col = coord
    if not (0 <= row < 10 and 0 <= col < 10):
        raise ValueError("Coordinate out of bounds")
    return f"{COLUMN_LABELS[col]}{row + 1}"
