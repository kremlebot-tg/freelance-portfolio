'use strict';
// Capture existing portfolio mockups, never customer sessions or live services.
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require(process.env.REDND_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'assets/previews');
const base = new URL(process.env.REDND_PREVIEW_BASE || 'http://127.0.0.1:8788/');
if (!['127.0.0.1', 'localhost'].includes(base.hostname)) throw new Error('Only a local source is allowed');
const scenes = [
  { id: 'scout', selector: '.sc-window, .visual .window' },
  { id: 'subscriptions', selector: '.sub-state + div > div', maxHeight: 390, start: true },
  { id: 'crm', selector: '.crm-network' },
  { id: 'vetpulse', selector: 'div[style*="max-width: 460px"]', maxHeight: 390 },
  { id: 'autopricer', selector: '.pnl-wrap' },
  { id: 'mutual', selector: '.ph-fit__in', offset: 65, maxHeight: 430 },
  { id: 'faith', selector: '.ph-fit__in', offset: 65, maxHeight: 400 }
];
const selected = (process.env.REDND_PREVIEW_ONLY || '').split(',').filter(Boolean);
if (selected.some(id => !scenes.some(scene => scene.id === id))) throw new Error('Unknown preview scene');
async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.REDND_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
  const results = [];
  try {
    for (const locale of ['ru', 'en']) {
      const context = await browser.newContext({ viewport: { width: 1280, height: 1000 }, deviceScaleFactor: 1.5, reducedMotion: 'reduce' });
      await context.addInitScript(() => {
        localStorage.setItem('theme', 'dark');
        localStorage.setItem('rednd_analytics_consent', 'declined');
      });
      await context.route('**/*', route => {
        const request = route.request();
        const url = new URL(request.url());
        if (request.method() !== 'GET' || (url.origin !== base.origin && url.protocol !== 'data:')) return route.abort();
        return route.continue();
      });
      const page = await context.newPage();
      for (const scene of scenes) {
        if (selected.length && !selected.includes(scene.id)) continue;
        await page.goto(new URL(`${locale === 'en' ? 'en/' : ''}case-${scene.id}.html`, base).href, { waitUntil: 'networkidle' });
        await page.locator(scene.selector).waitFor();
        await page.evaluate(() => document.fonts.ready);
        if (scene.start) {
          await page.getByRole('button', { name: '/start', exact: true }).click();
          await page.getByRole('button', { name: /1.*(месяц|month)/i }).first().waitFor();
        }
        if (scene.id === 'vetpulse') {
          await page.locator(scene.selector).getByRole('button').first().click();
          await page.waitForFunction(selector => !!document.querySelector(selector)?.querySelector('[style*="border-left"]'), scene.selector);
        }
        if (scene.id === 'mutual') {
          await page.locator('.m-btn--acc').click();
          await page.locator('.m-btn--acc').click();
          await page.locator('.m-map').waitFor();
        }
        const target = page.locator(scene.selector).first();
        await target.scrollIntoViewIfNeeded();
        const box = await target.boundingBox();
        const offset = scene.offset || 0;
        const height = Math.min(box.height - offset, scene.maxHeight || box.height);
        const file = `${scene.id}${locale === 'en' ? '-en' : ''}.jpg`;
        await page.screenshot({ path: path.join(output, file), type: 'jpeg', quality: 83, clip: { x: box.x, y: box.y + offset, width: box.width, height } });
        const stat = await fs.stat(path.join(output, file));
        results.push({ file, bytes: stat.size, source: `${locale === 'en' ? 'en/' : ''}case-${scene.id}.html`, selector: scene.selector });
      }
      await context.close();
    }
  } finally { await browser.close(); }
  console.log(JSON.stringify({ files: results.length, bytes: results.reduce((n, r) => n + r.bytes, 0), results }));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
