# 🍿 PopCornHub

**Application Web & API pour la gestion d'une vidéothèque**

PopCornHub est une application web complète permettant de gérer une vidéothèque : films, favoris, locations, avis utilisateurs, etc. Elle repose sur une architecture à deux niveaux avec un backend API Flask et un frontend Web Flask, pouvant être déployés sur deux machines distinctes.

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

---

## 📖 Description

PopCornHub est une application permettant de :

- 🎞️ Consulter les films avec leurs détails, affiches et acteurs
- 📚 Gérer sa vidéothèque personnelle
- ⭐ Ajouter des films en favoris
- 🛒 Gérer les locations et les retours
- ✍️ Publier des avis sur les films
- 👥 Créer et gérer des comptes utilisateurs
- 🔧 Pour les administrateurs : ajouter, supprimer et gérer les films via TMDb

Une série de données d'exemple est fournie dans `data/data.json` pour faciliter les tests.

---

## 🏗️ Architecture du projet

```
PopCornHub
│
├── Machine 1 : Backend Flask API
│   └── popcornhub-api/
│        ├── app.py
│        ├── requirements.txt
│        ├── data/data.json
│        └── Dockerfile
│
└── Machine 2 : Frontend Web Flask
    └── popcornhub-web/
         ├── app.py
         ├── templates/
         ├── static/
         ├── Dockerfile
         └── config.py
```

---

## ⚙️ Technologies utilisées

- **Flask** - Framework pour l'API et le frontend
- **Python 3.x** - Langage de programmation
- **HTML / CSS / Jinja / Bootstrap** - Interface utilisateur
- **JSON** - Stockage des données
- **Docker & Docker Compose** - Conteneurisation
- **TMDb API** - Intégration avec The Movie Database

---

## 🚀 Installation & Lancement

### Prérequis

- Docker et Docker Compose installés
- Accès réseau entre les deux machines

### Déploiement sur deux machines

| Machine | Service | Fichier à lancer |
|---------|---------|------------------|
| Machine 1 | Backend API | `docker-compose-api.yml` |
| Machine 2 | Frontend Web | `docker-compose-web.yml` |

### Étape 1 : Cloner le projet (sur les deux machines)

```bash
git clone git@gitlab-mi.univ-reims.fr:rt0705/popcornhub.git
cd popcornhub
```

### Étape 2 : Lancer l'API (Machine 1)

```bash
docker-compose -f docker-compose-api.yml up --build
```

➡️ **API disponible sur** : `http://localhost:5000`

### Étape 3 : Lancer le site Web (Machine 2)

Avant de lancer le frontend, configurez l'adresse de l'API dans `popcornhub-web/config.py` :

```python
API_BASE_URL = "http://IP_MACHINE_API:5000"
```

Remplacez `IP_MACHINE_API` par l'adresse IP de la Machine 1.

Puis lancez le frontend :

```bash
docker-compose -f docker-compose-web.yml up --build
```

➡️ **Interface Web disponible sur** : `http://localhost:8080`

### Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| Interface web | `http://localhost:8080` | Site utilisateur |
| Backend API | `http://localhost:5000` | API REST Flask |

---

## 🗂️ Gestion des données

Le fichier de données est situé dans :

```
popcornhub-api/data/data.json
```

Il contient les informations suivantes :

- Utilisateurs
- Films
- Favoris
- Avis
- Locations

📌 **Note** : Des données d'exemple ont été ajoutées pour faciliter l'évaluation et les tests.

---

## 🎬 Intégration TMDb

Le projet utilise **The Movie Database (TMDb)** pour récupérer automatiquement :

- Affiches des films
- Titres et descriptions
- Notes et popularité
- Informations sur les acteurs
- Genres

L'intégration se fait via l'API publique de TMDb.

---

## 🔐 Comptes disponibles

| Rôle | Identifiant | Mot de passe |
|------|-------------|--------------|
| 👑 Administrateur | `admin` | `admin` |

---

## 📁 Structure du projet

```
PopCornHub/
│
├── popcornhub-api/           # Backend API
│   ├── app.py                # Application Flask API
│   ├── requirements.txt      # Dépendances Python
│   ├── data/
│   │   └── data.json         # Base de données JSON
│   └── Dockerfile            # Configuration Docker
│
├── popcornhub-web/           # Frontend Web
│   ├── app.py                # Application Flask Web
│   ├── config.py             # Configuration (URL API)
│   ├── templates/            # Templates Jinja
│   ├── static/               # Fichiers statiques (CSS, JS)
│   └── Dockerfile            # Configuration Docker
│
├── docker-compose-api.yml    # Docker Compose pour l'API
├── docker-compose-web.yml    # Docker Compose pour le Web
└── README.md                 # Ce fichier
```

---

## 🧪 Instructions

### Procédure de test

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
