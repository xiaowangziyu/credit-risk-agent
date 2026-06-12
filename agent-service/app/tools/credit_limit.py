"""授信额度与期限测算工具（策略式）。
基于评分、营收、担保方式和行业系数，给出授信额度/利率/期限区间建议。"""
from typing import Dict, Optional
from .base import BaseTool, Result
from app.models import CreditSuggestion

INDUSTRY_COEF = {
    "科技服务业": 1.3,
    "先进制造业": 1.2,
    "现代物流": 1.0,
    "绿色低碳产业": 1.25,
    "生物医药": 1.3,
    "商贸零售": 0.9,
    "建筑装饰": 0.85,
}

GUARANTEE_COEF = {"信用": 1.0, "保证担保": 1.1, "抵押": 1.3, "质押": 1.35}

SCORE_RATE = [(85, 3.85), (75, 4.35), (65, 4.75), (50, 5.35), (0, 5.85)]
SCORE_TERM = [(85, 36), (75, 24), (65, 18), (50, 12), (0, 6)]


def _pick(arr, score: float):
    for th, v in arr:
        if score >= th:
            return v
    return arr[-1][1]


class CreditLimitTool(BaseTool):
    """授信额度/利率/期限测算。"""
    name: str = "credit_limit"
    description: str = "基于企业营收、评分、担保方式与所属行业，给出授信额度区间、利率、期限建议。"

    def execute(self, company_name: str,
                revenue: Optional[float] = None,
                guarantee: str = "信用",
                industry: Optional[str] = None,
                score: Optional[float] = None) -> Result:
        from app.services.storage import storage

        info = storage.get_company(company_name)
        if not info:
            return Result(ok=False, message=f"尚未抓取到「{company_name}」，请先调用 company_search / risk_scoring。",
                          data={"need_next_step": "risk_scoring", "target_company": company_name})

        final_revenue = revenue or info.revenue
        final_industry = industry or info.industry
        final_score = score if score is not None else info.score
        final_guarantee = guarantee

        if not final_revenue or final_revenue <= 0:
            return Result(ok=False, message=f"「{company_name}」暂无可用于额度测算的营收数据。",
                          data={"need_next_step": "risk_scoring", "missing_field": "revenue"})

        coef = INDUSTRY_COEF.get(final_industry, 1.0) if final_industry else 1.0
        g_coef = GUARANTEE_COEF.get(final_guarantee, 1.0)

        base = final_revenue * 0.15
        low = round(base * 0.7 * g_coef, 2)
        high = round(base * g_coef * 1.2, 2)
        best = round((low + high) / 2, 2)

        rate = _pick(SCORE_RATE, final_score or 70)
        term = _pick(SCORE_TERM, final_score or 70)

        suggestion = CreditSuggestion(
            company_name=company_name,
            credit_range_low=low,
            credit_range_high=high,
            credit_best=best,
            suggested_term_months=term,
            suggested_rate=rate,
            suggested_guarantee=final_guarantee,
            industry_coef=coef,
            guarantee_coef=g_coef,
            score_coef=(final_score or 70) / 100,
            basis=f"基于营收 {final_revenue} 万元与行业系数 {coef}、担保系数 {g_coef} 综合测算。"
        )

        return Result(ok=True,
                      message=f"授信测算完成：建议额度 {best} 万元（{low}–{high}），期限 {term} 个月，利率 LPR {rate}%。",
                      data=suggestion.model_dump())


tool = CreditLimitTool()


def run(company_name: str, revenue: Optional[float] = None, guarantee: str = "信用",
        industry: Optional[str] = None, score: Optional[float] = None) -> Dict:
    return tool.execute(company_name=company_name, revenue=revenue, guarantee=guarantee,
                       industry=industry, score=score).model_dump()
