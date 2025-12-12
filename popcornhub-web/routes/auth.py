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

from services.data import load_data, save_data
from services.auth_utils import login_required


auth_bp = Blueprint("auth", __name__)


def find_user_by_username(data, username):
    for u in data["users"]:
        if u["username"].lower() == username.lower():
            return u
    return None


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    data = load_data()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Tous les champs sont obligatoires.", "danger")
            return redirect(url_for("auth.signup"))

        existing = find_user_by_username(data, username)
        if existing is not None:
            flash("Ce nom d'utilisateur existe déjà.", "danger")
            return redirect(url_for("auth.signup"))

        new_user = {
            "id": (max((u["id"] for u in data["users"]), default=0) + 1),
            "username": username,
            "password_hash": generate_password_hash(password),
        }

        data["users"].append(new_user)
        save_data(data)

        flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    data = load_data()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = find_user_by_username(data, username)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
            return render_template("login.html"), 401

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        next_url = request.args.get("next")
        return redirect(next_url or url_for("index"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("Vous êtes maintenant déconnecté(e).", "info")
    return redirect(url_for("index"))