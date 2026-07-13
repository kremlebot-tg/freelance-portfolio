// ============================================================
// НАСТРОЙКИ САЙТА — единственный файл, который нужно править.
// ============================================================
window.SITE_CONFIG = {
  // --- Отправка формы заявки (Yandex Cloud, РФ → Telegram) ---
  // Бэкенд: API Gateway → Cloud Function в Yandex Cloud (ru-central1).
  // Заявка сначала пишется в Object Storage в РФ (152-ФЗ), потом уведомление
  // в Telegram. Токен бота и chat_id — в Lockbox, НЕ здесь. См. README.
  formEndpoint: 'https://d5d7olk60q94hjb111lj.kocrdvxt.apigw.yandexcloud.net/submit',
  // Если endpoint пустой — форма показывает демо-режим. Сейчас задан.

  // --- Веб-аналитика (Яндекс Метрика, данные в РФ) ---
  // Вставьте НОМЕР счётчика (только цифры, напр. 98765432). Создать счётчик:
  // https://metrika.yandex.ru → «Добавить счётчик». Пока пусто — Метрика НЕ
  // подключается (ни cookie, ни запросов). Политику конфиденциальности уже
  // обновил под использование Метрики.
  metrikaId: '',
  // Вебвизор — запись сессий (движения мыши, ввод). Выключен: формы с
  // персональными данными не записываются. Включать осознанно.
  metrikaWebvisor: false,

  // --- Прямые контакты (страницы «Связаться» / Contact) ---
  telegram: '@re_dnd',
  email: 'politushkin@gmail.com',

  // --- Цены услуг ---
  // Только стартовые «от», точная цена обсуждается — так и подписано на сайте.
  prices: {
    leads: 'от 4 900 ₽',
    payments: 'от 8 900 ₽',
    ai: 'от 9 900 ₽',
    miniapps: 'от 16 900 ₽',
  },
  pricesEn: {
    leads: 'from $49',
    payments: 'from $89',
    ai: 'from $99',
    miniapps: 'from $179',
  },

  // --- Реквизиты (подвал) ---
  requisites: 'ИНН 502991709786 · ОГРНИП 325774600194672',
  requisitesFull: 'ИП Яценко Даниил Александрович',
  requisitesEn: 'Sole proprietor · TIN 502991709786',  // для EN достаточно TIN, ОГРНИП не нужен

  // --- Отзывы (главная страница) ---
  // Секция скрыта, пока массив пуст. Формат:
  // { text: 'Текст отзыва…', name: 'Имя Фамилия', role: 'Должность, компания' }
  testimonials: [],

  // --- «Обо мне» / About ---
  aboutPhoto: '',    // ← путь к фото Даниила, напр. 'photo.jpg' (файл в корень);
                     //    пока пусто — показывается кружок с инициалами
  aboutLines: [],    // ← 1–2 личные строки на русской странице
  aboutLinesEn: [],  // ← то же для английской (иначе скрыто)
};

// ============================================================
// Яндекс Метрика — подключается ТОЛЬКО если задан metrikaId.
// Обезличенная аналитика, данные обрабатываются в РФ. Чтобы отключить —
// очистите metrikaId в SITE_CONFIG выше.
// ============================================================
(function () {
  var cfg = window.SITE_CONFIG || {};
  var id = String(cfg.metrikaId || '').trim();
  if (!id) return;
  (function (m, e, t, r, i, k, a) {
    m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
    m[i].l = 1 * new Date();
    for (var j = 0; j < e.scripts.length; j++) { if (e.scripts[j].src === r) { return; } }
    k = e.createElement(t); a = e.getElementsByTagName(t)[0];
    k.async = 1; k.src = r; a.parentNode.insertBefore(k, a);
  })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
  window.ym(id, 'init', {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: !!cfg.metrikaWebvisor
  });
})();

// ============================================================
// Тултипы на тег-чипы стека. Находит span'ы моноширинного стека
// (JetBrains Mono) с текстом-термином и вешает пояснение по наведению/
// фокусу/тапу. Ноль внешних запросов, работает на всех страницах.
// ============================================================
(function () {
  var TT = {
    "Python": { ru: "Язык программирования, на котором пишут ботов и логику.", en: "General-purpose programming language used to build bots and backends." },
    "pandas": { ru: "Библиотека Python для работы с таблицами и расчётами.", en: "Python library for crunching tables of numbers and data." },
    "Ozon Seller API": { ru: "Канал, по которому программа читает данные магазина на Ozon.", en: "Ozon's data channel a program uses to read shop data." },
    "API поставщика": { ru: "Способ автоматически получать данные из системы поставщика.", en: "A supplier's data channel that programs read stock and prices from." },
    "Flutter": { ru: "Набор инструментов Google для создания мобильных приложений.", en: "Google's toolkit for building mobile apps from one codebase." },
    "Dart": { ru: "Язык программирования, на котором работает Flutter.", en: "Programming language that Flutter apps are written in." },
    "iOS": { ru: "Операционная система айфонов и айпадов от Apple.", en: "Apple's operating system for iPhones and iPads." },
    "офлайн-first": { ru: "Приложение работает без интернета, данные хранятся на устройстве.", en: "App works without internet; data lives on the device." },
    "aiogram": { ru: "Библиотека Python для создания Telegram-ботов.", en: "Python library for building Telegram bots." },
    "FastAPI": { ru: "Инструмент Python для создания веб-сервисов и API.", en: "Python tool for building web services and APIs." },
    "SQLite": { ru: "Компактная база данных, хранящаяся в одном файле.", en: "Lightweight database stored as a single file." },
    "LLM": { ru: "ИИ-модель, понимающая и генерирующая текст, как ChatGPT.", en: "AI model that understands and writes text, like ChatGPT." },
    "Telegram Mini App": { ru: "Полноценное приложение, открывающееся прямо внутри Telegram.", en: "A full app that opens right inside Telegram." },
    "Mini App": { ru: "Полноценное приложение, открывающееся прямо внутри Telegram.", en: "A full app that opens right inside Telegram." },
    "Bot API": { ru: "Интерфейс Telegram, через который программы управляют ботами.", en: "Telegram's interface for programs to control bots." },
    "ЮКасса": { ru: "Российский сервис приёма онлайн-платежей картами.", en: "Russian service for accepting online card payments." },
    "VPS": { ru: "Арендованный сервер в интернете, где работает приложение.", en: "Rented internet server that keeps an app running." },
    "UX-прототип": { ru: "Кликабельный макет приложения, собранный до написания кода.", en: "Clickable mockup of an app before real code exists." },
    "продуктовый дизайн": { ru: "Проектирование того, как продукт работает и ощущается.", en: "Designing how a product works and feels for users." },
    "ИИ": { ru: "Искусственный интеллект, выполняющий задачи вместо человека.", en: "Artificial intelligence that performs tasks in a person's place." },
    "CRM": { ru: "Система для учёта контактов и отношений с клиентами.", en: "System for tracking contacts and customer relationships." },
    "Telegram Bot API": { ru: "Интерфейс Telegram, через который программы управляют ботами.", en: "Telegram's interface for programs to control bots." },
    "Telegram Mini Apps": { ru: "Полноценные приложения прямо внутри Telegram.", en: "Full apps that run right inside Telegram." },
    "YooKassa": { ru: "Российский сервис приёма онлайн-платежей картами.", en: "Russian service for accepting online card payments." },
    "LLM / ИИ": { ru: "ИИ-модель, понимающая и генерирующая текст, как ChatGPT.", en: "AI model that understands and writes text, like ChatGPT." },
    "LLM / AI": { ru: "ИИ-модель, понимающая и генерирующая текст, как ChatGPT.", en: "AI model that understands and writes text, like ChatGPT." },
    "SQLAlchemy": { ru: "Инструмент Python для работы с базой данных через объекты.", en: "Python toolkit for working with a database through objects." },
    "Vetmanager API": { ru: "Программный интерфейс ветеринарной учётной системы Vetmanager.", en: "The API of the Vetmanager veterinary practice system." },
    "мультиарендность": { ru: "Один сервис обслуживает много клиник, данные изолированы.", en: "One service serves many clinics with fully isolated data." },
    "multi-tenancy": { ru: "Один сервис обслуживает много клиник, данные изолированы.", en: "One service serves many clinics with fully isolated data." }
  };
  var lang = (location.pathname.indexOf('/en/') !== -1) ? 'en' : 'ru';
  function apply() {
    var s = document.getElementsByTagName('span'), i, el, t, d, ff;
    for (i = 0; i < s.length; i++) {
      el = s[i];
      if (el.getAttribute('data-tt')) continue;
      if (el.children.length) continue;
      t = (el.textContent || '').trim();
      d = TT[t];
      if (!d) continue;
      try { ff = getComputedStyle(el).fontFamily || ''; } catch (e) { ff = ''; }
      if (ff.indexOf('JetBrains') === -1) continue;
      el.setAttribute('data-tt', '1');
      el.className = (el.className ? el.className + ' ' : '') + 'tt';
      el.setAttribute('tabindex', '0');
      el.setAttribute('data-tip', d[lang] || d.ru);
      el.setAttribute('aria-label', t + ' — ' + (d[lang] || d.ru));
    }
  }
  function boot() { apply(); var n = 0, iv = setInterval(function () { apply(); if (++n > 16) clearInterval(iv); }, 250); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
