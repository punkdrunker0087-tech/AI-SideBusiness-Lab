"""1. ガバナンス構造 ―― 三線防衛モデルと職務分掌。

第一線（開発・運用）・第二線（リスク管理・コンプライアンス、独立レビュー）・
第三線（内部監査）の役割を明確にし、**同一人物が提案と承認の両方を行えない**
（職務分掌）ことをコードで強制する。
"""
from dataclasses import dataclass
from enum import Enum


class Line(Enum):
    FIRST = "第一線(開発・運用)"
    SECOND = "第二線(リスク管理・コンプライアンス)"
    THIRD = "第三線(内部監査)"


@dataclass
class Person:
    name: str
    line: Line
    can_approve: bool = False


class SegregationOfDutiesError(Exception):
    pass


def verify_segregation(proposer: Person, approver: Person) -> None:
    """提案者と承認者が同一人物・同一ラインでないことを検証する。

    第一線が提案したものは、第二線以上が承認する必要がある
    （第一線同士の"自己承認"を防ぐ）。違反時は例外を送出する。
    """
    if proposer.name == approver.name:
        raise SegregationOfDutiesError(
            f"職務分掌違反: 提案者と承認者が同一人物です（{proposer.name}）")
    if proposer.line == Line.FIRST and approver.line == Line.FIRST:
        raise SegregationOfDutiesError(
            "職務分掌違反: 第一線内だけでの承認は認められません"
            "（第二線以上のレビューが必要）")
    if not approver.can_approve:
        raise SegregationOfDutiesError(
            f"承認権限違反: {approver.name}には承認権限がありません")


def require_approval(proposer: Person, approver: Person, action: str,
                     actor_log_fn=None) -> dict:
    """承認を要求し、職務分掌を検証した上で記録する。"""
    verify_segregation(proposer, approver)
    result = {
        "action": action, "proposer": proposer.name, "proposer_line": proposer.line.value,
        "approver": approver.name, "approver_line": approver.line.value, "status": "approved",
    }
    if actor_log_fn:
        actor_log_fn("approval", result, actor=approver.name)
    return result
