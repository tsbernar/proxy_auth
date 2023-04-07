from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import generate_password_hash

from .auth import login_required
from .models import User, db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/")
@login_required
def index():
    users = User.query.all()
    return render_template("admin.html", users=users)


@admin_bp.route("/add-user", methods=["POST"])
@login_required
def add_user():
    if session["is_admin"]:
        username = request.form["username"]
        password = request.form["password"]
        is_admin = request.form.get("is_admin") == "1"
        user = User(username=username, password=password, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash(f"User {username} added successfully", "success")
        return redirect(url_for("admin.index"))
    return "not authorized", 401


@admin_bp.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if session["is_admin"]:
        user = User.query.get(user_id)
        if not user:
            flash(f"User with id {user_id} not found", "error")
            return redirect(url_for("admin.index"))
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted successfully", "success")
        return redirect(url_for("admin.index"))
    return "not authorized", 401
