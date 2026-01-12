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
      background: #f6a5b5;
      border-color: #d46a7a;
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
      background: #c1121f;
      border-color: #780000;
      color: #ffffff;
      font-weight: 700;
    }
    .placement-card {
      display: grid;
      gap: 12px;
    }
    .placement-controls,
    .placement-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .placement-card button {
      background: #1d4ed8;
      color: #ffffff;
      border: none;
      padding: 8px 12px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }
    .placement-card button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    #reset-placement {
      background: #64748b;
    }
    #start-game {
      background: #16a34a;
    }
    .fleet-progress {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 6px;
      font-size: 13px;
      color: #475569;
    }
    .fleet-progress li {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .fleet-progress .placed {
      color: #16a34a;
      font-weight: 600;
    }
    .victory-overlay {
      position: fixed;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(15, 23, 42, 0.75);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease;
      z-index: 10;
    }
    .victory-card {
      background: #ffffff;
      color: #1c2333;
      padding: 28px 36px;
      border-radius: 16px;
      box-shadow: 0 20px 40px rgba(15, 23, 42, 0.35);
      text-align: center;
      transform: translateY(20px) scale(0.96);
      opacity: 0;
    }
    body.game-over .victory-overlay {
      opacity: 1;
      pointer-events: auto;
    }
    body.game-over .victory-card {
      animation: victory-pop 0.6s ease forwards;
    }
    .victory-card.victory {
      border: 2px solid #22c55e;
      box-shadow: 0 20px 40px rgba(34, 197, 94, 0.35);
    }
    .victory-card.defeat {
      border: 2px solid #ef4444;
      box-shadow: 0 20px 40px rgba(239, 68, 68, 0.35);
    }
    .victory-card.draw {
      border: 2px solid #f59e0b;
      box-shadow: 0 20px 40px rgba(245, 158, 11, 0.35);
    }
    @keyframes victory-pop {
      0% {
        transform: translateY(20px) scale(0.96);
        opacity: 0;
      }
      70% {
        transform: translateY(-4px) scale(1.02);
        opacity: 1;
      }
      100% {
        transform: translateY(0) scale(1);
        opacity: 1;
      }
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
      <div class="card placement-card">
        <strong>Placement de la flotte</strong>
        <p class="log" id="placement-status">Sélectionnez une case pour placer le navire.</p>
        <div class="placement-controls">
          <button id="orientation-toggle" type="button">Orientation : horizontale</button>
          <button id="reset-placement" type="button">Réinitialiser</button>
        </div>
        <div class="placement-actions">
          <button id="start-game" type="button" disabled>Démarrer la partie</button>
        </div>
        <ul id="fleet-progress" class="fleet-progress"></ul>
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
  <div id="victory-overlay" class="victory-overlay" aria-live="polite">
    <div id="victory-card" class="victory-card">
      <h2 id="victory-title">Victoire !</h2>
      <p id="victory-message">La flotte ennemie est coulée.</p>
    </div>
  </div>

  <script>
    const columnLabels = "ABCDEFGHIJ";
    const HIT_DELAY_MS = 500;
    const state = {
      gameId: null,
      status: "idle",
      playerShotsRemaining: 0,
      botShotsRemaining: 0,
      playerBoard: null,
      botBoard: null,
      lastPlayerResult: null,
      lastBotResult: null,
      resolving: false,
      pendingTimeout: null,
      placementMode: true,
      placementOrientation: "horizontal",
      placements: [],
    };
    const fleet = [
      { name: "Porte-avion", length: 5 },
      { name: "Croiseur", length: 4 },
      { name: "Contretorpilleur", length: 3 },
      { name: "Contretorpilleur", length: 3 },
      { name: "Torpilleur", length: 2 },
    ];
    const boardSize = 10;

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
      const sunk = new Set(board.sunk || []);
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

          if (options.onCellClick) {
            button.addEventListener("click", () => {
              if (button.disabled) {
                return;
              }
              options.onCellClick(coord);
            });
            button.disabled = options.isDisabled ? options.isDisabled(coord) : false;
          } else if (options.clickable) {
            button.addEventListener("click", () => {
              if (button.disabled) {
                return;
              }
              fireAt(coord);
            });
            button.disabled =
              hits.has(coord) ||
              misses.has(coord) ||
              state.status !== "in_progress" ||
              state.resolving;
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
      const placementStatus = document.getElementById("placement-status");
      const victoryOverlay = document.getElementById("victory-overlay");
      const victoryCard = document.getElementById("victory-card");
      const victoryTitle = document.getElementById("victory-title");
      const victoryMessage = document.getElementById("victory-message");

      if (state.placementMode) {
        statusEl.textContent = "Placement de votre flotte";
      } else {
        statusEl.textContent = state.gameId
          ? `Partie ${state.status.replace("_", " ")} (ID ${state.gameId})`
          : "En attente…";
      }

      shotsEl.textContent =
        state.gameId && !state.placementMode
          ? `Vous: ${state.playerShotsRemaining} | Bot: ${state.botShotsRemaining}`
          : "—";

      if (!state.placementMode && (state.lastPlayerResult || state.lastBotResult)) {
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

      if (state.placementMode) {
        const nextShip = fleet[state.placements.length];
        placementStatus.textContent = nextShip
          ? `À placer : ${nextShip.name} (${nextShip.length} cases)`
          : "Flotte prête. Vous pouvez démarrer la partie.";
      } else {
        placementStatus.textContent = "Partie en cours.";
      }

      if (state.status === "won" || state.status === "lost" || state.status === "draw") {
        document.body.classList.add("game-over");
        victoryCard.classList.remove("victory", "defeat", "draw");
        if (state.status === "won") {
          victoryTitle.textContent = "Victoire !";
          victoryMessage.textContent = "La flotte ennemie est coulée.";
          victoryCard.classList.add("victory");
        } else if (state.status === "lost") {
          victoryTitle.textContent = "Défaite…";
          victoryMessage.textContent = "Le bot a eu raison de votre flotte.";
          victoryCard.classList.add("defeat");
        } else {
          victoryTitle.textContent = "Match nul";
          victoryMessage.textContent = "Plus de munitions pour les deux camps.";
          victoryCard.classList.add("draw");
        }
        victoryOverlay.setAttribute("aria-hidden", "false");
      } else {
        document.body.classList.remove("game-over");
        victoryOverlay.setAttribute("aria-hidden", "true");
      }
    }

    function updateBoards() {
      if (state.placementMode) {
        renderBoard(document.getElementById("player-grid"), buildPlacementBoard(), {
          onCellClick: handlePlacementClick,
          isDisabled: () => false,
        });
        renderBoard(document.getElementById("bot-grid"), buildEmptyBoard());
      } else {
        renderBoard(document.getElementById("player-grid"), state.playerBoard);
        renderBoard(document.getElementById("bot-grid"), state.botBoard, { clickable: true });
      }
      updateStatus();
      updatePlacementControls();
    }

    function buildEmptyBoard() {
      return { size: boardSize, hits: [], misses: [], sunk: [], ships: [] };
    }

    function buildPlacementBoard() {
      return {
        size: boardSize,
        hits: [],
        misses: [],
        sunk: [],
        ships: state.placements.map((ship) => ({
          name: ship.name,
          length: ship.length,
          coordinates: ship.positions,
          hits: [],
          sunk: false,
        })),
      };
    }

    function updatePlacementControls() {
      const startButton = document.getElementById("start-game");
      const orientationButton = document.getElementById("orientation-toggle");
      const resetButton = document.getElementById("reset-placement");
      const fleetProgress = document.getElementById("fleet-progress");
      const isReady = state.placements.length === fleet.length;

      startButton.disabled = !state.placementMode || !isReady || state.resolving;
      orientationButton.disabled = !state.placementMode;
      resetButton.disabled = !state.placementMode;
      orientationButton.textContent =
        state.placementOrientation === "horizontal"
          ? "Orientation : horizontale"
          : "Orientation : verticale";

      fleetProgress.innerHTML = "";
      fleet.forEach((ship, index) => {
        const listItem = document.createElement("li");
        const label = document.createElement("span");
        label.textContent = `${ship.name} (${ship.length})`;
        const status = document.createElement("span");
        status.textContent = state.placements[index] ? "placé" : "à placer";
        if (state.placements[index]) {
          status.classList.add("placed");
        }
        listItem.appendChild(label);
        listItem.appendChild(status);
        fleetProgress.appendChild(listItem);
      });
    }

    function resetPlacement() {
      state.gameId = null;
      state.status = "idle";
      state.playerShotsRemaining = 0;
      state.botShotsRemaining = 0;
      state.playerBoard = null;
      state.botBoard = null;
      state.lastPlayerResult = null;
      state.lastBotResult = null;
      state.resolving = false;
      state.placementMode = true;
      state.placementOrientation = "horizontal";
      state.placements = [];
      updateBoards();
    }

    function handlePlacementClick(coord) {
      if (!state.placementMode) {
        return;
      }
      const nextShip = fleet[state.placements.length];
      if (!nextShip) {
        return;
      }
      const positions = computeShipPositions(coord, nextShip.length, state.placementOrientation);
      if (!positions) {
        alert("Le navire dépasse la grille.");
        return;
      }
      if (!isPlacementValid(positions)) {
        alert("Le navire chevauche ou touche un autre navire.");
        return;
      }
      state.placements.push({
        name: nextShip.name,
        length: nextShip.length,
        positions: positions.map(([row, col]) => coordinateLabel(row, col)),
      });
      updateBoards();
    }

    function computeShipPositions(coord, length, orientation) {
      const start = parseCoordinate(coord);
      if (!start) {
        return null;
      }
      const [row, col] = start;
      const positions = [];
      for (let step = 0; step < length; step++) {
        const nextRow = row + (orientation === "vertical" ? step : 0);
        const nextCol = col + (orientation === "horizontal" ? step : 0);
        if (nextRow < 0 || nextRow >= boardSize || nextCol < 0 || nextCol >= boardSize) {
          return null;
        }
        positions.push([nextRow, nextCol]);
      }
      return positions;
    }

    function parseCoordinate(coord) {
      const column = coord[0];
      const row = Number.parseInt(coord.slice(1), 10) - 1;
      const col = columnLabels.indexOf(column);
      if (Number.isNaN(row) || col < 0) {
        return null;
      }
      return [row, col];
    }

    function isPlacementValid(positions) {
      const existing = new Set();
      state.placements.forEach((ship) => {
        ship.positions.forEach((pos) => existing.add(pos));
      });
      for (const [row, col] of positions) {
        const label = coordinateLabel(row, col);
        if (existing.has(label)) {
          return false;
        }
        for (let dr = -1; dr <= 1; dr++) {
          for (let dc = -1; dc <= 1; dc++) {
            const neighborRow = row + dr;
            const neighborCol = col + dc;
            if (
              neighborRow < 0 ||
              neighborRow >= boardSize ||
              neighborCol < 0 ||
              neighborCol >= boardSize
            ) {
              continue;
            }
            const neighborLabel = coordinateLabel(neighborRow, neighborCol);
            if (existing.has(neighborLabel)) {
              return false;
            }
          }
        }
      }
      return true;
    }

    async function createGame() {
      if (state.pendingTimeout) {
        clearTimeout(state.pendingTimeout);
        state.pendingTimeout = null;
      }
      if (state.placements.length !== fleet.length) {
        alert("Placez toute votre flotte avant de démarrer.");
        return;
      }
      const response = await fetch("/games", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_ships: state.placements }),
      });
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
      state.resolving = false;
      state.placementMode = false;
      updateBoards();
    }

    async function fireAt(coord) {
      if (!state.gameId || state.status !== "in_progress" || state.resolving) {
        return;
      }
      if (state.pendingTimeout) {
        clearTimeout(state.pendingTimeout);
        state.pendingTimeout = null;
      }
      state.resolving = true;
      updateBoards();
      const previousPlayerBoard = state.playerBoard;
      const previousBotShotsRemaining = state.botShotsRemaining;
      const response = await fetch(`/games/${state.gameId}/shots`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: coord }),
      });
      if (!response.ok) {
        const error = await response.json();
        alert(error.error || "Coup invalide");
        state.resolving = false;
        updateBoards();
        return;
      }
      const data = await response.json();
      state.playerShotsRemaining = data.player_shots_remaining;
      state.botBoard = data.bot_board;
      state.lastPlayerResult = data.player_result;
      const hasBotShot = Boolean(data.bot_result);

      if (hasBotShot) {
        state.status = "in_progress";
        state.botShotsRemaining = previousBotShotsRemaining;
        state.playerBoard = previousPlayerBoard;
        state.lastBotResult = null;
        updateBoards();
        state.pendingTimeout = window.setTimeout(() => {
          state.status = data.status;
          state.botShotsRemaining = data.bot_shots_remaining;
          state.playerBoard = data.player_board;
          state.lastBotResult = data.bot_result;
          state.resolving = false;
          state.pendingTimeout = null;
          updateBoards();
        }, HIT_DELAY_MS);
      } else {
        state.status = data.status;
        state.botShotsRemaining = data.bot_shots_remaining;
        state.playerBoard = data.player_board;
        state.lastBotResult = data.bot_result;
        state.resolving = false;
        updateBoards();
      }
    }

    document.getElementById("new-game").addEventListener("click", resetPlacement);
    document.getElementById("orientation-toggle").addEventListener("click", () => {
      state.placementOrientation =
        state.placementOrientation === "horizontal" ? "vertical" : "horizontal";
      updatePlacementControls();
    });
    document.getElementById("reset-placement").addEventListener("click", resetPlacement);
    document.getElementById("start-game").addEventListener("click", createGame);
    resetPlacement();
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
