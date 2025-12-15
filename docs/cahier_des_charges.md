# JavaFleet — Cahier des charges

## Table des matières
- [Introduction](#introduction)
- [Règles du jeu](#règles-du-jeu)
- [Liste des navires](#liste-des-navires)
- [Stratégies de tir](#stratégies-de-tir)
  - [Stratégie 1 — Aléatoire](#stratégie-1--aléatoire)
  - [Stratégie 2 — Hunt & Target](#stratégie-2--hunt--target)
  - [Stratégie 3 — Hunt & Target 2](#stratégie-3--hunt--target-2)
  - [Stratégie 4 — Probabilités](#stratégie-4--probabilités)
- [JavaFleet](#javafleet)
  - [Règles retenues](#règles-retenues)
  - [Exigences techniques](#exigences-techniques)
  - [Bonus et extensions](#bonus-et-extensions)

## Introduction
La bataille navale est un jeu de société opposant deux joueurs qui placent secrètement leurs navires sur une grille et tentent de couler la flotte adverse. Chaque coup consiste à désigner une coordonnée (ex. « B6 ») et à apprendre si le tir touche un navire.

## Règles du jeu
- Deux grilles de 10×10 par joueur (lignes 1–10, colonnes A–J).
- Deux navires ne doivent pas être adjacents.
- À chaque tour, un joueur annonce une case ; l’adversaire répond par « plouf », « touché » ou « touché-coulé ».
- La partie s’arrête quand toutes les cases d’une flotte sont coulées ou après 30 tirs.

## Liste des navires
### Disposition standard
- 1 Porte-avion (5 cases)
- 1 Croiseur (4 cases)
- 2 Contretorpilleurs (3 cases)
- 1 Torpilleur (2 cases)

### Disposition alternative (Belgique)
- 1 Cuirassé (4 cases)
- 2 Croiseurs (3 cases)
- 3 Torpilleurs (2 cases)
- 4 Sous-marins (1 case)

## Stratégies de tir
### Stratégie 1 — Aléatoire
- Tir complètement aléatoire.
- En moyenne : ~95,4 coups pour gagner.

### Stratégie 2 — Hunt & Target
- Dès qu’une case est touchée, viser les cases voisines pour couler le navire.
- En moyenne : ~66,2 coups pour gagner.

### Stratégie 3 — Hunt & Target 2
- Chasse par maillage :
  - Tirer une case sur deux pour détecter le torpilleur.
  - Tirer une case sur trois pour détecter le contretorpilleur.
  - Tirer une case sur quatre pour détecter le croiseur.
  - Tirer une case sur cinq pour détecter le porte-avion.
- En moyenne : ~55,2 coups pour gagner.

### Stratégie 4 — Probabilités
- Algorithme :
  1. Initialiser toutes les cases à 0.
  2. Ajouter 1 à chaque case où un bateau peut être caché.
  3. Répéter pour tous les types et nombres de bateaux.
  4. Tirer sur la case avec la valeur la plus élevée.
  5. En cas de touche, tirer sur les cases voisines, sinon revenir à l’étape 1.
- En moyenne : ~46 coups pour gagner.

## JavaFleet
### Règles retenues
- Réponse immédiate du serveur : « plouf », « touché » ou « touché-coulé ».
- 30 tirs par joueur.
- Flotte utilisée :
  - 1 Porte-avion (5 cases)
  - 1 Croiseur (4 cases)
  - 2 Contretorpilleurs (3 cases)
  - 1 Torpilleur (2 cases)
- Possibilité de rendre la flotte configurable via fichier, en conservant les ratios.

### Exigences techniques
- **Client** : Java 21 ou Java 25 avec JavaFX.
- **Serveur** :
  - Java 21 ou Java 25, **ou**
  - Python ≥ 3.10 (ex. Flask).

### Bonus et extensions
- Options configurables : flotte, nombre de tirs, taille du plateau, règle des navires non adjacents.
- Règles configurables : feedback direct/retardé, types d’armes.
- Tirs spéciaux : salves, tir de zone (¼ du plateau), etc.
- Radar : indiquer s’il existe des navires dans une zone sélectionnée.
- Effets : sons, animation de vagues/bulles lors de la pose ou destruction d’un navire.
- IA / bot.
- Personnalisation utilisateur : pseudo, couleur des navires.
- Retour en arrière (undo).
- Historique de partie exportable et rejouable.
- Statistiques (par partie et globales) : temps, premier joueur, premier navire touché/coulé, dernier navire coulé, ratio parties gagnées/jouées.
- Comptes utilisateurs avec niveau basé sur le ratio de victoires.
