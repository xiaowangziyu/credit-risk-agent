"""
风控规则校验工具（ReAct专用）。
提供准入/负面/舆情规则集的查询与匹配能力，供 Agent 自主判断企业是否满足准入条件。
"""
from typing import Dict, List
from .base import BaseTool, Result
from app.models import CompanyInfo, RuleMatchResult, RuleItem

# 规则库（可改为外部配置）
RULES = {
    "admission": [
        RuleItem(
            rule_id="ADM_001",
            title="企业经营状态正常",
            description="企业需为在营/存续/开业状态，不得为吊销/注销/停业",
            weight="P0",
            risk_level="高风险"
        ),
        RuleItem(
            rule_id="ADM_002",
            title="法定代表人无重大失信记录",
            description="法定代表人无失信被执行人（终本案件）限制",
            weight="P0",
            risk_level="高风险"
        ),
        RuleItem(
            rule_id="ADM_003",
            title="近2年无重大行政处罚",
            description="无超过 50 万元的行政处罚记录",
            weight="P1",
            risk_level="中风险"
        ),
        RuleItem(
            rule_id="ADM_004",
            title="无重大股权冻结/质押",
            description="控股股东股权冻结比例不超过 30%",
            weight="P1",
            risk_level="中风险"
        ),
    ],
    "negative": [
        RuleItem(
            rule_id="NEG_001",
            title="无重大司法诉讼被告身份",
            description="近1年无作为被告的合同纠纷/借贷纠纷金额超过 1000 万",
            weight="P0",
            risk_level="高风险"
        ),
        RuleItem(
            rule_id="NEG_002",
            title="无经营异常名录记录",
            description="未被市场监管部门列入经营异常名录",
            weight="P1",
            risk_level="中风险"
        ),
        RuleItem(
            rule_id="NEG_003",
            title="无环保/安监重大违规",
            description="无环保/安监/消防的重大违规处罚",
            weight="P2",
            risk_level="低风险"
        ),
    ],
    "industry": [
        RuleItem(
            rule_id="IND_001",
            title="行业授信政策支持",
            description="所属行业属于银行普惠/重点支持行业",
            weight="P0",
            risk_level="低风险"
        ),
        RuleItem(
            rule_id="IND_002",
            title="非限制性行业",
            description="不属于两高一剩/涉房/涉融监管行业",
            weight="P0",
            risk_level="高风险"
        ),
    ],
}

# 行业白名单（示例）
WHITELIST_INDUSTRIES = {"科技服务业", "先进制造业", "绿色低碳产业", "现代物流", "现代农业", "生物医药"}
RESTRICTED_INDUSTRIES = {"房地产开发", "两高一剩行业", "融资担保", "小额贷款"}


class RuleCheckerTool(BaseTool):
    """风控规则校验工具。
    输入：{company_name: str, category: "admission" | "negative" | "industry" | "all"}
    输出：命中的规则列表与结论
    """

    name: str = "risk_rule_check"
    description: str = """
根据企业基础信息与行业，匹配风控规则库，输出是否命中禁入/负面规则、命中项明细、整体准入结论。
category 可选：admission（准入）/ negative（负面）/ industry（行业）/ all（全部）。
    """.strip()

    def execute(self, company_name: str, category: str = "all") -> Result:
        """匹配规则并返回结构化结果。若企业信息已抓取完毕，可直接给出结论；
        若关键信息缺失，会在 missing_fields 中提示 Agent 需要继续调用其他工具。"""
        from app.services.storage import storage

        info = storage.get_company(company_name)
        if not info:
            return Result(
                ok=False,
                message=f"尚未抓取到「{company_name}」的基础信息，请先调用 company_search 或 risk_scoring。",
                data={"need_next_step": "company_search", "target_company": company_name}
            )

        target = {k: v for k, v in RULES.items()} if category == "all" else {category: RULES.get(category, [])}
        hits = []
        missing_fields = []
        pass_count = 0
        total_count = 0
        top_risk = "低风险"

        for _cat, rule_list in target.items():
            for rule in rule_list:
                total_count += 1
                # 规则命中逻辑（示例，实际可按真实字段细化）
                hit_msg = None
                if rule.rule_id == "ADM_001":
                    if info.operation_status and info.operation_status not in {"在营", "存续", "开业"}:
                        hit_msg = f"经营状态为「{info.operation_status}」"
                    else:
                        pass_count += 1
                elif rule.rule_id == "ADM_002":
                    if info.legal_person_risk == "有失信":
                        hit_msg = f"法定代表人存在失信被执行人记录"
                    else:
                        pass_count += 1
                elif rule.rule_id == "ADM_003":
                    if info.penalty_count and info.penalty_count > 2:
                        hit_msg = f"近2年存在 {info.penalty_count} 次行政处罚"
                    else:
                        pass_count += 1
                elif rule.rule_id == "NEG_001":
                    if info.litigation_risk == "有重大诉讼":
                        hit_msg = "近1年存在重大诉讼被告记录"
                    else:
                        pass_count += 1
                elif rule.rule_id == "NEG_002":
                    if info.abnormal_operation:
                        hit_msg = "企业在经营异常名录中"
                    else:
                        pass_count += 1
                elif rule.rule_id == "IND_001":
                    if info.industry and info.industry in WHITELIST_INDUSTRIES:
                        pass_count += 1
                    elif info.industry and info.industry in RESTRICTED_INDUSTRIES:
                        hit_msg = f"「{info.industry}」属于非支持行业"
                    elif not info.industry:
                        missing_fields.append("所属行业")
                    else:
                        pass_count += 1
                elif rule.rule_id == "IND_002":
                    if info.industry and info.industry in RESTRICTED_INDUSTRIES:
                        hit_msg = f"「{info.industry}」属于限制性行业"
                    else:
                        pass_count += 1
                else:
                    # 其余规则按保守判断为通过（需要后续补充数据）
                    if not info.revenue and not info.litigation_risk:
                        missing_fields.append("营收/司法数据")
                    pass_count += 1

                if hit_msg:
                    hits.append(RuleMatchResult(
                        rule_id=rule.rule_id,
                        title=rule.title,
                        description=rule.description,
                        hit_detail=hit_msg,
                        weight=rule.weight,
                        risk_level=rule.risk_level,
                        status="HIT"
                    ))
                    if rule.risk_level == "高风险" or rule.weight == "P0":
                        top_risk = "高风险"
                    elif top_risk != "高风险" and rule.risk_level == "中风险":
                        top_risk = "中风险"
                else:
                    hits.append(RuleMatchResult(
                        rule_id=rule.rule_id,
                        title=rule.title,
                        description=rule.description,
                        hit_detail="未命中",
                        weight=rule.weight,
                        risk_level=rule.risk_level,
                        status="PASS"
                    ))

        conclusion = "通过"
        if top_risk == "高风险":
            conclusion = "建议拒绝"
        elif top_risk == "中风险":
            conclusion = "有条件通过"

        return Result(
            ok=True,
            message=f"完成规则校验：{pass_count}/{total_count} 项通过，结论：{conclusion}",
            data={
                "company_name": company_name,
                "rule_categories": list(target.keys()),
                "hit_rules": [h.model_dump() for h in hits],
                "pass_count": pass_count,
                "hit_count": total_count - pass_count,
                "total_count": total_count,
                "conclusion": conclusion,
                "overall_risk": top_risk,
                "missing_fields": sorted(set(missing_fields))
            }
        )


tool = RuleCheckerTool()


def run(company_name: str, category: str = "all") -> Dict:
    """兼容外部直接函数式调用。"""
    r = tool.execute(company_name=company_name, category=category)
    return r.model_dump()
