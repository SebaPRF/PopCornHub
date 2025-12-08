from flask import Flask, jsonify, request, abort
from pathlib import Path
import json
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Fichier JSON partagé (volume /data monté par docker-compose)
DATA_PATH = Path("/data/data.json")


def load_data():
    """Charge le contenu de data.json, crée la structure vide si nécessaire."""
    if not DATA_PATH.exists():
        data = {
            "users": [],
            "favorites": {},
            "library": {},
            "rentals": [],
            "reviews": [],
        }
        save_data(data)
        return data

    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    """Écrit data.json de manière atomique."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(DATA_PATH)


def init_admin():
    """Crée un admin par défaut si aucun admin n'existe encore."""
    data = load_data()
    users = data.get("users", [])
    has_admin = any(u.get("is_admin") for u in users)

    if not has_admin:
        admin_id = max((u["id"] for u in users), default=0) + 1
        users.append(
            {
                "id": admin_id,
                "username": "admin",
                "email": "admin@popcornhub.local",
                "password_hash": generate_password_hash("admin"),
                "is_admin": True,
            }
        )
        data["users"] = users
        save_data(data)
        print("✅ Admin API créé : login=admin / password=admin")


init_admin()


@app.get("/data")
def get_data():
    """GET /data -> renvoie tout le JSON."""
    return jsonify(load_data()), 200


@app.put("/data")
def put_data():
    """
    PUT /data
    Body JSON = structure complète à sauvegarder.
    """
    if not request.is_json:
        abort(400, description="Body must be JSON")
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400, description="Root JSON must be an object")
    save_data(data)
    return "", 204


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)