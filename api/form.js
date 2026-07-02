/**
 * Vercel Serverless Function: форма заявки → сообщение в Telegram.
 * (Переезд с Cloudflare Workers: *.workers.dev нестабилен из РФ.)
 *
 * Включение (см. README, раздел «Форма → Telegram (Vercel)»):
 *   1. vercel.com → Add New… → Project → импортировать этот репозиторий → Deploy
 *   2. Project → Settings → Environment Variables → добавить:
 *        TG_BOT_TOKEN — токен бота от @BotFather   (тип Sensitive)
 *        TG_CHAT_ID   — ваш chat_id                 (тип Sensitive)
 *      и передеплоить (Deployments → ⋯ → Redeploy)
 *   3. URL функции https://<проект>.vercel.app/api/form вписать
 *      в site-config.js → formEndpoint
 *
 * Свой домен в будущем: добавьте его в env ALLOWED_ORIGINS
 * (через запятую), код менять не нужно.
 *
 * Токен НИКОГДА не попадает в код сайта или репозиторий — только в env Vercel.
 */

// Rate-limit: не больше N заявок с одного IP за окно.
// ОГРАНИЧЕНИЕ: память живёт в пределах одного инстанса serverless-функции —
// при масштабировании/холодном старте счётчик обнуляется. Это осознанный
// best-effort без внешних зависимостей; основная защита от ботов — honeypot.
const RATE = new Map();
const RATE_MAX = 5;          // заявок
const RATE_WINDOW = 600_000; // за 10 минут

const DEFAULT_ORIGINS = [
  'https://kremlebot-tg.github.io',
  'http://localhost:8788',
];

module.exports = async (req, res) => {
  const extra = (process.env.ALLOWED_ORIGINS || '')
    .split(',').map(s => s.trim()).filter(Boolean);
  const allowedOrigins = [...extra, ...DEFAULT_ORIGINS];
  const origin = req.headers.origin || '';
  res.setHeader('Access-Control-Allow-Origin',
    allowedOrigins.includes(origin) ? origin : allowedOrigins[0]);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Vary', 'Origin');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'method not allowed' });

  // rate-limit по IP (за прокси Vercel реальный IP — первый в x-forwarded-for)
  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  const now = Date.now();
  const rec = RATE.get(ip);
  if (rec && now - rec.ts < RATE_WINDOW) {
    if (rec.n >= RATE_MAX) return res.status(429).json({ error: 'too many requests' });
    rec.n++;
  } else {
    RATE.set(ip, { n: 1, ts: now });
  }

  // Vercel сам парсит JSON-тело при Content-Type: application/json
  let data = req.body;
  if (typeof data === 'string') { try { data = JSON.parse(data); } catch { data = null; } }
  if (!data || typeof data !== 'object') return res.status(400).json({ error: 'bad json' });

  // honeypot: скрытое поле «website» заполняют только боты.
  // Отвечаем «успехом», чтобы бот не понял, что отсеян.
  if (data.website) return res.status(200).json({ ok: true });

  const task = String(data.task || '').slice(0, 2000).trim();
  const type = String(data.type || '').slice(0, 100).trim();
  const budget = String(data.budget || '').slice(0, 100).trim();
  const contact = String(data.contact || '').slice(0, 200).trim();
  if (!task || !contact) return res.status(400).json({ error: 'task and contact are required' });

  const lang = data.lang === 'en' ? 'EN' : 'RU';
  const text =
    `[${lang}] Новая заявка с сайта\n\n` +
    `Задача: ${task}\n` +
    `Тип: ${type || '—'}\n` +
    `Бюджет: ${budget || '—'}\n` +
    `Контакт: ${contact}`;

  const tg = await fetch(`https://api.telegram.org/bot${process.env.TG_BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: process.env.TG_CHAT_ID, text }),
  });
  if (!tg.ok) return res.status(502).json({ error: 'telegram delivery failed' });

  return res.status(200).json({ ok: true });
};
