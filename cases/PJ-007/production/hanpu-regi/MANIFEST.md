# MANIFEST — 頒布レジ v1.1

## 配布パッケージ構成

### 製品版ZIP（hanpu-regi-v1.1.zip、¥780）
| パッケージ内パス | 内容 |
|---|---|
| hanpu-regi.html | 本体（製品版、`const FREE = false`） |
| README.md | 使用方法・対象環境・注意事項 |
| LICENSE.md | 利用許諾 |

### 無料版ZIP（hanpu-regi-free.zip、¥0）
| パッケージ内パス | 内容 |
|---|---|
| hanpu-regi-free.html | 本体（無料版、頒布物3種まで・CSV書き出しなし） |
| README.md / LICENSE.md | 共通 |

## ビルド方法（単一ソース）

無料版は`const FREE = false;`→`true`のsed置換のみで生成（PJ-006と同方式）。
localStorageキー共通のため無料版→製品版へデータ引き継ぎ可。

## 品質保証

Playwright + Chromium（モバイルビューポート390px）でE2Eテスト実施:
会計計算（合計・お釣り）・在庫連動（頒布/完売/取消復元）・売上台帳互換
CSV・JSONバックアップ・リロード永続化・横スクロールなし・無料版ゲート・
XSSエスケープ。全項目パス・コンソールエラー0件（2026-07-09）。

## AI生成開示

全コード・ドキュメントはClaude（Anthropicの生成AIモデル）によって
設計・生成された（AI生成率: 実質100%）。
