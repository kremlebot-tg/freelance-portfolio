#!/usr/bin/env python3
# DEPRECATED (2026-07-04): форма переехала на Vercel (api/form.js).
# Причина: IP VPS совпадает с VPN-сервером — у клиентов под VPN
# запросы к form.rednd.ru таймаутились. Сервис на VPS оставлен
# работающим, но фронт его больше не использует.
"""Эндпоинт формы Re:dnd: POST /submit → сообщение в Telegram.

Только стандартная библиотека Python — на сервере не нужны pip/venv.
Слушает 127.0.0.1:$FORM_PORT (по умолчанию 8011) — наружу только через nginx.

Секреты — в /etc/rednd-form.env (права 600), НЕ в этом файле:
    TG_BOT_TOKEN=...
    TG_CHAT_ID=...
    ALLOWED_ORIGINS=https://rednd.ru,https://www.rednd.ru
    FORM_PORT=8011

Логика повторяет прежний api/form.js: CORS по белому списку, honeypot
с фейковым успехом, rate-limit по IP, обрезка длин, префикс [RU]/[EN].
"""
import json
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ.get('TG_BOT_TOKEN', '')
CHAT_ID = os.environ.get('TG_CHAT_ID', '')
ALLOWED = [o.strip() for o in os.environ.get(
    'ALLOWED_ORIGINS', 'https://rednd.ru,https://www.rednd.ru'
).split(',') if o.strip()]

RATE_MAX = 5          # заявок
RATE_WINDOW = 600     # за 10 минут
_rate = {}
_rate_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = 'rednd-form/1.0'

    def _cors_headers(self):
        origin = self.headers.get('Origin', '')
        self.send_header('Access-Control-Allow-Origin',
                         origin if origin in ALLOWED else ALLOWED[0])
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Vary', 'Origin')

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            return self._json(200, {'ok': True, 'configured': bool(TOKEN and CHAT_ID)})
        return self._json(404, {'error': 'not found'})

    def do_POST(self):
        if self.path.rstrip('/') != '/submit':
            return self._json(404, {'error': 'not found'})

        # rate-limit по IP (реальный IP приходит от nginx в X-Forwarded-For)
        ip = (self.headers.get('X-Forwarded-For', '').split(',')[0].strip()
              or self.client_address[0])
        now = time.time()
        with _rate_lock:
            n, ts = _rate.get(ip, (0, now))
            if now - ts > RATE_WINDOW:
                n, ts = 0, now
            if n >= RATE_MAX:
                return self._json(429, {'error': 'too many requests'})
            _rate[ip] = (n + 1, ts)
            if len(_rate) > 10_000:   # не даём словарю расти бесконечно
                _rate.clear()

        try:
            length = min(int(self.headers.get('Content-Length', 0)), 64_000)
            data = json.loads(self.rfile.read(length))
            assert isinstance(data, dict)
        except Exception:
            return self._json(400, {'error': 'bad json'})

        # honeypot: скрытое поле «website» заполняют только боты;
        # отвечаем «успехом», чтобы бот не понял, что отсеян
        if data.get('website'):
            return self._json(200, {'ok': True})

        task = str(data.get('task', ''))[:2000].strip()
        typ = str(data.get('type', ''))[:100].strip()
        budget = str(data.get('budget', ''))[:100].strip()
        contact = str(data.get('contact', ''))[:200].strip()
        if not task or not contact:
            return self._json(400, {'error': 'task and contact are required'})

        lang = 'EN' if data.get('lang') == 'en' else 'RU'
        text = (f'[{lang}] Новая заявка с сайта\n\n'
                f'Задача: {task}\n'
                f'Тип: {typ or "—"}\n'
                f'Бюджет: {budget or "—"}\n'
                f'Контакт: {contact}')

        req = urllib.request.Request(
            f'https://api.telegram.org/bot{TOKEN}/sendMessage',
            data=json.dumps({'chat_id': CHAT_ID, 'text': text}).encode(),
            headers={'Content-Type': 'application/json'},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                ok = 200 <= resp.status < 300
        except Exception:
            ok = False
        if not ok:
            return self._json(502, {'error': 'telegram delivery failed'})
        return self._json(200, {'ok': True})

    def log_message(self, fmt, *args):
        pass  # не пишем IP посетителей в journal


if __name__ == '__main__':
    port = int(os.environ.get('FORM_PORT', '8011'))
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
