import os

# =======================
# CLÉ SECRÈTE FLASK
# =======================
# En prod tu peux la passer via une variable d'environnement SECRET_KEY,
# sinon on utilise une valeur par défaut.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-popcornhub-secret-key")

# =======================
# CONFIG TMDB
# =======================

# Ta clé TMDB (celle que tu as copiée dans l’interface TMDB)
# - soit tu la mets en dur ici
# - soit tu la passes via la variable d’environnement TMDB_API_KEY
TMDB_API_KEY = os.environ.get(
    "TMDB_API_KEY",
    "c3480147e43da7baac0b6bb5a88ebc25"  # <-- remplace par ta clé si tu veux la mettre en dur
)

# URL de base de l’API TMDB
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# URL de base pour les images TMDB
TMDB_IMG_BASE = "https://image.tmdb.org/t/p"