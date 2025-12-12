import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-popcornhub-secret-key")

TMDB_API_KEY = os.environ.get(
    "TMDB_API_KEY",
    "c3480147e43da7baac0b6bb5a88ebc25"
)

TMDB_BASE_URL = "https://api.themoviedb.org/3"

TMDB_IMG_BASE = "https://image.tmdb.org/t/p"