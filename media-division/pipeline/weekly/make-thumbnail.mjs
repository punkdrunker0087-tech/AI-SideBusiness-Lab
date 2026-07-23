// 週次まとめ動画のサムネイル生成（1280x720 PNG）
//
//   node make-thumbnail.mjs <thumb.json> [out.png]
//
// thumb.json形式: { "week": "WEEK 1", "headline": "...", "stats": [{"num":"5","label":"本の実録"}] }

import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readdirSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const [thumbPath, outPng = 'thumbnail.png'] = process.argv.slice(2);
if (!thumbPath) { console.error('usage: node make-thumbnail.mjs <thumb.json> [out.png]'); process.exit(1); }

const thumb = JSON.parse(readFileSync(thumbPath, 'utf8'));

let chromium;
try { ({ chromium } = await import('playwright')); }
catch { ({ chromium } = await import('playwright-core')); }
const launchOpts = { args: ['--no-sandbox'] };
const pwDir = process.env.PLAYWRIGHT_BROWSERS_PATH;
if (pwDir) {
  const hit = readdirSync(pwDir).find((d) => /^chromium-\d+$/.test(d));
  if (hit) launchOpts.executablePath = join(pwDir, hit, 'chrome-linux', 'chrome');
}
const browser = await chromium.launch(launchOpts);
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
await page.addInitScript(`window.THUMB=${JSON.stringify(thumb)};`);
await page.goto('file://' + resolve(HERE, 'thumbnail-template.html'));
await page.waitForTimeout(300);
await page.screenshot({ path: outPng });
await browser.close();
console.log(`完成: ${outPng}`);
