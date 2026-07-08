# Re:dnd — сайт-портфолио

Двуязычный (RU + `/en/`) статический сайт на **https://rednd.ru**: Telegram-боты, мини-аппы, кейсы
с живыми демо. Дизайн — Claude Design (формат `.dc.html` + рантайм
`support.js`), инженерия и деплой — Claude Code.

## ⚡ Что вписать после клона

### 1. Контакты, цены, реквизиты — [site-config.js](site-config.js)

```js
formEndpoint: 'https://<...>.apigw.yandexcloud.net/submit',  // Yandex Cloud (см. ниже)
telegram: '@re_dnd',
email: 'politushkin@gmail.com',
requisites / requisitesFull,      // ← отчество и ОГРНИП вместо плейсхолдеров
prices / pricesEn,                // ← стартовые цены («от»)
testimonials, aboutPhoto, aboutLines / aboutLinesEn
```

### 2. Форма → Telegram (Yandex Cloud, РФ)

Заявки с обеих форм (RU и EN) приходят сообщением в Telegram с префиксом
`[RU]`/`[EN]`. Бэкенд — в **Yandex Cloud** (регион ru-central1, данные в РФ):

```
POST → API Gateway → Cloud Function → (1) запись заявки в Object Storage (РФ)
                                     → (2) только при успехе — sendMessage в Telegram
```

Порядок (1)→(2) обязателен по ч.5 ст.18 152-ФЗ: первичная запись ПДн граждан
РФ — в базе на территории РФ, и лишь затем возможна трансграничная передача
(Telegram). Упала запись в бакет → `502`, в Telegram ничего не уходит.

Исходник функции — [yandex-function/index.py](yandex-function/index.py)
(только stdlib; SigV4 к Object Storage вручную; секреты читаются из Lockbox
в рантайме по IAM-токену сервисного аккаунта — в env только id, не значения).

**Ресурсы (облако cloud-log-24-1, folder default):**

| Ресурс | Имя / id |
|---|---|
| Service account | `rednd-leads-writer` = `ajebeonci4uufifi4skq` |
| Bucket (приватный) | `rednd-leads` (ru-central1) |
| Cloud Function | `rednd-form` = `d4enp1ve4p0rdbiqddol` |
| API Gateway | `rednd-form-gw` = `d5d7olk60q94hjb111lj` |
| Lockbox (S3-ключ) | `rednd-form-s3` = `e6q4640d42b80lv0apuv` |
| Lockbox (Telegram) | `rednd-form-telegram` = `e6quh6r1v7fv7h6bidkt` |

Endpoint (в `site-config.js`): `https://d5d7olk60q94hjb111lj.kocrdvxt.apigw.yandexcloud.net/submit`

**Секреты Telegram** живут в Lockbox `rednd-form-telegram`, не в коде. Обновить
значения (функция читает последнюю версию сама, редеплой не нужен):

```bash
~/yandex-cloud/bin/yc lockbox secret add-version --name rednd-form-telegram \
  --payload '[{"key":"TG_BOT_TOKEN","textValue":"..."},{"key":"TG_CHAT_ID","textValue":"..."}]'
```

Обновить сам код функции:

```bash
cd yandex-function && zip -j /tmp/fn.zip index.py
~/yandex-cloud/bin/yc serverless function version create --function-id d4enp1ve4p0rdbiqddol \
  --runtime python312 --entrypoint index.handler --memory 128m --execution-timeout 30s \
  --source-path /tmp/fn.zip --service-account-id ajebeonci4uufifi4skq \
  --environment LEADS_BUCKET=rednd-leads --environment S3_SECRET_ID=e6q4640d42b80lv0apuv \
  --environment TG_SECRET_ID=e6quh6r1v7fv7h6bidkt
```

Защита от спама: honeypot + rate-limit 5 заявок / 10 минут с IP (per-instance
best-effort). Другой домен формы в будущем — в env функции `ALLOWED_ORIGINS`
(через запятую) или в белый список `ALLOWED_ORIGINS` в `index.py`.

> **TODO (владельцу, не инженеру):** как оператор ПДн, ИП Яценко, возможно,
> обязан подать **уведомление об обработке ПДн в Роскомнадзор** (ст. 22 152-ФЗ).
> Это задача владельца — проверить необходимость и подать при необходимости.

> **Нюанс прав доступа:** запись в бакет сейчас разрешена folder-level ролью
> `storage.uploader` (write-only) у SA `rednd-leads-writer`. Строгий
> bucket-scope через CLI не вышел (ACL account-грант «Unimplemented»,
> policy-principal для SA требует canonical-id из консоли). Тонкая настройка —
> в веб-консоли: Bucket `rednd-leads` → доступ → добавить SA с правом «запись»,
> затем снять folder-роль. Риск минимален: роль write-only, SA выделенный,
> в folder один бакет.

### 2а. Старый эндпоинт на VPS — ПОГАШЕН

Форма раньше жила на VPS (`server/`, сервис `rednd-form`, vhost
`form.rednd.ru`) и на Vercel (`api/form.js`) — оба выведены из работы, фронт
использует только Yandex Cloud. Код `server/` и `api/` оставлен в репо как
история. VPS-сервис погашен (`systemctl disable --now rednd-form` + снят
симлинк vhost). VPN-стек не затронут.

### 3. Юридические страницы — показать юристу

`privacy.html` и `consent.html` — типовые тексты под 152-ФЗ, написанные
под фактическое поведение сайта (форма собирает только контакт и описание
задачи; первичная запись в Object Storage Yandex Cloud в РФ, затем
уведомление в Telegram — трансграничная передача; без cookies и аналитики).
`/en/privacy.html` — generic-версия. ⚠️ Перед серьёзным использованием покажите
тексты юристу.

## Структура

| Файл | Что это |
|---|---|
| `index.html`, `projects.html`, `services.html`, `about.html`, `contact.html`, `case-*.html`, `privacy.html`, `consent.html` | Русские страницы |
| `en/*` | Английская версия (те же имена файлов; свои Header/Footer/CaseCTA; consent-страницы нет) |
| `Header.dc.html`, `Footer.dc.html`, `CaseCTA.dc.html` | Общие компоненты — подгружаются рантаймом по имени, **не переименовывать** (в `/en/` — свои копии) |
| `support.js` | Рантайм Claude Design (изменены: пути React → `vendor/` относительно самого скрипта) |
| `site-config.js` | ✏️ Всё редактируемое |
| `yandex-function/index.py` | Бэкенд формы (Cloud Function, Yandex Cloud) |
| `api/`, `server/` | История: прежние бэкенды формы (Vercel, VPS) — не используются |
| `vendor/`, `fonts/` | React 18.3.1 UMD и шрифты локально — сайт без внешних запросов |
| `ios-frame.jsx` → `ios-frame.js` | Исходник и прекомпилированная iOS-рамка для демо |

## Локальный запуск

```bash
python3 -m http.server 8788
# → http://localhost:8788 и http://localhost:8788/en/
```

Через `file://` не работает — рантайму нужен HTTP.

## Деплой

GitHub Pages собирает сайт прямо из ветки `main` (branch-based сборка,
`.nojekyll` в корне) — автоматически при каждом пуше:

```bash
git push
```

Примечание: раньше деплой шёл через Actions (`.github/workflows/deploy.yml`),
но 2026-07-02 очередь Actions-деплоев Pages весь вечер висела — переключил
на ветковую сборку, она идёт другим пайплайном. Workflow оставлен на ручной
запуск; как вернуть его — комментарий внутри файла.

## Если правите ios-frame.jsx

```bash
npm i @babel/standalone@7.29.0
node -e "const B=require('@babel/standalone'),fs=require('fs');fs.writeFileSync('ios-frame.js',B.transform(fs.readFileSync('ios-frame.jsx','utf8'),{filename:'ios-frame.jsx',presets:['react','typescript']}).code)"
```

## Демо в кейсах

Все 5 демо (обе языковые версии) — клиентские, на моковых данных.

**TODO (хуки под будущие бэкенды):**
- `case-subscriptions.html` — «оплата» это мок-экран ЮKassa; живая оплата =
  бэкенд с вебхуками (обработчик `onPay` — точка подключения)
- `case-crm.html` — «извлечение фактов» заскриптовано на 3 примерах;
  живой вариант — вызов LLM через серверный прокси

## Известные особенности

- Варнинги `[dc-runtime] {{ r.* }} never resolved` на автопрайсере —
  поведение рантайма Claude Design, есть и в оригинальном экспорте.
- У шрифта Sora нет кириллицы — русские заголовки рендерятся системным
  fallback-шрифтом (так было и в оригинале; латиница в `/en/` — настоящей Sora).
