from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from datetime import datetime

from config import SECRET_KEY

# Services maison
from services.data import load_data
from services.tmdb import tmdb_get, tmdb_movie_to_film

# ---------- Création de l'app ----------

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Limites TMDb / pagination
MAX_FILMS = 1000            # on limite à 1000 films max
TMDB_PAGE_SIZE = 20         # taille d'une page TMDb
MAX_PAGES = MAX_FILMS // TMDB_PAGE_SIZE


# ---------- Helper auth : login_required ----------

def login_required(view):
    """
    Décorateur pour forcer la connexion.
    Utilisé dans les blueprints via 'from app import login_required'.
    """
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


# ---------- Enregistrement des blueprints ----------

from routes.auth import auth_bp
from routes.films import films_bp
from routes.favorites import favorites_bp
from routes.profile import profile_bp

app.register_blueprint(auth_bp)
app.register_blueprint(films_bp)
app.register_blueprint(favorites_bp)
app.register_blueprint(profile_bp)


# ---------- Accueil : liste de films TMDb ----------

@app.route("/", endpoint="index")
def index():
    data = load_data()

    # ----- paramètres de la requête -----
    q = request.args.get("q", "").strip()
    genre_id = request.args.get("genre", "").strip()
    try:
        page = int(request.args.get("page", 1) or 1)
    except ValueError:
        page = 1
    page = max(page, 1)

    params = {"page": page}

    # ----- appel TMDb suivant le contexte -----
    try:
        if q:
            params["query"] = q
            tmdb_page = tmdb_get("/search/movie", params)

        elif genre_id:
            params["with_genres"] = genre_id
            tmdb_page = tmdb_get("/discover/movie", params)

        else:
            tmdb_page = tmdb_get("/movie/popular", params)

        movies = tmdb_page.get("results", []) or []
    except Exception:
        tmdb_page = {}
        movies = []

    # ----- masquer les films supprimés (si jamais tu utilises encore deleted_films) -----
    deleted_ids = set(data.get("deleted_films", []))
    movies = [m for m in movies if m.get("id") not in deleted_ids]

    films_page = [tmdb_movie_to_film(m) for m in movies]

    # ----- pagination / limites -----
    total_results_api = tmdb_page.get("total_results", len(movies))
    total_pages_api = tmdb_page.get("total_pages", 1)
    max_pages = min(total_pages_api, MAX_PAGES)

    if page > max_pages and max_pages > 0:
        page = max_pages

    total_films = min(total_results_api, MAX_FILMS)

    # ----- favoris / vidéothèque (ancienne structure library pour compat) -----
    favorite_ids = set()
    library_ids = set()
    if session.get("user_id"):
        uid = str(session["user_id"])
        favorite_ids = set(data.get("favorites", {}).get(uid, []))
        library_ids = set(data.get("library", {}).get(uid, []))

    # ----- liste des genres -----
    try:
        genres_data = tmdb_get("/genre/movie/list", {"language": "fr-FR"})
        genres = genres_data.get("genres", [])
    except Exception:
        genres = []

    return render_template(
        "index.html",
        films=films_page,
        total_films=total_films,
        page=page,
        total_pages=max_pages,
        favorite_ids=favorite_ids,
        library_ids=library_ids,
        q=q,
        genres=genres,
        selected_genre=genre_id,
    )


# ---------- Lancement ----------

if __name__ == "__main__":
    # debug=False en prod, True si tu veux les erreurs détaillées
    app.run(host="0.0.0.0", port=5000, debug=False)