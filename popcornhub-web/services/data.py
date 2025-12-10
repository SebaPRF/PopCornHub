import os
import requests

# Adresse par défaut de l'API quand on est dans Docker
# (nom du service dans docker-compose-api.yml)
DEFAULT_API_URL = "http://popcornhub-api:5000"

# Permet de surcharger facilement en dehors de Docker :
#   API_URL=http://127.0.0.1:5000 flask run
API_URL = os.getenv("API_URL", DEFAULT_API_URL)


def load_data():
    r = requests.get(f"{API_URL}/data", timeout=5)
    r.raise_for_status()
    return r.json()


def save_data(data):
    r = requests.put(f"{API_URL}/data", json=data, timeout=5)
    r.raise_for_status()


def get_next_id(items):
    return (max((obj["id"] for obj in items), default=0) + 1) if items else 1


def find_user_by_username(data, username):
    for u in data["users"]:
        if u["username"].lower() == username.lower():
            return u
    return None


def find_user_by_email(data, email):
    for u in data["users"]:
        if u["email"].lower() == email.lower():
            return u
    return None


def get_user_by_id(data, user_id):
    for u in data["users"]:
        if u["id"] == user_id:
            return u
    return None


def find_ownership(data, user_id, movie_id):
    """Retourne l'enregistrement 'user_owns' pour un user/film ou None."""
    for own in data.get("user_owns", []):
        if own["user_id"] == user_id and own["movie_id"] == movie_id:
            return own
    return None