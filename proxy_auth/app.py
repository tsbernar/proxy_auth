import logging
from pathlib import Path

import click
import yaml
from flask import Flask, redirect, url_for, session, request
from pydantic import BaseModel
from .models import db, User
from .auth import auth_bp, login_required
from .admin import admin_bp
import getpass


app = Flask(__name__, static_folder=None)
logger = logging.getLogger(__name__)


class LoggingConfig(BaseModel):
    log_level: str
    log_file: Path


class ValidatedConfig(BaseModel):
    logging: LoggingConfig
    database_file: Path
    secret_key: str
    port: int


def setup_logging(config: LoggingConfig):
    log_level = config.log_level
    log_file = config.log_file
    log_fmt = "[%(asctime)s] %(levelname)s %(filename)s:%(funcName)s:%(lineno)i :: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        filename=log_file, format=log_fmt, level=log_level, datefmt=datefmt
    )


@app.route("/", methods=["GET"])
@login_required
def proxy():
    return redirect(url_for("admin.index"))


@app.route("/auth")
def auth():
    if "proxy_user_id" not in session:
        logger.info("User not logged in.")
        return "not authorized", 401
    logger.info(f"User authorized {session['proxy_username']} {request}")
    return "authorized", 200


def get_y_n_input(prompt: str) -> bool:
    answer_str = input(prompt + " (y,n):")
    match answer_str.lower():
        case "y":
            return True
        case "n":
            return False
        case _:
            print("Must input 'y' or 'n'")
            get_y_n_input(prompt=prompt)


def add_user_cli():
    with app.app_context():
        username = input("username:")
        if User.query.filter_by(username=username).first():
            print("user name already exists")
            add_user_cli()
            return
        is_admin = get_y_n_input("is admin")
        password = getpass.getpass()
        logger.info(f"Creating user {username}")
        user = User(username=username, password=password, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()


def create_app(config):
    config = ValidatedConfig(**yaml.safe_load(open(config)))
    setup_logging(config.logging)
    app.config["config"] = config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(config.database_file)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = config.secret_key
    # Prefix this so downstream apps don't override
    app.config["SESSION_COOKIE_NAME"] = "proxy_session"
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    db.init_app(app)

    return app


@click.command
@click.argument("config", required=True)
@click.option("--add_user", is_flag=True, default=False)
def main(config, add_user):
    app = create_app(config)
    if add_user:
        add_user_cli()
        return

    app.run(host="0.0.0.0", port=config.port)


if __name__ == "__main__":
    main()
