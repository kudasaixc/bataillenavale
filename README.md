# Bataille Navale — JavaFleet

Ce dépôt contient le cahier des charges et une première implémentation serveur (Python + Flask) pour JavaFleet, un jeu de bataille navale.

## Contenu
- `docs/cahier_des_charges.md` : spécification fonctionnelle et technique (règles du jeu, stratégies, exigences client/serveur et pistes d’extensions).
- `server/` : serveur Flask minimal, logique de grille et d’affrontement contre un bot aléatoire.
- `requirements.txt` : dépendances Python pour le serveur.

## Lancer le serveur Python
1. Créez un environnement virtuel et installez les dépendances :
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Démarrez le serveur Flask :
   ```bash
   python -m server.app
   # ou FLASK_APP=server.app flask run
   ```

## Jouer via l’API REST

Le serveur expose trois endpoints :

- `POST /games` : crée une partie et retourne son état initial.
- `GET /games/<id>` : retourne l’état courant (nombre de tirs, boards, statut).
- `POST /games/<id>/shots` : tire sur la case demandée, fait jouer le bot puis renvoie les deux résultats et les boards mis à jour.

La grille fait 10×10, avec la flotte standard (porte-avion 5, croiseur 4, 2× contretorpilleur 3, torpilleur 2) et 30 tirs par joueur. Un bot tire de façon aléatoire à chaque fois que vous tirez.

### Exemple rapide
```bash
# Créer une partie
curl -s -X POST http://localhost:5000/games | jq

# Tirer sur une case (remplacez <id>)
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"target": "B6"}' \
  http://localhost:5000/games/<id>/shots | jq
```

Les réponses contiennent les coups joués, les boards (avec vos bateaux révélés, ceux du bot masqués), le nombre de tirs restants et le statut (`in_progress`, `won`, `lost`, `draw`).

### Placer vos bateaux manuellement (optionnel)
Par défaut, votre flotte et celle du bot sont placées aléatoirement en respectant la non-adjacence. Vous pouvez fournir votre placement lors de la création d’une partie :

```bash
curl -s -X POST http://localhost:5000/games \
  -H "Content-Type: application/json" \
  -d '{
        "player_ships": [
          {"name": "Porte-avion", "positions": ["A1", "A2", "A3", "A4", "A5"]},
          {"name": "Croiseur", "positions": ["C1", "D1", "E1", "F1"]},
          {"name": "Contretorpilleur", "positions": ["H2", "H3", "H4"]},
          {"name": "Contretorpilleur", "positions": ["D5", "E5", "F5"]},
          {"name": "Torpilleur", "positions": ["J10", "J9"]}
        ]
      }' | jq
```

Les positions doivent être alignées (horizontal/vertical), respecter les longueurs attendues et ne pas se toucher. Vous pouvez aussi fournir `bot_ships` pour des tests ou des replays, sinon le bot sera placé aléatoirement.

### Boucle de jeu
1. Créez la partie (`POST /games`).
2. Affichez/rafraîchissez l’état (`GET /games/<id>`) si besoin.
3. Tirez (`POST /games/<id>/shots` avec `{"target": "B6"}`), l’API renvoie votre résultat et le tir du bot.
4. Continuez jusqu’au statut `won`, `lost` ou `draw`.

## Base de données / SQL
Aucune base SQL n’est requise pour ce serveur : l’état des parties est conservé en mémoire. Vous n’avez rien à configurer côté client ni serveur. Si vous ajoutez plus tard des fonctionnalités comme l’historique ou les comptes utilisateurs, vous pourrez introduire une base (ex. PostgreSQL) et exposer la configuration correspondante.

## Client JavaFX
Le client JavaFX reste à développer. Il peut consommer l’API REST exposée par le serveur Flask (création de partie, tir). Reportez-vous au cahier des charges pour les règles et extensions possibles.
