import json
import os
import re
import httpx
import random
from typing import Dict, Any, Optional
from services.llm_service import llm_service
from config.settings import settings

# 风险级别配置
RISK_CONFIG = {
    "low": {
        "registered_capital_range": (5000, 50000),
        "establishment_year_range": (2010, 2018),
        "employee_count_range": (100, 1000),
        "annual_revenue_range": (5000, 50000),
        "paid_capital_ratio": 0.8,
        "business_status": ["存续"],
        "has_negative_info": False,
        "risk_tags": []
    },
    "medium": {
        "registered_capital_range": (500, 5000),
        "establishment_year_range": (2015, 2021),
        "employee_count_range": (10, 100),
        "annual_revenue_range": (500, 5000),
        "paid_capital_ratio": 0.5,
        "business_status": ["存续", "开业"],
        "has_negative_info": False,
        "risk_tags": ["轻微风险", "关注"]
    },
    "high": {
        "registered_capital_range": (10, 500),
        "establishment_year_range": (2019, 2024),
        "employee_count_range": (0, 20),
        "annual_revenue_range": (-5000, 500),
        "paid_capital_ratio": 0.2,
        "business_status": ["存续", "开业", "歇业", "停业"],
        "has_negative_info": True,
        "risk_tags": ["经营异常", "诉讼纠纷", "亏损严重", "高风险"]
    }
}

# 常见姓氏列表
SURNAMES = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
            "徐", "孙", "马", "朱", "胡", "郭", "何", "林", "罗", "高"]

# 常见名字列表
FIRST_NAMES = ["伟", "强", "勇", "军", "敏", "磊", "涛", "鹏", "杰", "峰",
               "娜", "静", "丽", "敏", "芳", "燕", "婷", "雪", "梅", "兰"]

# 行业列表
INDUSTRIES = [
    {"name": "科技服务业", "keywords": ["科技", "软件", "信息", "互联网", "数据", "智能"]},
    {"name": "装备制造", "keywords": ["制造", "机械", "设备", "重工"]},
    {"name": "贸易流通", "keywords": ["贸易", "批发", "零售", "商贸"]},
    {"name": "建筑工程", "keywords": ["建筑", "工程", "建设", "施工"]},
    {"name": "物流运输", "keywords": ["物流", "运输", "快递", "仓储"]},
    {"name": "食品生产", "keywords": ["食品", "饮料", "餐饮", "烘焙"]},
    {"name": "医疗器械", "keywords": ["医药", "医疗", "器械", "健康"]},
    {"name": "电子制造", "keywords": ["电子", "芯片", "半导体", "元器件"]},
    {"name": "金融服务", "keywords": ["金融", "投资", "证券", "租赁"]}
]

# 城市列表
CITIES = [
    {"name": "北京", "district": ["朝阳区", "海淀区", "西城区", "东城区"]},
    {"name": "上海", "district": ["浦东新区", "徐汇区", "静安区", "黄浦区"]},
    {"name": "广州", "district": ["天河区", "越秀区", "白云区", "番禺区"]},
    {"name": "深圳", "district": ["南山区", "福田区", "宝安区", "龙华区"]},
    {"name": "杭州", "district": ["西湖区", "余杭区", "滨江区", "拱墅区"]},
    {"name": "南京", "district": ["玄武区", "鼓楼区", "建邺区", "江宁区"]}
]


def _parse_capital_to_wan(capital_str):
    """将 '5000万元' / '1.5亿元' 等格式转换为纯数字（万元）"""
    if not capital_str:
        return 0
    try:
        match = re.search(r'(\d+\.?\d*)', str(capital_str))
        if not match:
            return 0
        num = float(match.group(1))
        if "亿" in str(capital_str):
            return int(num * 10000)
        elif "万" in str(capital_str):
            return int(num)
        else:
            return int(num)
    except:
        return 0


def _parse_employee_count(emp_str):
    """将 '86人' 等格式转换为纯数字"""
    if not emp_str:
        return 0
    try:
        match = re.search(r'(\d+)', str(emp_str))
        if match:
            return int(match.group(1))
        return 0
    except:
        return 0


def _parse_revenue_to_wan(revenue_str):
    """将 '3500万元' / '亏损8500万元' 等格式转换为数字（万元）"""
    if not revenue_str:
        return 0
    try:
        if "亏" in str(revenue_str):
            match = re.search(r'(\d+\.?\d*)', str(revenue_str))
            if match:
                num = float(match.group(1))
                if "亿" in str(revenue_str):
                    return -int(num * 10000)
                return -int(num)
        else:
            match = re.search(r'(\d+\.?\d*)', str(revenue_str))
            if match:
                num = float(match.group(1))
                if "亿" in str(revenue_str):
                    return int(num * 10000)
                return int(num)
        return 0
    except:
        return 0


def _parse_years(years_str):
    """将 '5.5年' 转换为纯数字"""
    if not years_str:
        return 0
    try:
        match = re.search(r'(\d+\.?\d*)', str(years_str))
        if match:
            return float(match.group(1))
        return 0
    except:
        return 0


def _generate_random_name():
    """生成随机中文姓名"""
    surname = random.choice(SURNAMES)
    if random.random() > 0.5:
        name = random.choice(FIRST_NAMES) + random.choice(FIRST_NAMES)
    else:
        name = random.choice(FIRST_NAMES)
    return surname + name


def _generate_credit_code():
    """生成18位统一社会信用代码"""
    code = "91"
    for _ in range(16):
        code += str(random.randint(0, 9))
    return code


def _generate_address():
    """生成随机地址"""
    city = random.choice(CITIES)
    district = random.choice(city["district"])
    street_names = ["大道", "路", "街", "巷", "弄"]
    street = random.choice(["中心", "商务", "科技", "产业", "创新"]) + random.choice(street_names)
    number = str(random.randint(1, 999)) + "号"
    return f"{city['name']}{district}{street}{number}"


def _determine_industry(company_name):
    """根据企业名称判断行业"""
    for industry in INDUSTRIES:
        for keyword in industry["keywords"]:
            if keyword in company_name:
                return industry["name"]
    return random.choice(INDUSTRIES)["name"]


def _generate_business_scope(industry):
    """根据行业生成经营范围"""
    scope_templates = {
        "科技服务业": ["计算机软硬件开发", "信息技术咨询", "互联网技术服务", "数据处理", "人工智能技术开发"],
        "装备制造": ["机械设备制造", "零部件加工", "自动化设备研发", "工业机器人生产"],
        "贸易流通": ["货物进出口", "国内贸易", "批发零售", "供应链管理"],
        "建筑工程": ["建筑工程施工", "装饰装修", "市政工程", "园林绿化"],
        "物流运输": ["货物运输", "仓储服务", "物流配送", "供应链管理"],
        "食品生产": ["食品生产加工", "食品销售", "饮料制造", "餐饮服务"],
        "医疗器械": ["医疗器械销售", "医疗设备研发", "健康咨询", "医疗服务"],
        "电子制造": ["电子产品制造", "电子元器件生产", "半导体器件加工"],
        "金融服务": ["融资租赁", "投资咨询", "资产管理", "财务顾问"]
    }
    templates = scope_templates.get(industry, scope_templates["科技服务业"])
    selected = random.sample(templates, min(3, len(templates)))
    return "；".join(selected) + "。"


def _normalize_company_data(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """统一企业数据格式，注册资本/人/营收/年限转为纯数字"""
    if not company_data:
        return company_data

    # 添加数字字段（供后端逻辑使用）
    company_data["registered_capital_wan"] = _parse_capital_to_wan(company_data.get("registered_capital", ""))
    company_data["annual_revenue_wan"] = _parse_revenue_to_wan(company_data.get("annual_revenue", ""))
    company_data["employee_count_num"] = _parse_employee_count(company_data.get("employee_count", ""))
    company_data["registered_years_num"] = _parse_years(company_data.get("registered_years", ""))

    # 注册资本转为纯数字（前端字段名已包含"万元"）
    company_data["registered_capital"] = company_data["registered_capital_wan"]

    # 实缴资本也转为数字
    company_data["paid_capital"] = _parse_capital_to_wan(company_data.get("paid_capital", ""))

    # 年营收转为数字
    company_data["annual_revenue"] = company_data["annual_revenue_wan"]

    # 员工人数转为数字
    company_data["employee_count"] = company_data["employee_count_num"]

    # 注册年限转为数字
    company_data["registered_years"] = company_data["registered_years_num"]

    return company_data


class CompanySearchTool:
    def __init__(self):
        self.local_db_path = os.path.join(settings.SAMPLE_COMPANIES_DIR, "companies.json")
        self._load_local_db()
        # 聚合数据API配置
        self.juhe_api_key = settings.JUHE_API_KEY
        self.juhe_api_url = "http://api.juheapi.com/jhapi/search_company"

    def generate_simulated_data(self, company_name: str, risk_level: str = "medium") -> Dict[str, Any]:
        """根据风险级别生成模拟企业数据"""
        config = RISK_CONFIG.get(risk_level, RISK_CONFIG["medium"])
        
        # 根据风险级别生成企业属性
        registered_capital = random.randint(*config["registered_capital_range"])
        establishment_year = random.randint(*config["establishment_year_range"])
        employee_count = random.randint(*config["employee_count_range"])
        annual_revenue = random.randint(*config["annual_revenue_range"])
        
        # 计算注册年限
        registered_years = round(2025 - establishment_year + random.uniform(-0.5, 0.5), 1)
        
        # 计算实缴资本
        paid_capital = int(registered_capital * config["paid_capital_ratio"] * random.uniform(0.8, 1.2))
        
        # 确定行业
        industry = _determine_industry(company_name)
        
        # 生成地址和城市信息
        address = _generate_address()
        city = address[:2]
        
        # 生成负面信息（仅高风险企业）
        negative_info = []
        if config["has_negative_info"]:
            negative_options = [
                "存在经营异常记录",
                "有未结案诉讼纠纷",
                "连续三年亏损",
                "被列为被执行人",
                "税务异常",
                "行政处罚记录"
            ]
            negative_info = random.sample(negative_options, random.randint(1, 3))
        
        company_data = {
            "name": company_name,
            "credit_code": _generate_credit_code(),
            "legal_representative": _generate_random_name(),
            "registered_capital": registered_capital,
            "establishment_date": f"{establishment_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "business_status": random.choice(config["business_status"]),
            "industry": industry,
            "business_scope": _generate_business_scope(industry),
            "address": address,
            "registration_authority": f"{city}市市场监督管理局",
            "annual_revenue": annual_revenue,
            "employee_count": employee_count,
            "registered_years": registered_years,
            "industry_category": industry,
            "paid_capital": paid_capital,
            "company_type": random.choice(["有限责任公司", "股份有限公司"]),
            "social_insurance_count": max(0, int(employee_count * random.uniform(0.5, 0.9))),
            "negative_info": negative_info,
            "risk_tags": config["risk_tags"],
            "risk_level": risk_level,
            "data_source": "模拟数据"
        }
        
        return _normalize_company_data(company_data)

    def _load_local_db(self):
        if os.path.exists(self.local_db_path):
            with open(self.local_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.local_companies = data.get("companies", [])
        else:
            self.local_companies = []

    def search_local(self, company_name: str) -> Optional[Dict[str, Any]]:
        for company in self.local_companies:
            if company_name in company["name"] or company["name"] in company_name:
                result = company.copy()
                result["data_source"] = "本地样本数据"
                return _normalize_company_data(result)
        return None

    def list_local_companies(self) -> list:
        return [c["name"] for c in self.local_companies]

    async def search_juhe_api(self, company_name: str) -> Optional[Dict[str, Any]]:
        """调用聚合数据API查询企业信息"""
        if not self.juhe_api_key or not company_name.strip():
            return None

        try:
            params = {
                "key": self.juhe_api_key,
                "keyword": company_name,
                "type": "0",  # 0-模糊查询，1-精确查询
                "page": "1",
                "pagesize": "1"
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.juhe_api_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("error_code") != 0:
                    print(f"[DEBUG] Juhe API error: {data.get('reason')}")
                    return None

                result = data.get("result", {}).get("data", [])
                if not result:
                    return None

                company_info = result[0]
                return {
                    "name": company_info.get("companyName", company_name),
                    "credit_code": company_info.get("creditCode", ""),
                    "legal_representative": company_info.get("legalPerson", ""),
                    "registered_capital": company_info.get("registeredCapital", ""),
                    "establishment_date": company_info.get("establishDate", ""),
                    "business_status": company_info.get("status", "存续"),
                    "industry": company_info.get("industry", ""),
                    "business_scope": company_info.get("businessScope", ""),
                    "address": company_info.get("address", ""),
                    "registration_authority": company_info.get("registrationAuthority", ""),
                    "annual_revenue": company_info.get("annualRevenue", ""),
                    "employee_count": company_info.get("staffNum", ""),
                    "registered_years": self._calculate_years(company_info.get("establishDate", "")),
                    "industry_category": self._map_industry(company_info.get("industry", "")),
                    "paid_capital": company_info.get("paidInCapital", ""),
                    "company_type": company_info.get("companyType", ""),
                    "data_source": "工商公开数据"
                }

        except Exception as e:
            print(f"[DEBUG] Juhe API request failed: {str(e)}")
            return None

    def _calculate_years(self, establish_date: str) -> str:
        """根据成立日期计算注册年限"""
        if not establish_date:
            return "0年"
        try:
            from datetime import datetime
            date = datetime.strptime(establish_date, "%Y-%m-%d")
            now = datetime.now()
            years = (now - date).days / 365
            return f"{years:.1f}年"
        except:
            return "0年"

    def _map_industry(self, industry: str) -> str:
        """将行业映射到标准分类"""
        industry_mapping = {
            "科技": "科技服务业",
            "软件": "科技服务业",
            "信息": "科技服务业",
            "互联网": "科技服务业",
            "制造": "装备制造",
            "机械": "装备制造",
            "电子": "电子制造",
            "贸易": "贸易流通",
            "批发": "贸易流通",
            "零售": "贸易流通",
            "建筑": "建筑工程",
            "工程": "建筑工程",
            "物流": "物流运输",
            "运输": "物流运输",
            "食品": "食品生产",
            "医药": "医疗器械",
            "医疗": "医疗器械",
            "金融": "金融服务",
            "租赁": "金融服务"
        }
        for keyword, category in industry_mapping.items():
            if keyword in industry:
                return category
        return "其他"

    async def generate_demo_data(self, company_name: str) -> Dict[str, Any]:
        prompt = f"""请按工商标准格式为企业「{company_name}」生成结构化工商信息演示数据。要求：

1. 统一社会信用代码：格式91XXXXXXXXXXXXXXXXX（18位）
2. 法定代表人：随机生成合理中文姓名
3. 注册资本：合理估算，单位"万元"（如"5000万元"），不要带"人民币"
4. 成立日期：2015-2023年间合理日期（YYYY-MM-DD）
5. 经营状态：存续
6. 所属行业：根据企业名称判断
7. 经营范围：根据行业生成3-5条
8. 注册地址：中国一线城市合理地址
9. 登记机关：对应城市市场监督管理局
10. 年营业收入：合理估算，单位"万元"（如"3500万元"），不要带"人民币"
11. 员工人数：数字+人（如"86人"）
12. 注册年限：根据成立日期计算到2025年的年数（如"5.5年"）
13. 行业类别：科技服务业/装备制造/贸易流通/建筑工程/物流运输/食品生产/医疗器械/电子制造
14. 实缴资本：合理估算，单位"万元"
15. 工商类型：有限责任公司/股份有限公司
16. 参保人数：数字+人

请严格按以下JSON格式输出：

{{
  "name": "{company_name}",
  "credit_code": "",
  "legal_representative": "",
  "registered_capital": "",
  "establishment_date": "",
  "business_status": "存续",
  "industry": "",
  "business_scope": "",
  "address": "",
  "registration_authority": "",
  "annual_revenue": "",
  "employee_count": "",
  "registered_years": "",
  "industry_category": ""
}}

只输出JSON，不要其他文字。"""

        messages = [
            {"role": "system", "content": "你是一个工商信息数据生成助手，擅长根据企业名称生成合理的演示数据。数据格式严格JSON格式输出。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await llm_service.chat(messages, temperature=0.6)
            json_str = re.search(r'\{[\s\S]*\}', response)
            if json_str:
                company_data = json.loads(json_str.group())
                company_data["name"] = company_name
                company_data["data_source"] = "演示数据"
                return _normalize_company_data(company_data)
        except Exception as e:
            pass

        return _normalize_company_data({
            "name": company_name,
            "credit_code": "913100000000000000",
            "legal_representative": "张经理",
            "registered_capital": "1000万元",
            "establishment_date": "2020-01-01",
            "business_status": "存续",
            "industry": "商务服务业",
            "business_scope": "企业管理咨询；商务信息咨询；市场营销策划。",
            "address": "上海市浦东新区某某路88号",
            "registration_authority": "上海市市场监督管理局",
            "annual_revenue": "5000万元",
            "employee_count": "50人",
            "registered_years": "5.0年",
            "industry_category": "商务服务",
            "data_source": "演示数据"
        })

    async def search_company(self, company_name: str) -> Dict[str, Any]:
        # 1. 首先查询本地样本库（用于测试数据）
        local_result = self.search_local(company_name)
        if local_result:
            return local_result

        # 2. 根据企业名称特征和随机概率决定风险级别，生成参差不齐的模拟数据
        # 使用模拟数据，不调用真实工商数据API
        risk_level = self._determine_risk_level(company_name)
        return self.generate_simulated_data(company_name, risk_level)

    def _determine_risk_level(self, company_name: str) -> str:
        """根据企业名称特征和随机概率决定风险级别"""
        # 根据企业名称中的关键词初步判断
        high_risk_keywords = ["贸易行", "个体户", "工作室", "咨询中心", "服务部", "小店", "商行", "物流", "货运"]
        low_risk_keywords = ["集团", "股份", "科技", "控股", "有限责任", "有限公司", "科技股份", "技术", "有限", "工程", "建筑", "制造", "医疗", "电子", "食品", "器械"]
        
        for keyword in high_risk_keywords:
            if keyword in company_name:
                # 高风险关键词，70%概率为高风险，30%为中风险
                return "high" if random.random() < 0.7 else "medium"
        
        for keyword in low_risk_keywords:
            if keyword in company_name:
                # 低风险关键词，60%概率为低风险，30%为中风险，10%为高风险
                rand = random.random()
                if rand < 0.6:
                    return "low"
                elif rand < 0.9:
                    return "medium"
                else:
                    return "high"
        
        # 无明显特征，按概率分布分配风险级别
        # 30%低风险，40%中风险，30%高风险
        rand = random.random()
        if rand < 0.3:
            return "low"
        elif rand < 0.7:
            return "medium"
        else:
            return "high"


company_search_tool = CompanySearchTool()
