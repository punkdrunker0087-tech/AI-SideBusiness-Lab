"""2. 規制インベントリ ―― 適用法令の管理台帳。

⚠️ 以下のエントリは構造の例示であり、法的助言ではない。実際の適用法令・
管理方法は市場・証券会社・投資主体・法域によって異なるため、必ず
コンプライアンス部門・弁護士に確認すること。
"""
from dataclasses import dataclass, field
import datetime

import audit_log


@dataclass
class RegulationEntry:
    name: str                # 規制名
    scope: str                 # 適用範囲
    owner: str                  # 管理責任者
    control_method: str          # 管理方法
    evidence: str                 # 証跡（どこに何が残るか）
    last_reviewed: str = None


# 例示テンプレート（実際の運用では法域・商品ごとに正式なリーガルレビューが必要）
EXAMPLE_TEMPLATE = [
    RegulationEntry("市場アクセス規制", "取引所への直接/間接アクセス", "コンプライアンス部",
                    "接続前チェックリスト・年次認証", "承認記録・認証書"),
    RegulationEntry("空売り規制", "信用売り・貸株を伴う取引", "リスク管理部",
                    "発注前フラグ管理・残高照合", "日次残高レポート"),
    RegulationEntry("最良執行義務", "顧客注文の執行", "執行管理チーム",
                    "TCA(取引コスト分析)による継続評価", "執行品質レポート"),
    RegulationEntry("市場操作禁止", "全取引", "第二線(コンプライアンス)",
                    "市場公正性モニタリング(本フレームワーク`market_integrity.py`)",
                    "検知ログ・レビュー記録"),
    RegulationEntry("記録保存義務", "全取引記録", "IT/コンプライアンス部",
                    "監査ログの保存(`audit_log.py`)", "保存期間管理台帳"),
    RegulationEntry("AML/KYC", "該当する場合(口座開設等)", "コンプライアンス部",
                    "本人確認手続き(該当する場合)", "確認記録"),
    RegulationEntry("個人情報保護", "顧客・従業員データ", "情報セキュリティ部",
                    "アクセス制御・暗号化", "アクセスログ"),
]


def register(entry: RegulationEntry, actor: str = "compliance") -> dict:
    entry.last_reviewed = datetime.date.today().isoformat()
    return audit_log.record("config", {
        "type": "regulation_entry", "name": entry.name, "scope": entry.scope,
        "owner": entry.owner, "control_method": entry.control_method,
        "evidence": entry.evidence, "last_reviewed": entry.last_reviewed,
    }, actor=actor)


def build_inventory(actor: str = "compliance") -> list:
    return [register(e, actor) for e in EXAMPLE_TEMPLATE]
