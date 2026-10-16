from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Comment, Post, Tag, User
from ..utils import parse_tags, render_markdown

posts_bp = Blueprint("posts", __name__)


def _get_or_create_tags(raw):
    tags = []
    for name in parse_tags(raw):
        tag = Tag.query.filter(db.func.lower(Tag.name) == name.lower()).first()
        if tag is None:
            tag = Tag(name=name)
            db.session.add(tag)
        tags.append(tag)
    return tags


def _current_user():
    uid = get_jwt_identity()
    return db.session.get(User, int(uid)) if uid else None


@posts_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    tag_name = request.args.get("tag", "").strip()
    query = Post.query.order_by(Post.created_at.desc())
    active_tag = None
    if tag_name:
        active_tag = Tag.query.filter(db.func.lower(Tag.name) == tag_name.lower()).first_or_404()
        query = query.filter(Post.tags.contains(active_tag))
    pagination = query.paginate(page=page, per_page=5, error_out=False)
    return render_template("index.html", pagination=pagination,
                           posts=pagination.items, active_tag=active_tag)


@posts_bp.route("/tags")
def tags():
    all_tags = Tag.query.order_by(Tag.name).all()
    return render_template("tags.html", tags=all_tags)


@posts_bp.route("/mine")
@jwt_required(locations=["cookies"])
def my_posts():
    user = _current_user()
    page = request.args.get("page", 1, type=int)
    pagination = (Post.query.filter_by(user_id=user.id)
                  .order_by(Post.created_at.desc())
                  .paginate(page=page, per_page=10, error_out=False))
    return render_template("my_posts.html", pagination=pagination,
                           posts=pagination.items)


@posts_bp.route("/post/<int:post_id>")
def detail(post_id):
    post = Post.query.get_or_404(post_id)
    comments = post.comments.order_by(Comment.created_at.asc()).all()
    return render_template("post_detail.html", post=post, comments=comments)


@posts_bp.route("/post/new", methods=["GET", "POST"])
@jwt_required(locations=["cookies"])
def create():
    user = _current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body_md = request.form.get("body_md", "").strip()
        if not title or not body_md:
            flash("标题与正文不能为空", "danger")
            return render_template("editor.html", post=None,
                                   tags_str=request.form.get("tags", ""))
        post = Post(title=title, body_md=body_md,
                    body_html=render_markdown(body_md), author=user)
        post.tags = _get_or_create_tags(request.form.get("tags", ""))
        db.session.add(post)
        db.session.commit()
        flash("发布成功", "success")
        return redirect(url_for("posts.detail", post_id=post.id))
    return render_template("editor.html", post=None, tags_str="")


@posts_bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@jwt_required(locations=["cookies"])
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    user = _current_user()
    if post.user_id != user.id:
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body_md = request.form.get("body_md", "").strip()
        if not title or not body_md:
            flash("标题与正文不能为空", "danger")
            return render_template("editor.html", post=post,
                                   tags_str=request.form.get("tags", ""))
        post.title = title
        post.body_md = body_md
        post.body_html = render_markdown(body_md)
        post.tags = _get_or_create_tags(request.form.get("tags", ""))
        db.session.commit()
        flash("保存成功", "success")
        return redirect(url_for("posts.detail", post_id=post.id))
    return render_template("editor.html", post=post,
                           tags_str=", ".join(t.name for t in post.tags))


@posts_bp.route("/post/<int:post_id>/delete", methods=["POST"])
@jwt_required(locations=["cookies"])
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    user = _current_user()
    if post.user_id != user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("文章已删除", "info")
    return redirect(url_for("posts.index"))


@posts_bp.route("/post/<int:post_id>/comments", methods=["POST"])
@jwt_required(locations=["cookies"])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    user = _current_user()
    body = request.form.get("body", "").strip()
    if not body:
        flash("评论内容不能为空", "danger")
        return redirect(url_for("posts.detail", post_id=post.id))
    db.session.add(Comment(body=body, author=user, post=post))
    db.session.commit()
    flash("评论已发表", "success")
    return redirect(url_for("posts.detail", post_id=post.id))


@posts_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@jwt_required(locations=["cookies"])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user = _current_user()
    if comment.user_id != user.id:
        abort(403)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash("评论已删除", "info")
    return redirect(url_for("posts.detail", post_id=post_id))
