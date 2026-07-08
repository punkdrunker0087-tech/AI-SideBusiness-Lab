# MANIFEST — クリエイター売上台帳 v1.1

## 配布パッケージ構成

### 製品版ZIP（creator-sales-ledger-v1.zip、¥1,480）

| パッケージ内パス | 取得元 | 内容 |
|---|---|---|
| creator-sales-ledger.html | 本フォルダ同名ファイル | 本体（製品版、`const FREE = false`） |
| README.md | 本フォルダ同名ファイル | 使用方法・注意事項 |
| LICENSE.md | 本フォルダ同名ファイル | 利用許諾 |

### 無料版ZIP（creator-sales-ledger-free.zip、¥0）

| パッケージ内パス | 取得元 | 内容 |
|---|---|---|
| creator-sales-ledger-free.html | 本フォルダ同名ファイル | 本体（無料版、記録50件まで・CSV書き出しなし） |
| README.md | 共通 | 使用方法・無料版と製品版の違いを含む |
| LICENSE.md | 共通 | 利用許諾 |

## ビルド方法（単一ソース）

無料版は製品版と同一ソースで、`const FREE = false;` を `true` に
変更したもののみが差分（`sed`で生成）。機能差はランタイムのゲート
（記録件数上限・CSV書き出し・ヘッダー表記）で制御される。
localStorageキーは共通のため、無料版→製品版へデータがそのまま
引き継がれる。

## 品質保証

- Playwright + Chromium によるE2Eテストを製品版・無料版の両方で実施
  （記録・集計精度・グラフ描画・CSV/JSONダウンロード・リロード永続化・
  無料版ゲート動作。コンソールエラー0件）
- 外部依存ゼロ（CDN・外部フォント・API不使用）。オフライン動作

## AI生成開示

本パッケージの全コード・ドキュメントはClaude（Anthropicの生成AI
モデル）によって設計・生成された（AI生成率: 実質100%）。
