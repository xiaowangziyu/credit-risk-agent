"""基础数据模型（Pydantic v2）。"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CompanyInfo(BaseModel):
    company_name: str
    unified_code: Optional[str] = None
    credit_code: Optional[str] = None
    company_type: Optional[str] = None
    legal_person: Optional[str] = None
    establish_date: Optional[str] = None
    registered_capital: Optional[float] = None
    paid_capital: Optional[float] = None
    operation_status: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    business_scope: Optional[str] = None
    insurance_count: Optional[int] = None
    shareholder_count: Optional[int] = None
    branch_count: Optional[int] = None
    litigation_count: Optional[int] = None
    litigation_risk: Optional[str] = None
    credit_history: Optional[str] = None
    revenue: Optional[float] = None
    score: Optional[float] = None
    legal_person_risk: Optional[str] = None
    abnormal_operation: Optional[bool] = False
    penalty_count: Optional[int] = 0
    operation_years: Optional[int] = None
    source: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class ScoreDimension(BaseModel):
    dimension: str
    score: float
    weight: float
    note: Optional[str] = None


class ScoreItem(BaseModel):
    dimension: str
    weight: float
    score: float
    max_score: float
    reason: Optional[str] = None


class ScoreResult(BaseModel):
    company_name: str
    total_score: float
    risk_level: str
    score_items: Optional[List[ScoreItem]] = None
    breakdown: Optional[List[Dict[str, Any]]] = None
    note: Optional[str] = None


class RuleItem(BaseModel):
    rule_id: str
    title: str
    description: str
    weight: str
    risk_level: str


class RuleMatchResult(BaseModel):
    rule_id: str
    title: str
    description: str
    hit_detail: str
    weight: str
    risk_level: str
    status: str  # PASS / HIT


class RuleCheckResult(BaseModel):
    company_name: str
    rule_categories: List[str] = []
    hit_rules: List[RuleMatchResult] = []
    pass_count: int = 0
    hit_count: int = 0
    total_count: int = 0
    conclusion: str
    overall_risk: str


class CreditSuggestion(BaseModel):
    company_name: str
    credit_range_low: float
    credit_range_high: float
    credit_best: float
    suggested_term_months: int
    suggested_rate: float
    suggested_guarantee: str
    industry_coef: float
    guarantee_coef: float
    score_coef: float
    basis: str


class Section(BaseModel):
    section_id: str
    title: str
    summary: str
    highlights: Optional[List[str]] = None
    data: Optional[Any] = None


class DueDiligenceReport(BaseModel):
    company_name: str
    overall_risk: str
    conclusion: str
    sections: List[Section]
    source_ids: List[str] = []
    disclaimer: str = ""
    generated_at: Optional[str] = None
