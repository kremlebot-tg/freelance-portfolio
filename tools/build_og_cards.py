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
    else:
        kicker = "ИНТЕРАКТИВНОЕ ДЕМО · OZON" if language == "ru" else "INTERACTIVE DEMO · OZON"
        title = "Безопасный\nрепрайсер" if language == "ru" else "Safe repricing\ncontrols"
        subtitle = "Dry-run → проверка → подтверждение" if language == "ru" else "Dry run → review → approval"
        footer = "rednd.ru · синтетические данные" if language == "ru" else "rednd.ru · synthetic data"
        draw_autopricer_panel(draw, language)

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


def assets() -> dict[Path, bytes]:
    return {
        ROOT / "og-case-scout.png": png_bytes(build_card("scout", "ru")),
        ROOT / "og-case-scout-en.png": png_bytes(build_card("scout", "en")),
        ROOT / "og-case-autopricer.png": png_bytes(build_card("autopricer", "ru")),
        ROOT / "og-case-autopricer-en.png": png_bytes(build_card("autopricer", "en")),
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
