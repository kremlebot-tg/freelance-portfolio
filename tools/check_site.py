#!/usr/bin/env python3
"""Fast, dependency-free checks for the static site and its public surface."""

from __future__ import annotations

from collections import Counter
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlparse
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SITE_ORIGIN = "https://rednd.ru"
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")
INDEX_ROBOTS = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
SEO_HEAD_START = "<!-- SEO-GENERATED:BEGIN -->"
SEO_HEAD_END = "<!-- SEO-GENERATED:END -->"
SEO_CRUMB_START = "<!-- SEO-BREADCRUMBS:BEGIN -->"
SEO_CRUMB_END = "<!-- SEO-BREADCRUMBS:END -->"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.refs: list[tuple[str, str]] = []
        self.lang = ""
        self.title_depth = 0
        self.title = ""
        self.descriptions: list[str] = []
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.alternates: list[tuple[str, str]] = []
        self.meta_names: dict[str, list[str]] = {}
        self.meta_properties: dict[str, list[str]] = {}
        self.h1_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.lang = values.get("lang", "")
        if tag == "title":
            self.title_depth += 1
        if tag == "h1":
            self.h1_count += 1
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "meta" and values.get("name", "").lower() == "description":
            self.descriptions.append(values.get("content", "").strip())
        if tag == "meta" and values.get("name", "").lower() == "robots":
            self.robots.append(values.get("content", "").strip().lower())
        if tag == "meta" and values.get("name"):
            key = values["name"].lower()
            self.meta_names.setdefault(key, []).append(values.get("content", "").strip())
        if tag == "meta" and values.get("property"):
            key = values["property"].lower()
            self.meta_properties.setdefault(key, []).append(values.get("content", "").strip())
        if tag == "link" and values.get("rel", "").lower() == "canonical":
            self.canonicals.append(values.get("href", "").strip())
        if tag == "link" and values.get("rel", "").lower() == "alternate" and values.get("hreflang"):
            self.alternates.append((values["hreflang"].lower(), values.get("href", "").strip()))
        for attr in ("href", "src"):
            if values.get(attr):
                self.refs.append((attr, values[attr]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title += data


def page_for_url(url: str) -> Path:
    path = unquote(urlparse(url).path)
    if path.endswith("/"):
        path += "index.html"
    return ROOT / path.lstrip("/")


def local_target(page: Path, raw: str) -> Path | None:
    ref = raw.strip()
    if not ref or ref.startswith(("#", "//")) or ref.startswith(SKIP_SCHEMES):
        return None
    if "{{" in ref or "}}" in ref:
        return None
    path = unquote(urlparse(ref).path)
    if not path:
        return None
    target = ROOT / path.lstrip("/") if path.startswith("/") else page.parent / path
    if target.is_dir() or path.endswith("/"):
        target /= "index.html"
    return target.resolve()


def json_ld_graphs(source: str) -> tuple[list[dict[str, object]], list[str]]:
    """Return all JSON-LD graph nodes and any decoding/shape failures."""
    graph: list[dict[str, object]] = []
    failures: list[str] = []
    blocks = re.findall(
        r'<script\s+type="application/ld\+json">(.*?)</script>', source, flags=re.DOTALL
    )
    for index, block in enumerate(blocks, start=1):
        try:
            payload = json.loads(block)
        except json.JSONDecodeError as exc:
            failures.append(f"JSON-LD block {index} is invalid: {exc}")
            continue
        nodes = payload.get("@graph") if isinstance(payload, dict) else None
        if not isinstance(nodes, list) or not all(isinstance(node, dict) for node in nodes):
            failures.append(f"JSON-LD block {index} must contain an object @graph")
            continue
        graph.extend(nodes)
    return graph, failures


def main() -> int:
    failures: list[str] = []
    parsed: dict[Path, PageParser] = {}

    for page in sorted(ROOT.rglob("*.html")):
        if any(part in {".git", "node_modules", "_site"} for part in page.parts):
            continue
        parser = PageParser()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - diagnostic path
            failures.append(f"{page.relative_to(ROOT)}: HTML parse failed: {exc}")
            continue
        parsed[page.resolve()] = parser
        duplicates = [value for value, count in Counter(parser.ids).items() if count > 1]
        if duplicates:
            failures.append(f"{page.relative_to(ROOT)}: duplicate ids: {', '.join(duplicates)}")
        for attr, ref in parser.refs:
            target = local_target(page, ref)
            if target is not None and not target.exists():
                failures.append(f"{page.relative_to(ROOT)}: missing {attr} target {ref}")

    ns = {
        "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "xhtml": "http://www.w3.org/1999/xhtml",
    }
    sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
    urls = [node.text or "" for node in sitemap.findall("s:url/s:loc", ns)]
    sitemap_urls = set(urls)
    sitemap_lastmod = {
        node.findtext("s:loc", default="", namespaces=ns):
        node.findtext("s:lastmod", default="", namespaces=ns)
        for node in sitemap.findall("s:url", ns)
    }
    indexable_parsers: list[PageParser] = []
    if len(urls) != len(set(urls)):
        failures.append("sitemap.xml: duplicate URLs")
    for url in urls:
        page = page_for_url(url).resolve()
        parser = parsed.get(page)
        if parser is None:
            failures.append(f"sitemap.xml: missing page for {url}")
            continue
        indexable_parsers.append(parser)
        rel = page.relative_to(ROOT)
        if parser.lang not in {"ru", "en"}:
            failures.append(f"{rel}: missing or unsupported html lang")
        if not parser.title.strip():
            failures.append(f"{rel}: missing title")
        elif not 20 <= len(parser.title.strip()) <= 70:
            failures.append(f"{rel}: title length outside 20–70 characters")
        if len(parser.descriptions) != 1 or not parser.descriptions[0]:
            failures.append(f"{rel}: expected one non-empty meta description")
        elif not 60 <= len(parser.descriptions[0]) <= 220:
            failures.append(f"{rel}: meta description length outside 60–220 characters")
        if parser.canonicals != [url]:
            failures.append(f"{rel}: canonical must be exactly {url}")
        if any("noindex" in directive for directive in parser.robots):
            failures.append(f"{rel}: indexable sitemap page must not be noindex")
        alternates = dict(parser.alternates)
        if len(parser.alternates) != 3 or set(alternates) != {"ru", "en", "x-default"}:
            failures.append(f"{rel}: expected ru, en and x-default alternate links")
        for language, alternate_url in alternates.items():
            if alternate_url not in sitemap_urls:
                failures.append(f"{rel}: {language} alternate is absent from sitemap: {alternate_url}")
        if parser.h1_count != 1:
            failures.append(f"{rel}: expected one h1, found {parser.h1_count}")

        source = page.read_text(encoding="utf-8")
        if parser.robots != [INDEX_ROBOTS]:
            failures.append(f"{rel}: expected exactly the explicit index robots directive")
        if source.count(SEO_HEAD_START) != 1 or source.count(SEO_HEAD_END) != 1:
            failures.append(f"{rel}: expected one deterministic generated SEO head block")

        expected_meta = {
            "color-scheme": "light dark",
            "twitter:card": "summary_large_image",
        }
        for name, expected in expected_meta.items():
            if parser.meta_names.get(name) != [expected]:
                failures.append(f"{rel}: meta name={name!r} must be exactly {expected!r}")
        for name in ("twitter:title", "twitter:description", "twitter:image", "twitter:image:alt"):
            values = parser.meta_names.get(name, [])
            if len(values) != 1 or not values[0]:
                failures.append(f"{rel}: expected one non-empty meta name={name!r}")

        expected_locale = "en_US" if parser.lang == "en" else "ru_RU"
        expected_alternate_locale = "ru_RU" if parser.lang == "en" else "en_US"
        expected_properties = {
            "og:site_name": "Re:dnd",
            "og:locale": expected_locale,
            "og:locale:alternate": expected_alternate_locale,
            "og:url": url,
        }
        for name, expected in expected_properties.items():
            if parser.meta_properties.get(name) != [expected]:
                failures.append(f"{rel}: meta property={name!r} must be exactly {expected!r}")
        for name in ("og:title", "og:description", "og:image", "og:image:alt"):
            values = parser.meta_properties.get(name, [])
            if len(values) != 1 or not values[0]:
                failures.append(f"{rel}: expected one non-empty meta property={name!r}")

        prefix = "../" if str(rel).startswith("en/") else "./"
        runtime_contract = (
            f'<script defer src="{prefix}site-config.js?v=20260814a"></script>',
            f'<script defer src="{prefix}vendor/react.production.min.js"',
            f'<script defer src="{prefix}vendor/react-dom.production.min.js"',
            f'<script defer src="{prefix}support.js"></script>',
        )
        for token in runtime_contract:
            if source.count(token) != 1:
                failures.append(f"{rel}: expected one optimized runtime token {token!r}")

        schema_graph, schema_failures = json_ld_graphs(source)
        for failure in schema_failures:
            failures.append(f"{rel}: {failure}")
        if source.count('<script type="application/ld+json">') != 1:
            failures.append(f"{rel}: expected exactly one JSON-LD script")
        schema_types = {node.get("@type") for node in schema_graph}
        if rel.name == "index.html" and rel.parent == Path("."):
            expected_types = {"Organization", "WebSite", "ProfessionalService"}
        elif rel == Path("en/index.html"):
            expected_types = {"Organization", "WebSite", "ProfessionalService"}
        else:
            expected_page_type = {
                "about.html": "ProfilePage",
                "services.html": "CollectionPage",
                "projects.html": "CollectionPage",
                "contact.html": "ContactPage",
            }.get(rel.name, "WebPage")
            expected_types = {"BreadcrumbList", expected_page_type}
            if rel.name.startswith("case-"):
                expected_types.add("CreativeWork")
        missing_schema = expected_types - schema_types
        if missing_schema:
            failures.append(f"{rel}: missing schema types {sorted(missing_schema)}")

        is_home = url in {f"{SITE_ORIGIN}/", f"{SITE_ORIGIN}/en/"}
        if is_home:
            if SEO_CRUMB_START in source or SEO_CRUMB_END in source or 'class="rd-breadcrumbs"' in source:
                failures.append(f"{rel}: home page must not render breadcrumbs")
        else:
            if source.count(SEO_CRUMB_START) != 1 or source.count(SEO_CRUMB_END) != 1:
                failures.append(f"{rel}: expected one generated breadcrumb block")
            if source.count('class="rd-breadcrumbs"') != 1:
                failures.append(f"{rel}: expected one visible breadcrumb navigation")
            breadcrumb_nodes = [node for node in schema_graph if node.get("@type") == "BreadcrumbList"]
            if len(breadcrumb_nodes) != 1:
                failures.append(f"{rel}: expected one BreadcrumbList node")
            else:
                items = breadcrumb_nodes[0].get("itemListElement")
                expected_count = 3 if rel.name.startswith("case-") else 2
                if not isinstance(items, list) or len(items) != expected_count:
                    failures.append(f"{rel}: BreadcrumbList must contain {expected_count} items")
                elif not isinstance(items[-1], dict) or items[-1].get("item") != url:
                    failures.append(f"{rel}: final breadcrumb item must reference its canonical URL")
            webpage_nodes = [node for node in schema_graph if node.get("@id") == f"{url}#webpage"]
            if len(webpage_nodes) != 1:
                failures.append(f"{rel}: expected one canonical webpage schema node")
            else:
                webpage = webpage_nodes[0]
                if webpage.get("url") != url:
                    failures.append(f"{rel}: webpage schema URL must match canonical")
                if webpage.get("dateModified") != sitemap_lastmod.get(url):
                    failures.append(f"{rel}: webpage schema dateModified must match sitemap lastmod")

        if rel.name in {"projects.html", "services.html"}:
            item_lists = [
                node.get("mainEntity")
                for node in schema_graph
                if node.get("@id") == f"{url}#webpage"
            ]
            expected_items = 8 if rel.name == "projects.html" else 5
            if (
                len(item_lists) != 1
                or not isinstance(item_lists[0], dict)
                or item_lists[0].get("@type") != "ItemList"
                or item_lists[0].get("numberOfItems") != expected_items
            ):
                failures.append(f"{rel}: expected an ItemList with {expected_items} entries")

        if rel.name == "projects.html":
            heading_token = '<h2 style="margin:0;font:600 clamp(20px,2.4vw,25px)/1.25 Sora,sans-serif">'
            if source.count(heading_token) != 8:
                failures.append(f"{rel}: all eight project cards must use semantic h2 headings")

    for field, values in (
        ("title", [parser.title.strip() for parser in indexable_parsers if parser.title.strip()]),
        ("meta description", [parser.descriptions[0] for parser in indexable_parsers if parser.descriptions]),
    ):
        duplicates = [value for value, count in Counter(values).items() if count > 1]
        if duplicates:
            failures.append(f"sitemap.xml: duplicate {field} values: {duplicates}")

    for node in sitemap.findall("s:url", ns):
        url = node.findtext("s:loc", default="", namespaces=ns)
        lastmods = node.findall("s:lastmod", ns)
        if len(lastmods) != 1 or not (lastmods[0].text or "").strip():
            failures.append(f"sitemap.xml: {url} must have exactly one lastmod")
        else:
            try:
                modified = date.fromisoformat((lastmods[0].text or "").strip())
                if modified > date.today():
                    failures.append(f"sitemap.xml: future lastmod for {url}")
            except ValueError:
                failures.append(f"sitemap.xml: invalid lastmod for {url}")
        xml_alternates = {
            (link.get("hreflang") or "").lower(): link.get("href") or ""
            for link in node.findall("xhtml:link", ns)
        }
        xml_links = node.findall("xhtml:link", ns)
        if len(xml_links) != 3 or set(xml_alternates) != {"ru", "en", "x-default"}:
            failures.append(f"sitemap.xml: {url} needs ru, en and x-default alternates")
        for language, alternate_url in xml_alternates.items():
            if alternate_url not in sitemap_urls:
                failures.append(f"sitemap.xml: {url} {language} alternate is not listed: {alternate_url}")

    noindex_pages = {
        "privacy.html": "https://rednd.ru/privacy.html",
        "consent.html": "https://rednd.ru/consent.html",
        "partner-apply.html": "https://rednd.ru/partner-apply.html",
        "en/privacy.html": "https://rednd.ru/en/privacy.html",
        "en/consent.html": "https://rednd.ru/en/consent.html",
        "en/partner-apply.html": "https://rednd.ru/en/partner-apply.html",
    }
    for relative, canonical in noindex_pages.items():
        parser = parsed[(ROOT / relative).resolve()]
        if parser.robots != ["noindex,follow"]:
            failures.append(f"{relative}: expected exactly noindex,follow")
        if parser.canonicals != [canonical]:
            failures.append(f"{relative}: canonical must remain self-referential")
        if canonical in sitemap_urls:
            failures.append(f"sitemap.xml: noindex page listed: {canonical}")
        source = (ROOT / relative).read_text(encoding="utf-8")
        prefix = "../" if relative.startswith("en/") else "./"
        for token in (
            f'<script defer src="{prefix}site-config.js?v=20260814a"></script>',
            f'<script defer src="{prefix}vendor/react.production.min.js"',
            f'<script defer src="{prefix}vendor/react-dom.production.min.js"',
            f'<script defer src="{prefix}support.js"></script>',
        ):
            if source.count(token) != 1:
                failures.append(f"{relative}: expected one optimized runtime token {token!r}")

    not_found = parsed[(ROOT / "404.html").resolve()]
    if not_found.robots != ["noindex,follow"]:
        failures.append("404.html: expected exactly noindex,follow")

    for relative in ("index.html", "en/index.html"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        blocks = re.findall(
            r'<script\s+type="application/ld\+json">(.*?)</script>', source, flags=re.DOTALL
        )
        if len(blocks) != 1:
            failures.append(f"{relative}: expected one JSON-LD block")
            continue
        try:
            graph = json.loads(blocks[0]).get("@graph", [])
        except json.JSONDecodeError as exc:
            failures.append(f"{relative}: invalid JSON-LD: {exc}")
            continue
        types = {item.get("@type") for item in graph if isinstance(item, dict)}
        if not {"Organization", "WebSite", "ProfessionalService"}.issubset(types):
            failures.append(f"{relative}: missing Organization, WebSite or ProfessionalService schema")
        if '"@type": "Person"' in source or "#founder" in source:
            failures.append(f"{relative}: stale individual-provider schema")

    team_contract = {
        "index.html": ("Мы проектируем и собираем", "Что мы делаем"),
        "en/index.html": ("We design and build", "What we build"),
        "Header.dc.html": ("О команде",),
        "en/Header.dc.html": ("Team",),
        "Footer.dc.html": ("О команде",),
        "en/Footer.dc.html": ("Team",),
        "about.html": ("О команде Re:dnd", "назначаем ответственного"),
        "en/about.html": ("The Re:dnd team", "assign one person"),
        "contact.html": ("формируем команду", "одного ответственного"),
        "en/contact.html": ("form a team", "assign one person"),
        "partner-apply.html": ("Команда оценивает и ведёт проект",),
        "en/partner-apply.html": ("The team scopes and leads the project",),
    }
    for relative, required_copy in team_contract.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for copy in required_copy:
            if copy not in source:
                failures.append(f"{relative}: missing team-positioning copy {copy!r}")
    stale_personal_copy = (
        "Об авторе", "Я проектирую", "Отвечу лично", "отвечаю обычно", "Веду проект",
        "I design and build", "I will reply personally", "independent product practice",
        "One accountable person handles", "project creator",
    )
    for relative in team_contract:
        source = (ROOT / relative).read_text(encoding="utf-8")
        for copy in stale_personal_copy:
            if copy in source:
                failures.append(f"{relative}: stale individual-positioning copy {copy!r}")

    for forbidden in ("README.md", "package.json", "package-lock.json", "ios-frame.jsx"):
        if forbidden in {Path(urlparse(url).path).name for url in urls}:
            failures.append(f"sitemap.xml: internal file listed: {forbidden}")

    for relative in ("contact.html", "partner-apply.html", "en/contact.html", "en/partner-apply.html"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        if "payload.stored === true" not in source or "error.stored ? 'stored' : 'network'" not in source:
            failures.append(f"{relative}: missing stored-but-not-notified response handling")
        if source.count('required aria-required="true"') < 2:
            failures.append(f"{relative}: required fields need native and assistive semantics")

    subscription_transparency = {
        "case-subscriptions.html": (
            "интерактивный прототип",
            "Реальные платежи и backend здесь не подключены",
            "не создаёт счёт и не списывает деньги",
            "Реальную автоматизацию оплаты этот прототип не подтверждает",
        ),
        "en/case-subscriptions.html": (
            "interactive prototype",
            "Real payments and a backend are not connected here",
            "creates no invoice and charges no money",
            "This prototype does not prove live payment automation",
        ),
    }
    subscription_overclaims = (
        "Бот принимает регулярную оплату",
        "Оплата и доступ работают на автомате",
        "The bot takes recurring payments",
        "Payments and access run on their own",
        "subscription bot with recurring payments",
    )
    for relative, required_copy in subscription_transparency.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for copy in required_copy:
            if copy not in source:
                failures.append(f"{relative}: missing transparent prototype label {copy!r}")
        for claim in subscription_overclaims:
            if claim in source:
                failures.append(f"{relative}: unsupported live-payment claim {claim!r}")

    autopricer_pages = {
        "case-autopricer.html": ("синтетических данных", "средняя расчётная маржа"),
        "en/case-autopricer.html": ("synthetic data", "avg calculated margin"),
    }
    for relative, required_copy in autopricer_pages.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        if source.count('type="range"') != 5 or source.count('onInput="{{ on') != 5:
            failures.append(f"{relative}: all five demo ranges must update continuously via onInput")
        if 'onChange="{{ on' in source:
            failures.append(f"{relative}: demo range still uses delayed onChange handling")
        for copy in required_copy:
            if copy not in source:
                failures.append(f"{relative}: missing transparent demo label {copy!r}")

    case_pages = sorted(ROOT.glob("case-*.html")) + sorted((ROOT / "en").glob("case-*.html"))
    expected_case_names = {
        "case-scout.html", "case-chainya.html", "case-subscriptions.html", "case-crm.html",
        "case-vetpulse.html", "case-autopricer.html", "case-mutual.html", "case-faith.html",
    }
    for directory in (ROOT, ROOT / "en"):
        actual = {page.name for page in directory.glob("case-*.html")}
        if actual != expected_case_names:
            failures.append(
                f"{directory.relative_to(ROOT) or '.'}: RU/EN case parity mismatch; "
                f"missing={sorted(expected_case_names - actual)}, extra={sorted(actual - expected_case_names)}"
            )

    glance_layouts: set[str] = set()
    for page in case_pages:
        source = page.read_text(encoding="utf-8")
        if source.count('class="case-glance"') != 1:
            failures.append(f"{page.relative_to(ROOT)}: expected one case status summary")
        for role in ("check", "proof", "boundary"):
            if source.count(f'data-role="{role}"') != 1:
                failures.append(f"{page.relative_to(ROOT)}: expected one case summary role {role!r}")
        for layout in ("split", "rail", "evidence"):
            if f'data-layout="{layout}"' in source:
                glance_layouts.add(layout)
        has_shared_process = 'class="case-process__flow"' in source and 'class="case-process__link"' in source
        has_vetpulse_process = 'class="flow"' in source and 'class="flow-link"' in source
        if not (has_shared_process or has_vetpulse_process):
            failures.append(f"{page.relative_to(ROOT)}: missing visual business-process flow")
        if has_shared_process:
            expected_counts = {
                'class="case-process__kicker"': 1,
                'class="case-process__stage"': 4,
                'class="case-process__link"': 4,
                'class="case-process__outcome"': 3,
            }
            for token, expected in expected_counts.items():
                actual = source.count(token)
                if actual != expected:
                    failures.append(
                        f"{page.relative_to(ROOT)}: expected {expected} process tokens {token!r}, found {actual}"
                    )
    if glance_layouts != {"split", "rail", "evidence"}:
        failures.append(f"case summaries: expected three visual layouts, found {sorted(glance_layouts)}")

    chainya_en = (ROOT / "en/case-chainya.html").read_text(encoding="utf-8")
    for token in ("32 items · 4 journeys · 254 tests", "The server verifies critical data", "https://chainya.ru/"):
        if token not in chainya_en:
            failures.append(f"en/case-chainya.html: missing verified case evidence {token!r}")

    templated_process_copy = ("как работает бизнес-процесс", "how the business workflow works")
    for page in case_pages:
        source = page.read_text(encoding="utf-8")
        for copy in templated_process_copy:
            if copy in source:
                failures.append(f"{page.relative_to(ROOT)}: generic process kicker {copy!r}")

    process_claim_regressions = {
        "case-subscriptions.html": ("подписанное уведомление",),
        "en/case-subscriptions.html": ("signed notification",),
        "case-faith.html": ("Каждый урок проходит внешнюю экспертную рецензию",),
        "en/case-faith.html": ("Every lesson goes through external expert review",),
    }
    for relative, forbidden_copy in process_claim_regressions.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for copy in forbidden_copy:
            if copy in source:
                failures.append(f"{relative}: unsupported process claim {copy!r}")

    scout_workflow_copy = {
        "case-scout.html": ("общий неназначенный пул", "без автоматической раздачи", "чужая рабочая очередь не раскрывается"),
        "en/case-scout.html": ("shared unassigned pool", "without automatic distribution", "without exposing another teammate's work queue"),
    }
    for relative, required_copy in scout_workflow_copy.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for copy in required_copy:
            if copy not in source:
                failures.append(f"{relative}: missing multi-user workflow boundary {copy!r}")

    repricer_overclaims = (
        "каждый активный товар был в плюсе",
        "переоценивает каталог в плюс",
        "reprices the catalogue into profit",
        "every active product turns a profit",
    )
    for page in ROOT.rglob("*.html"):
        if any(part in {".git", "node_modules", "_site"} for part in page.parts):
            continue
        source = page.read_text(encoding="utf-8")
        for claim in repricer_overclaims:
            if claim in source:
                failures.append(f"{page.relative_to(ROOT)}: unsupported repricer claim {claim!r}")

    vetpulse_required = {
        "case-vetpulse.html": (
            "интерактивный прототип",
            "AI-модель, серверная часть и Vetmanager не подключены",
            "три заскриптованных сценария",
        ),
        "en/case-vetpulse.html": (
            "interactive prototype",
            "Live AI, a backend and Vetmanager are not connected",
            "three scripted scenarios",
        ),
        "vetpulse/index.html": (
            'content="noindex,follow"',
            "Продуктовый прототип · вымышленные данные",
            "Интеграция — следующий этап",
        ),
        "vetpulse/demo.html": (
            "Это сценарный прототип",
            "ничего не отправляют наружу",
            "не реальные результаты",
        ),
    }
    for relative, required_copy in vetpulse_required.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for copy in required_copy:
            if copy not in source:
                failures.append(f"{relative}: missing transparent prototype label {copy!r}")

    vetpulse_overclaims = (
        "Мультиарендный AI-SaaS",
        "multi-tenant AI-SaaS",
        "Мультиарендный SaaS",
        "multi-tenant SaaS",
        "Соответствие 152-ФЗ",
        "Бесплатный пилот",
        "полностью внедрённая",
        "всё уже работает",
        "Ошибке неоткуда взяться",
    )
    for relative in vetpulse_required:
        source = (ROOT / relative).read_text(encoding="utf-8")
        for claim in vetpulse_overclaims:
            if claim in source:
                failures.append(f"{relative}: unsupported VetPulse claim {claim!r}")

    theme = (ROOT / "theme.css").read_text(encoding="utf-8")
    site_config = (ROOT / "site-config.js").read_text(encoding="utf-8")
    motion_contract = {
        "theme.css": (
            ".rd-breadcrumbs {",
            "html.rd-motion-ready .rd-motion-observed * { animation-play-state: paused !important; }",
            "@media (prefers-reduced-motion: reduce)",
            "transform: rotate(-8deg) scale(1.04)",
        ),
        "site-config.js": (
            "function observeMotionScenes(root)",
            "rd-motion-observed",
            "observeMotionScenes(root);",
            "function enforceRequiredFields(root)",
            "enforceRequiredFields(root);",
        ),
    }
    for relative, required_tokens in motion_contract.items():
        source = theme if relative == "theme.css" else site_config
        for token in required_tokens:
            if token not in source:
                failures.append(f"{relative}: missing motion-safety contract {token!r}")
    for forbidden in ("filter: saturate", "rotate(360deg)"):
        if forbidden in theme:
            failures.append(f"theme.css: avoid expensive or distracting motion {forbidden!r}")

    for relative in ("Header.dc.html", "en/Header.dc.html"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        if 'class="rd-skip-link" href="#main-content"' not in source:
            failures.append(f"{relative}: missing keyboard skip link")
        for token in ("opacity:0", "visibility:hidden", "pointer-events:none", "transform:translateY(-8px)"):
            if token not in source:
                failures.append(f"{relative}: mobile menu lacks reversible close transition {token!r}")
        if ".hdr-nav{display:none!important" in source:
            failures.append(f"{relative}: mobile menu close still uses abrupt display:none")

    infinite_scene_tokens = (
        "wkDot 1.1s infinite",
        "wkBlink 1s step-end infinite",
        "wkPulse 1.9s ease-out .5s infinite",
    )
    for relative in ("index.html", "en/index.html", "contact.html", "en/contact.html"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        for token in infinite_scene_tokens:
            if token in source:
                failures.append(f"{relative}: decorative scene animation must be finite: {token!r}")

    for page, parser in parsed.items():
        source = page.read_text(encoding="utf-8")
        rel = page.relative_to(ROOT)
        if "theme.css?v=" in source and "theme.css?v=20260814a" not in source:
            failures.append(f"{rel}: stale theme.css cache token")
        if "site-config.js?v=" in source and "site-config.js?v=20260814a" not in source:
            failures.append(f"{rel}: stale site-config.js cache token")

    pages_workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    for token in (
        "test -f _site/.well-known/security.txt",
        "test -f _site/.nojekyll",
        "include-hidden-files: true",
    ):
        if token not in pages_workflow:
            failures.append(f"pages.yml: hidden public files are not protected by {token!r}")

    vetpulse_demo = (ROOT / "vetpulse/demo.html").read_text(encoding="utf-8")
    if "*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}" not in vetpulse_demo:
        failures.append("vetpulse/demo.html: missing universal reduced-motion fallback")

    if failures:
        print("Site checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Site checks passed: {len(parsed)} HTML files, {len(urls)} sitemap URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
