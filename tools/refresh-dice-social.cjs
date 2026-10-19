'use strict';
// Refresh only the mark area of committed social cards, retaining their actual content.
// Needs the existing sharp package. No network, new dependencies or product mutations.
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const sharp = require(process.env.REDND_SHARP_MODULE || 'sharp');

async function main() {
  const svg = await fs.readFile(path.join(root, 'favicon.svg'));
  const mark = await sharp(svg).resize(100, 100).png().toBuffer();
  const brandDirectory = path.join(root, 'assets/brand');
  await fs.mkdir(brandDirectory, { recursive: true });
  await fs.writeFile(path.join(brandDirectory, 'telegram-dice.png'), mark);
  const icon = await sharp(mark).resize(50, 50).png().toBuffer();
  const erase = Buffer.from('<svg width="66" height="66"><rect width="66" height="66" fill="#0d1721"/></svg>');
  for (const name of ['scout', 'autopricer', 'crm', 'faith', 'mutual', 'subscriptions']) {
    for (const language of ['', '-en']) {
      const target = path.join(root, `og-case-${name}${language}.png`);
      const original = await fs.readFile(target);
      const result = await sharp(original).composite([{ input: erase, top: 62, left: 64 }, { input: icon, top: 70, left: 72 }]).png().toBuffer();
      await fs.writeFile(target, result);
      console.log(path.relative(root, target));
    }
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
