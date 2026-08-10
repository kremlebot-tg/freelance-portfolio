#!/usr/bin/env python3
"""Fast, dependency-free checks for the static site and its public surface."""

from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
SITE_ORIGIN = "https://rednd.ru"
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")


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
        if tag == "link" and values.get("rel", "").lower() == "canonical":
            self.canonicals.append(values.get("href", "").strip())
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

    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
    urls = [node.text or "" for node in sitemap.findall("s:url/s:loc", ns)]
    if len(urls) != len(set(urls)):
        failures.append("sitemap.xml: duplicate URLs")
    for url in urls:
        page = page_for_url(url).resolve()
        parser = parsed.get(page)
        if parser is None:
            failures.append(f"sitemap.xml: missing page for {url}")
            continue
        rel = page.relative_to(ROOT)
        if parser.lang not in {"ru", "en"}:
            failures.append(f"{rel}: missing or unsupported html lang")
        if not parser.title.strip():
            failures.append(f"{rel}: missing title")
        if len(parser.descriptions) != 1 or not parser.descriptions[0]:
            failures.append(f"{rel}: expected one non-empty meta description")
        if parser.canonicals != [url]:
            failures.append(f"{rel}: canonical must be exactly {url}")
        if parser.h1_count != 1:
            failures.append(f"{rel}: expected one h1, found {parser.h1_count}")

    for forbidden in ("README.md", "package.json", "package-lock.json", "ios-frame.jsx"):
        if forbidden in {Path(urlparse(url).path).name for url in urls}:
            failures.append(f"sitemap.xml: internal file listed: {forbidden}")

    for relative in ("contact.html", "partner-apply.html", "en/contact.html", "en/partner-apply.html"):
        source = (ROOT / relative).read_text(encoding="utf-8")
        if "payload.stored === true" not in source or "error.stored ? 'stored' : 'network'" not in source:
            failures.append(f"{relative}: missing stored-but-not-notified response handling")

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
    for page in case_pages:
        source = page.read_text(encoding="utf-8")
        has_shared_process = 'class="case-process__flow"' in source and 'class="case-process__link"' in source
        has_vetpulse_process = 'class="flow"' in source and 'class="flow-link"' in source
        if not (has_shared_process or has_vetpulse_process):
            failures.append(f"{page.relative_to(ROOT)}: missing visual business-process flow")

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

    if failures:
        print("Site checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Site checks passed: {len(parsed)} HTML files, {len(urls)} sitemap URLs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
