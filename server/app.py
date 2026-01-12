from __future__ import annotations

import random
from typing import Dict, Iterable, List, Optional, Set, Tuple

from flask import Flask, Response, jsonify, request

from .game import DEFAULT_FLEET, Game, parse_coordinate


_games: Dict[str, Game] = {}

INDEX_HTML = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Bataille Navale — JavaFleet</title>
  <style>
    :root {
      color-scheme: light;
    }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      margin: 0;
      background: #f4f6fb;
      color: #1c2333;
    }
    header {
      padding: 24px 32px;
      background: #1c2333;
      color: #f8f9fb;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    header h1 {
      font-size: 20px;
      margin: 0;
    }
    header button {
      background: #ffb703;
      color: #1c2333;
      border: none;
      padding: 10px 16px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }
    main {
      padding: 24px 32px 40px;
      display: grid;
      gap: 24px;
    }
    .status {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }
    .card {
      background: #ffffff;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 6px 18px rgba(26, 32, 44, 0.08);
    }
    .boards {
      display: grid;
      gap: 24px;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    }
    .board-title {
      font-size: 16px;
      margin: 0 0 12px;
    }
    .grid {
      display: grid;
      gap: 4px;
      justify-content: start;
      user-select: none;
    }
    .cell {
      width: 30px;
      height: 30px;
      border-radius: 6px;
      border: 1px solid #d7dce6;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      background: #f4f6fb;
      color: #1c2333;
    }
    .cell.label {
      background: transparent;
      border: none;
      font-weight: 600;
    }
    .cell.button {
      cursor: pointer;
    }
    .cell.button:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }
    .cell.ship {
      background: #cfe2ff;
      border-color: #89b4f8;
    }
    .cell.hit {
      background: #ef476f;
      border-color: #c0392b;
      color: #ffffff;
      font-weight: 700;
    }
    .cell.miss {
      background: #8ecae6;
      border-color: #219ebc;
      color: #ffffff;
      font-weight: 700;
    }
    .cell.sunk {
      background: #7f1d1d;
      border-color: #4c0519;
      color: #ffffff;
      font-weight: 700;
    }
    .log {
      font-size: 14px;
      margin: 0;
      color: #4a5568;
    }
  </style>
</head>
<body>
  <header>
    <h1>Bataille Navale — JavaFleet</h1>
    <button id="new-game">Nouvelle partie</button>
  </header>
  <main>
    <section class="status">
      <div class="card">
        <strong>Statut</strong>
        <p class="log" id="game-status">En attente…</p>
      </div>
      <div class="card">
        <strong>Coups restants</strong>
        <p class="log" id="shots-remaining">—</p>
      </div>
      <div class="card">
        <strong>Dernier échange</strong>
        <p class="log" id="last-exchange">—</p>
      </div>
    </section>
    <section class="boards">
      <div class="card">
        <h2 class="board-title">Votre grille</h2>
        <div id="player-grid" class="grid"></div>
      </div>
      <div class="card">
        <h2 class="board-title">Grille ennemie (cliquez pour tirer)</h2>
        <div id="bot-grid" class="grid"></div>
      </div>
    </section>
  </main>

  <script>
    const columnLabels = "ABCDEFGHIJ";
    const state = {
      gameId: null,
      status: "idle",
      playerShotsRemaining: 0,
      botShotsRemaining: 0,
      playerBoard: null,
      botBoard: null,
      lastPlayerResult: null,
      lastBotResult: null,
    };

    function coordinateLabel(row, col) {
      return `${columnLabels[col]}${row + 1}`;
    }

    function renderBoard(container, board, options = {}) {
      if (!board) {
        container.innerHTML = "";
        return;
      }
      const size = board.size;
      container.innerHTML = "";
      container.style.gridTemplateColumns = `repeat(${size + 1}, 30px)`;
      container.style.gridTemplateRows = `repeat(${size + 1}, 30px)`;

      const hits = new Set(board.hits || []);
      const misses = new Set(board.misses || []);
      const ships = new Set();
      const sunk = new Set();
      if (board.ships) {
        board.ships.forEach((ship) => {
          ship.coordinates.forEach((coord) => ships.add(coord));
          if (ship.sunk) {
            ship.coordinates.forEach((coord) => sunk.add(coord));
          }
        });
      }

      const corner = document.createElement("div");
      corner.className = "cell label";
      container.appendChild(corner);

      for (let col = 0; col < size; col++) {
        const label = document.createElement("div");
        label.className = "cell label";
        label.textContent = columnLabels[col];
        container.appendChild(label);
      }

      for (let row = 0; row < size; row++) {
        const rowLabel = document.createElement("div");
        rowLabel.className = "cell label";
        rowLabel.textContent = String(row + 1);
        container.appendChild(rowLabel);

        for (let col = 0; col < size; col++) {
          const coord = coordinateLabel(row, col);
          const button = document.createElement("button");
          button.className = "cell button";
          button.dataset.coord = coord;

          if (ships.has(coord)) {
            button.classList.add("ship");
          }
          if (hits.has(coord)) {
            button.classList.add("hit");
            button.textContent = "X";
          } else if (misses.has(coord)) {
            button.classList.add("miss");
            button.textContent = "•";
          }
          if (sunk.has(coord)) {
            button.classList.add("sunk");
            button.textContent = "☠";
          }

          if (options.clickable) {
            button.addEventListener("click", () => {
              if (button.disabled) {
                return;
              }
              fireAt(coord);
            });
            if (hits.has(coord) || misses.has(coord) || state.status !== "in_progress") {
              button.disabled = true;
            }
          } else {
            button.disabled = true;
          }

          container.appendChild(button);
        }
      }
    }

    function updateStatus() {
      const statusEl = document.getElementById("game-status");
      const shotsEl = document.getElementById("shots-remaining");
      const exchangeEl = document.getElementById("last-exchange");

      statusEl.textContent = state.gameId
        ? `Partie ${state.status.replace("_", " ")} (ID ${state.gameId})`
        : "En attente…";

      shotsEl.textContent = state.gameId
        ? `Vous: ${state.playerShotsRemaining} | Bot: ${state.botShotsRemaining}`
        : "—";

      if (state.lastPlayerResult || state.lastBotResult) {
        const player = state.lastPlayerResult
          ? `Vous: ${state.lastPlayerResult.coordinate} (${state.lastPlayerResult.feedback})`
          : "Vous: —";
        const bot = state.lastBotResult
          ? `Bot: ${state.lastBotResult.coordinate} (${state.lastBotResult.feedback})`
          : "Bot: —";
        exchangeEl.textContent = `${player} | ${bot}`;
      } else {
        exchangeEl.textContent = "—";
      }
    }

    function updateBoards() {
      renderBoard(document.getElementById("player-grid"), state.playerBoard);
      renderBoard(document.getElementById("bot-grid"), state.botBoard, { clickable: true });
      updateStatus();
    }

    async function createGame() {
      const response = await fetch("/games", { method: "POST" });
      if (!response.ok) {
        alert("Impossible de créer la partie.");
        return;
      }
      const data = await response.json();
      state.gameId = data.id;
      state.status = data.status;
      state.playerShotsRemaining = data.player_shots_remaining;
      state.botShotsRemaining = data.bot_shots_remaining;
      state.playerBoard = data.player_board;
      state.botBoard = data.bot_board;
      state.lastPlayerResult = null;
      state.lastBotResult = null;
      updateBoards();
    }

    async function fireAt(coord) {
      if (!state.gameId || state.status !== "in_progress") {
        return;
      }
      const response = await fetch(`/games/${state.gameId}/shots`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: coord }),
      });
      if (!response.ok) {
        const error = await response.json();
        alert(error.error || "Coup invalide");
        return;
      }
      const data = await response.json();
      state.status = data.status;
      state.playerShotsRemaining = data.player_shots_remaining;
      state.botShotsRemaining = data.bot_shots_remaining;
      state.playerBoard = data.player_board;
      state.botBoard = data.bot_board;
      state.lastPlayerResult = data.player_result;
      state.lastBotResult = data.bot_result;
      updateBoards();
    }

    document.getElementById("new-game").addEventListener("click", createGame);
    createGame();
  </script>
</body>
</html>
"""


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return Response(INDEX_HTML, mimetype="text/html")

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
