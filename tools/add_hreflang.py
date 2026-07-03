#!/usr/bin/env python3
"""Проставляет hreflang-пары (ru/en/x-default) на все парные страницы.

Идемпотентен: старые hreflang-строки удаляет и вставляет заново.
Запуск из корня репозитория: python3 tools/add_hreflang.py
"""
import pathlib
import re

BASE = 'https://rednd.ru/'
PAIRED = [
    'index.html', 'projects.html', 'services.html', 'about.html',
    'contact.html', 'privacy.html',
    'case-crm.html', 'case-autopricer.html', 'case-subscriptions.html',
    'case-mutual.html', 'case-faith.html',
]

def block(name: str) -> str:
    ru = BASE + ('' if name == 'index.html' else name)
    en = BASE + 'en/' + ('' if name == 'index.html' else name)
    return (
        f'<link rel="alternate" hreflang="ru" href="{ru}">\n'
        f'<link rel="alternate" hreflang="en" href="{en}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{ru}">\n'
    )

def process(path: pathlib.Path, name: str) -> None:
    t = path.read_text(encoding='utf-8')
    t = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n', '', t)
    marker = re.search(r'<link rel="icon"[^>]*>\n', t)
    assert marker, path
    t = t[:marker.end()] + block(name) + t[marker.end():]
    path.write_text(t, encoding='utf-8')
    print('hreflang:', path)

root = pathlib.Path(__file__).resolve().parent.parent
for name in PAIRED:
    for p in (root / name, root / 'en' / name):
        if p.exists():
            process(p, name)
        else:
            print('SKIP (нет файла):', p)
