"""综合尽调报告生成工具。
聚合所有工具产出，输出一份结构化、审计可查的风控尽调报告。"""
from typing import Dict, List, Optional
from .base import BaseTool, Result
from app.models import DueDiligenceReport, Section


class ReportSummaryTool(BaseTool):
    """生成综合尽调报告。
    参数：company_name，可选 include_sections 用于指定输出的章节。
    """
    name: str = "due_diligence_report"
    description: str = """
基于已存储的企业信息（工商、评分、规则命中、授信建议），
输出结构化的风控尽调报告，包含企业画像、评分、规则结论、授信建议与摘要。
    """.strip()

    def execute(self, company_name: str, include_sections: Optional[List[str]] = None) -> Result:
        from app.services.storage import storage

        info = storage.get_company(company_name)
        if not info:
            return Result(ok=False, message=f"尚未抓取到「{company_name}」，请先执行企业检索与评分。",
                          data={"need_next_step": "company_search", "target_company": company_name})

        # 拉取评分/规则/授信
        score = storage.get_score(company_name)
        rule = storage.get_rule_result(company_name)
        credit = storage.get_credit(company_name)

        sections: List[Section] = []

        sections.append(Section(
            section_id="profile",
            title="企业画像",
            summary=f"{info.company_name}（{info.credit_code}）法定代表人：{info.legal_person or '-'}，经营状态：{info.operation_status or '-'}，所属行业：{info.industry or '-'}，注册地址：{info.address or '-'}。",
            highlights=[
                f"注册资本：{info.registered_capital or '-'} 万元",
                f"参保人数：{info.insurance_count or '-'}",
                f"成立日期：{info.establish_date or '-'}",
                f"主要经营范围：{info.business_scope or '-'}",
            ],
            data={
                "legal_person": info.legal_person,
                "operation_status": info.operation_status,
                "industry": info.industry,
                "registered_capital": info.registered_capital,
                "insurance_count": info.insurance_count,
                "establish_date": info.establish_date,
            }
        ))

        if score is not None:
            sections.append(Section(
                section_id="score",
                title="评分与风险等级",
                summary=f"综合评分 {score.total_score} 分，风险等级判定为 {score.risk_level}，评分模型包含 {len(score.score_items or [])} 个维度。",
                highlights=[
                    f"主体资质：{get_dim_score(score, '主体资质')}",
                    f"经营稳定性：{get_dim_score(score, '经营稳定性')}",
                    f"司法风险：{get_dim_score(score, '司法风险')}",
                ],
                data=score.model_dump()
            ))

        if rule is not None:
            sections.append(Section(
                section_id="admission",
                title="准入规则与负面结论",
                summary=f"准入规则校验结论：{rule.conclusion}（总体风险：{rule.overall_risk}）。"
                        f"共 {rule.total_count} 条规则，命中 {rule.hit_count} 条。",
                highlights=[
                    f"{h.title}：{h.hit_detail}（{h.weight} / {h.risk_level}）"
                    for h in (rule.hit_rules or []) if h.status == "HIT"
                ][:5],
                data=rule.model_dump()
            ))

        if credit is not None:
            sections.append(Section(
                section_id="credit",
                title="授信建议",
                summary=f"建议授信额度：{credit.credit_best} 万元（{credit.credit_range_low}–{credit.credit_range_high}），"
                        f"期限：{credit.suggested_term_months} 个月，利率：LPR {credit.suggested_rate}%，担保方式：{credit.suggested_guarantee}。",
                highlights=[
                    f"行业系数：{credit.industry_coef}",
                    f"担保系数：{credit.guarantee_coef}",
                    f"测算依据：{credit.basis}",
                ],
                data=credit.model_dump()
            ))

        report = DueDiligenceReport(
            company_name=company_name,
            overall_risk=rule.overall_risk if rule else (score.risk_level if score else "未评估"),
            conclusion=credit.suggested_guarantee + " / " + (rule.conclusion if rule else "未评估"),
            sections=sections,
            source_ids=[],
            disclaimer="本报告基于公开数据与策略规则生成，仅供授信决策参考。",
            generated_at=None,
        )

        return Result(ok=True, message=f"「{company_name}」综合尽调报告已生成。", data=report.model_dump())


def get_dim_score(score, dim: str) -> str:
    """从评分明细中取出对应维度的分数字符串。"""
    if not score.score_items:
        return "—"
    for item in score.score_items:
        if item.dimension == dim:
            return f"{item.score}/{item.max_score}"
    return "—"


tool = ReportSummaryTool()


def run(company_name: str, include_sections: Optional[List[str]] = None) -> Dict:
    return tool.execute(company_name=company_name, include_sections=include_sections).model_dump()
