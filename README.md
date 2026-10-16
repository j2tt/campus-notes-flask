# 校园笔记分享系统（Flask 版）

一个可真实运行的学生简历项目：基于 **Flask + MySQL/SQLite + Jinja2 + Bootstrap 5** 的校园笔记/博客系统，支持 Markdown 写作、标签分类、评论互动，并提供 JWT 鉴权的 REST API，实现完整的前后端交互与数据增删改查。

## 功能清单（对应简历描述）

| 简历描述 | 实现情况 |
| --- | --- |
| Flask、MySQL、Bootstrap 及 Jinja2 开发博客系统 | 应用工厂 + 蓝图（auth / posts / api）；MySQL 为主库（`schema.sql`），可切 SQLite；Bootstrap 5 CDN + Jinja2 模板渲染全部页面 |
| 用户注册登录 | 注册 / 登录 / 登出，werkzeug security 密码哈希 |
| 文章发布与 Markdown 渲染 | 发布 / 编辑 / 删除 / 分页列表 / 详情；服务端 `markdown` 渲染（fenced_code、tables、toc），`bleach` 白名单清洗防 XSS |
| 标签分类 | 文章-标签多对多；列表页按标签筛选；标签页展示全部标签及文章数 |
| 评论功能 | 登录用户发表评论、删除本人评论（页面 + API 双通道） |
| JWT 接口鉴权 | flask-jwt-extended，token 同时支持 HttpOnly Cookie（服务端渲染页面）与 `Authorization: Bearer` 头（`/api/*` 接口） |
| 前后端交互与数据增删改查 | 页面表单 + REST API 两套入口，覆盖用户/文章/评论/标签的 CRUD |

## 技术栈

- 后端：Python 3、Flask 3、Flask-SQLAlchemy、Flask-JWT-Extended
- 数据库：MySQL 8（PyMySQL 驱动，`schema.sql` 建库建表）/ SQLite（本地演示）
- 渲染与安全：Jinja2、markdown（fenced_code/tables/toc）、bleach（XSS 白名单清洗）
- 前端：Bootstrap 5（CDN）、原生 HTML 表单

## 目录结构

```
campus-notes-flask/
├── run.py                # 启动入口（自动建表）
├── seed.py               # 种子脚本：2 个演示用户 + 6 篇带标签 Markdown 文章 + 评论
├── schema.sql            # MySQL 建库建表脚本
├── requirements.txt
└── app/
    ├── __init__.py       # 应用工厂 create_app()，注册蓝图、JWT 错误处理
    ├── config.py         # 配置：DB_DRIVER=sqlite 切换数据库，JWT 双 locations
    ├── extensions.py     # db / jwt 扩展实例
    ├── models.py         # User / Post / Tag / Comment + post_tags 多对多
    ├── utils.py          # Markdown 渲染 + bleach 清洗、标签解析
    ├── blueprints/
    │   ├── auth.py       # 页面注册/登录/登出 + /api/auth/*
    │   ├── posts.py      # 页面：列表/详情/编辑器/标签/我的文章/评论
    │   └── api.py        # REST API：/api/posts、/api/comments、/api/tags
    └── templates/        # base / index / login / register / post_detail /
                          # editor / tags / my_posts（Jinja2 + Bootstrap 5）
```

## 运行方式

### 方式一：SQLite（本地一键演示，默认验证方式）

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:DB_DRIVER="sqlite"
.\.venv\Scripts\python seed.py     # 建表 + 灌入演示数据
.\.venv\Scripts\python run.py      # http://127.0.0.1:5000
```

### 方式二：MySQL（生产/简历环境）

```powershell
# 1. 建库建表
mysql -u root -p < schema.sql
# 2. 默认连接 mysql+pymysql://root:root@localhost:3306/notes_db?charset=utf8mb4
#    也可用 $env:DATABASE_URL="mysql+pymysql://user:pass@host:3306/notes_db?charset=utf8mb4" 覆盖
.\.venv\Scripts\python seed.py
.\.venv\Scripts\python run.py
```

其他环境变量：`SECRET_KEY`、`JWT_SECRET_KEY`、`PORT`（默认 5000）。

## 演示账号（seed.py 创建）

| 用户名 | 密码 | 邮箱 |
| --- | --- | --- |
| alice | alice123 | alice@campus.edu |
| bob | bob123 | bob@campus.edu |

## REST API 列表

| 方法 | 路径 | 鉴权 | 说明 |
| --- | --- | --- | --- |
| POST | /api/auth/register | 否 | 注册 `{"username","email","password"}` |
| POST | /api/auth/login | 否 | 登录，返回 `access_token` |
| GET | /api/auth/me | 是 | 当前用户信息 |
| GET | /api/posts | 否 | 文章列表，支持 `page` / `per_page` / `tag` 筛选 |
| POST | /api/posts | 是 | 新建文章 `{"title","body_md","tags":[...]}` |
| GET | /api/posts/<id> | 否 | 文章详情（含渲染后 HTML） |
| PUT | /api/posts/<id> | 是（作者） | 修改标题/正文/标签 |
| DELETE | /api/posts/<id> | 是（作者） | 删除文章 |
| GET | /api/posts/<id>/comments | 否 | 评论列表 |
| POST | /api/posts/<id>/comments | 是 | 发表评论 `{"body"}` |
| DELETE | /api/comments/<id> | 是（作者） | 删除评论 |
| GET | /api/tags | 否 | 全部标签及文章数 |

### curl 快速验证

```powershell
# 注册 + 登录拿 token
curl -X POST http://127.0.0.1:5000/api/auth/register -H "Content-Type: application/json" -d "@register.json"
curl -X POST http://127.0.0.1:5000/api/auth/login -H "Content-Type: application/json" -d "@login.json"
# 带 Bearer 创建 Markdown 文章（中文 JSON 建议用 -d "@file.json" 传 UTF-8 文件）
curl -X POST http://127.0.0.1:5000/api/posts -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json; charset=utf-8" -d "@post.json"
# 列表 / 标签筛选 / 评论 / 修改 / 删评论
curl "http://127.0.0.1:5000/api/posts?tag=curl"
curl -X POST http://127.0.0.1:5000/api/posts/7/comments -H "Authorization: Bearer <TOKEN>" -d "@comment.json"
curl -X PUT http://127.0.0.1:5000/api/posts/7 -H "Authorization: Bearer <TOKEN>" -d "@update.json"
curl -X DELETE http://127.0.0.1:5000/api/comments/4 -H "Authorization: Bearer <TOKEN>"
```

## 页面路由

`/` 首页列表（分页、标签筛选）· `/login` `/register` `/logout` · `/post/<id>` 详情+评论区 · `/post/new` `/post/<id>/edit` Markdown 编辑器 · `/tags` 标签墙 · `/mine` 我的文章
