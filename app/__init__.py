from flask import Flask, jsonify, redirect, request, url_for
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from .config import Config
from .extensions import db, jwt


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    db.init_app(app)
    jwt.init_app(app)

    from .models import Comment, Post, Tag, User  # noqa: F401

    @jwt.unauthorized_loader
    def _unauthorized(reason):
        if request.path.startswith("/api/"):
            return jsonify({"msg": reason}), 401
        return redirect(url_for("auth.login", next=request.path))

    @jwt.expired_token_loader
    def _expired(jwt_header, jwt_payload):
        if request.path.startswith("/api/"):
            return jsonify({"msg": "token expired"}), 401
        return redirect(url_for("auth.login", next=request.path))

    @jwt.invalid_token_loader
    def _invalid(reason):
        if request.path.startswith("/api/"):
            return jsonify({"msg": reason}), 422
        return redirect(url_for("auth.login", next=request.path))

    @app.context_processor
    def inject_current_user():
        """向模板注入当前登录用户（通过 Cookie 中的 JWT 识别）。"""
        try:
            verify_jwt_in_request(optional=True, locations=["cookies"])
            uid = get_jwt_identity()
            if uid:
                user = db.session.get(User, int(uid))
                return {"current_user": user}
        except Exception:
            pass
        return {"current_user": None}

    from .blueprints.auth import auth_bp
    from .blueprints.posts import posts_bp
    from .blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
