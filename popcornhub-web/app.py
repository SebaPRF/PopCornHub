from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
import os

API_URL = os.getenv("API_URL", "http://10.11.37.1:5000")

import json
from pathlib import Path
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from config import SECRET_KEY, TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMG_BASE

import requests

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ---------- Limites TMDb / pagination (1000 films max) ----------
MAX_FILMS = 1000          
TMDB_PAGE_SIZE = 20      
MAX_PAGES = MAX_FILMS // TMDB_PAGE_SIZE  

# ---------- Gestion du fichier JSON (aucune base SQL) ----------

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


# ---------- Helpers TMDb ----------


def tmdb_get(path, params=None):
    """
    Appel générique à TMDb : GET /path?api_key=...
    """
    url = f"{TMDB_BASE_URL}{path}"
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    return r.json()


def tmdb_movie_to_film(movie, credits=None):
    """
    Convertit un objet 'movie' TMDb en dict 'film' compatible avec tes templates.
    """
    titre = movie.get("title") or movie.get("name")
    release_date = movie.get("release_date") or movie.get("first_air_date") or ""
    annee = int(release_date[:4]) if len(release_date) >= 4 else None
    resume = movie.get("overview") or ""
    poster_path = movie.get("poster_path")
    affiche_url = f"{TMDB_IMG_BASE}/w500{poster_path}" if poster_path else None

    genres = []
    if "genres" in movie:
        genres = [g.get("name") for g in movie.get("genres", []) if g.get("name")]
    elif "genre_ids" in movie:
        genres = []

    realisateur = ""
    if credits:
        directors = [
            c["name"]
            for c in credits.get("crew", [])
            if c.get("job") == "Director" and c.get("name")
        ]
        if directors:
            realisateur = ", ".join(directors)

    return {
        "id": movie["id"],
        "titre": titre,
        "annee": annee,
        "realisateur": realisateur,
        "resume": resume,
        "affiche_url": affiche_url,
        "genres": genres,
    }


def tmdb_search_person(name: str):
    if not name:
        return None
    data = tmdb_get("/search/person", {"query": name, "include_adult": False})
    results = data.get("results", [])
    if not results:
        return None
    return results[0]


def tmdb_person_image_url(person):
    from flask import url_for

    if not person:
        return url_for("static", filename="actors/default_actor.png")

    path = person.get("profile_path")
    if not path:
        return url_for("static", filename="actors/default_actor.png")

    return f"{TMDB_IMG_BASE}/w185{path}"


def tmdb_movie_trailer_key(title: str, year: int | None):
    """
    Recherche un film par titre + année, puis renvoie la clé YouTube d'un trailer.
    Utilisé dans film_detail.
    """
    if not title:
        return None
    params = {"query": title}
    if year:
        params["year"] = year
    data = tmdb_get("/search/movie", params)
    results = data.get("results", [])
    if not results:
        return None
    movie_id = results[0].get("id")
    if not movie_id:
        return None

    data = tmdb_get(f"/movie/{movie_id}/videos", {"language": "fr-FR"})
    videos = data.get("results", [])

    for v in videos:
        if (
            v.get("site") == "YouTube"
            and v.get("type") == "Trailer"
            and v.get("iso_639_1") in ("fr", "fr-FR")
        ):
            return v.get("key")

    # 2) n'importe quel trailer YouTube
    for v in videos:
        if v.get("site") == "YouTube" and v.get("type") == "Trailer":
            return v.get("key")

    return None


# ---------- Helpers auth ----------


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        data = load_data()
        user = get_user_by_id(data, session.get("user_id"))
        if not user or not user.get("is_admin"):
            flash("Accès réservé à l'administrateur.", "warning")
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapped

# ---------- Initialisation : création de l'admin dans data.json ----------

def init_data():
    data = load_data()
    has_admin = any(u.get("is_admin") for u in data["users"])
    if not has_admin:
        admin_id = get_next_id(data["users"])
        pwd_hash = generate_password_hash("admin")
        data["users"].append(
            {
                "id": admin_id,
                "username": "admin",
                "email": "admin@popcornhub.local",
                "password_hash": pwd_hash,
                "is_admin": True,
            }
        )
        save_data(data)
        print("✅ Admin créé : login=admin / password=admin")

# ---------- Routes auth ----------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    data = load_data()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Tous les champs sont obligatoires.", "danger")
            return redirect(url_for("signup"))

        # Vérifier si le nom d'utilisateur existe déjà
        existing = find_user_by_username(data, username)
        if existing is not None:
            flash("Ce nom d'utilisateur existe déjà.", "danger")
            return redirect(url_for("signup"))

        # Créer le nouvel utilisateur (sans email)
        new_user = {
            "id": get_next_id(data["users"]),
            "username": username,
            "password_hash": generate_password_hash(password),
            "is_admin": False,
        }

        data["users"].append(new_user)
        save_data(data)

        flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    data = load_data()

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = find_user_by_username(data, username)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Identifiants invalides.", "danger")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["is_admin"] = bool(user.get("is_admin"))

        flash("Connexion réussie.", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("index"))

    return render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    """Déconnecte l'utilisateur et le renvoie vers la vidéothèque."""
    session.clear()
    flash("Vous êtes maintenant déconnecté(e).", "info")
    return redirect(url_for("index"))

# ---------- Page profil (favoris + liste + locations) ----------

@app.route("/profile")
@login_required
def profile():
    data = load_data()
    user_id = session["user_id"]
    user_id_str = str(user_id)

    active_tab = request.args.get("tab", "favorites")

    fav_ids = data["favorites"].get(user_id_str, [])
    lib_ids = data["library"].get(user_id_str, [])

    def fetch_film_from_tmdb(tmdb_id):
        movie = tmdb_get(f"/movie/{tmdb_id}")
        return tmdb_movie_to_film(movie)

    favorite_films = [fetch_film_from_tmdb(fid) for fid in fav_ids]
    library_films = [fetch_film_from_tmdb(fid) for fid in lib_ids]

    # Locations
    now = datetime.utcnow()
    rentals = []
    for r in data["rentals"]:
        if r["user_id"] != user_id:
            continue
        movie = tmdb_get(f"/movie/{r['movie_id']}")
        film = tmdb_movie_to_film(movie)
        exp = datetime.fromisoformat(r["expires_at"])
        rentals.append(
            {
                "film": film,
                "rented_at": r["rented_at"],
                "expires_at": r["expires_at"],
                "is_active": exp > now,
                "price_eur": r["price_cents"] / 100.0,
            }
        )

    return render_template(
        "profile.html",
        active_tab=active_tab,
        favorite_films=favorite_films,
        library_films=library_films,
        rentals=rentals,
        favorite_ids=set(fav_ids),
        library_ids=set(lib_ids),
    )

# ---------- Accueil : films populaires TMDb ----------

@app.route("/")
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

    # ----- masquer les films "supprimés" par l'admin -----
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

    # ----- favoris / vidéothèque de l'utilisateur -----
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

# ---------- Page filmographie acteur ----------

@app.route("/actors/<actor_name>")
def actor_films(actor_name):
    # 1) Cherche l'acteur
    person = None
    try:
        person = tmdb_search_person(actor_name)
    except Exception:
        person = None

    if not person:
        return render_template(
            "actor_films.html",
            actor_name=actor_name,
            actor_image_url=tmdb_person_image_url(None),
            actor_bio="",
            films=[],
        )

    person_id = person["id"]
    credits = tmdb_get(f"/person/{person_id}/movie_credits")
    cast_movies = credits.get("cast", [])

    films_for_actor = [tmdb_movie_to_film(m) for m in cast_movies]

    actor_image_url = tmdb_person_image_url(person)
    actor_bio = person.get("known_for_department", "")

    return render_template(
        "actor_films.html",
        actor_name=person.get("name", actor_name),
        actor_image_url=actor_image_url,
        actor_bio=actor_bio,
        films=films_for_actor,
    )


# ---------- Détail d'un film ----------


@app.route("/films/<int:film_id>")
def film_detail(film_id):
    movie = tmdb_get(f"/movie/{film_id}", {"append_to_response": "credits"})
    credits = movie.get("credits", {})
    film = tmdb_movie_to_film(movie, credits=credits)

    # ----- acteurs + photos via TMDb -----
    actors = []
    for cast in credits.get("cast", [])[:8]:
        name = cast.get("name")
        if not name:
            continue
        try:
            person = tmdb_search_person(name)
        except Exception:
            person = None
        image_url = tmdb_person_image_url(person)
        actors.append({"name": name, "image_url": image_url})

    # ----- vidéothèque & favoris -----
    data = load_data()
    in_library = False
    is_favorite = False
    if session.get("user_id") and not session.get("is_admin"):
        uid = str(session["user_id"])
        in_library = film_id in data["library"].get(uid, [])
        is_favorite = film_id in data["favorites"].get(uid, [])

    # ----- avis -----
    reviews = [r for r in data["reviews"] if r["movie_id"] == film_id]

    users_by_id = {u["id"]: u for u in data["users"]}
    for r in reviews:
        u = users_by_id.get(r["user_id"])
        r["username"] = u["username"] if u else "?"

    if reviews:
        avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
        reviews_count = len(reviews)
    else:
        avg_rating = None
        reviews_count = 0

    user_review = None
    if session.get("user_id"):
        for r in reviews:
            if r["user_id"] == session["user_id"]:
                user_review = r
                break

    # ----- location active ? -----
    is_rented = False
    rental_expires_at = None
    if session.get("user_id"):
        for r in data["rentals"]:
            if r["user_id"] == session["user_id"] and r["movie_id"] == film_id:
                expires = datetime.fromisoformat(r["expires_at"])
                if expires > datetime.utcnow():
                    is_rented = True
                    rental_expires_at = expires
                break

    # ----- trailer YouTube via TMDb (recherche par titre/année) -----
    trailer_key = None
    try:
        trailer_key = tmdb_movie_trailer_key(film.get("titre"), film.get("annee"))
    except Exception:
        trailer_key = None

    return render_template(
        "film_detail.html",
        film=film,
        actors=actors,
        in_library=in_library,
        is_favorite=is_favorite,
        reviews=reviews,
        avg_rating=avg_rating,
        reviews_count=reviews_count,
        user_review=user_review,
        is_rented=is_rented,
        rental_expires_at=rental_expires_at,
        trailer_key=trailer_key,
    )


# ---------- Favoris (❤️) ----------


@app.post("/favorite/<int:film_id>")
@login_required
def toggle_favorite(film_id):
    data = load_data()
    uid = str(session["user_id"])
    fav_list = data["favorites"].setdefault(uid, [])

    if film_id in fav_list:
        fav_list.remove(film_id)
        flash("Retiré de vos favoris ❤️‍🩹", "info")
    else:
        fav_list.append(film_id)
        flash("Ajouté à vos favoris ❤️", "success")

    save_data(data)
    return redirect(request.referrer or url_for("index"))


@app.route("/favorites")
@login_required
def favorites():
    data = load_data()
    uid = str(session["user_id"])
    ids = data["favorites"].get(uid, [])

    films = []
    for fid in ids:
        movie = tmdb_get(f"/movie/{fid}")
        films.append(tmdb_movie_to_film(movie))

    return render_template("favorites.html", films=films)

# ---------- Videothèque personnelle / "Ma liste" (📌) ----------

@app.route("/my-library")
@login_required
def my_library():
    data = load_data()
    uid = str(session["user_id"])
    ids = data["library"].get(uid, [])

    films = []
    for fid in ids:
        movie = tmdb_get(f"/movie/{fid}")
        films.append(tmdb_movie_to_film(movie))

    return render_template("my_library.html", films=films)


@app.post("/films/<int:film_id>/add-to-library")
@login_required
def add_to_library(film_id):
    data = load_data()
    uid = str(session["user_id"])
    lib = data["library"].setdefault(uid, [])
    if film_id not in lib:
        lib.append(film_id)
        save_data(data)
        flash("Film ajouté à votre liste 📌", "success")
    return redirect(request.referrer or url_for("my_library"))


@app.post("/films/<int:film_id>/remove-from-library")
@login_required
def remove_from_library(film_id):
    data = load_data()
    uid = str(session["user_id"])
    lib = data["library"].setdefault(uid, [])
    if film_id in lib:
        lib.remove(film_id)
        save_data(data)
        flash("Film retiré de votre liste 📌", "info")
    return redirect(request.referrer or url_for("my_library"))


# ---------- Locations ----------


@app.post("/rent/<int:film_id>")
@login_required
def rent_film(film_id):
    data = load_data()
    user_id = session["user_id"]

    duration_days = 3
    price_cents = 399
    now = datetime.utcnow()

    for r in data["rentals"]:
        if r["user_id"] == user_id and r["movie_id"] == film_id:
            last_expires = datetime.fromisoformat(r["expires_at"])
            if last_expires > now:
                flash(
                    "Ce film est déjà loué jusqu’au "
                    f"{last_expires.strftime('%d/%m/%Y %H:%M')} 😄",
                    "warning",
                )
                return redirect(url_for("film_detail", film_id=film_id))

    expires = now + timedelta(days=duration_days)
    rental_id = get_next_id(data["rentals"])

    data["rentals"].append(
        {
            "id": rental_id,
            "user_id": user_id,
            "movie_id": film_id,
            "rented_at": now.isoformat(timespec="seconds"),
            "expires_at": expires.isoformat(timespec="seconds"),
            "price_cents": price_cents,
        }
    )
    save_data(data)

    flash(f"Film loué pour {duration_days} jours ✅", "success")
    return redirect(url_for("film_detail", film_id=film_id))


@app.get("/watch/<int:film_id>")
@login_required
def watch_film(film_id):
    data = load_data()
    user_id = session["user_id"]

    now = datetime.utcnow()
    is_active = False
    expires_at = None

    for r in data["rentals"]:
        if r["user_id"] == user_id and r["movie_id"] == film_id:
            exp = datetime.fromisoformat(r["expires_at"])
            if exp > now:
                is_active = True
                expires_at = exp
            break

    if not is_active:
        flash("Vous devez louer ce film pour le regarder.", "warning")
        return redirect(url_for("film_detail", film_id=film_id))

    movie = tmdb_get(f"/movie/{film_id}")
    film = tmdb_movie_to_film(movie)

    return render_template("watch.html", film=film, expires_at=expires_at)


@app.route("/my-rentals")
@login_required
def my_rentals():
    data = load_data()
    user_id = session["user_id"]

    now = datetime.utcnow()
    rentals = []

    for r in data["rentals"]:
        if r["user_id"] != user_id:
            continue
        movie = tmdb_get(f"/movie/{r['movie_id']}")
        film = tmdb_movie_to_film(movie)
        expires = datetime.fromisoformat(r["expires_at"])
        rentals.append(
            {
                "titre": film["titre"],
                "annee": film["annee"],
                "realisateur": film.get("realisateur"),
                "rented_at": r["rented_at"],
                "expires_at": r["expires_at"],
                "is_active": expires > now,
                "film_id": r["movie_id"],
                "price_eur": r["price_cents"] / 100.0,
            }
        )

    return render_template("my_rentals.html", rentals=rentals)


# ---------- Avis / notes ----------

@app.post("/films/<int:film_id>/review")
@login_required
def add_or_update_review(film_id):
    data = load_data()
    user_id = session["user_id"]

    try:
        rating = int(request.form["rating"])
    except (KeyError, ValueError):
        rating = 0
    comment = request.form.get("comment", "").strip()
    rating = max(1, min(5, rating))

    existing = None
    for r in data["reviews"]:
        if r["user_id"] == user_id and r["movie_id"] == film_id:
            existing = r
            break

    now = datetime.utcnow().isoformat(timespec="seconds")

    if existing:
        existing["rating"] = rating
        existing["comment"] = comment
        existing["created_at"] = now
    else:
        review_id = get_next_id(data["reviews"])
        data["reviews"].append(
            {
                "id": review_id,
                "user_id": user_id,
                "movie_id": film_id,
                "rating": rating,
                "comment": comment,
                "created_at": now,
            }
        )

    save_data(data)
    flash("Votre avis a été enregistré.", "success")
    return redirect(url_for("film_detail", film_id=film_id))


# ---------- Édition d'un film ----------

@app.route("/admin/films/<int:film_id>/edit", methods=["GET", "POST"])
@admin_required
def film_edit(film_id):
    movie = tmdb_get(f"/movie/{film_id}", {"append_to_response": "credits"})
    credits = movie.get("credits", {})
    film = tmdb_movie_to_film(movie, credits=credits)

    data = load_data()
    overrides = data.get("film_overrides", {})
    current = overrides.get(str(film_id), {})

    if request.method == "POST":
        titre = request.form.get("titre", "").strip() or film["titre"]
        resume = request.form.get("resume", "").strip() or film["resume"]
        realisateur = request.form.get("realisateur", "").strip() or film.get("realisateur", "")
        genres_str = request.form.get("genres", "").strip()
        genres = [g.strip() for g in genres_str.split(",")] if genres_str else film.get("genres", [])

        overrides[str(film_id)] = {
            "titre": titre,
            "resume": resume,
            "realisateur": realisateur,
            "genres": genres,
        }
        data["film_overrides"] = overrides
        save_data(data)

        flash("Film mis à jour (override admin).", "success")
        return redirect(url_for("film_detail", film_id=film_id))

    form_data = {
        "titre": current.get("titre", film["titre"]),
        "resume": current.get("resume", film["resume"]),
        "realisateur": current.get("realisateur", film.get("realisateur", "")),
        "genres": ", ".join(current.get("genres", film.get("genres", []))),
    }

    return render_template("film_form.html", film_id=film_id, form=form_data)

# ---------- Suppression d'un film ----------

@app.post("/admin/films/<int:film_id>/delete")
@admin_required
def film_delete(film_id):
    data = load_data()

    catalog = data.get("catalog", [])
    if film_id in catalog:
        catalog.remove(film_id)
        data["catalog"] = catalog

    deleted = set(data.get("deleted_films", []))
    deleted.add(film_id)
    data["deleted_films"] = list(deleted)

    save_data(data)

    flash("Le film a été supprimé de la vidéothèque.", "info")
    return redirect(url_for("index"))

# ---------- Ajout d'un film ----------
 
@app.route("/admin/films/add", methods=["GET", "POST"])
@admin_required
def admin_add_film():
    data = load_data()
    catalog = data.get("catalog", []) 

    error = None
    film = None 

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        year_str = request.form.get("year", "").strip()
        chosen_id = request.form.get("movie_id")

        if chosen_id:
            movie_id = int(chosen_id)

            data = load_data()
            catalog = data.get("catalog", [])
            deleted = set(data.get("deleted_films", []))

            if movie_id in catalog:
                error = "Ce film est déjà dans la vidéothèque."
            else:
                catalog.append(movie_id)
                data["catalog"] = catalog

                if movie_id in deleted:
                    deleted.remove(movie_id)
                    data["deleted_films"] = list(deleted)

                save_data(data)
                flash("Film ajouté à la vidéothèque.", "success")
                return redirect(url_for("film_detail", film_id=movie_id))

        else:
            if not title:
                error = "Veuillez saisir un titre."
            else:
                params = {"query": title}
                if year_str:
                    try:
                        params["year"] = int(year_str)
                    except ValueError:
                        pass

                try:
                    res = tmdb_get("/search/movie", params)
                    results = res.get("results", [])
                except Exception:
                    results = []
                    error = "Erreur lors de la recherche du film (TMDb)."

                if results:
                    movie = results[0]
                    movie_id = movie["id"]
                    film = {
                        "id": movie_id,
                        "titre": movie.get("title") or movie.get("original_title") or title,
                        "annee": (movie.get("release_date") or "")[:4],
                        "resume": movie.get("overview") or "",
                        "affiche_url": f"{TMDB_IMG_BASE}/w300{movie['poster_path']}" if movie.get("poster_path") else None,
                    }
                    if movie_id in catalog and not error:
                        error = "Ce film est déjà dans la vidéothèque."
                elif not error:
                    error = "Film non trouvé. Vérifiez le titre (et éventuellement l'année)."

    return render_template("admin_add_film.html", error=error, film=film)

# ---------- Lancement ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)