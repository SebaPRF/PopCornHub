from flask import Flask, jsonify, request, abort
from pathlib import Path
import json
from werkzeug.security import generate_password_hash

app = Flask(__name__)

DATA_PATH = Path("/data/data.json")

def load_data():
    if not DATA_PATH.exists():
        data = {
                "users": [],
                "library": {},
                "favorites": {},
                "reviews": [],
                "rentals": [],
                "user_owns": [],
                "deleted_films": [],
                "film_overrides": {},
                "catalog": []
                }
        save_data(data)
        return data

    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(DATA_PATH)

@app.get("/data")
def get_data():
    return jsonify(load_data()), 200


@app.put("/data")
def put_data():
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