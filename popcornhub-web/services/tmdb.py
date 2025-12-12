import requests
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMG_BASE


def tmdb_get(path, params=None):
    """Appel générique à l'API TMDb."""
    url = f"{TMDB_BASE_URL}{path}"
    params = params or {}
    params["api_key"] = TMDB_API_KEY
    params.setdefault("language", "fr-FR")
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    return r.json()


def tmdb_movie_to_film(movie, credits=None):
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

    for v in videos:
        if v.get("site") == "YouTube" and v.get("type") == "Trailer":
            return v.get("key")

    return None