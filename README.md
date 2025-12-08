# PopCornHub – Tiers présentation (Web)

Ce dépôt contient le **tiers présentation** de l'application PopCornHub, développé avec **Flask**.
Il s'agit du serveur WEB qui affiche les pages HTML aux utilisateurs et communique en JSON avec le
tiers de données (API REST) déployé sur une autre machine.

---

## 🌐 Architecture

- **Client (tiers 1)** : navigateur WEB
- **Serveur WEB (tiers 2)** : ce projet `popcornhub-web`
- **Serveur API / données (tiers 3)** : projet `popcornhub-api` (autre dépôt GitLab)

Le serveur WEB **ne touche jamais directement au fichier JSON** :  
il récupère et met à jour les données uniquement via l'API REST, au format **JSON**.

---

## 🧩 Technologies utilisées

- Python 3
- Flask
- Jinja2 (templates)
- Bootstrap 5
- Docker / docker-compose

---

## 🚀 Lancement (machine WEB)

Dans le dossier racine du projet :

```bash
docker-compose up --build