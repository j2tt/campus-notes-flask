from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Comment, Post, Tag, User
from ..utils import parse_tags, render_markdown

api_bp = Blueprint("api", __name__)


def _get_or_create_tags(names):
    tags = []
    for name in names:
        tag = Tag.query.filter(db.func.lower(Tag.name) == name.lower()).first()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def _parse_tag_names(data):
    raw = data.get("tags")
    if raw is None:
        return []
    if isinstance(raw, list):
        seen, result = set(), []
        for item in raw:
            name = str(item).strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                result.append(name)
        return result
    return parse_tags(str(raw))


@api_bp.get("/posts")
def list_posts():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    tag_name = request.args.get("tag", "").strip()
    query = Post.query.order_by(Post.created_at.desc())
    if tag_name:
        tag = Tag.query.filter(db.func.lower(Tag.name) == tag_name.lower()).first()
        if tag is None:
            return jsonify({"items": [], "total": 0, "page": page, "pages": 0})
        query = query.filter(Post.tags.contains(tag))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [p.to_dict(with_body=False) for p in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@api_bp.post("/posts")
@jwt_required()
def create_post():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body_md = (data.get("body_md") or "").strip()
    if not title or not body_md:
        return jsonify({"msg": "title and body_md required"}), 400
    user = db.session.get(User, int(get_jwt_identity()))
    post = Post(title=title, body_md=body_md,
                body_html=render_markdown(body_md), author=user)
    post.tags = _get_or_create_tags(_parse_tag_names(data))
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201


@api_bp.get("/posts/<int:post_id>")
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict())


@api_bp.put("/posts/<int:post_id>")
@jwt_required()
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != int(get_jwt_identity()):
        return jsonify({"msg": "forbidden"}), 403
    data = request.get_json(silent=True) or {}
    if "title" in data:
        post.title = (data["title"] or "").strip()
    if "body_md" in data:
        post.body_md = (data["body_md"] or "").strip()
        post.body_html = render_markdown(post.body_md)
    if "tags" in data:
        post.tags = _get_or_create_tags(_parse_tag_names(data))
    if not post.title or not post.body_md:
        return jsonify({"msg": "title and body_md must not be empty"}), 400
    db.session.commit()
    return jsonify(post.to_dict())


@api_bp.delete("/posts/<int:post_id>")
@jwt_required()
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != int(get_jwt_identity()):
        return jsonify({"msg": "forbidden"}), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify({"msg": "deleted"})


@api_bp.get("/posts/<int:post_id>/comments")
def list_comments(post_id):
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.asc()).all()
    return jsonify({"items": [c.to_dict() for c in comments]})


@api_bp.post("/posts/<int:post_id>/comments")
@jwt_required()
def create_comment(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"msg": "body required"}), 400
    user = db.session.get(User, int(get_jwt_identity()))
    comment = Comment(body=body, author=user, post=post)
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201


@api_bp.delete("/comments/<int:comment_id>")
@jwt_required()
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != int(get_jwt_identity()):
        return jsonify({"msg": "forbidden"}), 403
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"msg": "deleted"})


@api_bp.get("/tags")
def list_tags():
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify({"items": [t.to_dict(with_count=True) for t in tags]})
