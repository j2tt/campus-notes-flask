from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_jwt_extended import (create_access_token, get_jwt_identity,
                                jwt_required, set_access_cookies,
                                unset_jwt_cookies)

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


def _issue_token_response(user, redirect_url):
    resp = redirect(redirect_url)
    token = create_access_token(identity=str(user.id))
    set_access_cookies(resp, token)
    return resp


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("用户名、邮箱、密码均不能为空", "danger")
            return render_template("register.html")
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("用户名或邮箱已被占用", "danger")
            return render_template("register.html")
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("注册成功，已自动登录", "success")
        return _issue_token_response(user, url_for("posts.index"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("用户名或密码错误", "danger")
            return render_template("login.html")
        next_url = request.args.get("next") or url_for("posts.index")
        flash("登录成功", "success")
        return _issue_token_response(user, next_url)
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    resp = redirect(url_for("posts.index"))
    unset_jwt_cookies(resp)
    flash("已退出登录", "info")
    return resp


# ---------------- REST API：注册 / 登录 ----------------

@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not username or not email or not password:
        return jsonify({"msg": "username/email/password required"}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"msg": "username or email already taken"}), 409
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    user = User.query.filter_by(username=(data.get("username") or "").strip()).first()
    if user is None or not user.check_password(data.get("password") or ""):
        return jsonify({"msg": "bad username or password"}), 401
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()})


@auth_bp.route("/api/auth/me", methods=["GET"])
@jwt_required()
def api_me():
    user = db.session.get(User, int(get_jwt_identity()))
    return jsonify({"user": user.to_dict()})
