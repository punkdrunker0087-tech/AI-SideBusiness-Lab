"""J-Quants API (V2) クライアント ―― Point-in-Time財務データの取得。

## 認証方式（実地で確認・2026-07-23）
V2 APIはAPIキー方式（`x-api-key`ヘッダー）のみ。マイページの
「API Keys」から発行する（Googleアカウントでの登録でも問題なく使える。
メール/パスワードは不要）。

⚠️ ベースURLは`https://api.jquants.com/v2`（`api.jquants-pro.com`では
ない。実地の接続テストで確認済み）。

環境変数 `JQUANTS_API_KEY` にAPIキーをセットして使う。コードには
直接書かない。`.gitignore`でcredentials・キャッシュを除外している。

## 使用エンドポイント
- `/v2/fins/summary`: 決算短信サマリー（EPS・予想EPS・修正後予想・
  配当等。`DiscDate`=開示日つきなので、これを基準にPoint-in-Timeで
  扱える——「その開示日**より後**でなければ、その数値は市場参加者に
  見えていなかった」という先読み防止の基準そのものになる）。
- `/v2/equities/bars/daily`: 株価四本値（分割調整済み `Adj*` 列あり）。

⚠️ Freeプランのデータ範囲は実地確認で **約2年分（動的なローリング
ウィンドウ、確認時点で2024-04-30〜2026-04-30）**。範囲外の日付を指定
すると400エラー（"Your subscription covers the following dates: ..."）
になる。
"""
import os
import time

import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
BASE_URL = "https://api.jquants.com/v2"


class JQuantsAuthError(RuntimeError):
    pass


def _headers() -> dict:
    api_key = os.environ.get("JQUANTS_API_KEY")
    if not api_key:
        raise JQuantsAuthError("環境変数 JQUANTS_API_KEY が設定されていません。")
    return {"x-api-key": api_key}


def _get(path: str, params: dict) -> list:
    """ページネーションに対応した汎用GET。"""
    rows = []
    cursor = None
    while True:
        p = dict(params)
        if cursor:
            p["cursor"] = cursor
        resp = requests.get(f"{BASE_URL}{path}", params=p, headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data.get("data", []))
        cursor = data.get("cursor") or data.get("pagination_key")
        if not cursor:
            break
        time.sleep(0.2)
    return rows


def fetch_fins_summary(code: str = None, date: str = None, use_cache: bool = True) -> pd.DataFrame:
    """決算短信サマリーを取得する（`code`=銘柄コード or `date`=開示日）。

    銘柄コード指定時はその銘柄の開示履歴（複数期、Point-in-Time分析の核）
    が返る。`DiscDate`列を基準に「この開示日より後の時点でのみこの数値を
    使ってよい」という先読み防止ルールを適用すること。
    """
    if not code and not date:
        raise ValueError("code か date のいずれかを指定してください。")
    key = code or date
    safe_key = str(key).replace("/", "_")
    cache_path = os.path.join(CACHE_DIR, f"fins_summary_{safe_key}.csv")
    if use_cache and os.path.exists(cache_path):
        return pd.read_csv(cache_path)

    params = {}
    if code:
        params["code"] = code
    if date:
        params["date"] = date
    rows = _get("/fins/summary", params)

    df = pd.DataFrame(rows)
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


def fetch_daily_bars(code: str, date: str = None, use_cache: bool = True) -> pd.DataFrame:
    """株価四本値（分割調整済み）を取得する。`date`省略時は取得可能な全期間。"""
    safe_key = f"{code}_{date}" if date else code
    cache_path = os.path.join(CACHE_DIR, f"bars_{safe_key}.csv")
    if use_cache and os.path.exists(cache_path):
        return pd.read_csv(cache_path)

    params = {"code": code}
    if date:
        params["date"] = date
    rows = _get("/equities/bars/daily", params)

    df = pd.DataFrame(rows)
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


def check_connection() -> dict:
    """接続確認用: サンプル銘柄(8697=日本取引所グループ)の決算サマリーを1件取得する。"""
    df = fetch_fins_summary(code="86970", use_cache=False)
    return {"base_url": BASE_URL, "n_records": len(df),
           "columns_sample": df.columns.tolist()[:10] if not df.empty else []}


if __name__ == "__main__":
    result = check_connection()
    print("接続確認OK:", result)
