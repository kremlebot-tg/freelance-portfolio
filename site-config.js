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

  // --- Прямые контакты (страницы «Связаться» / Contact) ---
  telegram: '@re_dnd',
  email: 'politushkin@gmail.com',

  // --- Цены услуг ---
  // Только стартовые «от», точная цена обсуждается — так и подписано на сайте.
  prices: {
    leads: 'от 5 000 ₽',
    payments: 'от 8 000 ₽',
    ai: 'от 7 000 ₽',
    miniapps: 'от 15 000 ₽',
  },
  pricesEn: {
    leads: 'from $500',
    payments: 'from $900',
    ai: 'from $800',
    miniapps: 'from $1,500',
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
    "CRM": { ru: "Система для учёта контактов и отношений с клиентами.", en: "System for tracking contacts and customer relationships." }
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
