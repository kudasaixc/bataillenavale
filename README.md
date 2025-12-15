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
3. Ouvrez un nouveau terminal (virtuelenv activé) et créez une partie puis tirez :
   ```bash
   # Créer une partie
   curl -s -X POST http://localhost:5000/games | jq

   # Tirer sur une case (remplacez <id> par l'identifiant retourné ci-dessus)
   curl -s -X POST \
     -H "Content-Type: application/json" \
     -d '{"target": "B6"}' \
     http://localhost:5000/games/<id>/shots | jq
   ```

Le serveur gère une grille 10×10, la flotte standard (porte-avion 5, croiseur 4, 2× contretorpilleur 3, torpilleur 2), 30 tirs par joueur, et un bot qui joue de façon aléatoire. Les tirs renvoient « plouf », « touché » ou « touché-coulé ». L’état de partie est conservé en mémoire tant que le serveur tourne.

## Base de données / SQL
Aucune base SQL n’est requise pour ce serveur : l’état des parties est conservé en mémoire. Vous n’avez rien à configurer côté client ni serveur. Si vous ajoutez plus tard des fonctionnalités comme l’historique ou les comptes utilisateurs, vous pourrez introduire une base (ex. PostgreSQL) et exposer la configuration correspondante.

## Client JavaFX
Le client JavaFX reste à développer. Il peut consommer l’API REST exposée par le serveur Flask (création de partie, tir). Reportez-vous au cahier des charges pour les règles et extensions possibles.
