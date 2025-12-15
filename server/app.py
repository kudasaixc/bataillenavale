from __future__ import annotations

import random
from typing import Dict, Iterable, List, Optional, Set, Tuple

from flask import Flask, jsonify, request

from .game import DEFAULT_FLEET, Game, parse_coordinate


_games: Dict[str, Game] = {}


def create_app() -> Flask:
    app = Flask(__name__)

    @app.post("/games")
    def create_game():
        body = request.get_json(silent=True) or {}
        seed = body.get("seed")
        rng = random.Random(seed) if seed is not None else random.Random()
        try:
            player_layout = _parse_ships(body.get("player_ships"))
            bot_layout = _parse_ships(body.get("bot_ships"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        try:
            game = Game.create(
                fleet=DEFAULT_FLEET,
                rng=rng,
                player_layout=player_layout,
                bot_layout=bot_layout,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        _games[game.id] = game
        return jsonify(game.to_public_dict()), 201

    @app.get("/games/<game_id>")
    def get_game(game_id: str):
        game = _games.get(game_id)
        if not game:
            return jsonify({"error": "Game not found"}), 404
        return jsonify(game.to_public_dict())

    @app.post("/games/<game_id>/shots")
    def fire(game_id: str):
        game = _games.get(game_id)
        if not game:
            return jsonify({"error": "Game not found"}), 404

        payload = request.get_json(silent=True) or {}
        target = payload.get("target")
        if not target:
            return jsonify({"error": "Missing target"}), 400
        try:
            coord = parse_coordinate(target)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        try:
            results = game.fire(coord)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        response_body = {
            "status": game.status,
            "player_shots_remaining": game.player_shots_remaining,
            "bot_shots_remaining": game.bot_shots_remaining,
            "player_result": results["player"].to_dict() if results["player"] else None,
            "bot_result": results["bot"].to_dict() if results["bot"] else None,
            "player_board": game.player_board.to_public_view(reveal_ships=True),
            "bot_board": game.bot_board.to_public_view(reveal_ships=False),
        }
        return jsonify(response_body)

    return app


def _parse_ships(raw: Optional[Iterable[dict]]) -> Optional[List[Tuple[str, int, Set[Tuple[int, int]]]]]:
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError("Ship layout must be a list of ships")

    parsed: List[Tuple[str, int, Set[Tuple[int, int]]]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise ValueError("Each ship must be an object")
        name = entry.get("name")
        positions = entry.get("positions")
        if not name or not positions:
            raise ValueError("Each ship needs 'name' and 'positions'")
        if not isinstance(positions, list):
            raise ValueError("'positions' must be a list")

        coords = set()
        for label in positions:
            coords.add(parse_coordinate(str(label)))

        length = entry.get("length", len(coords))
        parsed.append((name, int(length), coords))

    return parsed


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
