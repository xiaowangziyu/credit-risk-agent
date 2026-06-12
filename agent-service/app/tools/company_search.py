"""
企业基础信息检索工具（模拟爱企查/企查查）。
提供企业工商、司法、经营信息的模拟查询能力。
"""
from typing import Dict, Optional
from .base import BaseTool, Result
from app.models import CompanyInfo
from app.services.storage import storage

# 模拟企业数据库
MOCK_COMPANIES = {
    "深圳市智联科技有限公司": {
        "company_name": "深圳市智联科技有限公司",
        "unified_code": "91440300MA5XXXXXXX",
        "company_type": "有限责任公司",
        "legal_person": "张三",
        "establish_date": "2015-03-20",
        "registered_capital": 5000,
        "paid_capital": 3000,
        "operation_status": "存续",
        "industry": "科技服务业",
        "insurance_count": 128,
        "revenue": 8500,
        "legal_person_risk": "无",
        "penalty_count": 0,
        "litigation_risk": "无",
        "abnormal_operation": False,
        "address": "深圳市南山区科技园南区",
    },
    "广州华南制造有限公司": {
        "company_name": "广州华南制造有限公司",
        "unified_code": "91440100MA5YYYYYY",
        "company_type": "有限责任公司",
        "legal_person": "李四",
        "establish_date": "2012-08-15",
        "registered_capital": 8000,
        "paid_capital": 6000,
        "operation_status": "存续",
        "industry": "先进制造业",
        "insurance_count": 256,
        "revenue": 12000,
        "legal_person_risk": "无",
        "penalty_count": 1,
        "litigation_risk": "无",
        "abnormal_operation": False,
        "address": "广州市黄埔区开发区",
    },
    "深圳蓝天物流股份有限公司": {
        "company_name": "深圳蓝天物流股份有限公司",
        "unified_code": "91440300MA5ZZZZZZ",
        "company_type": "股份有限公司",
        "legal_person": "王五",
        "establish_date": "2008-11-30",
        "registered_capital": 10000,
        "paid_capital": 10000,
        "operation_status": "存续",
        "industry": "现代物流",
        "insurance_count": 189,
        "revenue": 15000,
        "legal_person_risk": "无",
        "penalty_count": 0,
        "litigation_risk": "无重大诉讼",
        "abnormal_operation": False,
        "address": "深圳市宝安区物流园",
    },
    "东莞绿源能源科技有限公司": {
        "company_name": "东莞绿源能源科技有限公司",
        "unified_code": "91441900MA5AAAAAA",
        "company_type": "有限责任公司",
        "legal_person": "赵六",
        "establish_date": "2018-05-20",
        "registered_capital": 3000,
        "paid_capital": 2000,
        "operation_status": "存续",
        "industry": "绿色低碳产业",
        "insurance_count": 67,
        "revenue": 4500,
        "legal_person_risk": "无",
        "penalty_count": 0,
        "litigation_risk": "无",
        "abnormal_operation": False,
        "address": "东莞市松山湖高新区",
    },
    "北京中关村软件园科技": {
        "company_name": "北京中关村软件园科技",
        "unified_code": "91110108MA5BBBBBB",
        "company_type": "有限责任公司",
        "legal_person": "孙七",
        "establish_date": "2010-01-10",
        "registered_capital": 6000,
        "paid_capital": 4500,
        "operation_status": "存续",
        "industry": "科技服务业",
        "insurance_count": 145,
        "revenue": 9200,
        "legal_person_risk": "无",
        "penalty_count": 0,
        "litigation_risk": "无",
        "abnormal_operation": False,
        "address": "北京市海淀区中关村",
    },
    "上海自贸区供应链管理": {
        "company_name": "上海自贸区供应链管理",
        "unified_code": "91310115MA5CCCCCC",
        "company_type": "有限责任公司",
        "legal_person": "周八",
        "establish_date": "2014-07-01",
        "registered_capital": 12000,
        "paid_capital": 8000,
        "operation_status": "存续",
        "industry": "现代物流",
        "insurance_count": 210,
        "revenue": 18000,
        "legal_person_risk": "无",
        "penalty_count": 0,
        "litigation_risk": "无",
        "abnormal_operation": False,
        "address": "上海市浦东新区自贸区",
    },
}


class CompanySearchTool(BaseTool):
    """企业基础信息检索工具。"""
    
    name: str = "company_search"
    description: str = """
    检索企业工商基础信息（统一社会信用代码、法人、注册资本、经营状态等）、司法风险信息（诉讼、失信记录等）、经营数据（参保人数、营收规模等）。
    输入：企业名称（精确匹配或模糊匹配）。
    输出：结构化的企业信息对象。
    """
    
    def execute(self, company_name: str, fuzzy: bool = False) -> Result:
        """检索企业信息。"""
        # 精确匹配
        if company_name in MOCK_COMPANIES:
            data = MOCK_COMPANIES[company_name]
            company_info = CompanyInfo(**data)
            storage.save_company(company_info)
            return Result(
                ok=True,
                message=f"成功检索到企业「{company_name}」的基础信息",
                data={
                    "company_name": company_name,
                    "info": data,
                    "data_source": "模拟工商数据库"
                }
            )
        
        # 模糊匹配
        if fuzzy:
            matches = [name for name in MOCK_COMPANIES.keys() if company_name in name]
            if matches:
                return Result(
                    ok=True,
                    message=f"找到 {len(matches)} 个匹配结果",
                    data={
                        "company_name": company_name,
                        "matches": matches,
                        "data_source": "模拟工商数据库"
                    }
                )
        
        return Result(
            ok=False,
            message=f"未找到企业「{company_name}」的信息",
            data={"company_name": company_name}
        )


tool = CompanySearchTool()


def run(company_name: str, fuzzy: bool = False) -> Dict:
    """兼容外部直接函数式调用。"""
    r = tool.execute(company_name=company_name, fuzzy=fuzzy)
    return r.model_dump()


def suggest_companies() -> list:
    """返回推荐的企业列表（用于前端下拉选择）。"""
    return list(MOCK_COMPANIES.keys())