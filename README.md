# 🍿 PopCornHub

**Application web de gestion de vidéothèque et de locations de films**

PopCornHub est une application web complète permettant aux utilisateurs de :
- gérer leur vidéothèque personnelle,
- proposer leurs films à la location,
- louer des films à d’autres utilisateurs,
- laisser des avis,
- consulter des fiches films enrichies via TMDb.

L’application repose sur **Flask**, utilise **TMDb** pour les données cinéma,  
et stocke les données localement dans un fichier **JSON**.

---

## 📌 Table des matières

- [Description](#-description)
- [Architecture du projet](#️-architecture-du-projet)
- [Technologies utilisées](#️-technologies-utilisées)
- [Installation & Lancement](#-installation--lancement)
- [Gestion des données](#️-gestion-des-données)
- [Intégration TMDb](#-intégration-tmdb)
- [Comptes disponibles](#-comptes-disponibles)
- [Structure du projet](#-structure-du-projet)
- [Instructions](#-instructions)
- [Licence](#-licence)

## 🎯 Objectif du projet

Ce projet a été réalisé dans un cadre pédagogique.  
L’objectif est de mettre en place une application web **fonctionnelle**, **cohérente**, et **facile à déployer**, sans dépendance complexe (pas de base de données SQL).

---

## 🧠 Fonctionnalités principales

### 🎞️ Films
- Recherche et affichage des films via **TMDb**
- Affiche, synopsis, année, genres, acteurs
- Bande-annonce (YouTube)

### 📚 Vidéothèque personnelle
- Ajouter un film à sa vidéothèque
- Définir les formats possédés :
  - Blu-ray
  - Digital / Streaming
- Définir :
  - prix de location
  - durée maximale
- Rendre un film **public ou privé**
- Modifier ou supprimer un film de sa vidéothèque

### 🛒 Locations
- Louer un film à un autre utilisateur
- Choisir le format (Blu-ray / Digital)
- Choisir la durée de location via un **popup**
- Un exemplaire ne peut être loué **qu’une seule fois à la fois**
- Si déjà loué :
  - affichage “Indisponible”
  - date de disponibilité indiquée
- Rendre un film avant la date de fin
- Les locations s’affichent dans le profil avec :
  - affiche du film
  - dates
  - format
  - bouton “Rendre”

### ✍️ Avis
- Ajouter ou modifier un avis sur un film
- Note de 1 à 5
- Commentaire
- Moyenne affichée sur la fiche film

### 👤 Utilisateurs
- Création de compte
- Connexion / Déconnexion
- Pas de compte administrateur (inutile pour le projet)

---

## 🏗️ Architecture du projet

```
PopCornHub/
│
├── popcornhub-web/              
│   ├── app.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── films.py
│   │   ├── profile.py
│   ├── services/
│   │   ├── data.py
│   │   ├── tmdb.py
│   │   ├── auth_utils.py
│   ├── templates/
│   ├── static/
│   └── Dockerfile
│
├── data/
│   └── data.json                
│
├── docker-compose.yml
└── README.md
```

---

## 🗂️ Gestion des données

Les données sont stockées dans un fichier JSON :
   data/data.json

Il contient :
- utilisateurs
- vidéothèques
- locations
- avis

👉 **Aucune base de données externe**  
👉 Les données sont persistantes tant que le fichier existe

---

## 🎬 Intégration TMDb

PopCornHub utilise l’API **The Movie Database (TMDb)** pour :
- récupérer les films
- affiches
- acteurs
- bandes-annonces

Une clé API TMDb est nécessaire.

---

## ⚙️ Installation & Lancement (simple)

### ✅ Prérequis
- Docker
- Docker Compose

---

### ▶️ Lancement du projet

Une seule commande suffit :

```bash
docker-compose up --build
```

➡️ **API disponible sur** : `http://localhost:5000`

## 🧪 Utilisation rapide

1. **Cloner le projet** sur deux machines distinctes
2. **Lancer l'API** sur la Machine 1 avec `docker-compose-api.yml`
3. **Configurer l'URL de l'API** dans `popcornhub-web/config.py`
4. **Lancer l'interface Web** sur la Machine 2 avec `docker-compose-web.yml`
5. **Se connecter** avec le compte administrateur :
   - Identifiant : `admin`
   - Mot de passe : `admin`

### Fonctionnalités à tester

- ✅ Ajout et suppression d'un film
- ✅ Import de film via TMDb
- ✅ Création et connexion d'un utilisateur
- ✅ Ajout de films en favoris
- ✅ Location de films et gestion des retours
- ✅ Publication d'avis sur les films

**Note** : Les données sont automatiquement persistées dans `data/data.json`.

---

## 📜 Licence

Projet réalisé par Sébastien Porfiri et Elie Coutelle dans le cadre pédagogique du module **RT0705** – Université de Reims Champagne-Ardenne.

---

🍿 **Bon visionnage et bon test !**

# 🍿 PopCornHub

PopCornHub est une application web (Flask) de **gestion de vidéothèque** et de **location de films entre utilisateurs**.
Les fiches films (affiche, synopsis, casting, etc.) sont récupérées via **TMDb**, et toutes les données applicatives sont persistées dans un simple fichier **JSON**.

---

## ✨ Ce que permet l’application

- 🔎 Rechercher des films (TMDb) et consulter une fiche détaillée (acteurs, bande‑annonce, avis…)
- 📚 Ajouter un film à sa vidéothèque, définir les formats (Blu‑ray / Digital), prix et durée max
- 🌍 Rendre un exemplaire **public** (louable par les autres) ou **privé**
- 🛒 Louer un film à un autre utilisateur en choisissant **format** + **nombre de jours** (popup)
- ⛔ Un exemplaire ne peut être loué **qu’une seule fois à la fois** :
  - si déjà loué → affichage **Indisponible** + **Disponible à partir du …**
- 🔁 Rendre un film avant la fin prévue (confirmation)
- ✍️ Ajouter / modifier un avis (note 1→5 + commentaire)

---

## 🧱 Architecture (projet)

```
PopCornHub/
├── data/
│   └── data.json
│
├── popcornhub-api/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── popcornhub-web/
│   ├── app.py
│   ├── config.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── favorites.py
│   │   ├── films.py
│   │   └── profile.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_utils.py
│   │   ├── data.py
│   │   └── tmdb.py
│   ├── static/
│   │   ├── actors/
│   │   ├── img/
│   │   ├── js/
│   │   ├── default_poster.png
│   │   └── style.css
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── signup.html
│       ├── profile.html
│       ├── film_detail.html
│       ├── film_availability.html
│       ├── actor_films.html
│       ├── my_library.html
│       ├── my_rentals.html
│       └── film_form.html
│
├── docker-compose.yml
└── README.md
```

---

## 📦 Prérequis

- Docker
- Docker Compose
- Une clé API TMDb

---

## 🔑 Configuration TMDb

L’app utilise TMDb. Il faut donc fournir une clé API.

Selon votre `docker-compose.yml`, la clé peut être passée via une variable d’environnement.
Le plus simple : créer un fichier `.env` à la racine du projet :

```bash
TMDB_API_KEY=VOTRE_CLE_TMDB
```

Si votre projet attend un autre nom de variable (ex: `TMDB_BEARER_TOKEN`), adaptez‑le à votre `config.py`.

---

## ▶️ Installation & Lancement (sur une seule machine)

1) Cloner le dépôt

```bash
git clone <URL_DU_REPO>
```

2) Se placer dans le dossier du projet

```bash
cd popcornhub
```

3) Build + run

```bash
docker-compose up --build
```

4) Ouvrir l’application

- **Web** : `http://localhost:8080`
- **API** : `http://localhost:5000` (souvent utilisé en interne par le web)

> Si votre `docker-compose.yml` expose d’autres ports, utilisez ceux indiqués dans le fichier.

---

## 🗃️ Données & persistance

Toutes les données (utilisateurs, vidéothèques, locations, avis, etc.) sont stockées dans :

- `data/data.json`

Tant que ce fichier existe (et que le volume Docker est bien monté), vos données restent persistantes.

---

## 🧪 Utilisation rapide (flow conseillé)

1. Créer un compte utilisateur
2. Se connecter
3. Rechercher un film
4. Ajouter le film à sa vidéothèque
5. Définir les formats et les prix (Blu‑ray / Digital + durée max)
6. Rendre le film **public**
7. Se connecter avec un autre compte
8. Louer le film (choisir format + nombre de jours via le popup)
9. Rendre le film (confirmation)
10. Laisser un avis sur le film

---

## 📝 Notes de fonctionnement (important)

- **Un exemplaire = (owner_id + movie_id)**
  - tant qu’un exemplaire est loué → il est **bloqué**
  - la page *Exemplaires disponibles* affiche alors **Indisponible** + la date **Disponible à partir du …**
  - une fois rendu → il redevient louable

---

## 🧾 Licence / Crédits

Projet réalisé par Sébastien Porfiri et Elie Coutelle dans un cadre pédagogique (RT0705 – Université de Reims Champagne‑Ardenne).

🍿 Bon test !