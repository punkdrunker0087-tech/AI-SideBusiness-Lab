"""9. インシデント対応 ―― 検知→初動→エスカレーション→原因分析→復旧→再発防止。

重大インシデントは意思決定者・連絡先・代替手段を事前に定義しておく
（`ESCALATION_CONTACTS`）。障害時に安全側へ移行できることを重視する。
"""
import datetime
from dataclasses import dataclass, field
from enum import Enum

import audit_log


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStage(Enum):
    DETECTED = "detected"
    INITIAL_RESPONSE = "initial_response"
    ESCALATED = "escalated"
    ROOT_CAUSE = "root_cause"
    RECOVERED = "recovered"
    POST_MORTEM = "post_mortem"


# 重大インシデント時の連絡・代替手段（事前定義。実際の連絡先は運用者が設定）
ESCALATION_CONTACTS = {
    Severity.CRITICAL: {"decision_maker": "CRO(仮)", "contact": "緊急連絡網(仮)",
                        "fallback": "全ポジションのフラット化・新規発注停止"},
    Severity.HIGH: {"decision_maker": "リスク管理責任者(仮)", "contact": "オンコール担当(仮)",
                    "fallback": "該当戦略の停止"},
}


@dataclass
class Incident:
    incident_id: str
    description: str
    severity: Severity
    stage: IncidentStage = IncidentStage.DETECTED
    detected_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    initial_response_at: str = None
    recovered_at: str = None
    timeline: list = field(default_factory=list)

    def _log(self, stage: IncidentStage, detail: str, actor: str):
        self.stage = stage
        entry = {"stage": stage.value, "detail": detail, "actor": actor,
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        self.timeline.append(entry)
        audit_log.record("incident", {
            "incident_id": self.incident_id, "severity": self.severity.value,
            **entry,
        }, actor=actor)

    def initial_response(self, detail: str, actor: str):
        self.initial_response_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._log(IncidentStage.INITIAL_RESPONSE, detail, actor)

    def escalate(self, actor: str):
        contact = ESCALATION_CONTACTS.get(self.severity)
        detail = (f"エスカレーション先: {contact['decision_maker']}"
                 if contact else "エスカレーション基準に該当せず(低重要度)")
        self._log(IncidentStage.ESCALATED, detail, actor)

    def root_cause(self, detail: str, actor: str):
        self._log(IncidentStage.ROOT_CAUSE, detail, actor)

    def recover(self, detail: str, actor: str):
        self.recovered_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._log(IncidentStage.RECOVERED, detail, actor)

    def post_mortem(self, prevention_plan: str, actor: str):
        self._log(IncidentStage.POST_MORTEM, prevention_plan, actor)

    def time_to_initial_response_seconds(self) -> float:
        if not self.initial_response_at:
            return None
        d = (datetime.datetime.fromisoformat(self.initial_response_at)
            - datetime.datetime.fromisoformat(self.detected_at))
        return d.total_seconds()
