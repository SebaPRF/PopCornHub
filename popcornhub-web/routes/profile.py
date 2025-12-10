from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request,
)
from datetime import datetime

from services.data import (
    load_data,
    save_data,
    get_user_by_id,
    find_ownership,
)
from services.tmdb import tmdb_get, tmdb_movie_to_film

from services.auth_utils import login_required

profile_bp = Blueprint("profile_bp", __name__)


def _build_profile_context():
    data = load_data()
    user_id = session["user_id"]

    # 1) Infos utilisateur
    user = get_user_by_id(data, user_id)

    # 2) Exemplaires possédés (structure user_owns)
    ownerships = [
        own for own in data.get("user_owns", [])
        if own.get("user_id") == user_id
    ]

    # 2b) Compatibilité ancienne logique "library"
    uid_str = str(user_id)
    legacy_ids = data.get("library", {}).get(uid_str, [])
    already_owned_ids = {own["movie_id"] for own in ownerships}

    for fid in legacy_ids:
        if fid in already_owned_ids:
            continue
        ownerships.append(
            {
                "user_id": user_id,
                "movie_id": fid,
                "has_bluray": False,
                "has_digital": False,
                "bluray_price": None,
                "digital_price": None,
                "bluray_max_days": None,
                "digital_max_days": None,
                "is_public": False,
            }
        )

    # 3) Construire la liste des films pour l'affichage
    library_movies = []
    for own in ownerships:
        film_id = own["movie_id"]
        try:
            movie = tmdb_get(f"/movie/{film_id}")
            film = tmdb_movie_to_film(movie)
        except Exception:
            film = {
                "id": film_id,
                "titre": f"Film #{film_id}",
                "annee": None,
                "realisateur": "",
                "resume": "",
                "affiche_url": None,
                "genres": [],
            }

        library_movies.append(
            {
                "movie": film,
                "ownership": own,
            }
        )

    # 4) Locations utilisateur
    now = datetime.utcnow()
    rentals = []

    for r in data.get("rentals", []):
        if r.get("user_id") != user_id:
            continue

        film_id = r["movie_id"]
        try:
            movie = tmdb_get(f"/movie/{film_id}")
            film = tmdb_movie_to_film(movie)
        except Exception:
            film = {
                "id": film_id,
                "titre": f"Film #{film_id}",
                "annee": None,
                "realisateur": "",
            }

        expires = datetime.fromisoformat(r["expires_at"])
        rentals.append(
            {
                "titre": film["titre"],
                "annee": film["annee"],
                "realisateur": film.get("realisateur"),
                "rented_at": r["rented_at"],
                "expires_at": r["expires_at"],
                "is_active": expires > now,
                "film_id": film_id,
                "price_eur": r["price_cents"] / 100.0,
            }
        )

    return {
        "user": user,
        "library_movies": library_movies,
        "rentals": rentals,
    }


@profile_bp.route("/profile", endpoint="profile")
@login_required
def profile():
    ctx = _build_profile_context()
    ctx["active_tab"] = "library"
    return render_template("profile.html", **ctx)


@profile_bp.route("/profile/locations", endpoint="profile_locations")
@login_required
def profile_locations():
    ctx = _build_profile_context()
    ctx["active_tab"] = "locations"
    return render_template("profile.html", **ctx)


@profile_bp.post("/profile/library/<int:film_id>/toggle-public", endpoint="toggle_library_public")
@login_required
def toggle_library_public(film_id):
    """Rend un film de la vidéothèque public ou privé."""
    data = load_data()
    user_id = session["user_id"]

    own = find_ownership(data, user_id, film_id)
    if not own:
        flash("Ce film n'est pas dans votre vidéothèque.", "warning")
        return redirect(url_for("profile"))

    current = bool(own.get("is_public", False))
    own["is_public"] = not current
    save_data(data)

    flash(
        "Le film est maintenant {}."
        .format("public" if own["is_public"] else "privé"),
        "success",
    )
    return redirect(url_for("profile"))


@profile_bp.post("/profile/library/<int:film_id>/update", endpoint="update_library_item")
@login_required
def update_library_item(film_id):
    """Met à jour formats + prix pour un film dans la vidéothèque."""
    data = load_data()
    user_id = session["user_id"]

    own = find_ownership(data, user_id, film_id)
    if not own:
        flash("Ce film n'est pas dans votre vidéothèque.", "warning")
        return redirect(url_for("profile"))

    has_bluray = bool(request.form.get("has_bluray"))
    has_digital = bool(request.form.get("has_digital"))

    if not has_bluray and not has_digital:
        flash("Veuillez choisir au moins un format (Blu-ray ou Digital).", "warning")
        return redirect(url_for("profile"))

    def parse_float(field):
        raw = request.form.get(field, "").strip()
        if not raw:
            return None
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            return None

    def parse_int(field):
        raw = request.form.get(field, "").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    own["has_bluray"] = has_bluray
    own["has_digital"] = has_digital
    own["bluray_price"] = parse_float("bluray_price") if has_bluray else None
    own["digital_price"] = parse_float("digital_price") if has_digital else None
    own["bluray_max_days"] = parse_int("bluray_max_days") if has_bluray else None
    own["digital_max_days"] = parse_int("digital_max_days") if has_digital else None

    save_data(data)
    flash("Votre vidéothèque a été mise à jour.", "success")
    return redirect(url_for("profile"))


@profile_bp.post("/library/<int:film_id>/delete", endpoint="delete_library_item")
@login_required
def delete_library_item(film_id):
    """Supprime un film de la vidéothèque de l'utilisateur."""
    data = load_data()
    user_id = session["user_id"]

    # 1) Supprimer dans user_owns
    owns_before = len(data.get("user_owns", []))
    data["user_owns"] = [
        own
        for own in data.get("user_owns", [])
        if not (own.get("user_id") == user_id and own.get("movie_id") == film_id)
    ]
    owns_after = len(data.get("user_owns", []))

    # 2) Compat ancienne structure "library"
    uid_str = str(user_id)
    lib = data.get("library", {}).get(uid_str)
    if isinstance(lib, list) and film_id in lib:
        lib.remove(film_id)

    save_data(data)

    if owns_after < owns_before or (isinstance(lib, list) and film_id not in lib):
        flash("Film supprimé de votre vidéothèque.", "success")
    else:
        flash("Ce film n'était pas dans votre vidéothèque.", "warning")

    return redirect(url_for("profile"))