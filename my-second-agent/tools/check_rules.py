from typing import Dict, Any, List
import re


class RuleCheckTool:
    def __init__(self):
        self.forbidden_statuses = ["吊销", "注销", "停业", "清算", "歇业", "关闭"]
        self.warning_words = ["吊销", "注销", "停业", "清算", "歇业", "关闭"]
        # 严重风险信号 - 命中即拒绝
        self.severe_risks = [
            "失信被执行人", "重大诉讼", "连续三年亏损", "连续亏损",
            "资产负债率过高", "逾期租金", "多起法律诉讼"
        ]

    def _parse_years(self, years) -> float:
        """解析注册年限，支持字符串和数字"""
        try:
            # 如果已经是数字，直接返回
            if isinstance(years, (int, float)):
                return float(years)
            years_str = str(years)
            match = re.search(r'(\d+\.?\d*)', years_str)
            if match:
                return float(match.group(1))
            return 0
        except:
            return 0

    def _parse_capital(self, capital) -> float:
        """解析注册资本，支持字符串和数字"""
        try:
            # 如果已经是数字，直接返回
            if isinstance(capital, (int, float)):
                return float(capital)
            capital_str = str(capital)
            match = re.search(r'(\d+\.?\d*)', capital_str)
            if match:
                num = float(match.group(1))
                if "亿" in capital_str:
                    num = num * 10000
                return num
            return 0
        except:
            return 0

    def _parse_revenue(self, revenue) -> float:
        """解析营收，支持字符串和数字"""
        try:
            # 如果已经是数字，直接返回（正数表示盈利，负数表示亏损）
            if isinstance(revenue, (int, float)):
                return float(revenue)
            revenue_str = str(revenue)
            # 检测是否为亏损状态
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

    def _parse_employee_count(self, emp) -> int:
        """解析员工人数，支持字符串和数字"""
        try:
            # 如果已经是数字，直接返回
            if isinstance(emp, (int, float)):
                return int(emp)
            emp_str = str(emp)
            match = re.search(r'(\d+)', emp_str)
            if match:
                return int(match.group(1))
            return 0
        except:
            return 0

    def check_rules(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        results = {
            "passed": True,
            "violations": [],
            "warnings": [],
            "reasons": []
        }

        # 1. 经营状态检查（禁入）
        business_status = company_data.get("business_status", "")
        if any(word in business_status for word in self.forbidden_statuses):
            results["passed"] = False
            results["violations"].append(f"经营状态异常：{business_status}")
            results["reasons"].append(f"经营状态不符合准入标准：{business_status}")

        # 2. 成立时间检查（禁入）
        registered_years = self._parse_years(company_data.get("registered_years", "0"))
        if registered_years < 1:
            results["passed"] = False
            results["violations"].append(f"成立时间过短：{company_data.get('registered_years')}")
            results["reasons"].append("企业成立未满1年，经营稳定性不足")

        # 3. 注册资本检查（禁入）
        capital = self._parse_capital(company_data.get("registered_capital", "0"))
        if capital < 100:
            results["passed"] = False
            results["violations"].append(f"注册资本过低：{company_data.get('registered_capital')}")
            results["reasons"].append("注册资本低于100万元，抗风险能力不足")
        elif capital < 500:
            results["warnings"].append(f"注册资本偏低：{company_data.get('registered_capital')}")

        # 4. 行业禁入检查
        industry = company_data.get("industry", "")
        if any(word in industry for word in ["高污染", "高耗能", "虚拟货币", "非法金融"]):
            results["passed"] = False
            results["violations"].append(f"行业禁入：{industry}")
            results["reasons"].append("属于禁入行业")

        # 5. 员工人数检查（严重情况）
        employee_count = self._parse_employee_count(company_data.get("employee_count", "0"))
        if employee_count == 0:
            results["passed"] = False
            results["violations"].append(f"员工人数为0，疑似空壳企业")
            results["reasons"].append("员工人数为0，无实际经营迹象")
        elif employee_count < 5:
            results["warnings"].append(f"员工人数过少：{employee_count}人，可能存在经营稳定性风险")

        # 6. 营业收入检查
        annual_revenue = self._parse_revenue(company_data.get("annual_revenue", "0"))
        if annual_revenue < 0:
            results["warnings"].append(f"企业亏损：{company_data.get('annual_revenue')}")
            if annual_revenue < -3000:
                results["passed"] = False
                results["violations"].append(f"严重亏损：{company_data.get('annual_revenue')}")
                results["reasons"].append("年度亏损超过3000万元，财务风险极高")
        elif annual_revenue == 0:
            results["passed"] = False
            results["violations"].append("年营业收入为0，无实际经营活动")
            results["reasons"].append("无实际经营收入")
        elif annual_revenue < 500:
            results["warnings"].append(f"营业收入较低：{company_data.get('annual_revenue')}")

        # 7. 读取风险标志 risk_flags
        risk_flags = company_data.get("risk_flags", [])
        if risk_flags:
            for flag in risk_flags:
                # 检查是否有严重风险信号
                is_severe = any(severe in flag for severe in self.severe_risks)
                if is_severe:
                    results["passed"] = False
                    results["violations"].append(f"重大风险：{flag}")
                    results["reasons"].append(f"检测到重大风险信号：{flag}")

        # 8. 综合判断 - 如果违规项 >= 1，passed 即为 False
        if len(results["violations"]) >= 1:
            results["passed"] = False

        return results


rule_check_tool = RuleCheckTool()
