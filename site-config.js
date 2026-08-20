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
  // обновлена под использование Метрики.
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

  // --- Подтверждённые отзывы (главная страница) ---
  // Секция скрыта, пока массив пуст. Добавлять только с разрешением автора
  // отзыва и без редактирования смысла. Формат:
  // { text: 'Текст отзыва…', name: 'Имя Фамилия', role: 'Должность, компания' }
  testimonials: [],

  // --- «О команде» / Team ---
  aboutPhoto: '',    // ← путь к фотографии команды, если появится (файл в корень);
                     //    пока пусто — показывается кружок с инициалами
  aboutLines: [],    // ← 1–2 подтверждённые строки о команде на русской странице
  aboutLinesEn: [],  // ← то же для английской (иначе скрыто)
};

// ============================================================
// Яндекс Метрика подключается только после явного выбора посетителя.
// Решение хранится локально в браузере и может быть изменено на странице
// политики конфиденциальности. До согласия сторонний скрипт не запрашивается.
// ============================================================
(function () {
  var cfg = window.SITE_CONFIG || {};
  var id = String(cfg.metrikaId || '').trim();
  var storageKey = 'rednd_analytics_consent';
  var isEnglish = location.pathname.indexOf('/en/') !== -1;
  var loaded = false;
  var controlsBound = false;
  var api = window.REDND_ANALYTICS = {
    reachGoal: function () { return false; }
  };

  if (!id) return;

  function readChoice() {
    try { return localStorage.getItem(storageKey) || ''; } catch (e) { return ''; }
  }

  function saveChoice(value) {
    try { localStorage.setItem(storageKey, value); } catch (e) {}
  }

  function loadMetrika() {
    if (loaded) return;
    loaded = true;
    (function (m, e, t, r, i, k, a) {
      m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
      m[i].l = 1 * new Date();
      for (var j = 0; j < e.scripts.length; j++) { if (e.scripts[j].src === r) { return; } }
      k = e.createElement(t); a = e.getElementsByTagName(t)[0];
      k.async = 1; k.src = r; k.dataset.redndAnalytics = 'true';
      a.parentNode.insertBefore(k, a);
    })(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js', 'ym');
    window.ym(id, 'init', {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: !!cfg.metrikaWebvisor
    });
  }

  function stopMetrika() {
    if (window.ym && loaded) {
      try { window.ym(id, 'destruct'); } catch (e) {}
    }
    loaded = false;
    var script = document.querySelector('script[data-rednd-analytics="true"]');
    if (script) script.remove();
  }

  // Единая точка отправки целей. Она намеренно ничего не буферизует:
  // действия до согласия не должны попадать в аналитику задним числом.
  // Параметры ниже описывают только экран и элемент интерфейса — значения
  // полей формы и другие пользовательские данные сюда не передаются.
  function reachGoal(target, params) {
    if (readChoice() !== 'accepted' || !loaded || typeof window.ym !== 'function') return false;
    if (!/^[A-Za-z0-9_-]+$/.test(String(target || ''))) return false;
    try {
      window.ym(id, 'reachGoal', target, params || {});
      return true;
    } catch (e) {
      return false;
    }
  }

  api.reachGoal = reachGoal;

  function currentPage() {
    var path = location.pathname.replace(/\/+$/, '');
    return path.split('/').pop() || 'index.html';
  }

  function placementOf(element) {
    var explicit = element.closest('[data-analytics-placement]');
    if (explicit) {
      var placement = String(explicit.getAttribute('data-analytics-placement') || '').trim();
      if (/^[A-Za-z0-9_-]+$/.test(placement)) return placement;
    }
    if (element.closest('header')) return 'header';
    if (element.closest('footer')) return 'footer';
    if (element.closest('.case-cta-link,dc-import[name="CaseCTA"]')) return 'case_cta';
    return 'main';
  }

  function withContext(extra) {
    var params = {
      language: isEnglish ? 'en' : 'ru',
      page: currentPage()
    };
    for (var key in (extra || {})) {
      if (Object.prototype.hasOwnProperty.call(extra, key)) params[key] = extra[key];
    }
    return params;
  }

  function bindFunnelTracking() {
    document.addEventListener('click', function (event) {
      var anchor = event.target && event.target.closest ? event.target.closest('a[href]') : null;
      if (!anchor) return;
      var rawHref = (anchor.getAttribute('href') || '').trim();
      if (!rawHref || rawHref.charAt(0) === '#') return;

      if (/^mailto:/i.test(rawHref)) {
        reachGoal('contact_channel', withContext({ channel: 'email', placement: placementOf(anchor) }));
        return;
      }

      var url;
      try { url = new URL(rawHref, location.href); } catch (e) { return; }
      if (/^(?:www\.)?(?:t\.me|telegram\.me)$/i.test(url.hostname)) {
        reachGoal('contact_channel', withContext({ channel: 'telegram', placement: placementOf(anchor) }));
        return;
      }
      if (url.origin !== location.origin) return;

      var destination = url.pathname.split('/').pop() || 'index.html';
      var caseMatch = destination.match(/^case-([a-z0-9-]+)\.html$/i);
      if (caseMatch) {
        reachGoal('case_open', withContext({ case_id: caseMatch[1].toLowerCase(), placement: placementOf(anchor) }));
      } else if (destination === 'contact.html') {
        reachGoal('contact_open', withContext({ placement: placementOf(anchor) }));
      } else if (destination === 'partner-apply.html') {
        reachGoal('partner_open', withContext({ placement: placementOf(anchor) }));
      }
    });

    document.addEventListener('input', function (event) {
      var form = event.target && event.target.closest
        ? event.target.closest('form[data-conversion-form]')
        : null;
      if (!form || form.getAttribute('data-analytics-started') === 'true') return;
      form.setAttribute('data-analytics-started', 'true');
      reachGoal('form_start', withContext({
        form_kind: form.getAttribute('data-conversion-form') || 'contact'
      }));
    });
  }

  function updateControls() {
    var accepted = readChoice() === 'accepted';
    var controls = document.querySelectorAll('[data-analytics-consent-control]');
    for (var i = 0; i < controls.length; i++) {
      controls[i].textContent = accepted
        ? (isEnglish ? 'Disable analytics' : 'Отключить аналитику')
        : (isEnglish ? 'Allow analytics' : 'Разрешить аналитику');
      controls[i].setAttribute('aria-pressed', accepted ? 'true' : 'false');
    }
  }

  function closeBanner() {
    var banner = document.getElementById('rd-cookie-consent');
    if (banner) banner.remove();
  }

  function accept() {
    saveChoice('accepted');
    closeBanner();
    loadMetrika();
    updateControls();
  }

  function decline() {
    saveChoice('declined');
    closeBanner();
    stopMetrika();
    updateControls();
  }

  function createBanner() {
    if (readChoice() || document.getElementById('rd-cookie-consent')) return;
    var banner = document.createElement('aside');
    banner.id = 'rd-cookie-consent';
    banner.className = 'rd-cookie';
    banner.setAttribute('aria-label', isEnglish ? 'Analytics settings' : 'Настройки аналитики');

    var copy = document.createElement('p');
    copy.appendChild(document.createTextNode(isEnglish
      ? 'May we use Yandex Metrica to understand which pages are useful? It stays off until you allow it. '
      : 'Можно включить Яндекс Метрику, чтобы понимать, какие страницы полезны? До вашего согласия она выключена. '));
    var privacy = document.createElement('a');
    privacy.href = 'privacy.html';
    privacy.textContent = isEnglish ? 'Privacy policy' : 'Политика конфиденциальности';
    copy.appendChild(privacy);

    var actions = document.createElement('div');
    actions.className = 'rd-cookie__actions';
    var reject = document.createElement('button');
    reject.type = 'button';
    reject.className = 'rd-cookie__button';
    reject.textContent = isEnglish ? 'No, thanks' : 'Не включать';
    reject.addEventListener('click', decline);
    var approve = document.createElement('button');
    approve.type = 'button';
    approve.className = 'rd-cookie__button rd-cookie__button--primary';
    approve.textContent = isEnglish ? 'Allow analytics' : 'Разрешить';
    approve.addEventListener('click', accept);
    actions.appendChild(reject);
    actions.appendChild(approve);
    banner.appendChild(copy);
    banner.appendChild(actions);
    document.body.appendChild(banner);
  }

  function bindControls() {
    if (!controlsBound) {
      controlsBound = true;
      document.addEventListener('click', function (event) {
        var target = event.target && event.target.closest
          ? event.target.closest('[data-analytics-consent-control]')
          : null;
        if (!target) return;
        if (readChoice() === 'accepted') decline(); else accept();
      });
    }
    updateControls();
  }

  function bootAnalyticsChoice() {
    bindControls();
    bindFunnelTracking();
    var choice = readChoice();
    if (choice === 'accepted') loadMetrika();
    else if (!choice) createBanner();
    // DC-компоненты появляются после DOMContentLoaded, поэтому повторно
    // подхватываем кнопку управления на странице политики.
    setTimeout(bindControls, 700);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootAnalyticsChoice);
  else bootAnalyticsChoice();
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

  /* Не ставим {{ photoSrc }} прямо в src: браузер успевал запросить
     буквальный mustache-URL до запуска DC-рантайма. */
  function hydrateDeferredImages(root) {
    var images = (root || document).querySelectorAll('img[data-photo-src]');
    for (var i = 0; i < images.length; i++) {
      var src = (images[i].getAttribute('data-photo-src') || '').trim();
      if (src && src.indexOf('{{') === -1 && images[i].getAttribute('src') !== src) images[i].setAttribute('src', src);
    }
  }

  function enforceRequiredFields(root) {
    var fields = (root || document).querySelectorAll('[data-form-task],[data-form-about],[data-form-contact]');
    for (var i = 0; i < fields.length; i++) {
      fields[i].required = true;
      fields[i].setAttribute('required', '');
      fields[i].setAttribute('aria-required', 'true');
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
    var items = scope.querySelectorAll('main h2,.rd-card,main > article,.case-process,main .flow');
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

  function observeMotionScenes(root) {
    if (!revealObserver || reduceMotion) return;
    var scope = root || document;
    var scenes = scope.querySelectorAll('.wk-scene,.m-app,.case-process,main .flow');
    for (var i = 0; i < scenes.length; i++) {
      if (scenes[i].classList.contains('rd-motion-observed')) continue;
      scenes[i].classList.add('rd-motion-observed');
      revealObserver.observe(scenes[i]);
    }
  }

  function enhance(root) {
    if (!document.body) return;
    var main = document.querySelector('main');
    if (main && !main.id) main.id = 'main-content';
    hydrateDeferredImages(root);
    enforceRequiredFields(root);
    markDisplayType(root);
    markCards(root);
    markChrome(root);
    markLayouts(root);
    observeReveals(root);
    observeMotionScenes(root);
  }

  function updateChrome() {
    var header = document.querySelector('header');
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 10);
  }

  function bootPolish() {
    if (started || !document.body) return;
    started = true;
    try { reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}

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
