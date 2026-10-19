'use strict';
// Local Chromium QA. Uses an existing Playwright installation and never submits forms.
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require(process.env.REDND_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'docs/audits/telegram-polish-2026-10-19');
const base = process.env.REDND_QA_BASE || 'http://127.0.0.1:8788/';
const cases = ['scout', 'chainya', 'krem', 'subscriptions', 'crm', 'vetpulse', 'autopricer', 'mutual', 'faith'];
const modes = [
  { theme: 'light', width: 390, pages: ['index.html', 'projects.html', 'services.html', 'about.html', 'contact.html', 'en/index.html', 'en/projects.html', ...cases.map(name => `case-${name}.html`)] },
  { theme: 'dark', width: 1280, pages: ['index.html', 'projects.html', 'services.html', 'about.html', 'contact.html', 'en/index.html', 'en/projects.html', ...cases.map(name => `case-${name}.html`)] },
  { theme: 'light', width: 320, pages: ['index.html', 'projects.html', 'en/projects.html'] },
  { theme: 'dark', width: 390, pages: ['index.html', 'projects.html', 'en/projects.html'] },
  { theme: 'light', width: 768, pages: ['projects.html'] }
];
async function main() {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.REDND_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true });
  const checks = [];
  const errors = [];
  try {
    for (const mode of modes) {
      const context = await browser.newContext({ viewport: { width: mode.width, height: 900 }, reducedMotion: 'reduce' });
      await context.addInitScript(theme => {
        if (!localStorage.getItem('theme')) localStorage.setItem('theme', theme);
      }, mode.theme);
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
      for (const target of mode.pages) {
        await page.goto(new URL(target, base).href, { waitUntil: 'networkidle' });
        await page.locator('header .hdr-logo-mark').waitFor();
        await page.evaluate(() => document.fonts.ready);
        if (target.endsWith('projects.html')) {
          for (let y = 0; y < await page.evaluate(() => document.body.scrollHeight); y += 650) {
            await page.evaluate(value => scrollTo(0, value), y);
            await page.waitForTimeout(50);
          }
          await page.waitForFunction(() => [...document.querySelectorAll('.rd-project-preview__image')].every(img => !img.hasAttribute('data-preview-src') && img.complete && img.naturalWidth > 1));
        }
        const check = await page.evaluate(() => ({
          theme: document.documentElement.getAttribute('data-theme'),
          width: innerWidth,
          documentWidth: document.documentElement.scrollWidth,
          mainPadding: getComputedStyle(document.querySelector('main')).paddingLeft,
          logo: { src: document.querySelector('.hdr-logo-mark').getAttribute('src'), width: document.querySelector('.hdr-logo-mark').naturalWidth },
          previews: [...document.querySelectorAll('.rd-project-preview__image')].map(img => ({ fit: getComputedStyle(img).objectFit, width: img.naturalWidth, caption: getComputedStyle(img.parentElement, '::after').fontSize, wrap: getComputedStyle(img.parentElement, '::after').whiteSpace })),
          type: [...document.querySelectorAll('.rd-cyr-display')].slice(0, 4).map(el => ({ text: el.textContent.trim().slice(0, 55), weight: getComputedStyle(el).fontWeight, family: getComputedStyle(el).fontFamily }))
        }));
        checks.push({ target, theme: mode.theme, width: mode.width, check });
        if (check.documentWidth > mode.width || check.theme !== mode.theme || check.logo.width !== 512) errors.push(JSON.stringify({ target, mode, check }));
        if (check.previews.some(item => item.fit !== 'contain' || item.width <= 1 || item.caption !== '12.5px' || item.wrap !== 'normal')) errors.push(`Preview contract failed: ${target} ${mode.width}`);
        if (['index.html', 'projects.html'].includes(target) && mode.width !== 320) {
          await page.evaluate(() => scrollTo(0, 0));
          await page.screenshot({ path: path.join(output, `${target.replace('.html', '')}-${mode.theme}-${mode.width}.jpg`), type: 'jpeg', quality: 80 });
        }
      }
      // The mobile menu remains keyboard-closeable and retains the selected theme.
      if (mode.width === 390 && mode.theme === 'light') {
        await page.goto(new URL('index.html', base).href, { waitUntil: 'networkidle' });
        await page.getByRole('button', { name: 'Открыть меню', exact: true }).click();
        await page.getByRole('button', { name: 'Включить тёмную тему', exact: true }).click();
        await page.keyboard.press('Escape');
        if (await page.locator('header').getAttribute('data-open') !== 'false') errors.push('Escape did not close mobile menu');
        await page.locator('main a[data-hero-action="projects"]').click();
        await page.locator('.rd-project-preview__image').first().waitFor();
        if (await page.locator('html').getAttribute('data-theme') !== 'dark') errors.push('Theme changed during navigation');
      }
      await context.close();
    }
    const motionContext = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'no-preference' });
    const motionPage = await motionContext.newPage();
    await motionPage.goto(new URL('projects.html', base).href, { waitUntil: 'networkidle' });
    const card = motionPage.locator('.rd-card').first();
    await card.scrollIntoViewIfNeeded();
    await motionPage.waitForTimeout(650);
    await card.hover();
    await motionPage.waitForTimeout(300);
    const motion = await card.evaluate(el => ({ opacity: getComputedStyle(el).opacity, transform: getComputedStyle(el).transform }));
    if (motion.opacity !== '1' || motion.transform !== 'none') errors.push(`Motion contract failed: ${JSON.stringify(motion)}`);
    await motionContext.close();
    const report = { checkedAt: new Date().toISOString(), base, browser: await browser.version(), scenarios: checks.length, motion, errors, checks };
    await fs.writeFile(path.join(output, 'result.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ scenarios: checks.length, errors, output }));
    if (errors.length) process.exitCode = 1;
  } finally { await browser.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
