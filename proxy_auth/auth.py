import functools
import logging

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .models import User

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "proxy_user_id" not in session:
            logger.info("User not logged in.")
            session["next_url"] = request.url
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid username or password", "error")
        else:
            session["proxy_user_id"] = user.id
            session["proxy_username"] = user.username
            session["is_admin"] = user.is_admin
            flash("You were logged in", "success")

            next_url = session.get("next_url")
            if next_url:
                session.pop("next_url")
                return redirect(next_url)
            else:
                return redirect(url_for("admin.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("proxy_user_id", None)
    session.pop("proxy_username", None)
    session.pop("is_admin", None)
    session.pop("proxy_path", None)
    flash("You were logged out", "success")
    return redirect(url_for("auth.login"))
