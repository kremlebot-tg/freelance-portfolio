# Re:dnd — сайт-портфолио

Двуязычный (RU + `/en/`) статический сайт на **https://rednd.ru**: Telegram-боты, мини-аппы, кейсы
с живыми демо. Дизайн — Claude Design (формат `.dc.html` + рантайм
`support.js`), инженерия и деплой — Claude Code.

## ⚡ Что вписать после клона

### 1. Контакты, цены, реквизиты — [site-config.js](site-config.js)

```js
formEndpoint: 'https://form.rednd.ru/submit',  // эндпоинт на нашем VPS
telegram: '@re_dnd',
email: 'politushkin@gmail.com',
requisites / requisitesFull,      // ← отчество и ОГРНИП вместо плейсхолдеров
prices / pricesEn,                // ← стартовые цены («от»)
testimonials, aboutPhoto, aboutLines / aboutLinesEn
```

### 2. Форма → Telegram (эндпоинт на нашем VPS)

Заявки с обеих форм (RU и EN) приходят сообщением в Telegram с префиксом
`[RU]`/`[EN]`. Бэкенд — маленький python-сервис (только stdlib, без
зависимостей) на нашем сервере: `form.rednd.ru` → nginx → `127.0.0.1:8010`
→ Bot API. Исходники в [server/](server/):

| Файл | Куда встаёт на сервере |
|---|---|
| `server/form_server.py` | `/opt/rednd-form/form_server.py` |
| `server/rednd-form.service` | `/etc/systemd/system/rednd-form.service` |
| `server/nginx-form.rednd.ru.conf` | `/etc/nginx/sites-available/form.rednd.ru.conf` (+симлинк в sites-enabled) |

**Секреты** — в `/etc/rednd-form.env` (права 600, владелец root), формат:

```
TG_BOT_TOKEN=123456:ABC-...
TG_CHAT_ID=123456789
ALLOWED_ORIGINS=https://rednd.ru,https://www.rednd.ru
```

После правки секретов: `systemctl restart rednd-form`.

**Как получить токен и chat_id:**
1. `@BotFather` → `/newbot` → нейтральное имя → скопировать **token**
2. Написать боту `/start`, открыть
   `https://api.telegram.org/bot<ТОКЕН>/getUpdates` → `"chat":{"id":…}` —
   это **chat_id**

**Обслуживание:** `systemctl status rednd-form`, логи —
`journalctl -u rednd-form -n 50`. SSL продлевает certbot автоматически
(`certbot renew --dry-run` для проверки). Защита от спама: honeypot +
rate-limit 5 заявок / 10 минут с IP (в памяти процесса). Пока секреты —
плейсхолдеры, эндпоинт отвечает 502 на отправку (форма покажет «не
получилось отправить»); health-проверка: `curl https://form.rednd.ru/health`.

### 3. Юридические страницы — показать юристу

`privacy.html` и `consent.html` — типовые тексты под 152-ФЗ, написанные
под фактическое поведение сайта (форма собирает только контакт и описание
задачи; передача через собственный сервер form.rednd.ru с доставкой в
Telegram — передача в Telegram трансграничная; без cookies и аналитики). `/en/privacy.html` —
generic-версия без 152-ФЗ. ⚠️ Перед серьёзным использованием покажите
тексты юристу.

## Структура

| Файл | Что это |
|---|---|
| `index.html`, `projects.html`, `services.html`, `about.html`, `contact.html`, `case-*.html`, `privacy.html`, `consent.html` | Русские страницы |
| `en/*` | Английская версия (те же имена файлов; свои Header/Footer/CaseCTA; consent-страницы нет) |
| `Header.dc.html`, `Footer.dc.html`, `CaseCTA.dc.html` | Общие компоненты — подгружаются рантаймом по имени, **не переименовывать** (в `/en/` — свои копии) |
| `support.js` | Рантайм Claude Design (изменены: пути React → `vendor/` относительно самого скрипта) |
| `site-config.js` | ✏️ Всё редактируемое |
| `server/` | Исходники бэкенда формы (деплоятся на VPS, см. выше) |
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
