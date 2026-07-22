"""4. ポジション限度 ―― 個別銘柄・セクター・資産クラス・ポートフォリオ全体の
複数レベルで管理する。ソフトリミット＝注意喚起、ハードリミット＝新規注文停止。
"""
from dataclasses import dataclass, field

import audit_log


@dataclass
class LimitLevel:
    name: str
    soft_limit: float
    hard_limit: float


@dataclass
class LimitBreach:
    level: str
    entity: str
    current_value: float
    limit_type: str    # "soft" or "hard"
    limit_value: float
    action: str


def check_level(level: LimitLevel, entity: str, current_value: float) -> LimitBreach:
    """1レベル（例: 個別銘柄）の現在値を、ソフト/ハード両方の上限と照合する。"""
    abs_val = abs(current_value)
    if abs_val > level.hard_limit:
        return LimitBreach(level.name, entity, current_value, "hard", level.hard_limit,
                          "新規注文停止・エスカレーション必須")
    if abs_val > level.soft_limit:
        return LimitBreach(level.name, entity, current_value, "soft", level.soft_limit,
                          "注意喚起（新規注文は可・監視強化）")
    return None


def check_all_levels(exposures: dict, levels: dict, actor: str = "risk_management") -> list:
    """exposures: {レベル名: {エンティティ名: 現在値}}, levels: {レベル名: LimitLevel}。"""
    breaches = []
    for level_name, entity_values in exposures.items():
        level = levels.get(level_name)
        if level is None:
            continue
        for entity, value in entity_values.items():
            breach = check_level(level, entity, value)
            if breach:
                breaches.append(breach)
                audit_log.record("limit_breach", {
                    "level": breach.level, "entity": breach.entity,
                    "current_value": breach.current_value, "limit_type": breach.limit_type,
                    "limit_value": breach.limit_value, "action": breach.action,
                }, actor=actor)
    return breaches


def format_breaches(breaches: list) -> str:
    if not breaches:
        return "○ 全レベルで制限内"
    lines = []
    for b in breaches:
        flag = "🔴HARD" if b.limit_type == "hard" else "🟡SOFT"
        lines.append(f"  {flag} [{b.level}] {b.entity}: {b.current_value:,.0f} "
                     f"(上限{b.limit_value:,.0f}) → {b.action}")
    return "\n".join(lines)
