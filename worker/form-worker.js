/**
 * Cloudflare Worker: форма заявки → сообщение в Telegram.
 *
 * Деплой (см. README, раздел «Форма → Telegram»):
 *   1. dash.cloudflare.com → Workers & Pages → Create → Worker
 *   2. Вставить этот файл целиком, Deploy
 *   3. Settings → Variables and Secrets → добавить ДВА секрета (тип Secret):
 *        TG_BOT_TOKEN — токен бота от @BotFather
 *        TG_CHAT_ID   — ваш chat_id (куда слать заявки)
 *   4. URL воркера (https://<имя>.<аккаунт>.workers.dev) вписать
 *      в site-config.js → formEndpoint
 *
 * Токен НИКОГДА не попадает в код сайта или репозиторий — только в секреты.
 */

// Простейший rate-limit: не больше N заявок с одного IP за окно.
// Память воркера эфемерна (сбрасывается между «пробуждениями») —
// это осознанно «лучшее из бесплатного», основная защита — honeypot.
const RATE = new Map();
const RATE_MAX = 5;          // заявок
const RATE_WINDOW = 600_000; // за 10 минут

const ALLOWED_ORIGINS = [
  'https://kremlebot-tg.github.io',
  'http://localhost:8788',
];

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin',
  };
}

function json(body, status, cors) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...cors },
  });
}

export default {
  async fetch(request, env) {
    const cors = corsHeaders(request.headers.get('Origin') || '');
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (request.method !== 'POST') return json({ error: 'method not allowed' }, 405, cors);

    // rate-limit по IP
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const now = Date.now();
    const rec = RATE.get(ip);
    if (rec && now - rec.ts < RATE_WINDOW) {
      if (rec.n >= RATE_MAX) return json({ error: 'too many requests' }, 429, cors);
      rec.n++;
    } else {
      RATE.set(ip, { n: 1, ts: now });
    }

    const data = await request.json().catch(() => null);
    if (!data) return json({ error: 'bad json' }, 400, cors);

    // honeypot: скрытое поле «website» заполняют только боты.
    // Отвечаем «успехом», чтобы бот не понял, что отсеян.
    if (data.website) return json({ ok: true }, 200, cors);

    const task = String(data.task || '').slice(0, 2000).trim();
    const type = String(data.type || '').slice(0, 100).trim();
    const budget = String(data.budget || '').slice(0, 100).trim();
    const contact = String(data.contact || '').slice(0, 200).trim();
    if (!task || !contact) return json({ error: 'task and contact are required' }, 400, cors);

    const lang = data.lang === 'en' ? 'EN' : 'RU';
    const text =
      `[${lang}] Новая заявка с сайта\n\n` +
      `Задача: ${task}\n` +
      `Тип: ${type || '—'}\n` +
      `Бюджет: ${budget || '—'}\n` +
      `Контакт: ${contact}`;

    const tg = await fetch(`https://api.telegram.org/bot${env.TG_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: env.TG_CHAT_ID, text }),
    });
    if (!tg.ok) return json({ error: 'telegram delivery failed' }, 502, cors);

    return json({ ok: true }, 200, cors);
  },
};
