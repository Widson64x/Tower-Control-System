from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/')

@auth_bp.route("login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha_hash, senha):
            login_user(user)
            return redirect(url_for("home.home"))
        else:
            flash("Email ou senha incorretos!")
    return render_template("login.html")

@auth_bp.route("logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
