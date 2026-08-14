#!/usr/bin/env python3
"""Generate deterministic SEO metadata, breadcrumbs and structured data."""

from __future__ import annotations

import argparse
from html import escape, unescape
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://rednd.ru"
HEAD_START = "<!-- SEO-GENERATED:BEGIN -->"
HEAD_END = "<!-- SEO-GENERATED:END -->"
CRUMB_START = "<!-- SEO-BREADCRUMBS:BEGIN -->"
CRUMB_END = "<!-- SEO-BREADCRUMBS:END -->"
ORGANIZATION_ID = f"{ORIGIN}/#organization"
WEBSITE_ID = f"{ORIGIN}/#website"

LABELS = {
    "about.html": ("Команда", "Team"),
    "services.html": ("Услуги", "Services"),
    "projects.html": ("Проекты", "Projects"),
    "contact.html": ("Контакты", "Contact"),
    "partner.html": ("Партнёрам", "Partners"),
    "case-scout.html": ("Scout", "Scout"),
    "case-chainya.html": ("Чайня", "Chainya"),
    "case-crm.html": ("CRM для нетворкинга", "Networking CRM"),
    "case-subscriptions.html": ("Telegram-подписки", "Telegram subscriptions"),
    "case-autopricer.html": ("Репрайсер Ozon", "Ozon repricer"),
    "case-faith.html": ("Faith App", "Faith App"),
    "case-mutual.html": ("MUTUAL", "MUTUAL"),
    "case-vetpulse.html": ("ВетПульс", "VetPulse"),
}

SERVICES = {
    "ru": [
        "Telegram-боты и мини-приложения",
        "ИИ-ассистенты и агенты",
        "Интеграции и автоматизация",
        "Веб-сервисы и приложения",
        "Мобильные приложения",
    ],
    "en": [
        "Telegram bots and mini apps",
        "AI assistants and agents",
        "Integrations and automation",
        "Web services and applications",
        "Mobile applications",
    ],
}

CASE_ORDER = (
    "case-scout.html",
    "case-chainya.html",
    "case-subscriptions.html",
    "case-crm.html",
    "case-vetpulse.html",
    "case-autopricer.html",
    "case-mutual.html",
    "case-faith.html",
)

NOINDEX_PAGES = (
    "privacy.html",
    "consent.html",
    "partner-apply.html",
    "en/privacy.html",
    "en/consent.html",
    "en/partner-apply.html",
)


def sitemap_entries() -> list[tuple[str, str]]:
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    entries: list[tuple[str, str]] = []
    for node in root.findall("s:url", ns):
        url = node.findtext("s:loc", default="", namespaces=ns)
        lastmod = node.findtext("s:lastmod", default="", namespaces=ns)
        entries.append((url, lastmod))
    return entries


def relative_path(url: str) -> str:
    path = url.removeprefix(f"{ORIGIN}/")
    return f"{path}index.html" if not path or path.endswith("/") else path


def text_between(source: str, pattern: str, field: str) -> str:
    match = re.search(pattern, source, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"missing {field}")
    return unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def meta_content(source: str, key: str, value: str) -> str:
    pattern = rf'<meta\s+{key}="{re.escape(value)}"\s+content="([^"]*)"'
    return text_between(source, pattern, f"meta {key}={value}")


def strip_block(source: str, start: str, end: str) -> str:
    return re.sub(
        rf"[ \t]*{re.escape(start)}.*?{re.escape(end)}[ \t]*\n?",
        "",
        source,
        flags=re.DOTALL,
    )


def page_language(relative: str) -> str:
    return "en" if relative.startswith("en/") else "ru"


def page_label(relative: str) -> str:
    language = page_language(relative)
    return LABELS[Path(relative).name][1 if language == "en" else 0]


def breadcrumb_items(relative: str, canonical: str) -> list[tuple[str, str]]:
    language = page_language(relative)
    home_url = f"{ORIGIN}/en/" if language == "en" else f"{ORIGIN}/"
    items = [("Home" if language == "en" else "Главная", home_url)]
    if Path(relative).name.startswith("case-"):
        projects_url = f"{ORIGIN}/en/projects.html" if language == "en" else f"{ORIGIN}/projects.html"
        items.append(("Projects" if language == "en" else "Проекты", projects_url))
    items.append((page_label(relative), canonical))
    return items


def breadcrumb_html(relative: str, canonical: str) -> str:
    language = page_language(relative)
    items = breadcrumb_items(relative, canonical)
    parts: list[str] = []
    for index, (name, url) in enumerate(items):
        if index:
            parts.append('    <span aria-hidden="true">›</span>')
        if index == len(items) - 1:
            parts.append(f'    <span aria-current="page">{escape(name)}</span>')
        else:
            href = "index.html" if index == 0 else "projects.html"
            parts.append(f'    <a href="{href}">{escape(name)}</a>')
    label = "Breadcrumbs" if language == "en" else "Хлебные крошки"
    return "\n".join(
        [
            f"  {CRUMB_START}",
            f'  <nav class="rd-breadcrumbs" aria-label="{label}">',
            *parts,
            "  </nav>",
            f"  {CRUMB_END}",
        ]
    )


def breadcrumb_schema(relative: str, canonical: str) -> dict[str, object]:
    return {
        "@type": "BreadcrumbList",
        "@id": f"{canonical}#breadcrumbs",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": url,
            }
            for index, (name, url) in enumerate(breadcrumb_items(relative, canonical), start=1)
        ],
    }


def page_schema(
    relative: str,
    canonical: str,
    title: str,
    description: str,
    image: str,
    lastmod: str,
) -> list[dict[str, object]]:
    language = page_language(relative)
    language_tag = "en-US" if language == "en" else "ru-RU"
    filename = Path(relative).name
    page_type = {
        "about.html": "ProfilePage",
        "services.html": "CollectionPage",
        "projects.html": "CollectionPage",
        "contact.html": "ContactPage",
    }.get(filename, "WebPage")
    webpage: dict[str, object] = {
        "@type": page_type,
        "@id": f"{canonical}#webpage",
        "url": canonical,
        "name": title,
        "description": description,
        "inLanguage": language_tag,
        "dateModified": lastmod,
        "isPartOf": {"@id": WEBSITE_ID},
        "breadcrumb": {"@id": f"{canonical}#breadcrumbs"},
        "primaryImageOfPage": {"@type": "ImageObject", "url": image},
        "publisher": {"@id": ORGANIZATION_ID},
    }
    graph: list[dict[str, object]] = [breadcrumb_schema(relative, canonical), webpage]
    if filename == "about.html":
        webpage["mainEntity"] = {
            "@type": "Organization",
            "@id": ORGANIZATION_ID,
            "name": "Re:dnd",
            "url": f"{ORIGIN}/",
            "logo": f"{ORIGIN}/favicon.svg",
            "email": "mailto:politushkin@gmail.com",
            "sameAs": ["https://t.me/re_dnd"],
        }
    elif filename == "projects.html":
        project_base = f"{ORIGIN}/en/" if language == "en" else f"{ORIGIN}/"
        projects = CASE_ORDER
        webpage["mainEntity"] = {
            "@type": "ItemList",
            "numberOfItems": len(projects),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "name": LABELS[name][1 if language == "en" else 0],
                    "url": f"{project_base}{name}",
                }
                for index, name in enumerate(projects, start=1)
            ],
        }
    elif filename == "services.html":
        webpage["mainEntity"] = {
            "@type": "ItemList",
            "numberOfItems": len(SERVICES[language]),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "name": name,
                }
                for index, name in enumerate(SERVICES[language], start=1)
            ],
        }
    elif filename.startswith("case-"):
        work_id = f"{canonical}#case-study"
        webpage["mainEntity"] = {"@id": work_id}
        graph.append(
            {
                "@type": "CreativeWork",
                "@id": work_id,
                "url": canonical,
                "name": title,
                "headline": title,
                "description": description,
                "image": image,
                "genre": "Case study",
                "inLanguage": language_tag,
                "dateModified": lastmod,
                "creator": {"@id": ORGANIZATION_ID},
                "publisher": {"@id": ORGANIZATION_ID},
            }
        )
    else:
        webpage["about"] = {"@id": ORGANIZATION_ID}
    return graph


def generated_head(relative: str, source: str, url: str, lastmod: str) -> str:
    title = text_between(source, r"<title>(.*?)</title>", "title")
    description = meta_content(source, "name", "description")
    image = meta_content(source, "property", "og:image")
    language = page_language(relative)
    alternate_locale = "ru_RU" if language == "en" else "en_US"
    lines = [
        HEAD_START,
        '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">',
        '<meta name="color-scheme" content="light dark">',
        f'<meta property="og:locale:alternate" content="{alternate_locale}">',
        f'<meta property="og:image:alt" content="{escape(title, quote=True)}">',
        f'<meta name="twitter:image:alt" content="{escape(title, quote=True)}">',
    ]
    if 'name="twitter:title"' not in source:
        lines.append(f'<meta name="twitter:title" content="{escape(title, quote=True)}">')
    if 'name="twitter:description"' not in source:
        lines.append(f'<meta name="twitter:description" content="{escape(description, quote=True)}">')
    if relative not in {"index.html", "en/index.html"}:
        graph = page_schema(relative, url, title, description, image, lastmod)
        payload = json.dumps(
            {"@context": "https://schema.org", "@graph": graph},
            ensure_ascii=False,
            indent=2,
        )
        lines.extend(['<script type="application/ld+json">', payload, "</script>"])
    lines.append(HEAD_END)
    return "\n".join(lines)


def optimize_runtime(source: str, prefix: str) -> str:
    for old_theme_token in ("20260812a", "20260814b", "20260814c", "20260814d", "20260814e", "20260814f", "20260814g"):
        source = source.replace(
            f'{prefix}theme.css?v={old_theme_token}',
            f'{prefix}theme.css?v=20260815a',
        )
    source = source.replace(
        f'<script src="{prefix}site-config.js?v=20260812a"></script>',
        f'<script defer src="{prefix}site-config.js?v=20260815a"></script>',
    ).replace(
        f'<script src="{prefix}site-config.js?v=20260814a"></script>',
        f'<script defer src="{prefix}site-config.js?v=20260815a"></script>',
    ).replace(
        f'<script defer src="{prefix}site-config.js?v=20260814a"></script>',
        f'<script defer src="{prefix}site-config.js?v=20260815a"></script>',
    )
    font_href = f'{prefix}fonts/fonts.css' if prefix == "../" else "fonts/fonts.css"
    font_stylesheet = f'<link href="{font_href}" rel="stylesheet">'
    async_font_stylesheet = "\n".join(
        [
            f'<link rel="preload" href="{font_href}" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">',
            f'<noscript><link href="{font_href}" rel="stylesheet"></noscript>',
        ]
    )
    if async_font_stylesheet not in source:
        source = source.replace(font_stylesheet, async_font_stylesheet, 1)
    theme_link = f'<link rel="stylesheet" href="{prefix}theme.css?v=20260815a">'
    critical_fonts = [
        f'<link rel="preload" href="{prefix}fonts/inter-UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7W0Q5nw.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="preload" href="{prefix}fonts/sora-xMQ9uFFYT72X5wkB_18qmnndmSdSnh2BAfO5mnuyOo1lfiQwV6-xo6eeIw.woff2" as="font" type="font/woff2" crossorigin>',
    ] if prefix == "../" else [
        f'<link rel="preload" href="{prefix}fonts/inter-UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa0ZL7W0Q5n-wU.woff2" as="font" type="font/woff2" crossorigin>',
    ]
    critical_block = "\n".join(critical_fonts)
    if theme_link in source and critical_block not in source:
        source = source.replace(theme_link, f"{critical_block}\n{theme_link}", 1)
    scripts = "\n".join(
        [
            f'<script defer src="{prefix}vendor/react.production.min.js" integrity="sha384-DGyLxAyjq0f9SPpVevD6IgztCFlnMF6oW/XQGmfe+IsZ8TqEiDrcHkMLKI6fiB/Z" crossorigin="anonymous"></script>',
            f'<script defer src="{prefix}vendor/react-dom.production.min.js" integrity="sha384-gTGxhz21lVGYNMcdJOyq01Edg0jhn/c22nsx0kyqP0TxaV5WVdsSH1fSDUf5YJj1" crossorigin="anonymous"></script>',
            f'<script defer src="{prefix}support.js"></script>',
        ]
    )
    current = f'<script src="{prefix}support.js"></script>'
    if current in source:
        source = source.replace(current, scripts)
    elif f'<script defer src="{prefix}support.js"></script>' in source and "vendor/react.production.min.js" not in source:
        source = source.replace(f'<script defer src="{prefix}support.js"></script>', scripts)
    return source


def optimize_project_headings(source: str) -> str:
    """Give every linked case card a real heading without changing its layout."""
    return re.sub(
        r'<span style="font:600 clamp\(20px,2\.4vw,25px\)/1\.25 Sora,sans-serif">([^<]+)</span>',
        r'<h2 style="margin:0;font:600 clamp(20px,2.4vw,25px)/1.25 Sora,sans-serif">\1</h2>',
        source,
    )


def render_page(relative: str, url: str, lastmod: str) -> str:
    path = ROOT / relative
    source = path.read_text(encoding="utf-8")
    source = strip_block(source, HEAD_START, HEAD_END)
    source = strip_block(source, CRUMB_START, CRUMB_END)
    prefix = "../" if relative.startswith("en/") else "./"
    source = optimize_runtime(source, prefix)
    if Path(relative).name == "projects.html":
        source = optimize_project_headings(source)
    head = generated_head(relative, source, url, lastmod)
    source = source.replace("</head>", f"{head}\n</head>", 1)
    if relative not in {"index.html", "en/index.html"}:
        if Path(relative).name.startswith("case-"):
            source = re.sub(
                r'^\s*<a\b[^>\n]*href="projects\.html"[^>\n]*>← (?:Все проекты|All projects)</a>\s*$',
                "",
                source,
                count=1,
                flags=re.MULTILINE,
            )
        crumbs = breadcrumb_html(relative, url)
        source = re.sub(r"(<main\b[^>]*>)", rf"\1\n{crumbs}", source, count=1)
    return source


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed: list[str] = []
    entries = sitemap_entries()
    for url, lastmod in entries:
        relative = relative_path(url)
        rendered = render_page(relative, url, lastmod)
        path = ROOT / relative
        if rendered != path.read_text(encoding="utf-8"):
            changed.append(relative)
            if not args.check:
                path.write_text(rendered, encoding="utf-8")
    for relative in NOINDEX_PAGES:
        path = ROOT / relative
        source = path.read_text(encoding="utf-8")
        prefix = "../" if relative.startswith("en/") else "./"
        rendered = optimize_runtime(source, prefix)
        if rendered != source:
            changed.append(relative)
            if not args.check:
                path.write_text(rendered, encoding="utf-8")
    if args.check and changed:
        print("SEO output is stale:")
        for relative in changed:
            print(f"- {relative}")
        return 1
    if changed:
        print(f"Updated SEO output in {len(changed)} files")
    else:
        print("SEO output is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
