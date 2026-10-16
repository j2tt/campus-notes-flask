# -*- coding: utf-8 -*-
"""种子脚本：建表 + 创建 2 个演示用户和若干带标签的 Markdown 文章。

用法：
    # SQLite（本地演示）
    set DB_DRIVER=sqlite && python seed.py        # PowerShell: $env:DB_DRIVER="sqlite"
    # MySQL（需先执行 schema.sql 建库）
    python seed.py
"""
from app import create_app
from app.extensions import db
from app.models import Post, Tag, User
from app.utils import render_markdown

DEMO_POSTS = [
    {
        "title": "Flask 入门：应用工厂与蓝图",
        "tags": ["Python", "Flask", "后端"],
        "body": """# Flask 入门笔记

> 应用工厂模式让测试与多环境配置更轻松。

## 核心概念

- `create_app()` 工厂函数
- 蓝图拆分：`auth` / `posts` / `api`

```python
from flask import Flask

def create_app():
    app = Flask(__name__)
    return app
```

| 组件 | 作用 |
| ---- | ---- |
| 蓝图 | 路由模块化 |
| SQLAlchemy | ORM 数据访问 |
""",
    },
    {
        "title": "Markdown 渲染与 XSS 防护实践",
        "tags": ["Markdown", "安全", "Flask"],
        "body": """## 为什么需要 bleach

服务端渲染 Markdown 后必须做**白名单清洗**，否则 `<script>` 注入会造成 XSS。

1. `markdown` 库转 HTML（启用 fenced_code、tables、toc）
2. `bleach.clean()` 按白名单过滤标签与属性

```python
import bleach, markdown
html = markdown.markdown(text, extensions=["fenced_code", "tables"])
safe = bleach.clean(html, tags=ALLOWED_TAGS)
```
""",
    },
    {
        "title": "JWT 在前后端交互中的两种用法",
        "tags": ["JWT", "认证", "后端"],
        "body": """## 两种 Token 携带方式

本项目同时支持：

- **HttpOnly Cookie**：服务端渲染页面自动携带，防 JS 窃取
- **Authorization: Bearer**：供 `/api/*` REST 接口调用

```bash
curl -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/posts
```

> 登录即签发 JWT，受保护接口通过 `@jwt_required()` 鉴权。
""",
    },
    {
        "title": "MySQL 建库与 utf8mb4 注意事项",
        "tags": ["MySQL", "数据库"],
        "body": """## 建库脚本

```sql
CREATE DATABASE notes_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

- 生产用 MySQL，本地演示可切 SQLite
- 通过环境变量 `DB_DRIVER=sqlite` 一键切换

| 环境 | 连接串 |
| ---- | ------ |
| MySQL | mysql+pymysql://root:root@localhost:3306/notes_db |
| SQLite | sqlite:///notes.db |
""",
    },
    {
        "title": "Bootstrap 5 快速搭建校园风页面",
        "tags": ["前端", "Bootstrap"],
        "body": """## 页面清单

- 首页笔记列表（分页）
- 标签筛选页
- 文章详情 + 评论区
- Markdown 编辑器

> 全部使用 Bootstrap 5 CDN，无需构建步骤。

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
```
""",
    },
    {
        "title": "REST API 设计：增删改查一览",
        "tags": ["API", "后端", "JWT"],
        "body": """## 接口列表

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录拿 token |
| GET/POST | /api/posts | 列表 / 新建 |
| GET/PUT/DELETE | /api/posts/<id> | 详情 / 修改 / 删除 |
| POST/DELETE | /api/posts/<id>/comments | 评论增删 |
| GET | /api/tags | 全部标签 |
""",
    },
]

DEMO_COMMENTS = [
    (0, 1, "写得很清楚，蓝图部分受益了！"),
    (0, 0, "补充：蓝图里也可以挂模板文件夹。"),
    (2, 1, "原来 Cookie 和 Header 可以同时开，学习了。"),
]


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        alice = User(username="alice", email="alice@campus.edu")
        alice.set_password("alice123")
        bob = User(username="bob", email="bob@campus.edu")
        bob.set_password("bob123")
        db.session.add_all([alice, bob])
        db.session.flush()

        tag_map = {}
        posts = []
        authors = [alice, bob]
        for i, item in enumerate(DEMO_POSTS):
            post = Post(
                title=item["title"],
                body_md=item["body"],
                body_html=render_markdown(item["body"]),
                author=authors[i % 2],
            )
            for name in item["tags"]:
                key = name.lower()
                if key not in tag_map:
                    tag_map[key] = Tag(name=name)
                    db.session.add(tag_map[key])
                post.tags.append(tag_map[key])
            posts.append(post)
            db.session.add(post)
        db.session.flush()

        from app.models import Comment
        for post_idx, author_idx, body in DEMO_COMMENTS:
            db.session.add(Comment(body=body, author=authors[author_idx],
                                   post=posts[post_idx]))

        db.session.commit()
        print("种子数据完成：")
        print("  用户: alice/alice123, bob/bob123")
        print("  文章: %d 篇，标签: %d 个，评论: %d 条"
              % (len(posts), len(tag_map), len(DEMO_COMMENTS)))


if __name__ == "__main__":
    seed()
