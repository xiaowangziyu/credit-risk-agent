import json
import re
from typing import Dict, Any, List
from services.llm_service import llm_service


class ScorecardTool:
    def __init__(self):
        self.output_format = "维度名称 + 得分 + 满分 + 扣分原因"

    async def create_scorecard(self, company_data: Dict[str, Any], rule_result: Dict[str, Any]) -> Dict[str, Any]:
        company_json = json.dumps(company_data, ensure_ascii=False, indent=2)

        prompt = f"""你是风控策略师「小控」，请根据以下企业信息设计评分卡：

【企业信息】
{company_json}

【评分要求】
1. 自主设计6-8个评分维度，合理分配权重（总分100分）
2. 根据企业实际情况逐项打分
3. 输出格式严格遵循：
   维度名称 + 得分 + 满分 + 扣分原因
4. 打分需给出综合评分和风险等级

【评分维度建议参考】
- 企业基本资质（15-20分）
- 经营稳定性（20-25分）
- 财务健康度（20-25分）
- 行业与市场地位（10-15分）
- 信用记录与合规性（15-20分）
- 担保与增信能力（5-10分）

【风险等级划分】
- 85-100分：低风险
- 70-84分：中低风险
- 60-69分：中风险
- 50-59分：中高风险
- <50分：高风险

请按以下JSON格式输出（只输出JSON）：

{{
  "total_score": 分数,
  "risk_level": "低风险/中低风险/中风险/中高风险/高风险",
  "dimensions": [
    {{
      "name": "维度名称",
      "score": 得分,
      "full_score": 满分,
      "reason": "扣分原因或评分说明"
    }}
  ],
  "summary": "综合评价（200字以内的综合评价"
}}

请确保JSON格式正确，分数为数字。"""

        messages = [
            {"role": "system",
             "content": "你是一位经验丰富的风控策略师，擅长对企业进行信用风险评估。你会根据企业信息合理设计评分维度并公正打分。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_service.chat(messages, temperature=0.5)
            json_str = re.search(r'\{[\s\S]*\}', response)
            if json_str:
                scorecard = json.loads(json_str.group())
                return self._normalize_scorecard(scorecard)
        except Exception as e:
            pass

        return self._fallback_scorecard(company_data)

    def _normalize_scorecard(self, scorecard: Dict[str, Any]) -> Dict[str, Any]:
        if "total_score" not in scorecard:
            scorecard["total_score"] = 70
        if "risk_level" not in scorecard:
            scorecard["risk_level"] = "中低风险"
        if "dimensions" not in scorecard:
            scorecard["dimensions"] = []
        if "summary" not in scorecard:
            scorecard["summary"] = "企业整体经营状况良好。"

        total_calc = sum(d.get("score", 0) for d in scorecard["dimensions"])
        if total_calc > 0 and abs(scorecard["total_score"] - total_calc) > 5:
            scorecard["total_score"] = total_calc

        score = scorecard["total_score"]
        if score >= 85:
            scorecard["risk_level"] = "低风险"
        elif score >= 70:
            scorecard["risk_level"] = "中低风险"
        elif score >= 60:
            scorecard["risk_level"] = "中风险"
        elif score >= 50:
            scorecard["risk_level"] = "中高风险"
        else:
            scorecard["risk_level"] = "高风险"

        return scorecard

    def _fallback_scorecard(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """基于企业实际数据的动态评分卡（LLM不可用时使用）"""

        # 解析基础数据
        capital = 0
        try:
            match = re.search(r'(\d+)', str(company_data.get("registered_capital", "0")))
            if match:
                capital = float(match.group(1))
                if "亿" in str(company_data.get("registered_capital", "")):
                    capital = capital * 10000
        except:
            capital = 0

        # 解析营收（支持亏损/负数）
        revenue = 0
        is_loss = False
        try:
            rev_str = str(company_data.get("annual_revenue", "0"))
            if "亏" in rev_str or "-" in rev_str:
                is_loss = True
            match = re.search(r'(\d+\.?\d*)', rev_str)
            if match:
                revenue = float(match.group(1))
                if "亿" in rev_str:
                    revenue = revenue * 10000
                revenue = -revenue if is_loss else revenue
        except:
            revenue = 0

        # 解析员工人数
        employees = 0
        try:
            match = re.search(r'(\d+)', str(company_data.get("employee_count", "0")))
            if match:
                employees = int(match.group(1))
        except:
            employees = 0

        # 解析成立年限
        years = 0
        try:
            match = re.search(r'(\d+\.?\d*)', str(company_data.get("registered_years", "0")))
            if match:
                years = float(match.group(1))
        except:
            years = 0

        # 读取风险标志
        risk_flags = company_data.get("risk_flags", [])
        severe_risk_keywords = ["诉讼", "失信", "亏损", "负债率", "逾期", "异常", "空壳", "高管变更", "监管"]
        severe_risk_count = sum(1 for f in risk_flags if any(k in f for k in severe_risk_keywords))
        mild_risk_count = len(risk_flags) - severe_risk_count

        # 经营状态
        business_status = company_data.get("business_status", "存续")
        is_good_status = "存" in business_status or "营" in business_status

        # ========= 动态计算各维度评分 =========
        dimensions = []

        # 1. 企业基本资质（20分）
        basic_score = 20
        basic_reasons = []
        if capital < 100:
            basic_score -= 10
            basic_reasons.append("注册资本过低")
        elif capital < 500:
            basic_score -= 5
            basic_reasons.append("注册资本偏低")
        else:
            basic_reasons.append("注册资本充足")

        if years < 1:
            basic_score -= 8
            basic_reasons.append("成立时间过短")
        elif years < 3:
            basic_score -= 3
            basic_reasons.append("成立时间较短")
        else:
            basic_reasons.append("成立时间较长")
        basic_score = max(0, basic_score)
        dimensions.append({"name": "企业基本资质", "score": round(basic_score, 1),
                           "full_score": 20, "reason": "；".join(basic_reasons)})

        # 2. 经营稳定性（25分）
        stability_score = 25
        stability_reasons = []
        if not is_good_status:
            stability_score -= 15
            stability_reasons.append(f"经营状态异常：{business_status}")
        else:
            stability_reasons.append("经营状态正常")

        if employees == 0:
            stability_score -= 15
            stability_reasons.append("无在职员工")
        elif employees < 5:
            stability_score -= 8
            stability_reasons.append(f"员工人数过少（{employees}人）")
        elif employees < 20:
            stability_score -= 3
            stability_reasons.append(f"员工规模偏小（{employees}人）")
        else:
            stability_reasons.append(f"员工规模合理（{employees}人）")
        stability_score = max(0, stability_score)
        dimensions.append({"name": "经营稳定性", "score": round(stability_score, 1),
                           "full_score": 25, "reason": "；".join(stability_reasons)})

        # 3. 财务健康度（25分）
        fin_score = 25
        fin_reasons = []
        if is_loss:
            loss_amount = abs(revenue)
            if loss_amount > 3000:
                fin_score -= 20
                fin_reasons.append(f"严重亏损（亏损{loss_amount}万元）")
            elif loss_amount > 500:
                fin_score -= 15
                fin_reasons.append(f"中度亏损（亏损{loss_amount}万元）")
            else:
                fin_score -= 10
                fin_reasons.append(f"轻度亏损")
        elif revenue == 0:
            fin_score -= 20
            fin_reasons.append("无实际营业收入")
        elif revenue < 500:
            fin_score -= 8
            fin_reasons.append(f"营业收入较低（{revenue}万元）")
        elif revenue < 2000:
            fin_score -= 3
            fin_reasons.append(f"营业收入中等（{revenue}万元）")
        else:
            fin_reasons.append(f"营业收入良好（{revenue}万元）")
        fin_score = max(0, fin_score)
        dimensions.append({"name": "财务健康度", "score": round(fin_score, 1),
                           "full_score": 25, "reason": "；".join(fin_reasons)})

        # 4. 行业与市场地位（15分）
        industry = company_data.get("industry_category", "其他")
        ind_score = 15
        ind_reasons = []
        industry_list = ["金融", "租赁", "投资"]
        if any(key in industry for key in industry_list):
            ind_score -= 5
            ind_reasons.append("金融类行业受监管政策影响较大")
        else:
            ind_reasons.append("行业较为稳定")
        if revenue > 0 and capital > 0:
            capital_revenue_ratio = revenue / capital
            if capital_revenue_ratio < 0.1:
                ind_score -= 3
                ind_reasons.append("营收规模与注册资本不匹配")
            else:
                ind_reasons.append("营收与资本规模基本匹配")
        ind_score = max(0, ind_score)
        dimensions.append({"name": "行业与市场地位", "score": round(ind_score, 1),
                           "full_score": 15, "reason": "；".join(ind_reasons)})

        # 5. 信用记录与合规性（15分）
        credit_score = 15
        credit_reasons = []
        if severe_risk_count > 0:
            deduction = min(severe_risk_count * 5, 15)
            credit_score -= deduction
            credit_reasons.append(f"检测到{severe_risk_count}项重大风险信号")
        elif mild_risk_count > 0:
            deduction = min(mild_risk_count * 3, 8)
            credit_score -= deduction
            credit_reasons.append(f"检测到{mild_risk_count}项一般风险提示")
        else:
            credit_reasons.append("无明显信用风险记录")
        credit_score = max(0, credit_score)
        dimensions.append({"name": "信用记录与合规性", "score": round(credit_score, 1),
                           "full_score": 15, "reason": "；".join(credit_reasons)})

        # 计算总分
        total_score = sum(d["score"] for d in dimensions)
        total_score = round(total_score, 1)

        # 确定风险等级
        if total_score >= 85:
            risk_level = "低风险"
        elif total_score >= 70:
            risk_level = "中低风险"
        elif total_score >= 60:
            risk_level = "中风险"
        elif total_score >= 50:
            risk_level = "中高风险"
        else:
            risk_level = "高风险"

        # 生成综合评价
        summary_parts = []
        if is_loss:
            summary_parts.append(f"企业{company_data.get('name', '')}存在亏损问题")
        if severe_risk_count > 0:
            summary_parts.append(f"存在{severe_risk_count}项重大风险信号")
        if not is_good_status:
            summary_parts.append(f"经营状态为{business_status}")
        if total_score >= 70:
            summary_parts.append("整体风险可控，但需关注上述问题")
        elif total_score >= 50:
            summary_parts.append("整体风险较高，建议谨慎授信")
        else:
            summary_parts.append("整体风险极高，不建议授信")

        summary = "；".join(summary_parts)

        return {
            "total_score": total_score,
            "risk_level": risk_level,
            "dimensions": dimensions,
            "summary": summary
        }


scorecard_tool = ScorecardTool()
