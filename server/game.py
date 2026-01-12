from __future__ import annotations

import random
import uuid
from collections import Counter
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
            self._place_random_ship(name, length, rng)

    def place_ship(self, name: str, length: int, coords: Iterable[Coordinate]) -> None:
        coords_set = set(coords)
        if len(coords_set) != length:
            raise ValueError(f"Ship '{name}' must have exactly {length} distinct coordinates")
        if not self._is_straight_line(coords_set):
            raise ValueError(f"Ship '{name}' must be aligned vertically or horizontally")
        if not all(self._is_within_board(coord) for coord in coords_set):
            raise ValueError(f"Ship '{name}' has coordinates outside the board")
        if not self._can_place(coords_set):
            raise ValueError(f"Ship '{name}' overlaps or touches another ship")

        ship = Ship(name=name, length=length, coordinates=coords_set)
        self._add_ship(ship)

    def to_public_view(self, reveal_ships: bool = False) -> Dict[str, object]:
        sunk_coords: Set[Coordinate] = set()
        for ship in self.ships:
            if ship.is_sunk:
                sunk_coords.update(ship.coordinates)
        payload: Dict[str, object] = {
            "size": self.size,
            "hits": [format_coordinate(c) for c in sorted(self.hits)],
            "misses": [format_coordinate(c) for c in sorted(self.misses)],
            "sunk": [format_coordinate(c) for c in sorted(sunk_coords)],
        }
        if reveal_ships:
            payload["ships"] = [
                {
                    "name": ship.name,
                    "length": ship.length,
                    "coordinates": [format_coordinate(c) for c in sorted(ship.coordinates)],
                    "hits": [format_coordinate(c) for c in sorted(ship.hits)],
                    "sunk": ship.is_sunk,
                }
                for ship in self.ships
            ]
        return payload

    def _place_random_ship(self, name: str, length: int, rng: random.Random) -> None:
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
            if not self._is_within_board((r, c)):
                return None
            coords.add((r, c))
        return coords

    def _is_within_board(self, coord: Coordinate) -> bool:
        row, col = coord
        return 0 <= row < self.size and 0 <= col < self.size

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

    def _is_straight_line(self, coords: Set[Coordinate]) -> bool:
        rows = {r for r, _ in coords}
        cols = {c for _, c in coords}
        return len(rows) == 1 or len(cols) == 1

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
    bot_targets: List[Coordinate] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        fleet: Iterable[Tuple[str, int]],
        rng: Optional[random.Random] = None,
        player_layout: Optional[List[Tuple[str, int, Set[Coordinate]]]] = None,
        bot_layout: Optional[List[Tuple[str, int, Set[Coordinate]]]] = None,
    ) -> "Game":
        rng = rng or random.Random()
        player_board = Board()
        bot_board = Board()

        cls._place_fleet(board=player_board, fleet=fleet, rng=rng, layout=player_layout)
        cls._place_fleet(board=bot_board, fleet=fleet, rng=rng, layout=bot_layout)

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

        if self.player_shots_remaining == 0:
            self.status = "draw"
            return {"player": player_result, "bot": None}

        bot_result: Optional[ShotResult] = None
        if self.bot_shots_remaining > 0:
            bot_coord = self._pick_bot_coordinate(rng)
            bot_feedback, bot_sunk_name = self.player_board.shoot(bot_coord)
            self.bot_shots_remaining -= 1
            self.bot_shots.add(bot_coord)
            bot_result = ShotResult(feedback=bot_feedback, coordinate=bot_coord, sunk=bot_sunk_name)
            self._update_bot_targets(bot_coord, bot_feedback, rng)
            if self.player_board.all_sunk:
                self.status = "lost"

        if self.status == "in_progress" and self.bot_shots_remaining == 0:
            self.status = "draw"

        return {"player": player_result, "bot": bot_result}

    def _pick_bot_coordinate(self, rng: random.Random) -> Coordinate:
        while self.bot_targets:
            candidate = self.bot_targets.pop(0)
            if candidate not in self.bot_shots:
                return candidate

        available: List[Coordinate] = []
        for row in range(self.player_board.size):
            for col in range(self.player_board.size):
                coord = (row, col)
                if coord not in self.bot_shots:
                    available.append(coord)
        if not available:
            raise RuntimeError("Bot has no valid coordinates left")
        return rng.choice(available)

    def _update_bot_targets(self, coord: Coordinate, feedback: str, rng: random.Random) -> None:
        if feedback == "touché-coulé":
            self.bot_targets.clear()
            return
        if feedback != "touché":
            return

        row, col = coord
        candidates = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]
        rng.shuffle(candidates)
        for candidate in candidates:
            if self.player_board._is_within_board(candidate) and candidate not in self.bot_shots:
                if candidate not in self.bot_targets:
                    self.bot_targets.append(candidate)

    def to_public_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "player_shots_remaining": self.player_shots_remaining,
            "bot_shots_remaining": self.bot_shots_remaining,
            "board_size": self.player_board.size,
            "fleet": DEFAULT_FLEET,
            "player_board": self.player_board.to_public_view(reveal_ships=True),
            "bot_board": self.bot_board.to_public_view(reveal_ships=False),
        }

    @staticmethod
    def _place_fleet(
        board: Board,
        fleet: Iterable[Tuple[str, int]],
        rng: random.Random,
        layout: Optional[List[Tuple[str, int, Set[Coordinate]]]] = None,
    ) -> None:
        fleet_counter = Counter(fleet)
        if layout is None:
            board.place_fleet_randomly(fleet, rng)
            return

        layout_counter = Counter((name, length) for name, length, _ in layout)
        if layout_counter != fleet_counter:
            raise ValueError("Layout does not match expected fleet composition")

        for name, length, coords in layout:
            board.place_ship(name=name, length=length, coords=coords)


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
