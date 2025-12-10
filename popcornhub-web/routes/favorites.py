from flask import Blueprint, redirect, url_for, request, flash, session, render_template

from services.data import load_data, save_data
from services.tmdb import tmdb_get, tmdb_movie_to_film
from services.auth_utils import login_required

favorites_bp = Blueprint("favorites_bp", __name__)


@favorites_bp.post("/favorite/<int:film_id>", endpoint="toggle_favorite")
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


@favorites_bp.route("/favorites", endpoint="favorites")
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