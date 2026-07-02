# Сайт-портфолио — Даниил Яценко

Двуязычный (RU + `/en/`) статический сайт: Telegram-боты, мини-аппы, кейсы
с живыми демо. Дизайн — Claude Design (формат `.dc.html` + рантайм
`support.js`), инженерия и деплой — Claude Code.

## ⚡ Что вписать после клона

### 1. Контакты, цены, реквизиты — [site-config.js](site-config.js)

```js
formEndpoint: '',                 // ← URL Cloudflare Worker (см. ниже)
telegram: '@ваш_ник',             // ← ник в Telegram
email: 'politushin@gmail.com',
requisites / requisitesFull,      // ← отчество и ОГРНИП вместо плейсхолдеров
prices / pricesEn,                // ← стартовые цены («от»)
testimonials, aboutPhoto, aboutLines / aboutLinesEn
```

### 2. Форма → Telegram (Cloudflare Worker)

Заявки с обеих форм (RU и EN) приходят вам сообщением в Telegram с
префиксом `[RU]`/`[EN]`. Токен бота живёт в секретах Cloudflare — не в коде
и не в репозитории.

**Шаг 1. Бот:** в Telegram откройте `@BotFather` → `/newbot` → нейтральное
имя (например, «Site Leads») и username вида `..._leads_bot` → скопируйте
**token** (формат `123456:ABC-...`). Никому его не пересылайте.

**Шаг 2. chat_id:** напишите своему новому боту `/start` (иначе он не
сможет писать вам первым), затем откройте в браузере
`https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates` — в ответе найдите
`"chat":{"id":123456789,...}` — это ваш **chat_id**.

**Шаг 3. Worker:** [dash.cloudflare.com](https://dash.cloudflare.com) →
Workers & Pages → Create → Worker (имя любое) → Deploy → Edit code →
вставьте целиком [worker/form-worker.js](worker/form-worker.js) → Deploy.

**Шаг 4. Секреты:** в воркере Settings → Variables and Secrets →
добавьте два секрета (тип **Secret**, не Text):
- `TG_BOT_TOKEN` — токен из шага 1
- `TG_CHAT_ID` — id из шага 2

**Шаг 5.** Скопируйте URL воркера (`https://<имя>.<аккаунт>.workers.dev`)
в `site-config.js → formEndpoint`, закоммитьте и запушьте.

Защита от спама: скрытое honeypot-поле + rate-limit 5 заявок / 10 минут
с IP (best-effort, память воркера эфемерна). Пока `formEndpoint` пустой,
форма работает в честном демо-режиме.

### 3. Юридические страницы — показать юристу

`privacy.html` и `consent.html` — типовые тексты под 152-ФЗ, написанные
под фактическое поведение сайта (форма собирает только контакт и описание
задачи; передача через Cloudflare Workers с доставкой в Telegram — это
трансграничная передача; без cookies и аналитики). `/en/privacy.html` —
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
| `worker/form-worker.js` | Код Cloudflare Worker для формы (деплоится в Cloudflare, не на Pages) |
| `vendor/`, `fonts/` | React 18.3.1 UMD и шрифты локально — сайт без внешних запросов |
| `ios-frame.jsx` → `ios-frame.js` | Исходник и прекомпилированная iOS-рамка для демо |

## Локальный запуск

```bash
python3 -m http.server 8788
# → http://localhost:8788 и http://localhost:8788/en/
```

Через `file://` не работает — рантайму нужен HTTP.

## Деплой

GitHub Pages, автоматически при пуше в `main` (`.github/workflows/deploy.yml`):

```bash
git push
```

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
