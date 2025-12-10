from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
)
from datetime import datetime, timedelta

from services.data import (
    load_data,
    save_data,
    get_next_id,
    find_ownership,
)
from services.tmdb import (
    tmdb_get,
    tmdb_movie_to_film,
    tmdb_search_person,
    tmdb_person_image_url,
    tmdb_movie_trailer_key,
)

from services.auth_utils import login_required

films_bp = Blueprint("films_bp", __name__)

# ---------- Page filmographie acteur ----------

@films_bp.route("/actors/<actor_name>", endpoint="actor_films")
def actor_films(actor_name):
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

@films_bp.route("/films/<int:film_id>", endpoint="film_detail")
def film_detail(film_id):
    movie = tmdb_get(f"/movie/{film_id}", {"append_to_response": "credits"})
    credits = movie.get("credits", {})
    film = tmdb_movie_to_film(movie, credits=credits)

    # Acteurs
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

    data = load_data()
    in_library = False
    is_favorite = False
    if session.get("user_id"):
        uid = str(session["user_id"])
        in_library = film_id in data.get("library", {}).get(uid, [])
        is_favorite = film_id in data.get("favorites", {}).get(uid, [])

    # Avis
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

    # Location active ?
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

    # Propriétaires
    ownership_for_user = None
    owners_count = 0

    if session.get("user_id"):
        ownership_for_user = find_ownership(data, session["user_id"], film_id)

    owners_for_film = [
        o for o in data.get("user_owns", [])
        if o["movie_id"] == film_id
    ]
    owners_count = len(owners_for_film)

    # Trailer YouTube
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
        ownership_for_user=ownership_for_user,
        owners_count=owners_count,
    )


@films_bp.post("/films/<int:film_id>/own", endpoint="own_film")
@login_required
def own_film(film_id):
    """Déclare que l'utilisateur possède ce film (bluray / digital) + prix."""
    data = load_data()
    user_id = session["user_id"]

    has_bluray = bool(request.form.get("has_bluray"))
    has_digital = bool(request.form.get("has_digital"))

    if not has_bluray and not has_digital:
        flash("Veuillez choisir au moins un format (Blu-ray ou Digital).", "warning")
        return redirect(url_for("film_detail", film_id=film_id))

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

    bluray_price = parse_float("bluray_price") if has_bluray else None
    digital_price = parse_float("digital_price") if has_digital else None
    bluray_max_days = parse_int("bluray_max_days") if has_bluray else None
    digital_max_days = parse_int("digital_max_days") if has_digital else None

    existing = find_ownership(data, user_id, film_id)

    if existing:
        existing["has_bluray"] = has_bluray
        existing["has_digital"] = has_digital
        existing["bluray_price"] = bluray_price
        existing["digital_price"] = digital_price
        existing["bluray_max_days"] = bluray_max_days
        existing["digital_max_days"] = digital_max_days
    else:
        data.setdefault("user_owns", []).append(
            {
                "user_id": user_id,
                "movie_id": film_id,
                "has_bluray": has_bluray,
                "has_digital": has_digital,
                "bluray_price": bluray_price,
                "digital_price": digital_price,
                "bluray_max_days": bluray_max_days,
                "digital_max_days": digital_max_days,
                "is_public": False,
            }
        )

    save_data(data)
    flash("Le film a été ajouté à votre vidéothèque.", "success")
    return redirect(url_for("film_detail", film_id=film_id))


@films_bp.route("/films/<int:film_id>/availability", endpoint="film_availability")
def film_availability(film_id):
    # 1) Infos du film
    try:
        movie = tmdb_get(f"/movie/{film_id}")
        film = tmdb_movie_to_film(movie)
    except Exception:
        abort(404)

    # 2) Propriétaires
    data = load_data()
    users_by_id = {u["id"]: u for u in data.get("users", [])}

    ownerships_raw = [
        o
        for o in data.get("user_owns", [])
        if o.get("movie_id") == film_id and o.get("is_public", False)
    ]

    entries = []
    for own in ownerships_raw:
        user = users_by_id.get(own["user_id"])
        if not user:
            continue

        if session.get("user_id") == own["user_id"]:
            continue

        has_bluray = bool(own.get("has_bluray"))
        has_digital = bool(own.get("has_digital"))

        bluray_price = own.get("bluray_price")
        digital_price = own.get("digital_price")

        prices = [p for p in (bluray_price, digital_price) if p is not None]
        min_price = min(prices) if prices else None

        seller_rating = own.get("seller_rating")  # placeholder

        entries.append(
            {
                "owner_id": user["id"],
                "owner_name": user["username"],
                "has_bluray": has_bluray,
                "has_digital": has_digital,
                "bluray_price": bluray_price,
                "digital_price": digital_price,
                "bluray_max_days": own.get("bluray_max_days"),
                "digital_max_days": own.get("digital_max_days"),
                "min_price": min_price,
                "seller_rating": seller_rating,
            }
        )

    # 3) Filtres
    format_filter = request.args.get("format", "all")
    sort_by = request.args.get("sort_by", "price_asc")
    max_price_str = request.args.get("max_price", "").strip()

    if format_filter == "bluray":
        entries = [e for e in entries if e["has_bluray"]]
    elif format_filter == "digital":
        entries = [e for e in entries if e["has_digital"]]
    elif format_filter == "both":
        entries = [e for e in entries if e["has_bluray"] and e["has_digital"]]

    max_price = None
    if max_price_str:
        try:
            max_price = float(max_price_str.replace(",", "."))
        except ValueError:
            max_price = None

    if max_price is not None:
        entries = [
            e
            for e in entries
            if e["min_price"] is not None and e["min_price"] <= max_price
        ]

    def price_key(e):
        return e["min_price"] if e["min_price"] is not None else 999999

    def rating_key(e):
        return e["seller_rating"] if e["seller_rating"] is not None else 0

    if sort_by == "price_asc":
        key_func, reverse = price_key, False
    elif sort_by == "price_desc":
        key_func, reverse = price_key, True
    elif sort_by == "rating_desc":
        key_func, reverse = rating_key, True
    elif sort_by == "rating_asc":
        key_func, reverse = rating_key, False
    else:
        key_func, reverse = price_key, False

    entries.sort(key=key_func, reverse=reverse)

    return render_template(
        "film_availability.html",
        film=film,
        entries=entries,
        format_filter=format_filter,
        sort_by=sort_by,
        max_price=max_price_str,
    )


@films_bp.post("/films/<int:film_id>/rent-from-owner/<int:owner_id>", endpoint="rent_from_owner")
@login_required
def rent_from_owner(film_id, owner_id):
    """Loue un exemplaire précis depuis la page 'Exemplaires disponibles'."""
    data = load_data()
    user_id = session["user_id"]
    now = datetime.utcnow()

    # Vérifier location déjà active
    for r in data.get("rentals", []):
        if r["user_id"] == user_id and r["movie_id"] == film_id:
            last_expires = datetime.fromisoformat(r["expires_at"])
            if last_expires > now:
                flash(
                    "Vous avez déjà une location active pour ce film "
                    f"(jusqu’au {last_expires.strftime('%d/%m/%Y %H:%M')}).",
                    "warning",
                )
                return redirect(url_for("film_availability", film_id=film_id))

    # Retrouver l'exemplaire
    own = None
    for o in data.get("user_owns", []):
        if (
            o.get("user_id") == owner_id
            and o.get("movie_id") == film_id
            and o.get("is_public", False)
        ):
            own = o
            break

    if not own:
        flash("Cet exemplaire n’est plus disponible.", "warning")
        return redirect(url_for("film_availability", film_id=film_id))

    fmt = request.form.get("format")
    if fmt not in ("bluray", "digital"):
        flash("Veuillez choisir un format à louer.", "warning")
        return redirect(url_for("film_availability", film_id=film_id))

    if fmt == "bluray" and not own.get("has_bluray"):
        flash("Ce propriétaire ne propose plus le Blu-ray.", "warning")
        return redirect(url_for("film_availability", film_id=film_id))

    if fmt == "digital" and not own.get("has_digital"):
        flash("Ce propriétaire ne propose plus le streaming.", "warning")
        return redirect(url_for("film_availability", film_id=film_id))

    if fmt == "bluray":
        price = own.get("bluray_price")
        max_days = own.get("bluray_max_days")
    else:
        price = own.get("digital_price")
        max_days = own.get("digital_max_days")

    if price is None:
        price = own.get("bluray_price") or own.get("digital_price") or 3.99

    price_cents = int(round(price * 100))

    try:
        duration_days = int(request.form.get("duration_days") or (max_days or 3))
    except ValueError:
        duration_days = max_days or 3

    if duration_days < 1:
        duration_days = 1

    if max_days and duration_days > max_days:
        duration_days = max_days

    expires = now + timedelta(days=duration_days)
    rental_id = get_next_id(data["rentals"])

    data.setdefault("rentals", []).append(
        {
            "id": rental_id,
            "user_id": user_id,
            "movie_id": film_id,
            "owner_id": owner_id,
            "format": fmt,
            "rented_at": now.isoformat(timespec="seconds"),
            "expires_at": expires.isoformat(timespec="seconds"),
            "price_cents": price_cents,
        }
    )
    save_data(data)

    flash("Location créée avec succès ✅", "success")
    return redirect(url_for("profile_locations"))


@films_bp.post("/films/<int:film_id>/review", endpoint="add_or_update_review")
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