from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    posts = db.relationship("Post", backref="author", lazy="dynamic",
                            cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="author", lazy="dynamic",
                               cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email}


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)

    def to_dict(self, with_count=False):
        data = {"id": self.id, "name": self.name}
        if with_count:
            data["post_count"] = len(self.posts)
        return data


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body_md = db.Column(db.Text, nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    tags = db.relationship("Tag", secondary=post_tags, backref="posts")
    comments = db.relationship("Comment", backref="post", lazy="dynamic",
                               cascade="all, delete-orphan")

    def to_dict(self, with_body=True):
        data = {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author.username,
            "author_id": self.user_id,
            "tags": [t.name for t in self.tags],
            "comment_count": self.comments.count(),
        }
        if with_body:
            data["body_md"] = self.body_md
            data["body_html"] = self.body_html
        return data


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "body": self.body,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "author": self.author.username,
            "author_id": self.user_id,
            "post_id": self.post_id,
        }
