from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from services.data import load_data, save_data, find_user_by_username, get_next_id

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["GET", "POST"], endpoint="signup")
def signup():
    data = load_data()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Tous les champs sont obligatoires.", "danger")
            return redirect(url_for("signup"))

        existing = find_user_by_username(data, username)
        if existing is not None:
            flash("Ce nom d'utilisateur existe déjà.", "danger")
            return redirect(url_for("signup"))

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


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
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
        # on garde is_admin dans la session même si tu ne l'utilises plus
        session["is_admin"] = bool(user.get("is_admin"))

        flash("Connexion réussie.", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("index"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["GET", "POST"], endpoint="logout")
def logout():
    """Déconnecte l'utilisateur et le renvoie vers la vidéothèque."""
    session.clear()
    flash("Vous êtes maintenant déconnecté(e).", "info")
    return redirect(url_for("index"))