"""J-Quants API（無料プラン）クライアント ―― Point-in-Time財務データの取得。

## 認証フロー（無料プラン、v1）
1. 登録したメールアドレス・パスワードを `/token/auth_user` にPOSTし、
   リフレッシュトークン（有効期間1週間）を取得する。
2. リフレッシュトークンを `/token/auth_refresh` に渡し、IDトークン
   （有効期間24時間、以後のAPI呼び出しのBearerトークン）を取得する。

⚠️ 認証情報はコードに直接書かず、環境変数から読む
（`JQUANTS_EMAIL` / `JQUANTS_PASSWORD`、または既にリフレッシュトークンが
あれば `JQUANTS_REFRESH_TOKEN`）。`.gitignore`でcredentialsやキャッシュを
除外している。

⚠️ 無料プランの制約（AQM-01シリーズの調査で確認済み）: 提供される財務
データは**過去2年分・12週間の開示遅延**。本シリーズ（Project A/AQM-01）
のような15年間のPoint-in-Timeバックテストはこのデータだけでは組めない
点に注意。まずは「短期間でも独立した情報軸を持つか」という限定的な
問いから検証を始める。
"""
import os
import time

import pandas as pd
import requests

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
BASE_URL = "https://api.jquants.com/v1"


class JQuantsAuthError(RuntimeError):
    pass


def _get_refresh_token() -> str:
    token = os.environ.get("JQUANTS_REFRESH_TOKEN")
    if token:
        return token

    email = os.environ.get("JQUANTS_EMAIL")
    password = os.environ.get("JQUANTS_PASSWORD")
    if not email or not password:
        raise JQuantsAuthError(
            "認証情報が環境変数にありません。JQUANTS_EMAIL / JQUANTS_PASSWORD "
            "（またはJQUANTS_REFRESH_TOKEN）を設定してください。"
        )
    resp = requests.post(
        f"{BASE_URL}/token/auth_user",
        json={"mailaddress": email, "password": password},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "refreshToken" not in data:
        raise JQuantsAuthError(f"リフレッシュトークン取得失敗: {data}")
    return data["refreshToken"]


def get_id_token() -> str:
    """IDトークンを取得する（毎回リフレッシュトークンから再発行。24時間有効）。"""
    refresh_token = _get_refresh_token()
    resp = requests.post(
        f"{BASE_URL}/token/auth_refresh",
        params={"refreshtoken": refresh_token},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "idToken" not in data:
        raise JQuantsAuthError(f"IDトークン取得失敗: {data}")
    return data["idToken"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_id_token()}"}


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
        resp = requests.get(f"{BASE_URL}/fins/statements", params=params,
                            headers=_headers(), timeout=30)
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
    """接続確認用: IDトークン取得と、直近の開示情報を1件だけ試し取りする。"""
    token = get_id_token()
    resp = requests.get(
        f"{BASE_URL}/fins/statements",
        params={"code": "86970"},  # 例: 日本取引所グループ自身
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    n = len(data.get("statements", []))
    return {"id_token_prefix": token[:12] + "...", "sample_records": n}


if __name__ == "__main__":
    result = check_connection()
    print("接続確認OK:", result)
