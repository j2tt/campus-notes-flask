import os

from app import create_app
from app.extensions import db

app = create_app()


@app.cli.command("init-db")
def init_db():
    """创建全部数据表：flask --app run.py init-db"""
    db.create_all()
    print("数据库表已创建")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
