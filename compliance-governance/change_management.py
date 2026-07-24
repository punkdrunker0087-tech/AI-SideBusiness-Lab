"""8. アルゴリズム変更管理 ―― コード・設定・モデル更新を対象に、状態遷移を追跡する。

draft → tested → reviewed → approved → deployed → post_review
の順で進み、各段階を飛ばせない（状態機械）。
"""
from dataclasses import dataclass, field
from enum import Enum

import audit_log
import governance


class ChangeState(Enum):
    DRAFT = "draft"
    TESTED = "tested"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    POST_REVIEWED = "post_reviewed"
    ROLLED_BACK = "rolled_back"


_NEXT_STATE = {
    ChangeState.DRAFT: ChangeState.TESTED,
    ChangeState.TESTED: ChangeState.REVIEWED,
    ChangeState.REVIEWED: ChangeState.APPROVED,
    ChangeState.APPROVED: ChangeState.DEPLOYED,
    ChangeState.DEPLOYED: ChangeState.POST_REVIEWED,
}


class InvalidTransitionError(Exception):
    pass


@dataclass
class ChangeRequest:
    change_id: str
    reason: str
    impact_scope: str
    state: ChangeState = ChangeState.DRAFT
    history: list = field(default_factory=list)

    def advance(self, to_state: ChangeState, detail: str, actor: str) -> None:
        expected = _NEXT_STATE.get(self.state)
        if to_state != expected and to_state != ChangeState.ROLLED_BACK:
            raise InvalidTransitionError(
                f"不正な状態遷移: {self.state.value} → {to_state.value}"
                f"（次に進めるのは{expected.value if expected else 'なし'}のみ）")
        self.history.append({"from": self.state.value, "to": to_state.value,
                            "detail": detail, "actor": actor})
        self.state = to_state
        audit_log.record("change_request", {
            "change_id": self.change_id, "state": self.state.value,
            "detail": detail, "reason": self.reason, "impact_scope": self.impact_scope,
        }, actor=actor)

    def rollback(self, reason: str, actor: str) -> None:
        self.advance(ChangeState.ROLLED_BACK, f"ロールバック: {reason}", actor)


def full_workflow_example(change_id: str, reason: str, impact_scope: str,
                          test_results: str, risk_assessment: str,
                          proposer: governance.Person, approver: governance.Person) -> ChangeRequest:
    """変更理由→影響範囲→テスト結果→リスク評価→レビュー→承認→本番反映→事後確認
    の一連の流れを1回通す（デモ・テスト用のヘルパー）。
    """
    cr = ChangeRequest(change_id, reason, impact_scope)
    cr.advance(ChangeState.TESTED, test_results, proposer.name)
    cr.advance(ChangeState.REVIEWED, risk_assessment, approver.name)
    governance.verify_segregation(proposer, approver)  # 承認前に職務分掌を確認
    cr.advance(ChangeState.APPROVED, f"{approver.name}が承認", approver.name)
    cr.advance(ChangeState.DEPLOYED, "本番反映完了", proposer.name)
    cr.advance(ChangeState.POST_REVIEWED, "事後確認: 想定通り動作", approver.name)
    return cr
