#!/usr/bin/env node
// X投稿用「作成型」ブランドカード画像を生成する。
// 使い方: node generate-card.mjs '<JSON>' <出力パス.png>
// JSON例: {"bg":"#101a2b","accent":"#ffd333","title":"見出し","subtitle":"補足（任意）"}
import { chromium } from "playwright-core";
import fs from "node:fs";

const [, , jsonArg, outPath] = process.argv;
if (!jsonArg || !outPath) {
  console.error("使い方: node generate-card.mjs '<JSON>' <出力パス.png>");
  process.exit(1);
}
const spec = JSON.parse(jsonArg);
const bg = spec.bg || "#101a2b";
const accent = spec.accent || "#ffd333";
const title = spec.title || "";
const subtitle = spec.subtitle || "";

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face { font-display: swap; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    width:1200px; height:675px; background:${bg};
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    font-family:"IPAGothic","Hiragino Sans","Noto Sans JP",sans-serif; text-align:center; padding:80px;
  }
  .title { color:${accent}; font-size:56px; font-weight:700; line-height:1.4; max-width:960px; }
  .subtitle { color:#e8ecf2; font-size:28px; margin-top:32px; opacity:0.85; }
</style></head><body>
  <div class="title">${escapeHtml(title)}</div>
  ${subtitle ? `<div class="subtitle">${escapeHtml(subtitle)}</div>` : ""}
</body></html>`;

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await browser.newPage({ viewport: { width: 1200, height: 675 } });
await page.setContent(html);
await page.screenshot({ path: outPath });
await browser.close();
fs.accessSync(outPath);
console.log(`生成完了: ${outPath}`);
