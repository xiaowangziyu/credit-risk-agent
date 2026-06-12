import json
import re
import os
from typing import Dict, Any, Optional
from services.llm_service import llm_service
from config.settings import settings


class CreditCalculator:
    def __init__(self):
        self.industry_adjustments = {
            "科技服务业": (1.0, 1.2),
            "装备制造": (0.9, 1.1),
            "贸易流通": (0.8, 1.0),
            "建筑工程": (0.7, 0.9),
            "物流运输": (0.8, 1.0),
            "食品生产": (0.9, 1.0),
            "医疗器械": (1.0, 1.1),
            "电子制造": (0.9, 1.1)
        }

    def _parse_revenue(self, revenue_str: str) -> float:
        """解析营收，返回正数表示盈利额，负数表示亏损额，0表示无数据"""
        try:
            if not revenue_str or revenue_str in ("0", "0万元"):
                return 0
            is_loss = "亏" in revenue_str or "-" in revenue_str
            match = re.search(r'(\d+\.?\d*)', revenue_str)
            if match:
                num = float(match.group(1))
                if "亿" in revenue_str:
                    num = num * 10000
                return -num if is_loss else num
            return 0
        except:
            return 0

    def _simple_calc(self, total_score: float, annual_revenue: str, industry: str) -> Dict[str, Any]:
        revenue = self._parse_revenue(annual_revenue)

        # 亏损企业 - 不建议授信
        if revenue < 0:
            return {
                "suggested_amount_range": "不建议授信",
                "suggested_amount": "不建议授信",
                "suggested_period": "不建议授信",
                "calculation_basis": f"企业亏损（{annual_revenue}），不具备还款能力"
            }

        # 无营收企业 - 不建议授信
        if revenue == 0:
            return {
                "suggested_amount_range": "不建议授信",
                "suggested_amount": "不建议授信",
                "suggested_period": "不建议授信",
                "calculation_basis": "企业无实际营业收入"
            }

        # 高风险企业 - 极低额度或拒绝
        if total_score < 50:
            return {
                "suggested_amount_range": "不建议授信",
                "suggested_amount": "不建议授信",
                "suggested_period": "不建议授信",
                "calculation_basis": f"综合评分过低（{total_score}分），风险过高"
            }

        # 中高风险企业 - 低额度短期限
        if total_score < 60:
            ratio_low, ratio_high = 0.05, 0.08
            period = "3个月以内"
        elif total_score >= 85:
            ratio_low, ratio_high = 0.20, 0.30
            period = "12-24个月"
        elif total_score >= 70:
            ratio_low, ratio_high = 0.15, 0.20
            period = "6-12个月"
        else:
            ratio_low, ratio_high = 0.10, 0.15
            period = "3-6个月"

        adjust_low = 0.85
        adjust_high = 1.0
        if industry in self.industry_adjustments:
            adjust_low, adjust_high = self.industry_adjustments[industry]

        min_amount = round(max(revenue * ratio_low * adjust_low, 50), 0)
        max_amount = round(max(revenue * ratio_high * adjust_high, 100), 0)

        suggested = round((min_amount + max_amount) / 2, 0)

        return {
            "suggested_amount_range": f"{int(min_amount)}-{int(max_amount)}万元",
            "suggested_amount": f"{int(suggested)}万元",
            "suggested_period": period,
            "calculation_basis": f"基于{annual_revenue}营业收入×{int(ratio_low * 100)}-{int(ratio_high * 100)}%×行业调整系数{adjust_low}-{adjust_high}"
        }

    async def calculate_credit(self, company_data: Dict[str, Any], scorecard: Dict[str, Any]) -> Dict[str, Any]:
        total_score = scorecard.get("total_score", 70)
        annual_revenue = company_data.get("annual_revenue", "5000万元")
        industry = company_data.get("industry_category", "贸易流通")

        simple_result = self._simple_calc(total_score, annual_revenue, industry)

        prompt = f"""你是风控策略师「小控」，请根据企业信息和评分结果给出授信建议：

【企业信息】
企业名称：{company_data.get('name')}
所属行业：{company_data.get('industry')} / {industry}
年营业收入：{annual_revenue}
注册资本：{company_data.get('registered_capital')}
经营状态：{company_data.get('business_status')}

【评分结果】
综合评分：{total_score}分
风险等级：{scorecard.get('risk_level', '中低风险')}

【初步测算参考】
建议额度区间：{simple_result['suggested_amount_range']}
建议期限：{simple_result['suggested_period']}
计算依据：{simple_result['calculation_basis']}

【授信类型选项】（选择最合适的1-2种）
1. 流动资金授信 - 日常经营周转、货物采购备货、物流运费支付
2. 固定资产授信 - 设备购置更新
3. 仓单质押授信 - 有稳定库存存货的企业
4. 应收账款保理授信 - 应收账款占比较高
5. 投标保函授信 - 参与招投标项目
6. 纯信用授信 - 评分较高、合作良好的企业

【资金用途选项】（选择最合适的1-2种）
- 日常经营周转
- 货物采购备货
- 物流运费支付
- 设备购置更新
- 项目履约垫资

请按以下JSON格式输出（只输出JSON）：

{{
  "credit_types": ["授信类型1", "授信类型2"],
  "primary_credit_type": "主要推荐授信类型",
  "fund_purposes": ["用途1", "用途2"],
  "primary_fund_purpose": "主要推荐资金用途",
  "suggested_amount": "建议授信额度（万元）",
  "amount_range": "额度区间",
  "suggested_period": "建议授信期限",
  "interest_rate_suggestion": "利率建议",
  "guarantee_requirement": "担保要求",
  "approval_advice": "审批建议",
  "key_risks": ["主要风险点1", "主要风险点2"],
  "risk_mitigation": ["风险缓释措施1", "风险缓释措施2"],
  "summary": "综合授信建议（200字以内）"
}}"""

        messages = [
            {"role": "system",
             "content": "你是一位经验丰富的风控审批师，擅长根据企业资质和评分给出合理的授信建议。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_service.chat(messages, temperature=0.5)
            json_str = re.search(r'\{[\s\S]*\}', response)
            if json_str:
                result = json.loads(json_str.group())
                if "suggested_amount" not in result or not result["suggested_amount"]:
                    result["suggested_amount"] = simple_result["suggested_amount"]
                if "amount_range" not in result or not result["amount_range"]:
                    result["amount_range"] = simple_result["suggested_amount_range"]
                return result
        except Exception as e:
            pass

        # 基于评分和企业数据生成动态 fallback 结果
        risk_level = scorecard.get("risk_level", "中低风险")
        is_loss = "亏" in str(annual_revenue) or "-" in str(annual_revenue)
        risk_flags = company_data.get("risk_flags", [])

        if total_score < 50 or is_loss or "不建议" in simple_result["suggested_amount"]:
            return {
                "credit_types": [],
                "primary_credit_type": "不建议授信",
                "fund_purposes": [],
                "primary_fund_purpose": "不建议授信",
                "suggested_amount": "不建议授信",
                "amount_range": "不建议授信",
                "suggested_period": "不建议授信",
                "interest_rate_suggestion": "不适用",
                "guarantee_requirement": "不适用",
                "approval_advice": "建议拒绝",
                "key_risks": risk_flags if risk_flags else ["企业存在严重风险信号，不具备基本授信条件"],
                "risk_mitigation": ["建议先改善经营状况，待财务指标恢复健康后再申请授信"],
                "summary": f"企业综合评分{total_score}分（{risk_level}），存在明显风险，不建议授信。"
            }

        elif total_score < 60:
            return {
                "credit_types": ["流动资金授信"],
                "primary_credit_type": "流动资金授信",
                "fund_purposes": ["日常经营周转"],
                "primary_fund_purpose": "日常经营周转",
                "suggested_amount": simple_result["suggested_amount"],
                "amount_range": simple_result["suggested_amount_range"],
                "suggested_period": simple_result["suggested_period"],
                "interest_rate_suggestion": "基准贷款利率上浮30%-50%",
                "guarantee_requirement": "必须提供足额抵质押物+实际控制人连带责任担保",
                "approval_advice": "严格条件下审批",
                "key_risks": risk_flags if risk_flags else ["企业风险较高，需重点监控"],
                "risk_mitigation": ["要求提供完整财务报表并按月更新", "贷后检查频率提高至每月一次"],
                "summary": f"企业综合评分{total_score}分（{risk_level}），建议在严格担保条件下给予小额短期授信。"
            }
        else:
            return {
                "credit_types": ["流动资金授信"],
                "primary_credit_type": "流动资金授信",
                "fund_purposes": ["日常经营周转"],
                "primary_fund_purpose": "日常经营周转",
                "suggested_amount": simple_result["suggested_amount"],
                "amount_range": simple_result["suggested_amount_range"],
                "suggested_period": simple_result["suggested_period"],
                "interest_rate_suggestion": "基准贷款利率上浮10%-15%",
                "guarantee_requirement": "建议提供企业实际控制人连带责任担保",
                "approval_advice": "建议有条件通过",
                "key_risks": risk_flags if risk_flags else ["需关注行业周期波动风险", "加强贷后资金用途监控"],
                "risk_mitigation": ["要求提供财务报表定期更新", "设置合理的还款计划"],
                "summary": f"企业综合评分{total_score}分（{risk_level}），整体风险可控，建议给予适度授信额度。"
            }


credit_calculator = CreditCalculator()
