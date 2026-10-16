import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    # JWT 同时支持 HttpOnly Cookie（服务端渲染页面）与 Authorization Bearer 头（REST API）
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24 * 7  # 7 天

    DB_DRIVER = os.environ.get("DB_DRIVER", "mysql")
    if DB_DRIVER == "sqlite":
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL", "sqlite:///notes.db"
        )
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL",
            "mysql+pymysql://root:root@localhost:3306/notes_db?charset=utf8mb4",
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
