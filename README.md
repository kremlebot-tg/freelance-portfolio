# Сайт-портфолио — Даниил Яценко

Многостраничный статический сайт: Telegram-боты, мини-аппы, кейсы с живыми
демо. Дизайн — Claude Design (формат `.dc.html` + рантайм `support.js`),
инженерия и деплой — Claude Code.

## ⚡ Что вписать после клона (2 места)

### 1. Контакты и отправка формы — [site-config.js](site-config.js)

Единственный файл, который нужно править:

```js
window.SITE_CONFIG = {
  formEndpoint: '',            // ← endpoint Formspree (см. ниже)
  telegram: '@ваш_ник',        // ← ваш ник в Telegram, с @
  email: 'you@example.com',    // ← ваш email
};
```

**Как подключить отправку формы (Formspree, бесплатно до 50 заявок/мес):**
1. Зарегистрируйтесь на <https://formspree.io>
2. New form → в настройках формы укажите email-получатель
   (адрес хранится у Formspree, в коде сайта его нет)
3. Скопируйте endpoint вида `https://formspree.io/f/xxxxxxxx`
   в `formEndpoint`

Пока `formEndpoint` пустой, форма работает в демо-режиме (показывает
экран успеха, но никуда не шлёт) и подписана как прототип. Секретов в
клиентском коде нет: ID формы Formspree — публичный по дизайну сервиса,
email-получатель задаётся в кабинете Formspree.

### 2. Реквизиты ИП, цены, отзывы, фото — тоже в [site-config.js](site-config.js)

- `requisites` — ИНН/ОГРНИП для подвала (сейчас плейсхолдер с нулями)
- `prices` — стартовые цены услуг («от X ₽»)
- `testimonials` — отзывы; секция на главной появится сама, когда массив не пуст
- `aboutPhoto` / `aboutLines` — фото и личные строки на «Обо мне»

### 3. Юридические страницы — показать юристу

`privacy.html` (политика конфиденциальности) и `consent.html` (согласие на
обработку ПДн) — **типовые тексты под 152-ФЗ**, написанные под фактическое
поведение сайта (форма собирает только контакт и описание задачи, передача
через Formspree, без cookies и аналитики). ⚠️ Перед серьёзным использованием
покажите финальный текст юристу — особенно раздел о трансграничной передаче
(Formspree, США) и сроках хранения.

Имя «Даниил Яценко» уже вшито в страницы.

## Структура

| Файл | Что это |
|---|---|
| `index.html`, `projects.html`, `services.html`, `about.html`, `contact.html`, `case-*.html` | Страницы сайта (шаблоны Claude Design) |
| `Header.dc.html`, `Footer.dc.html` | Общие шапка/подвал — подгружаются рантаймом по имени, **не переименовывать** |
| `support.js` | Рантайм Claude Design (генерированный; изменены только пути к React → `vendor/`) |
| `site-config.js` | ✏️ Контакты и endpoint формы |
| `vendor/` | React 18.3.1 UMD, локально (байт-идентичен unpkg, SRI совпадает) |
| `fonts/` | Локальная копия Google Fonts (Sora, Inter, JetBrains Mono) |
| `ios-frame.jsx` → `ios-frame.js` | Исходник и прекомпилированная iOS-рамка для демо MUTUAL / Faith |

Сайт полностью автономный: ни одного внешнего запроса (React, шрифты,
Babel — всё локально или не требуется).

## Локальный запуск

```bash
python3 -m http.server 8788
# → http://localhost:8788
```

Открывать файлы через `file://` нельзя — рантайму нужен HTTP (fetch
шапки/подвала).

## Деплой

Хостинг — GitHub Pages, деплой автоматический при пуше в `main`
(workflow `.github/workflows/deploy.yml`). Передеплой одной командой:

```bash
git push
```

## Если правите ios-frame.jsx

Пересоберите `ios-frame.js` (нужен Node):

```bash
npm i @babel/standalone@7.29.0
node -e "const B=require('@babel/standalone'),fs=require('fs');fs.writeFileSync('ios-frame.js',B.transform(fs.readFileSync('ios-frame.jsx','utf8'),{filename:'ios-frame.jsx',presets:['react','typescript']}).code)"
```

## Демо в кейсах

Все 5 демо (граф CRM + извлечение фактов, автопрайсер, эмулятор
подписочного бота, прототип MUTUAL, урок Faith App) — клиентские, на
моковых данных, бэкенд не нужен.

**TODO (хуки под будущие бэкенды):**
- `case-subscriptions.html` — «оплата» это мок-экран ЮKassa; для живой
  оплаты нужен бэкенд с вебхуками ЮKassa (обработчик `onPay` в DCLogic —
  точка подключения)
- `case-crm.html` — «извлечение фактов» заскриптовано на 3 примерах;
  живой вариант — вызов LLM API через серверный прокси (обработчик
  кнопки «Извлечь факты»)

## Известные особенности

- В консоли на `case-autopricer.html` есть варнинги
  `[dc-runtime] {{ r.* }} never resolved` — это поведение рантайма
  Claude Design, есть и в оригинальном экспорте, на рендер не влияет.
- Заголовки (Sora) для кириллицы рендерятся системным fallback-шрифтом —
  у Sora нет кириллицы; так было и в оригинале с Google Fonts.
