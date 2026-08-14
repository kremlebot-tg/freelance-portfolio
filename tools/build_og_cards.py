#!/usr/bin/env python3
"""Build flat, truthful social cards for selected portfolio cases.

The generated PNG files are committed to the repository. Pillow is only needed
when the source cards are intentionally rebuilt; the website itself has no
runtime dependency on it.
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
WIDTH = 1200
HEIGHT = 630
FONT_DIR = Path("/System/Library/Fonts/Supplemental")
REGULAR_FONT = FONT_DIR / "Arial.ttf"
BOLD_FONT = FONT_DIR / "Arial Bold.ttf"

COLORS = {
    "background": "#0D1721",
    "panel": "#152533",
    "panel_alt": "#1A3040",
    "border": "#31536A",
    "text": "#F2F7FB",
    "muted": "#9CB0BE",
    "blue": "#43A8E8",
    "blue_soft": "#204B64",
    "green": "#58CE87",
    "green_soft": "#193D32",
    "amber": "#F2BE5C",
    "amber_soft": "#4B3B20",
}


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD_FONT if bold else REGULAR_FONT), size=size)


def draw_logo(draw: ImageDraw.ImageDraw) -> None:
    x, y, size = 72, 70, 50
    draw.rounded_rectangle((x, y, x + size, y + size), radius=13, fill=COLORS["blue"])
    for dx, dy in ((16, 16), (34, 16), (16, 34), (34, 34), (25, 25)):
        draw.ellipse((x + dx - 4, y + dy - 4, x + dx + 4, y + dy + 4), fill=COLORS["text"])
    draw.text((145, 78), "Re:dnd", font=font(29, bold=True), fill=COLORS["text"])


def draw_arrow(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.line((x, y, x + 26, y), fill=COLORS["blue"], width=3)
    draw.line((x + 19, y - 7, x + 26, y), fill=COLORS["blue"], width=3)
    draw.line((x + 19, y + 7, x + 26, y), fill=COLORS["blue"], width=3)


def draw_scout_panel(draw: ImageDraw.ImageDraw, language: str) -> None:
    labels = (
        ("ОБЩИЙ ПУЛ", "В РАБОТЕ", "СЛЕДУЮЩИЙ ШАГ")
        if language == "ru"
        else ("SHARED POOL", "IN PROGRESS", "NEXT ACTION")
    )
    panel = (790, 190, 1128, 486)
    draw.rounded_rectangle(panel, radius=25, fill=COLORS["panel"], outline=COLORS["border"], width=2)
    for index, label in enumerate(labels):
        top = 225 + index * 84
        accent = COLORS["green"] if index == 1 else COLORS["blue"]
        fill = COLORS["green_soft"] if index == 1 else COLORS["panel_alt"]
        draw.rounded_rectangle((826, top, 1092, top + 54), radius=15, fill=fill)
        draw.ellipse((847, top + 20, 861, top + 34), fill=accent)
        draw.text((878, top + 17), label, font=font(15, bold=True), fill=COLORS["text"])
        if index < 2:
            draw_arrow(draw, 946, top + 69)


def draw_autopricer_panel(draw: ImageDraw.ImageDraw, language: str) -> None:
    copy = {
        "ru": ("DRY-RUN", "Цена не отправляется", "ПОРОГ МАРЖИ", "РУЧНОЕ ПОДТВЕРЖДЕНИЕ"),
        "en": ("DRY RUN", "No price writes", "MARGIN FLOOR", "MANUAL APPROVAL"),
    }[language]
    panel = (790, 190, 1128, 486)
    draw.rounded_rectangle(panel, radius=25, fill=COLORS["panel"], outline=COLORS["border"], width=2)
    draw.rounded_rectangle((826, 224, 936, 262), radius=19, fill=COLORS["amber_soft"])
    draw.text((847, 235), copy[0], font=font(14, bold=True), fill=COLORS["amber"])
    draw.text((826, 284), copy[1], font=font(21, bold=True), fill=COLORS["text"])
    draw.text((826, 334), copy[2], font=font(13, bold=True), fill=COLORS["muted"])
    draw.line((826, 375, 1080, 375), fill=COLORS["border"], width=8)
    draw.line((826, 375, 1002, 375), fill=COLORS["blue"], width=8)
    draw.ellipse((989, 362, 1015, 388), fill=COLORS["blue"])
    draw.rounded_rectangle((826, 413, 1088, 455), radius=13, fill=COLORS["blue_soft"])
    draw.text((846, 426), copy[3], font=font(13, bold=True), fill=COLORS["text"])


def draw_flow_panel(
    draw: ImageDraw.ImageDraw,
    labels: tuple[str, str, str],
    *,
    highlight: int = 1,
) -> None:
    panel = (790, 190, 1128, 486)
    draw.rounded_rectangle(panel, radius=25, fill=COLORS["panel"], outline=COLORS["border"], width=2)
    for index, label in enumerate(labels):
        top = 225 + index * 84
        active = index == highlight
        accent = COLORS["green"] if active else COLORS["blue"]
        fill = COLORS["green_soft"] if active else COLORS["panel_alt"]
        draw.rounded_rectangle((826, top, 1092, top + 54), radius=15, fill=fill)
        draw.ellipse((847, top + 20, 861, top + 34), fill=accent)
        draw.text((878, top + 17), label, font=font(14, bold=True), fill=COLORS["text"])
        if index < 2:
            draw_arrow(draw, 946, top + 69)


def draw_faith_panel(draw: ImageDraw.ImageDraw, language: str) -> None:
    copy = {
        "ru": ("ТЕХНИЧЕСКАЯ СБОРКА", "03 / 05", "УРОК", "ТЕСТ", "ОФЛАЙН-БИБЛИОТЕКА"),
        "en": ("TECHNICAL BUILD", "03 / 05", "LESSON", "QUIZ", "OFFLINE LIBRARY"),
    }[language]
    panel = (790, 190, 1128, 486)
    draw.rounded_rectangle(panel, radius=25, fill=COLORS["panel"], outline=COLORS["border"], width=2)
    draw.text((826, 226), copy[0], font=font(13, bold=True), fill=COLORS["blue"])
    draw.text((826, 263), copy[1], font=font(45, bold=True), fill=COLORS["text"])
    draw.line((826, 331, 1088, 331), fill=COLORS["border"], width=2)
    for index, label in enumerate(copy[2:]):
        y = 358 + index * 38
        draw.ellipse((826, y + 4, 838, y + 16), fill=COLORS["green"] if index < 2 else COLORS["blue"])
        draw.text((852, y), label, font=font(14, bold=True), fill=COLORS["text"])


def build_chainya_en() -> Image.Image:
    image = Image.open(ROOT / "assets/cases/chainya/og.jpg").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 768, HEIGHT), fill="#15110F")
    draw.text((72, 67), "CHAINYA", font=font(31, bold=True), fill="#F4EFE9")
    draw.text((72, 170), "LIVE MULTILINGUAL WEBSITE", font=font(16, bold=True), fill="#D56A58")
    draw.multiline_text(
        (72, 220),
        "Tea catalogue,\norders and booking",
        font=font(49, bold=True),
        fill="#F4EFE9",
        spacing=2,
    )
    draw.text((72, 405), "Server-verified customer journeys", font=font(23), fill="#C7BDB5")
    draw.text((72, 535), "Moscow · 32 items · 3 languages", font=font(18), fill="#A99D95")
    return image


def build_vetpulse_en() -> Image.Image:
    background = "#F1F6F3"
    dark = "#102722"
    green = "#086153"
    muted = "#5E726C"
    orange = "#EE7047"
    image = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((72, 64, 126, 118), radius=14, fill=green)
    for dx, dy in ((17, 21), (27, 15), (37, 21), (22, 32), (32, 32)):
        draw.ellipse((72 + dx - 4, 64 + dy - 4, 72 + dx + 4, 64 + dy + 4), fill=orange)
    draw.text((145, 74), "VetPulse", font=font(29, bold=True), fill=dark)
    draw.text((72, 168), "PRODUCT PROTOTYPE", font=font(17, bold=True), fill="#0E8876")
    draw.multiline_text(
        (72, 211),
        "Testing the journey\nbefore development",
        font=font(52, bold=True),
        fill=dark,
        spacing=2,
    )
    draw.text((72, 365), "Enquiries · booking drafts · reminders · reactivation", font=font(22), fill=muted)
    draw.rounded_rectangle((72, 438, 262, 484), radius=23, fill="#FFFFFF", outline="#D8E3DE", width=2)
    draw.ellipse((92, 455, 106, 469), fill=orange)
    draw.text((121, 451), "FICTIONAL DATA", font=font(14, bold=True), fill=muted)
    draw.text((72, 535), "No live AI, backend or Vetmanager connection", font=font(17), fill="#7A8D86")

    draw.rounded_rectangle((804, 94, 1128, 536), radius=25, fill="#FFFFFF", outline="#D6E2DD", width=2)
    draw.text((836, 135), "INTERACTIVE CLINIC DESK", font=font(14, bold=True), fill=muted)
    draw.text((836, 177), "5", font=font(67, bold=True), fill=green)
    draw.text((914, 207), "sections", font=font(24, bold=True), fill=muted)
    draw.line((836, 264, 1096, 264), fill="#DDE7E3", width=2)
    for index, label in enumerate(("Overview", "Enquiries", "Booking drafts", "Reminders", "Reactivation"), start=1):
        y = 297 + (index - 1) * 45
        draw.text((836, y), f"{index:02d}", font=font(17), fill=dark)
        draw.text((878, y), label, font=font(17), fill=dark)
    return image


def build_card(kind: str, language: str) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    draw = ImageDraw.Draw(image)
    draw_logo(draw)

    if kind == "scout":
        kicker = "ЖИВОЙ ПРОДУКТ · CRM · DESKTOP" if language == "ru" else "LIVE PRODUCT · CRM · DESKTOP"
        title = "Scout"
        subtitle = "Поиск компаний → очередь работы" if language == "ru" else "Company discovery → work queue"
        footer = "rednd.ru · web + macOS + Windows"
        draw_scout_panel(draw, language)
    elif kind == "autopricer":
        kicker = "ИНТЕРАКТИВНОЕ ДЕМО · OZON" if language == "ru" else "INTERACTIVE DEMO · OZON"
        title = "Безопасный\nрепрайсер" if language == "ru" else "Safe repricing\ncontrols"
        subtitle = "Dry-run → проверка → подтверждение" if language == "ru" else "Dry run → review → approval"
        footer = "rednd.ru · синтетические данные" if language == "ru" else "rednd.ru · synthetic data"
        draw_autopricer_panel(draw, language)
    elif kind == "crm":
        kicker = "ПРОВЕРЯЕМОЕ ДЕМО · CRM" if language == "ru" else "VERIFIABLE DEMO · CRM"
        title = "Персональный CRM" if language == "ru" else "Personal CRM"
        subtitle = "Заметки о людях → граф связей" if language == "ru" else "Notes about people → relationship graph"
        footer = "rednd.ru · Telegram + web"
        labels = (
            ("ЗАМЕТКА", "2 ФАКТА", "НАПОМИНАНИЕ")
            if language == "ru"
            else ("NOTE", "2 FACTS", "REMINDER")
        )
        draw_flow_panel(draw, labels)
    elif kind == "faith":
        kicker = "ТЕХНИЧЕСКАЯ СБОРКА · FLUTTER" if language == "ru" else "TECHNICAL BUILD · FLUTTER"
        title = "Faith App"
        subtitle = "Урок → тест → офлайн-библиотека" if language == "ru" else "Lesson → quiz → offline library"
        footer = "rednd.ru · нужна экспертная рецензия" if language == "ru" else "rednd.ru · expert review required"
        draw_faith_panel(draw, language)
    elif kind == "mutual":
        kicker = "ИНТЕРАКТИВНЫЙ ПРОТОТИП · UX" if language == "ru" else "INTERACTIVE PROTOTYPE · UX"
        title = "MUTUAL"
        subtitle = "QR → взаимное согласие → знакомство" if language == "ru" else "QR → mutual consent → connection"
        footer = "rednd.ru · приватность заложена во флоу" if language == "ru" else "rednd.ru · privacy built into the flow"
        labels = (
            ("QR-СКАН", "ЗАПРОС", "ВЗАИМНЫЙ МЭТЧ")
            if language == "ru"
            else ("QR SCAN", "REQUEST", "MUTUAL MATCH")
        )
        draw_flow_panel(draw, labels, highlight=2)
    elif kind == "subscriptions":
        kicker = "ИНТЕРАКТИВНЫЙ ПРОТОТИП · TELEGRAM" if language == "ru" else "INTERACTIVE PROTOTYPE · TELEGRAM"
        title = "Сценарий\nподписки" if language == "ru" else "Subscription\njourney"
        subtitle = "Тариф → переход → управление доступом" if language == "ru" else "Plan → hand-off → access states"
        footer = "rednd.ru · без реальных платежей" if language == "ru" else "rednd.ru · no real payments"
        labels = (
            ("ТАРИФ", "ПЕРЕХОД", "ДОСТУП")
            if language == "ru"
            else ("PLAN", "HAND-OFF", "ACCESS")
        )
        draw_flow_panel(draw, labels)
    else:  # pragma: no cover - only internal, fixed card specs call this function
        raise ValueError(f"unknown card kind: {kind}")

    draw.text((72, 213), kicker, font=font(17, bold=True), fill=COLORS["blue"])
    title_font = font(64, bold=True)
    draw.multiline_text((72, 261), title, font=title_font, fill=COLORS["text"], spacing=0)
    subtitle_y = 358 if "\n" not in title else 414
    draw.text((72, subtitle_y), subtitle, font=font(25), fill=COLORS["muted"])
    draw.text((72, 552), footer, font=font(18), fill=COLORS["muted"])
    return image


def png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG", compress_level=9)
    return output.getvalue()


def jpeg_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="JPEG", quality=91, optimize=True, progressive=False, subsampling=2)
    return output.getvalue()


def assets() -> dict[Path, bytes]:
    return {
        ROOT / "og-case-scout.png": png_bytes(build_card("scout", "ru")),
        ROOT / "og-case-scout-en.png": png_bytes(build_card("scout", "en")),
        ROOT / "og-case-autopricer.png": png_bytes(build_card("autopricer", "ru")),
        ROOT / "og-case-autopricer-en.png": png_bytes(build_card("autopricer", "en")),
        ROOT / "og-case-crm.png": png_bytes(build_card("crm", "ru")),
        ROOT / "og-case-crm-en.png": png_bytes(build_card("crm", "en")),
        ROOT / "og-case-faith.png": png_bytes(build_card("faith", "ru")),
        ROOT / "og-case-faith-en.png": png_bytes(build_card("faith", "en")),
        ROOT / "og-case-mutual.png": png_bytes(build_card("mutual", "ru")),
        ROOT / "og-case-mutual-en.png": png_bytes(build_card("mutual", "en")),
        ROOT / "og-case-subscriptions.png": png_bytes(build_card("subscriptions", "ru")),
        ROOT / "og-case-subscriptions-en.png": png_bytes(build_card("subscriptions", "en")),
        ROOT / "assets/cases/chainya/og-en.jpg": jpeg_bytes(build_chainya_en()),
        ROOT / "vetpulse/og-cover-en.png": png_bytes(build_vetpulse_en()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="check committed files without changing them")
    args = parser.parse_args()

    failures: list[str] = []
    for path, expected in assets().items():
        if args.check:
            if not path.exists() or path.read_bytes() != expected:
                failures.append(str(path.relative_to(ROOT)))
        else:
            path.write_bytes(expected)
            print(f"wrote {path.relative_to(ROOT)} ({len(expected):,} bytes)")

    if failures:
        print("Social cards are missing or stale: " + ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
