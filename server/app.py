from __future__ import annotations

import random
from typing import Dict

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
        game = Game.create(fleet=DEFAULT_FLEET, rng=rng)
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
        }
        return jsonify(response_body)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
