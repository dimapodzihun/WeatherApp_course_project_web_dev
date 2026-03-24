import re

from flask import Blueprint, redirect, render_template, request, session, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db
from utils import login_required

auth_bp = Blueprint("auth", __name__)


def is_valid_email(email):
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(regex, email) is not None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect("/")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not is_valid_email(email):
            return render_template("auth/register.html", error="Невірний формат email")

        if len(password) < 8:
            return render_template("auth/register.html", error="Пароль має містити мінімум 8 символів")

        if password != confirm_password:
            return render_template("auth/register.html", error="Паролі не співпадають")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("auth/register.html", error="Цей email вже використовується")

        try:
            hashed_pw = generate_password_hash(password)
            new_user = User(email=email, password_hash=hashed_pw)
            db.session.add(new_user)
            db.session.commit()

            session["user_id"] = new_user.id
            session["user_email"] = new_user.email
            flash("Акаунт успішно створений! Ласкаво просимо.", "success")
            return redirect("/")
        except Exception:
            db.session.rollback()
            return render_template("auth/register.html", error="Помилка при збереженні. Спробуйте ще раз.")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect("/")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template("auth/login.html", error="Акаунт з таким email ще не створений")
            
        if not check_password_hash(user.password_hash, password):
            return render_template("auth/login.html", error="Невірний пароль")

        session["user_id"] = user.id
        session["user_email"] = user.email
        
        flash("Ви успішно увійшли в систему", "success")

        next_page = request.args.get("next")
        return redirect(next_page if next_page else "/")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


@auth_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    user = db.session.get(User, session["user_id"])
    if user:
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return redirect("/")
    session.clear()
    return redirect("/")
