import bleach
import markdown

ALLOWED_TAGS = [
    "a", "abbr", "acronym", "b", "blockquote", "br", "code", "del", "em",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p",
    "pre", "strong", "table", "tbody", "td", "th", "thead", "tr", "ul",
    "span", "div",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "code": ["class"],
    "span": ["class"],
    "div": ["class"],
    "th": ["align"],
    "td": ["align"],
}


def render_markdown(md_text):
    """Markdown -> HTML，启用 fenced_code / tables / toc 扩展，并用 bleach 白名单清洗防 XSS。"""
    html = markdown.markdown(
        md_text or "",
        extensions=["fenced_code", "tables", "toc"],
        output_format="html5",
    )
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )


def parse_tags(raw):
    """从逗号/空格分隔的字符串解析标签名列表，去重去空。"""
    if not raw:
        return []
    parts = [t.strip().lstrip("#") for t in raw.replace("，", ",").split(",")]
    if len(parts) == 1 and " " in parts[0]:
        parts = [p for p in parts[0].split() if p]
    seen, result = set(), []
    for p in parts:
        if p and p.lower() not in seen:
            seen.add(p.lower())
            result.append(p)
    return result
