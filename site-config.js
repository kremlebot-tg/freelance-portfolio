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
  metrikaId: '110708647',
  // Вебвизор — запись сессий (движения мыши, ввод). Выключен: формы с
  // персональными данными не записываются. Включать осознанно.
  metrikaWebvisor: false,

  // --- Прямые контакты (страницы «Связаться» / Contact) ---
  telegram: '@re_dnd',
  email: 'politushkin@gmail.com',

  // --- Цены услуг (5 направлений) ---
  // Стартовые «от»; мобильные приложения считаем индивидуально.
  prices: {
    telegram: 'от 7 000 ₽',
    ai: 'от 20 000 ₽',
    automation: 'от 15 000 ₽',
    web: 'от 40 000 ₽',
    mobile: 'по задаче',
  },
  pricesEn: {
    telegram: 'from $49',
    ai: 'from $99',
    automation: 'from $89',
    web: 'custom quote',
    mobile: 'custom quote',
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

// ============================================================
// Общая полировка интерфейса: единые карточки и CTA, активная шапка,
// прогресс чтения и спокойные появления при скролле. Всё progressive
// enhancement: при ошибке JS исходная разметка остаётся полностью рабочей.
// ============================================================
(function () {
  var started = false;
  var revealObserver = null;
  var mutationObserver = null;
  var mutationQueued = false;
  var reduceMotion = false;
  var isHome = /(?:^|\/)index\.html$/.test(location.pathname) || /\/$/.test(location.pathname);

  function hasCyrillic(text) { return /[А-Яа-яЁё]/.test(text || ''); }

  function markDisplayType(root) {
    var list = (root || document).querySelectorAll('[style]');
    for (var i = 0; i < list.length; i++) {
      var el = list[i];
      if (el.classList.contains('rd-cyr-display')) continue;
      if (isHeroElement(el)) continue;
      if (!hasCyrillic(el.textContent)) continue;
      if ((el.style.fontFamily || '').indexOf('Sora') !== -1) el.classList.add('rd-cyr-display');
    }
  }

  function isHeroElement(el) {
    if (!isHome) return false;
    var first = document.querySelector('main > section');
    return !!(first && first.contains(el));
  }

  function markCards(root) {
    var scope = root || document;
    var fixed = scope.querySelectorAll('.ex,.acc,.ch-stat,.ch-copy');
    var i;
    for (i = 0; i < fixed.length; i++) fixed[i].classList.add('rd-card');

    var nodes = scope.querySelectorAll('main a[style],main article[style],main div[style]');
    for (i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.classList.contains('rd-card') || isHeroElement(el)) continue;
      if (el.closest('[data-theme-lock],.ph-fit,.ch-browser')) continue;
      if (el.parentElement && el.parentElement.closest('.rd-card')) continue;
      var raw = el.getAttribute('style') || '';
      var background = el.style.background || el.style.backgroundColor || '';
      var border = el.style.border || '';
      var surface = background.indexOf('var(--surface)') !== -1 || raw.indexOf('background:var(--surface)') !== -1;
      var bordered = border.indexOf('solid') !== -1 || raw.indexOf('border:1px solid') !== -1;
      if (!surface || !bordered || el.children.length < 2) continue;
      el.classList.add('rd-card');
      if (border.indexOf('var(--accent-cta)') !== -1 || raw.indexOf('var(--accent-cta)') !== -1) el.classList.add('rd-featured');
    }
  }

  function markChrome(root) {
    var scope = root || document;
    var headings = scope.querySelectorAll('main h2');
    for (var i = 0; i < headings.length; i++) {
      var h = headings[i];
      if (h.closest('.rd-card,[data-theme-lock],.ph-fit')) {
        h.classList.remove('rd-section-title');
      } else if (!h.classList.contains('rd-section-title')) {
        h.classList.add('rd-section-title');
      }
    }
    var ctas = scope.querySelectorAll('.hdr-cta,a[href$="contact.html"],button[type="submit"],button[aria-busy]');
    for (i = 0; i < ctas.length; i++) {
      var el = ctas[i];
      if (isHeroElement(el) && !el.classList.contains('hdr-cta')) continue;
      var bg = el.style.background || '';
      if (el.classList.contains('hdr-cta') || bg.indexOf('accent') !== -1 || el.tagName === 'BUTTON') el.classList.add('rd-cta');
    }
  }

  function markLayouts(root) {
    var scope = root || document;
    var newest = scope.querySelectorAll('a[href$="case-chainya.html"]');
    var i;
    for (i = 0; i < newest.length; i++) {
      if (newest[i].classList.contains('rd-card')) newest[i].classList.add('rd-featured', 'rd-latest-case');
    }

    var parents = [];
    var cards = scope.querySelectorAll('main .rd-card');
    for (i = 0; i < cards.length; i++) {
      var parent = cards[i].parentElement;
      if (parent && parents.indexOf(parent) === -1) parents.push(parent);
    }
    for (i = 0; i < parents.length; i++) {
      var p = parents[i];
      var direct = Array.prototype.filter.call(p.children, function (n) { return n.classList && n.classList.contains('rd-card'); });
      if (direct.length === 5 && getComputedStyle(p).display === 'grid') p.classList.add('rd-five-grid');
      if (direct.length === 7 && getComputedStyle(p).display === 'grid') p.classList.add('rd-seven-grid');
    }
  }

  function observeReveals(root) {
    if (!revealObserver || reduceMotion) return;
    var scope = root || document;
    var items = scope.querySelectorAll('main h2,.rd-card,main > article');
    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      if (el.classList.contains('rd-reveal') || isHeroElement(el) || el.closest('[data-theme-lock],.ph-fit')) continue;
      if (el.tagName === 'H2' && el.closest('.rd-card')) continue;
      el.classList.add('rd-reveal');
      var siblings = el.parentElement ? Array.prototype.filter.call(el.parentElement.children, function (n) {
        return n.matches && (n.matches('.rd-card') || n.tagName === 'ARTICLE');
      }) : [];
      var idx = siblings.indexOf(el);
      if (idx > -1) el.style.setProperty('--rd-delay', String(Math.min(idx % 4, 3) * 65) + 'ms');
      revealObserver.observe(el);
    }
  }

  function enhance(root) {
    if (!document.body) return;
    markDisplayType(root);
    markCards(root);
    markChrome(root);
    markLayouts(root);
    observeReveals(root);
  }

  function updateChrome() {
    var header = document.querySelector('header');
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 10);
    var progress = document.querySelector('.rd-scroll-progress');
    if (progress) {
      var max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      progress.style.transform = 'scaleX(' + Math.min(1, Math.max(0, window.scrollY / max)) + ')';
    }
  }

  function bootPolish() {
    if (started || !document.body) return;
    started = true;
    try { reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

    var progress = document.createElement('div');
    progress.className = 'rd-scroll-progress';
    progress.setAttribute('aria-hidden', 'true');
    document.body.appendChild(progress);

    if (!reduceMotion && 'IntersectionObserver' in window) {
      document.documentElement.classList.add('rd-motion-ready');
      revealObserver = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          if (!entries[i].isIntersecting) continue;
          entries[i].target.classList.add('is-visible');
          revealObserver.unobserve(entries[i].target);
        }
      }, { rootMargin: '0px 0px -7% 0px', threshold: .08 });
    }

    enhance(document);
    updateChrome();
    window.addEventListener('scroll', updateChrome, { passive: true });
    window.addEventListener('resize', updateChrome, { passive: true });
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      var header = document.querySelector('header[data-open="true"]');
      var burger = header && header.querySelector('.hdr-burger');
      if (burger) burger.click();
    });

    mutationObserver = new MutationObserver(function (records) {
      if (mutationQueued) return;
      var useful = false;
      for (var i = 0; i < records.length; i++) {
        if (records[i].addedNodes && records[i].addedNodes.length) { useful = true; break; }
      }
      if (!useful) return;
      mutationQueued = true;
      requestAnimationFrame(function () {
        mutationQueued = false;
        enhance(document);
        updateChrome();
      });
    });
    mutationObserver.observe(document.body, { childList: true, subtree: true });
    setTimeout(function () { if (mutationObserver) mutationObserver.disconnect(); }, 8000);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootPolish); else bootPolish();
})();
