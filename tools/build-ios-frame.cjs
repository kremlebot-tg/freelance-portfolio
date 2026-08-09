const fs = require('node:fs');
const path = require('node:path');
const Babel = require('@babel/standalone');

const root = path.resolve(__dirname, '..');
const sourcePath = path.join(root, 'ios-frame.jsx');
const outputPath = path.join(root, 'ios-frame.js');
const banner = [
  '// GENERATED из ios-frame.jsx (Babel 7.29.0, presets: react+typescript).',
  '// Не редактировать руками — правьте ios-frame.jsx и пересоберите: см. README.',
].join('\n');
const transformed = Babel.transform(fs.readFileSync(sourcePath, 'utf8'), {
  filename: 'ios-frame.jsx',
  presets: ['react', 'typescript'],
}).code;
const compiled = `${banner}\n${transformed}\n`;

if (process.argv.includes('--check')) {
  const current = fs.readFileSync(outputPath, 'utf8');
  if (current !== compiled) {
    console.error('ios-frame.js is stale; run npm run build:ios-frame');
    process.exit(1);
  }
  console.log('ios-frame.js matches ios-frame.jsx');
} else {
  fs.writeFileSync(outputPath, compiled);
  console.log('Built ios-frame.js');
}
