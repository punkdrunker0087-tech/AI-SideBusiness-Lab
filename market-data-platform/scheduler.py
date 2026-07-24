"""スケジューリング ―― データ種別ごとの更新頻度に合わせて更新要否を判定する。

実際のジョブ実行（cron等）は環境依存のため、ここでは「このデータは
更新すべきか（=最後の取得からどれだけ経ったか）」を判定するロジックのみを
提供する。
"""
import datetime
from dataclasses import dataclass
from enum import Enum


class UpdateFrequency(Enum):
    TICK = "tick"           # 高頻度（本実装では対象外・設計のみ）
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


_INTERVAL_HOURS = {
    UpdateFrequency.TICK: 0,          # 常時（別基盤が必要）
    UpdateFrequency.DAILY: 20,        # 1日1回想定・多少の余裕を持たせる
    UpdateFrequency.WEEKLY: 24 * 6,
    UpdateFrequency.MONTHLY: 24 * 27,
}


@dataclass
class StalenessCheck:
    symbol: str
    frequency: UpdateFrequency
    last_updated: datetime.datetime
    now: datetime.datetime

    @property
    def hours_since_update(self) -> float:
        return (self.now - self.last_updated).total_seconds() / 3600

    @property
    def is_stale(self) -> bool:
        return self.hours_since_update >= _INTERVAL_HOURS[self.frequency]

    def summary(self) -> str:
        return (f"{self.symbol}: 最終更新から{self.hours_since_update:.1f}時間 "
               f"(基準={self.frequency.value}={_INTERVAL_HOURS[self.frequency]}時間) "
               f"→ {'⚠️ 更新が必要' if self.is_stale else '○ 最新'}")


def check_staleness(symbol: str, frequency: UpdateFrequency,
                    last_updated_iso: str, now: datetime.datetime = None) -> StalenessCheck:
    now = now or datetime.datetime.now(datetime.timezone.utc)
    last = datetime.datetime.fromisoformat(last_updated_iso)
    if last.tzinfo is None:
        last = last.replace(tzinfo=datetime.timezone.utc)
    return StalenessCheck(symbol=symbol, frequency=frequency, last_updated=last, now=now)
