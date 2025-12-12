# 🍿 PopCornHub

PopCornHub est une application web **Flask** de **gestion de vidéothèque** et de **location de films entre utilisateurs**.
Les fiches films (affiche, synopsis, casting, bande‑annonce…) sont récupérées via **TMDb**, et les données applicatives sont persistées dans un simple fichier **JSON**.

---

## 📌 Table des matières

- [Objectif](#-objectif)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture du projet](#️-architecture-du-projet)
- [Prérequis](#-prérequis)
- [Installation & lancement](#-installation--lancement)
- [Gestion des données](#️-gestion-des-données)
- [Utilisation rapide](#-utilisation-rapide)
- [Notes de fonctionnement](#-notes-de-fonctionnement)
- [Licence / Crédits](#-licence--crédits)

---

## 🎯 Objectif

Ce projet a été réalisé dans un cadre pédagogique.
L’objectif est de proposer une application **fonctionnelle**, **cohérente** et **facile à déployer**, sans base de données SQL (stockage en **JSON**).

---

## 🧠 Fonctionnalités

### 🎞️ Films
- Recherche et affichage via **TMDb**
- Affiche, synopsis, année, genres, acteurs
- Bande‑annonce (YouTube)

### 📚 Vidéothèque
- Ajouter un film à sa vidéothèque
- Définir les formats possédés : **Blu‑ray** et/ou **Digital / Streaming**
- Définir : **prix de location** + **durée maximale**
- Rendre un film **public** (louable) ou **privé**
- Modifier / supprimer un film de sa vidéothèque (avec confirmation)

### 🛒 Locations
- Louer un film à un autre utilisateur
- Choisir **format** + **nombre de jours** via un popup
- Un exemplaire ne peut être loué **qu’une seule fois à la fois**
- Si l’exemplaire est déjà loué : affichage **Indisponible** + **Disponible à partir du …**
- Rendre un film avant la date de fin (avec confirmation)
- Affichage des locations dans le profil (affiche, dates, format, bouton “Rendre”)

### ✍️ Avis
- Ajouter / modifier un avis sur un film
- Note de 1 à 5 + commentaire
- Moyenne affichée sur la fiche film

### 👤 Utilisateurs
- Création de compte
- Connexion / Déconnexion

---

## 🏗️ Architecture du projet

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

## ▶️ Installation & lancement

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
- **API** : `http://localhost:5000` (principalement utilisée par le web)

---

## 🗂️ Gestion des données

Toutes les données (utilisateurs, vidéothèques, locations, avis…) sont stockées dans :

- `data/data.json`

👉 Aucune base de données externe.
👉 Les données restent persistantes tant que le fichier (ou le volume) est conservé.

---

## 🧪 Utilisation rapide

1. Créer un compte utilisateur
2. Se connecter
3. Rechercher un film
4. Ajouter le film à sa vidéothèque
5. Définir les formats et prix
6. Rendre le film public
7. Louer un film depuis un autre compte
8. Rendre le film
9. Laisser un avis

---

## 📝 Notes de fonctionnement

- **Un exemplaire = (owner_id + movie_id)**
  - tant qu’un exemplaire est loué → il est **bloqué**
  - la page **Exemplaires disponibles** affiche alors **Indisponible** + **Disponible à partir du …**
  - une fois rendu → l’exemplaire redevient louable

---

## 🧾 Licence / Crédits

Projet réalisé par **Sébastien Porfiri** et **Elie Coutelle** dans le cadre pédagogique du module **RT0705** – Université de Reims Champagne‑Ardenne.

🍿 Bon test !