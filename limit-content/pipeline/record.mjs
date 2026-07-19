import { chromium } from 'playwright-core';
import { globSync } from 'node:fs';

const exe = globSync('/opt/pw-browsers/chromium-*/chrome-linux/chrome')[0];
const browser = await chromium.launch({ executablePath: exe, args: ['--no-sandbox'] });
const ctx = await browser.newContext({
  viewport: { width: 1080, height: 1920 },
  recordVideo: { dir: 'out', size: { width: 1080, height: 1920 } },
});
const page = await ctx.newPage();
await page.goto('file://' + process.cwd() + '/short.html');
await page.waitForTimeout(12500);
const path = await page.video().path();
await ctx.close();
await browser.close();
console.log('VIDEO:', path);
