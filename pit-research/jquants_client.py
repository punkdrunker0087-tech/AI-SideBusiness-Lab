"""J-Quantsクライアント ―― Point-in-Time財務データの取得。

## 認証方式（2種類に対応）
J-Quantsには少なくとも2つの認証方式が存在することを実地で確認した:

1. **APIキー方式（J-Quants Pro/新方式）**: マイページの「API Keys」から
   発行したキーを`x-api-key`ヘッダーで渡すだけ。メール/パスワードは
   不要（Googleアカウントでの登録でもこちらが使える）。
   環境変数 `JQUANTS_API_KEY` を使う。
2. **メール/パスワード方式（旧・無料プランv1）**: `/token/auth_user`に
   メール/パスワードをPOSTしてリフレッシュトークンを取得→
   `/token/auth_refresh`でIDトークンを取得→Bearerトークンとして使う。
   環境変数 `JQUANTS_EMAIL` / `JQUANTS_PASSWORD`（または既にリフレッシュ
   トークンがあれば `JQUANTS_REFRESH_TOKEN`）を使う。

`JQUANTS_API_KEY`が設定されていればそちらを優先する。

⚠️ 認証情報はコードに直接書かず、必ず環境変数から読む。
`.gitignore`でcredentialsやキャッシュを除外している。

⚠️ プラン・データ範囲の制約: 無料プランは過去2年分・12週間の開示遅延
（AQM-01シリーズの調査で確認済み）。Proプランであれば範囲が広い可能性が
あるが、実際の契約内容に応じて`check_connection()`で確認すること。
"""
import os
import time

import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
BASE_URL_V1 = "https://api.jquants.com/v1"
BASE_URL_V2 = "https://api.jquants-pro.com/v2"


class JQuantsAuthError(RuntimeError):
    pass


def _auth_mode() -> str:
    if os.environ.get("JQUANTS_API_KEY"):
        return "api_key"
    if os.environ.get("JQUANTS_EMAIL") and os.environ.get("JQUANTS_PASSWORD"):
        return "email_password"
    if os.environ.get("JQUANTS_REFRESH_TOKEN"):
        return "email_password"
    raise JQuantsAuthError(
        "認証情報が環境変数にありません。JQUANTS_API_KEY か、"
        "JQUANTS_EMAIL+JQUANTS_PASSWORD（またはJQUANTS_REFRESH_TOKEN）を設定してください。"
    )


def _get_refresh_token() -> str:
    token = os.environ.get("JQUANTS_REFRESH_TOKEN")
    if token:
        return token
    email = os.environ.get("JQUANTS_EMAIL")
    password = os.environ.get("JQUANTS_PASSWORD")
    resp = requests.post(
        f"{BASE_URL_V1}/token/auth_user",
        json={"mailaddress": email, "password": password},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "refreshToken" not in data:
        raise JQuantsAuthError(f"リフレッシュトークン取得失敗: {data}")
    return data["refreshToken"]


def _get_id_token() -> str:
    refresh_token = _get_refresh_token()
    resp = requests.post(
        f"{BASE_URL_V1}/token/auth_refresh",
        params={"refreshtoken": refresh_token},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "idToken" not in data:
        raise JQuantsAuthError(f"IDトークン取得失敗: {data}")
    return data["idToken"]


def _base_url_and_headers() -> tuple:
    """(base_url, headers) を認証方式に応じて返す。"""
    mode = _auth_mode()
    if mode == "api_key":
        api_key = os.environ["JQUANTS_API_KEY"]
        return BASE_URL_V2, {"x-api-key": api_key}
    id_token = _get_id_token()
    return BASE_URL_V1, {"Authorization": f"Bearer {id_token}"}


def fetch_statements(code: str = None, date: str = None, use_cache: bool = True) -> pd.DataFrame:
    """財務情報を取得する（`code`=銘柄コード or `date`=開示日、いずれか指定）。

    銘柄コード指定時はその銘柄の開示履歴（複数期）が返る＝Point-in-Time
    分析の核。開示日指定時はその日に開示された全銘柄分が返る。
    """
    if not code and not date:
        raise ValueError("code か date のいずれかを指定してください。")
    key = code or date
    safe_key = str(key).replace("/", "_")
    cache_path = os.path.join(CACHE_DIR, f"statements_{safe_key}.csv")
    if use_cache and os.path.exists(cache_path):
        return pd.read_csv(cache_path)

    base_url, headers = _base_url_and_headers()
    params = {}
    if code:
        params["code"] = code
    if date:
        params["date"] = date

    rows = []
    pagination_key = None
    while True:
        if pagination_key:
            params["pagination_key"] = pagination_key
        resp = requests.get(f"{base_url}/fins/statements", params=params,
                            headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rows.extend(data.get("statements", []))
        pagination_key = data.get("pagination_key")
        if not pagination_key:
            break
        time.sleep(0.2)

    df = pd.DataFrame(rows)
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(cache_path, index=False)
    return df


def check_connection() -> dict:
    """接続確認用: 認証情報の有効性と、直近の開示情報を1件だけ試し取りする。"""
    mode = _auth_mode()
    base_url, headers = _base_url_and_headers()
    resp = requests.get(
        f"{base_url}/fins/statements",
        params={"code": "86970"},  # 例: 日本取引所グループ自身
        headers=headers,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    n = len(data.get("statements", []))
    return {"auth_mode": mode, "base_url": base_url, "sample_records": n}


if __name__ == "__main__":
    result = check_connection()
    print("接続確認OK:", result)
