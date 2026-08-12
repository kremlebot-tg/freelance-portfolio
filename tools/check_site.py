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
        if "theme.css?v=" in source and "theme.css?v=20260812a" not in source:
            failures.append(f"{rel}: stale theme.css cache token")
        if "site-config.js?v=" in source and "site-config.js?v=20260812a" not in source:
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
