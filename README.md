# Re:dnd — сайт-портфолио

Двуязычный (RU + `/en/`) статический сайт на **https://rednd.ru**: Telegram-боты, мини-аппы, кейсы
с живыми демо. Дизайн — Claude Design (формат `.dc.html` + рантайм
`support.js`), инженерия и деплой — Claude Code.

## ⚡ Что вписать после клона

### 1. Контакты, цены, реквизиты — [site-config.js](site-config.js)

```js
formEndpoint: 'https://rednd-form.vercel.app/api/form',  // Vercel (см. ниже)
telegram: '@re_dnd',
email: 'politushkin@gmail.com',
requisites / requisitesFull,      // ← отчество и ОГРНИП вместо плейсхолдеров
prices / pricesEn,                // ← стартовые цены («от»)
testimonials, aboutPhoto, aboutLines / aboutLinesEn
```

### 2. Форма → Telegram (Vercel)

Заявки с обеих форм (RU и EN) приходят сообщением в Telegram с префиксом
`[RU]`/`[EN]`. Бэкенд — [api/form.js](api/form.js) на Vercel.

> Почему не VPS: IP `form.rednd.ru` совпадает с IP VPN-сервера, поэтому
> у клиентов, сидящих под этим VPN, запросы к форме таймаутились
> (`net::ERR_TIMED_OUT`). Vercel-домен доступен и из-под VPN, и без него.

**Включение (один раз):**
1. [vercel.com](https://vercel.com) → войти через GitHub → Add New… →
   Project → Import `kremlebot-tg/freelance-portfolio`
2. В поле **Project Name** вписать `rednd-form` (тогда URL совпадёт с уже
   прописанным в site-config.js), Framework — Other, ничего больше не
   менять → Deploy
3. Project → Settings → Environment Variables → добавить две переменные
   (тип **Sensitive**): `TG_BOT_TOKEN` и `TG_CHAT_ID` — те же значения,
   что лежат в `/etc/rednd-form.env` на VPS
4. Deployments → у последнего деплоя ⋯ → **Redeploy** (чтобы env подтянулись)
5. Проверить: `https://rednd-form.vercel.app/api/form` должен отвечать
   405 на GET (это норма — он принимает только POST). Если Vercel выдал
   другой домен — поправить `formEndpoint` в site-config.js и запушить.

Свой домен формы в будущем: добавить его в env `ALLOWED_ORIGINS`
(через запятую), код менять не нужно.

Защита от спама: honeypot + rate-limit 5 заявок / 10 минут с IP
(per-instance, best-effort). Пока проект на Vercel не создан или секреты
не вложены, форма показывает «не получилось отправить».

### 2а. Старый эндпоинт на VPS — DEPRECATED

`server/` и сервис `rednd-form` + vhost `form.rednd.ru` на VPS оставлены
работающими, но фронт их больше не использует. Можно погасить в любой
момент: `systemctl disable --now rednd-form` и убрать симлинк
`/etc/nginx/sites-enabled/form.rednd.ru.conf` (+ `nginx -t && systemctl
reload nginx`). VPN-стека это не касается.

### 3. Юридические страницы — показать юристу

`privacy.html` и `consent.html` — типовые тексты под 152-ФЗ, написанные
под фактическое поведение сайта (форма собирает только контакт и описание
задачи; передача через Vercel с доставкой в Telegram — трансграничная
передача; без cookies и аналитики). `/en/privacy.html` —
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
| `api/form.js` | Бэкенд формы (Vercel serverless) |
| `server/` | DEPRECATED: старый бэкенд формы на VPS (ещё работает, фронтом не используется) |
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
