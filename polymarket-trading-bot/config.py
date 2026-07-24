import os

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


PRIVATE_KEY = os.environ.get("POLY_PRIVATE_KEY", "")
API_KEY = os.environ.get("POLY_API_KEY", "")
API_SECRET = os.environ.get("POLY_API_SECRET", "")
API_PASSPHRASE = os.environ.get("POLY_API_PASSPHRASE", "")
FUNDER_ADDRESS = os.environ.get("POLY_FUNDER_ADDRESS", "")
CLOB_HOST = os.environ.get("POLY_CLOB_HOST", "https://clob.polymarket.com")

LIVE_TRADING = _bool(os.environ.get("LIVE_TRADING", "false"))
MAX_ORDER_USD = float(os.environ.get("MAX_ORDER_USD", "10"))
MAX_DAILY_LOSS_USD = float(os.environ.get("MAX_DAILY_LOSS_USD", "50"))
MARKET_KEYWORDS = [
    kw.strip() for kw in os.environ.get("MARKET_KEYWORDS", "").split(",") if kw.strip()
]
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))


def require_live_credentials() -> None:
    missing = [
        name
        for name, value in [
            ("POLY_PRIVATE_KEY", PRIVATE_KEY),
            ("POLY_API_KEY", API_KEY),
            ("POLY_API_SECRET", API_SECRET),
            ("POLY_API_PASSPHRASE", API_PASSPHRASE),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            "ライブ発注に必要な環境変数が未設定です: " + ", ".join(missing)
        )
