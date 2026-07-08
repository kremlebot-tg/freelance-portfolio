"""Re:dnd форма → Yandex Cloud Function (за API Gateway).

Поток (порядок обязателен по ч.5 ст.18 152-ФЗ):
  honeypot → валидация → (1) запись заявки в Object Storage (РФ, ru-central1)
  → и ТОЛЬКО при успехе → (2) уведомление в Telegram.
Упала запись в бакет → 502, в Telegram ничего не уходит.

Только стандартная библиотека Python — без requirements/зависимостей.
Секреты (S3-ключ бакета, токен/chat_id Telegram) НЕ в env и НЕ в коде:
читаются в рантайме из Lockbox по IAM-токену сервисного аккаунта функции.

Не-секретные параметры — в переменных окружения функции:
  LEADS_BUCKET   — имя бакета
  S3_SECRET_ID   — id Lockbox-секрета с ключами S3_KEY_ID / S3_SECRET
  TG_SECRET_ID   — id Lockbox-секрета с ключами TG_BOT_TOKEN / TG_CHAT_ID
"""
import base64
import hashlib
import hmac
import json
import os
import time
import urllib.request
import uuid
from datetime import datetime, timezone

BUCKET = os.environ["LEADS_BUCKET"]
S3_SECRET_ID = os.environ["S3_SECRET_ID"]
TG_SECRET_ID = os.environ["TG_SECRET_ID"]
S3_HOST = "storage.yandexcloud.net"
S3_REGION = "ru-central1"

ALLOWED_ORIGINS = ("https://rednd.ru", "https://www.rednd.ru")

# rate-limit по IP: best-effort, память живёт в пределах одного тёплого
# инстанса функции и сбрасывается при холодном старте/масштабировании.
# Основная защита от ботов — honeypot; это лишь грубый предохранитель.
RATE_MAX = 5
RATE_WINDOW = 600  # сек
_RATE: dict[str, tuple[int, float]] = {}

_iam = {"token": None, "exp": 0.0}
_lockbox_cache: dict[str, dict] = {}


def _iam_token() -> str:
    now = time.time()
    if _iam["token"] and now < _iam["exp"] - 60:
        return _iam["token"]
    req = urllib.request.Request(
        "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
        headers={"Metadata-Flavor": "Google"},
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        d = json.load(r)
    _iam["token"] = d["access_token"]
    _iam["exp"] = now + int(d.get("expires_in", 3600))
    return _iam["token"]


def _lockbox(secret_id: str) -> dict:
    now = time.time()
    c = _lockbox_cache.get(secret_id)
    if c and now < c["exp"]:
        return c["data"]
    req = urllib.request.Request(
        f"https://payload.lockbox.api.cloud.yandex.net/lockbox/v1/secrets/{secret_id}/payload",
        headers={"Authorization": f"Bearer {_iam_token()}"},
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        d = json.load(r)
    data = {e["key"]: e.get("textValue", "") for e in d.get("entries", [])}
    _lockbox_cache[secret_id] = {"data": data, "exp": now + 300}
    return data


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def _put_object(key_id: str, secret: str, bucket: str, obj_key: str, body: bytes) -> bool:
    """PUT объекта в Object Storage через S3 API с подписью AWS SigV4 (path-style)."""
    now = datetime.now(timezone.utc)
    amzdate = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body).hexdigest()
    canonical_uri = f"/{bucket}/{obj_key}"  # ключ состоит только из [A-Za-z0-9/_.-] — не требует энкодинга
    canonical_headers = (
        f"host:{S3_HOST}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{amzdate}\n"
    )
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = (
        f"PUT\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )
    scope = f"{datestamp}/{S3_REGION}/s3/aws4_request"
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n{amzdate}\n{scope}\n"
        f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    )
    k = _sign(("AWS4" + secret).encode(), datestamp)
    k = _sign(k, S3_REGION)
    k = _sign(k, "s3")
    k = _sign(k, "aws4_request")
    signature = hmac.new(k, string_to_sign.encode(), hashlib.sha256).hexdigest()
    authz = (
        f"AWS4-HMAC-SHA256 Credential={key_id}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    req = urllib.request.Request(
        f"https://{S3_HOST}/{bucket}/{obj_key}",
        data=body,
        method="PUT",
        headers={
            "Host": S3_HOST,
            "x-amz-date": amzdate,
            "x-amz-content-sha256": payload_hash,
            "Authorization": authz,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return 200 <= r.status < 300


def _send_telegram(token: str, chat_id: str, text: str):
    """Отправка в Telegram. Возвращает (ok, http_status, description) —
    description это поле от Telegram API (без секретов), для лога."""
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text}).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode("utf-8", "replace")
        return (200 <= r.status < 300), r.status, raw[:300]
    except urllib.error.HTTPError as e:  # Telegram отдаёт 4xx с JSON {ok,error_code,description}
        return False, e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:  # noqa: BLE001 — таймаут/сеть
        return False, -1, f"{type(e).__name__}: {e}"[:300]


def _cors(origin: str) -> dict:
    allow = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    return {
        "Access-Control-Allow-Origin": allow,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Vary": "Origin",
    }


def _resp(code: int, obj: dict, cors: dict) -> dict:
    headers = dict(cors)
    headers["Content-Type"] = "application/json"
    return {"statusCode": code, "headers": headers, "body": json.dumps(obj)}


def handler(event, context):
    method = (event.get("httpMethod") or "").upper()
    headers = event.get("headers") or {}
    origin = headers.get("Origin") or headers.get("origin") or ""
    cors = _cors(origin)

    if method == "OPTIONS":
        return {"statusCode": 204, "headers": cors, "body": ""}
    if method != "POST":
        return _resp(405, {"error": "method not allowed"}, cors)

    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8", "replace")
    try:
        data = json.loads(raw)
        assert isinstance(data, dict)
    except Exception:
        return _resp(400, {"error": "bad json"}, cors)

    # honeypot: скрытое поле «website» заполняют только боты → фейковый успех,
    # ничего не пишем и не шлём.
    if data.get("website"):
        return _resp(200, {"ok": True}, cors)

    ip = (
        ((event.get("requestContext") or {}).get("identity") or {}).get("sourceIp")
        or (headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        or "unknown"
    )
    now = time.time()
    n, ts = _RATE.get(ip, (0, now))
    if now - ts > RATE_WINDOW:
        n, ts = 0, now
    if n >= RATE_MAX:
        return _resp(429, {"error": "too many requests"}, cors)
    _RATE[ip] = (n + 1, ts)
    if len(_RATE) > 10_000:
        _RATE.clear()

    task = str(data.get("task", "") or "")[:2000].strip()
    typ = str(data.get("type", "") or "")[:100].strip()
    budget = str(data.get("budget", "") or "")[:100].strip()
    contact = str(data.get("contact", "") or "")[:200].strip()
    lang = "EN" if data.get("lang") == "en" else "RU"
    if not task or not contact:
        return _resp(400, {"error": "task and contact are required"}, cors)

    # --- шаг 1: первичная запись в Object Storage (РФ). Должна пройти ПЕРВОЙ. ---
    dt = datetime.now(timezone.utc)
    record = {
        "lang": lang, "task": task, "type": typ, "budget": budget,
        "contact": contact, "ip": ip,
        "received_at": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    obj_key = f"leads/{dt:%Y/%m/%d}/{dt:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex}.json"
    body = json.dumps(record, ensure_ascii=False).encode("utf-8")
    try:
        s3 = _lockbox(S3_SECRET_ID)
        wrote = _put_object(s3["S3_KEY_ID"], s3["S3_SECRET"], BUCKET, obj_key, body)
    except Exception:
        wrote = False
    if not wrote:
        # запись ПДн в РФ не удалась → по 152-ФЗ дальше не идём, Telegram не шлём
        return _resp(502, {"error": "storage write failed"}, cors)

    # --- шаг 2: уведомление в Telegram (только после успешной записи). ---
    # Заявка уже сохранена (152-ФЗ выполнен) — TG best-effort, его сбой
    # не роняет ответ пользователю (данные в бакете = источник истины),
    # но ошибку НЕ глушим: пишем код и описание от Telegram в лог.
    import sys as _sys
    try:
        tg = _lockbox(TG_SECRET_ID)
        tok = tg.get("TG_BOT_TOKEN", "")
        cid = tg.get("TG_CHAT_ID", "")
        # диагностика секрета без утечки значений
        print(
            f"[rednd-form][tg] token_len={len(tok)} "
            f"token_is_placeholder={tok == 'PLACEHOLDER_FILL_ME'} "
            f"chat_id_len={len(cid)} chat_id_is_placeholder={cid == 'PLACEHOLDER_FILL_ME'} "
            f"chat_id_is_digits={cid.lstrip('-').isdigit() if cid else False}",
            file=_sys.stderr,
        )
        text = (
            f"[{lang}] Новая заявка с сайта\n\n"
            f"Задача: {task}\n"
            f"Тип: {typ or '—'}\n"
            f"Бюджет: {budget or '—'}\n"
            f"Контакт: {contact}"
        )
        ok, status, desc = _send_telegram(tok, cid, text)
        if not ok:
            print(f"[rednd-form][tg] sendMessage FAILED http={status} resp={desc}", file=_sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"[rednd-form][tg] step error: {type(e).__name__}: {e}", file=_sys.stderr)

    return _resp(200, {"ok": True}, cors)
