"""极简记忆存储：进程内 dict 保存企业信息、评分、规则结论与授信建议。
后续可替换为 SQLite / Redis。"""
from typing import Dict, Optional, Any
from app.models import CompanyInfo, ScoreResult, RuleCheckResult, CreditSuggestion, DueDiligenceReport


class InMemoryStorage:
    def __init__(self) -> None:
        self._companies: Dict[str, CompanyInfo] = {}
        self._scores: Dict[str, ScoreResult] = {}
        self._rules: Dict[str, RuleCheckResult] = {}
        self._credits: Dict[str, CreditSuggestion] = {}
        self._reports: Dict[str, DueDiligenceReport] = {}
        self._events: Dict[str, list] = {}

    # ---- 企业基础信息 ----
    def save_company(self, info: CompanyInfo) -> None:
        self._companies[info.company_name] = info

    def get_company(self, company_name: str) -> Optional[CompanyInfo]:
        return self._companies.get(company_name)

    # ---- 评分 ----
    def save_score(self, score: ScoreResult) -> None:
        self._scores[score.company_name] = score

    def get_score(self, company_name: str) -> Optional[ScoreResult]:
        return self._scores.get(company_name)

    # ---- 规则 ----
    def save_rule_result(self, rule: RuleCheckResult) -> None:
        self._rules[rule.company_name] = rule

    def get_rule_result(self, company_name: str) -> Optional[RuleCheckResult]:
        return self._rules.get(company_name)

    # ---- 授信 ----
    def save_credit(self, credit: CreditSuggestion) -> None:
        self._credits[credit.company_name] = credit

    def get_credit(self, company_name: str) -> Optional[CreditSuggestion]:
        return self._credits.get(company_name)

    # ---- 报告 ----
    def save_report(self, report: DueDiligenceReport) -> None:
        self._reports[report.company_name] = report

    def get_report(self, company_name: str) -> Optional[DueDiligenceReport]:
        return self._reports.get(company_name)

    # ---- 事件日志 ----
    def append_event(self, company_name: str, event: Dict[str, Any]) -> None:
        self._events.setdefault(company_name, []).append(event)

    def list_events(self, company_name: str):
        return list(self._events.get(company_name, []))

    # ---- 全量 ----
    def list_companies(self):
        return list(self._companies.keys())


storage = InMemoryStorage()
