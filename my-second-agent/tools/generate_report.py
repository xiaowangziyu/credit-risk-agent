import json
from typing import Dict, Any, List
from datetime import datetime


class ReportGenerator:
    # 合规检查配置
    COMPLIANCE_CONFIG = {
        "single_limit_ratio": 0.7,  # 单户授信上限：净资产的70%
        "related_limit_ratio": 1.5,  # 关联企业限额：单户的1.5倍
        "industry_concentration": 0.3,  # 行业集中度上限：30%
        "annual_rate_limit": 14.8  # 年化利率上限（参考值）
    }

    # 禁止类行业
    PROHIBITED_INDUSTRIES = [
        "虚拟货币", "比特币", "区块链金融", "黄赌毒", "污染", "非法金融"
    ]

    # 风险行业
    RISK_INDUSTRIES = [
        "房地产", "钢铁", "水泥", "电解铝", "煤炭", "地方政府融资"
    ]

    def generate_report(self, company_data: Dict[str, Any], rule_result: Dict[str, Any],
                        scorecard: Dict[str, Any], credit_suggestion: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 安全获取数据，防止 None 值
        scorecard = scorecard or {}
        rule_result = rule_result or {}
        credit_suggestion = credit_suggestion or {}
        company_data = company_data or {}

        top_deductions = sorted(
            scorecard.get("dimensions", []),
            key=lambda d: d.get("full_score", 0) - d.get("score", 0),
            reverse=True
        )[:3]

        # 进行合规性检查
        compliance_check = self._check_compliance(company_data, credit_suggestion)

        # 风险预警信号
        risk_warnings = self._generate_risk_warnings(company_data, rule_result, scorecard)

        # 行业分析
        industry_analysis = self._analyze_industry(company_data.get("industry", ""))

        report = {
            "report_title": f"{company_data.get('name')} - 授信风控尽调报告",
            "generated_at": now,
            "report_version": "2.0",
            "section_1_enterprise_info": {
                "title": "一、企业基本信息",
                "content": {
                    "企业名称": company_data.get("name"),
                    "统一社会信用代码": company_data.get("credit_code"),
                    "法定代表人": company_data.get("legal_representative"),
                    "注册资本": company_data.get("registered_capital"),
                    "成立日期": company_data.get("establishment_date"),
                    "经营状态": company_data.get("business_status"),
                    "所属行业": company_data.get("industry"),
                    "行业类别": company_data.get("industry_category", ""),
                    "经营范围": company_data.get("business_scope"),
                    "注册地址": company_data.get("address"),
                    "登记机关": company_data.get("registration_authority"),
                    "年营业收入": company_data.get("annual_revenue"),
                    "员工人数": company_data.get("employee_count"),
                    "注册年限": company_data.get("registered_years"),
                    "实缴资本": company_data.get("paid_capital", ""),
                    "参保人数": company_data.get("social_insurance_count", ""),
                    "数据来源": company_data.get("data_source", "工商公开数据")
                }
            },
            "section_2_rule_check": {
                "title": "二、禁入规则校验",
                "passed": rule_result.get("passed", True),
                "violations": rule_result.get("violations", []),
                "warnings": rule_result.get("warnings", []),
                "conclusion": "通过禁入规则校验，可进入评分环节" if rule_result.get("passed", True) else "未通过禁入规则校验，建议拒绝授信"
            },
            "section_3_scorecard": {
                "title": "三、信用评分卡",
                "total_score": scorecard.get("total_score", 0),
                "risk_level": scorecard.get("risk_level", "中风险"),
                "dimensions": scorecard.get("dimensions", []),
                "summary": scorecard.get("summary", ""),
                "top_deductions": [
                    {
                        "维度名称": d.get("name"),
                        "得分": d.get("score", 0),
                        "满分": d.get("full_score", 0),
                        "扣分": d.get("full_score", 0) - d.get("score", 0),
                        "原因": d.get("reason", "")
                    }
                    for d in top_deductions
                ]
            },
            "section_4_credit_suggestion": {
                "title": "四、授信建议",
                "credit_type": credit_suggestion.get("primary_credit_type", "流动资金授信"),
                "fund_purpose": credit_suggestion.get("primary_fund_purpose", "日常经营周转"),
                "suggested_amount": credit_suggestion.get("suggested_amount", "200万元"),
                "amount_range": credit_suggestion.get("amount_range", "100-300万元"),
                "suggested_period": credit_suggestion.get("suggested_period", "12个月"),
                "interest_rate": credit_suggestion.get("interest_rate_suggestion", ""),
                "guarantee": credit_suggestion.get("guarantee_requirement", ""),
                "approval_advice": credit_suggestion.get("approval_advice", ""),
                "key_risks": credit_suggestion.get("key_risks", []),
                "risk_mitigation": credit_suggestion.get("risk_mitigation", []),
                "summary": credit_suggestion.get("summary", "")
            },
            "section_5_compliance_check": {
                "title": "五、合规性检查",
                "compliance_pass": compliance_check["compliance_pass"],
                "risk_items": compliance_check["risk_items"],
                "suggestions": compliance_check["suggestions"],
                "limit_check": compliance_check["limit_check"]
            },
            "section_6_industry_analysis": {
                "title": "六、行业分析",
                "industry_name": industry_analysis["industry_name"],
                "industry_risk": industry_analysis["industry_risk"],
                "market_outlook": industry_analysis["market_outlook"],
                "policy_environment": industry_analysis["policy_environment"],
                "risk_factors": industry_analysis["risk_factors"]
            },
            "section_7_risk_warnings": {
                "title": "七、风险预警信号",
                "risk_level": risk_warnings["risk_level"],
                "warning_signals": risk_warnings["warning_signals"],
                "historical_records": risk_warnings.get("historical_records", []),
                "recommended_monitoring": risk_warnings["recommended_monitoring"]
            },
            "section_8_conclusion": {
                "title": "八、综合结论",
                "conclusion": self._generate_conclusion(company_data, scorecard, credit_suggestion, compliance_check, risk_warnings),
                "final_recommendation": self._generate_final_recommendation(
                    rule_result, scorecard, compliance_check, risk_warnings
                )
            }
        }

        return report

    def _check_compliance(self, company_data: Dict[str, Any], credit_suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """进行合规性检查"""
        risk_items = []
        suggestions = []
        compliance_pass = True

        industry = company_data.get("industry", "")
        business_status = company_data.get("business_status", "")

        # 检查禁止类行业
        for prohibited in self.PROHIBITED_INDUSTRIES:
            if prohibited in industry:
                risk_items.append(f"企业所属行业「{industry}」属于禁止类业务")
                suggestions.append("立即终止授信流程，该行业禁止授信")
                compliance_pass = False

        # 检查风险行业
        for risk_industry in self.RISK_INDUSTRIES:
            if risk_industry in industry:
                risk_items.append(f"企业所属行业「{industry}」属于限制类行业，需额外审批")
                suggestions.append("补充相关资质证明，提供担保措施")

        # 检查经营状态
        if business_status in ["吊销", "注销", "停业", "清算中"]:
            risk_items.append(f"企业经营状态为「{business_status}」，不符合授信条件")
            suggestions.append("企业经营状态异常，不建议授信")
            compliance_pass = False

        # 额度合规性检查（基于净资产估算）
        registered_capital = company_data.get("registered_capital", 0)
        estimated_net_asset = registered_capital  # 简化估算：实缴资本≈净资产
        suggested_amount_str = str(credit_suggestion.get("suggested_amount", "0"))
        import re
        amount_match = re.search(r'(\d+)', suggested_amount_str)
        suggested_amount = int(amount_match.group(1)) if amount_match else 0

        single_limit = estimated_net_asset * self.COMPLIANCE_CONFIG["single_limit_ratio"]

        limit_check = {
            "estimated_net_asset": estimated_net_asset,
            "suggested_amount": suggested_amount,
            "single_limit": single_limit,
            "limit_pass": suggested_amount <= single_limit if single_limit > 0 else True
        }

        if suggested_amount > single_limit and single_limit > 0:
            risk_items.append(f"建议授信额度{suggested_amount}万元超过单户限额（净资产70%：{int(single_limit)}万元）")
            suggestions.append(f"建议将授信额度下调至{int(single_limit)}万元以内，或增加担保措施")
            compliance_pass = False

        return {
            "compliance_pass": compliance_pass,
            "risk_items": risk_items,
            "suggestions": suggestions,
            "limit_check": limit_check
        }

    def _generate_risk_warnings(self, company_data: Dict[str, Any], rule_result: Dict[str, Any],
                                scorecard: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险预警信号"""
        warning_signals = []
        recommended_monitoring = []
        risk_level = "正常"

        # 负面信息检查
        negative_info = company_data.get("negative_info", [])
        if negative_info:
            for info in negative_info:
                if "经营异常" in info:
                    warning_signals.append(f"⚠️ {info}")
                    recommended_monitoring.append("定期检查企业经营状态是否恢复正常")
                elif "诉讼" in info:
                    warning_signals.append(f"⚠️ {info}")
                    recommended_monitoring.append("关注诉讼进展，评估对经营的影响")
                elif "亏损" in info:
                    warning_signals.append(f"⚠️ {info}")
                    recommended_monitoring.append("跟踪企业财务状况，要求提供财务报表")
                elif "被执行" in info:
                    warning_signals.append(f"🚨 {info}（重大风险）")
                    recommended_monitoring.append("立即核查具体情况，必要时终止授信")
                elif "税务异常" in info:
                    warning_signals.append(f"⚠️ {info}")
                    recommended_monitoring.append("要求企业提供完税证明")

        # 风险标签
        risk_tags = company_data.get("risk_tags", [])
        if risk_tags:
            for tag in risk_tags:
                if "高风险" in tag:
                    warning_signals.append(f"🚨 风险标签：{tag}")
                    risk_level = "高风险"
                elif "轻微" in tag or "关注" in tag:
                    warning_signals.append(f"⚠️ 风险标签：{tag}")
                    if risk_level != "高风险":
                        risk_level = "关注"

        # 评分风险
        total_score = scorecard.get("total_score", 100)
        if total_score < 50:
            warning_signals.append(f"🚨 综合评分{total_score}分，风险极高")
            risk_level = "高风险"
            recommended_monitoring.append("建议拒绝授信或要求强担保")
        elif total_score < 60:
            warning_signals.append(f"⚠️ 综合评分{total_score}分，风险较高")
            if risk_level == "正常":
                risk_level = "较高"
            recommended_monitoring.append("建议降低授信额度，缩短授信期限")

        # 经营状态风险
        business_status = company_data.get("business_status", "")
        if business_status != "存续" and business_status != "开业":
            warning_signals.append(f"⚠️ 经营状态异常：{business_status}")
            risk_level = "较高"
            recommended_monitoring.append("核查企业经营状态变化原因")

        # 历史记录（模拟数据）
        historical_records = []
        if negative_info:
            historical_records.append({
                "record_type": "负面信息",
                "description": "、".join(negative_info),
                "impact": "需重点关注"
            })

        return {
            "risk_level": risk_level,
            "warning_signals": warning_signals,
            "historical_records": historical_records,
            "recommended_monitoring": recommended_monitoring
        }

    def _analyze_industry(self, industry: str) -> Dict[str, Any]:
        """行业分析"""
        industry_info = {
            "科技服务业": {
                "risk": "较低",
                "outlook": "政策支持力度大，行业景气度高",
                "policy": "享受税收优惠政策",
                "factors": ["技术更新快", "人才依赖度高", "轻资产运营"]
            },
            "装备制造": {
                "risk": "中等",
                "outlook": "行业周期性强，受宏观经济影响大",
                "policy": "符合产业升级方向",
                "factors": ["固定资产重", "资金占用大", "订单波动明显"]
            },
            "贸易流通": {
                "risk": "中等",
                "outlook": "竞争激烈，利润空间有限",
                "policy": "无特殊限制",
                "factors": ["现金流重要", "上下游依赖强", "价格波动"]
            },
            "建筑工程": {
                "risk": "较高",
                "outlook": "受房地产政策影响大",
                "policy": "需资质证书",
                "factors": ["账期长", "垫资多", "工程款回收风险"]
            },
            "物流运输": {
                "risk": "中等",
                "outlook": "电商带动行业发展",
                "policy": "需运输资质",
                "factors": ["运营成本高", "安全风险大", "油费波动"]
            },
            "食品生产": {
                "risk": "中等",
                "outlook": "民生行业，需求稳定",
                "policy": "需食品安全资质",
                "factors": ["监管严格", "原料成本波动", "保质期限制"]
            },
            "医疗器械": {
                "risk": "较低",
                "outlook": "老龄化社会需求增长",
                "policy": "准入门槛高，监管严",
                "factors": ["研发投入大", "渠道为王", "政策影响大"]
            },
            "电子制造": {
                "risk": "中等",
                "outlook": "出口导向型，受国际贸易影响",
                "policy": "享受出口退税",
                "factors": ["技术迭代快", "供应链复杂", "汇率风险"]
            },
            "金融服务": {
                "risk": "较高",
                "outlook": "强监管行业",
                "policy": "需金融牌照资质",
                "factors": ["杠杆率高", "合规要求严", "系统性风险"]
            }
        }

        # 查找匹配行业
        for ind_name, info in industry_info.items():
            if ind_name in industry or industry in ind_name:
                return {
                    "industry_name": ind_name,
                    "industry_risk": info["risk"],
                    "market_outlook": info["outlook"],
                    "policy_environment": info["policy"],
                    "risk_factors": info["factors"]
                }

        # 默认分析
        return {
            "industry_name": "其他行业",
            "industry_risk": "待评估",
            "market_outlook": "需进一步了解",
            "policy_environment": "无特殊政策信息",
            "risk_factors": ["行业特征待明确"]
        }

    def _generate_final_recommendation(self, rule_result: Dict[str, Any], scorecard: Dict[str, Any],
                                       compliance_check: Dict[str, Any], risk_warnings: Dict[str, Any]) -> str:
        """生成最终建议"""
        recommendations = []

        # 规则校验结果
        if not rule_result.get("passed", True):
            return "🚫 **拒绝授信**：企业未通过禁入规则校验，存在一票否决项"

        # 评分结果
        total_score = scorecard.get("total_score", 0)
        if total_score < 50:
            return "🚫 **拒绝授信**：企业综合评分过低，风险极高"
        elif total_score < 60:
            recommendations.append("⚠️ **审慎授信**：综合评分较低，需强担保或抵押")
        else:
            recommendations.append("✅ **可正常授信**：企业符合基本授信条件")

        # 合规检查
        if not compliance_check.get("compliance_pass", True):
            recommendations.append("⚠️ **合规提示**：存在合规问题，需补充材料或调整额度")

        # 风险预警
        if risk_warnings.get("risk_level") == "高风险":
            recommendations.append("🚨 **高风险预警**：建议提高担保要求，缩短授信期限")
        elif risk_warnings.get("risk_level") == "较高":
            recommendations.append("⚠️ **关注**：建议加强贷后监控")

        return "；".join(recommendations) if recommendations else "✅ **建议授信**"

    def _generate_conclusion(self, company_data: Dict[str, Any], scorecard: Dict[str, Any],
                             credit_suggestion: Dict[str, Any], compliance_check: Dict[str, Any],
                             risk_warnings: Dict[str, Any]) -> str:
        score = scorecard.get("total_score", 0)
        risk = scorecard.get("risk_level", "中风险")
        compliance_status = "合规" if compliance_check.get("compliance_pass", True) else "存在合规问题"
        risk_status = risk_warnings.get("risk_level", "正常")

        conclusion = f"经综合评估，{company_data.get('name')}综合评分{score}分，风险等级为{risk}，" \
                    f"合规性检查{compliance_status}，风险预警状态{risk_status}。" \
                    f"建议给予{credit_suggestion.get('suggested_amount', '200万元')}的" \
                    f"{credit_suggestion.get('primary_credit_type', '流动资金授信')}，" \
                    f"主要用于{credit_suggestion.get('primary_fund_purpose', '日常经营周转')}。"

        if not compliance_check.get("compliance_pass", True):
            conclusion += f"合规问题：{'；'.join(compliance_check.get('suggestions', []))}。"

        if risk_warnings.get("warning_signals"):
            conclusion += f"风险提示：{'；'.join(risk_warnings.get('warning_signals', [])[:2])}。"

        conclusion += "建议贷后加强监控，确保资金用途合规。"

        return conclusion


report_generator = ReportGenerator()
