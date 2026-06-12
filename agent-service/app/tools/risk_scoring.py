"""
评分卡打分工具。
根据企业基础信息计算综合风险评分。
"""
from typing import Dict
from .base import BaseTool, Result
from app.models import ScoreResult, ScoreItem
from app.services.storage import storage


class RiskScoringTool(BaseTool):
    """风险评分卡工具。"""
    
    name: str = "risk_scoring"
    description: str = """
    根据企业工商信息、司法风险、经营数据等进行多维度评分，输出综合得分与风险等级。
    输入：企业名称（需先调用 company_search 获取基础信息）。
    输出：结构化的评分结果，包含各维度得分、综合得分、风险等级。
    """
    
    def execute(self, company_name: str) -> Result:
        """执行评分。"""
        info = storage.get_company(company_name)
        if not info:
            return Result(
                ok=False,
                message=f"尚未抓取到「{company_name}」的基础信息，请先调用 company_search。",
                data={"need_next_step": "company_search", "target_company": company_name}
            )
        
        # 各维度评分
        items = []
        
        # 主体资质评分（30分）
        qual_score = self._calculate_qualification(info)
        items.append(ScoreItem(
            dimension="主体资质",
            weight=30,
            score=qual_score,
            max_score=30,
            reason=self._get_qualification_reason(info, qual_score)
        ))
        
        # 司法风险评分（30分）
        legal_score = self._calculate_legal(info)
        items.append(ScoreItem(
            dimension="司法风险",
            weight=30,
            score=legal_score,
            max_score=30,
            reason=self._get_legal_reason(info, legal_score)
        ))
        
        # 经营稳定性评分（25分）
        stable_score = self._calculate_stability(info)
        items.append(ScoreItem(
            dimension="经营稳定性",
            weight=25,
            score=stable_score,
            max_score=25,
            reason=self._get_stability_reason(info, stable_score)
        ))
        
        # 关联风险评分（15分）
        relation_score = self._calculate_relation(info)
        items.append(ScoreItem(
            dimension="关联风险",
            weight=15,
            score=relation_score,
            max_score=15,
            reason=self._get_relation_reason(info, relation_score)
        ))
        
        # 综合得分
        total_score = qual_score + legal_score + stable_score + relation_score
        
        # 风险等级
        if total_score >= 80:
            risk_level = "低风险"
        elif total_score >= 60:
            risk_level = "中风险"
        else:
            risk_level = "高风险"
        
        result = ScoreResult(
            company_name=company_name,
            total_score=total_score,
            risk_level=risk_level,
            score_items=items
        )
        
        storage.save_score(result)
        
        return Result(
            ok=True,
            message=f"评分完成：综合得分 {total_score} 分，风险等级：{risk_level}",
            data={
                "company_name": company_name,
                "total_score": total_score,
                "risk_level": risk_level,
                "dimensions": [item.model_dump() for item in items],
                "breakdown": {
                    "主体资质": qual_score,
                    "司法风险": legal_score,
                    "经营稳定性": stable_score,
                    "关联风险": relation_score
                }
            }
        )
    
    def _calculate_qualification(self, info) -> float:
        """计算主体资质得分。"""
        score = 25  # 基础分
        
        # 注册资本
        if info.registered_capital >= 5000:
            score += 3
        elif info.registered_capital >= 2000:
            score += 1
        
        # 实缴比例
        if info.paid_capital and info.registered_capital:
            ratio = info.paid_capital / info.registered_capital
            if ratio >= 0.8:
                score += 2
        
        return min(score, 30)
    
    def _get_qualification_reason(self, info, score) -> str:
        reasons = []
        if info.registered_capital >= 5000:
            reasons.append("注册资本充足")
        if info.paid_capital and info.registered_capital:
            if info.paid_capital / info.registered_capital >= 0.8:
                reasons.append("实缴比例高")
        return "; ".join(reasons) if reasons else "资质良好"
    
    def _calculate_legal(self, info) -> float:
        """计算司法风险得分。"""
        score = 30
        
        # 诉讼风险
        if info.litigation_risk == "有重大诉讼":
            score -= 15
        elif info.litigation_risk == "有诉讼":
            score -= 8
        
        # 法人失信
        if info.legal_person_risk == "有失信":
            score -= 20
        
        # 行政处罚
        if info.penalty_count and info.penalty_count > 2:
            score -= 10
        elif info.penalty_count and info.penalty_count > 0:
            score -= 5
        
        # 经营异常
        if info.abnormal_operation:
            score -= 15
        
        return max(0, score)
    
    def _get_legal_reason(self, info, score) -> str:
        reasons = []
        if info.litigation_risk == "有重大诉讼":
            reasons.append("存在重大诉讼")
        if info.legal_person_risk == "有失信":
            reasons.append("法人有失信记录")
        if info.penalty_count and info.penalty_count > 0:
            reasons.append(f"有{info.penalty_count}次行政处罚")
        if info.abnormal_operation:
            reasons.append("经营异常")
        return "; ".join(reasons) if reasons else "无重大司法风险"
    
    def _calculate_stability(self, info) -> float:
        """计算经营稳定性得分。"""
        score = 20
        
        # 成立年限
        import datetime
        if info.establish_date:
            try:
                establish = datetime.datetime.strptime(info.establish_date, "%Y-%m-%d")
                years = (datetime.datetime.now() - establish).days // 365
                if years >= 10:
                    score += 3
                elif years >= 5:
                    score += 1
            except:
                pass
        
        # 参保人数
        if info.insurance_count and info.insurance_count >= 100:
            score += 2
        
        # 营收规模
        if info.revenue and info.revenue >= 5000:
            score += 2
        elif info.revenue and info.revenue >= 2000:
            score += 1
        
        return min(score, 25)
    
    def _get_stability_reason(self, info, score) -> str:
        reasons = []
        if info.establish_date:
            try:
                import datetime
                establish = datetime.datetime.strptime(info.establish_date, "%Y-%m-%d")
                years = (datetime.datetime.now() - establish).days // 365
                if years >= 10:
                    reasons.append("成立年限长")
            except:
                pass
        if info.insurance_count and info.insurance_count >= 100:
            reasons.append("员工规模稳定")
        if info.revenue and info.revenue >= 5000:
            reasons.append("营收规模较大")
        return "; ".join(reasons) if reasons else "经营稳定"
    
    def _calculate_relation(self, info) -> float:
        """计算关联风险得分。"""
        score = 15
        
        # 行业支持度
        supported = {"科技服务业", "先进制造业", "绿色低碳产业", "现代物流", "生物医药"}
        if info.industry in supported:
            score += 0
        else:
            score -= 3
        
        return max(0, score)
    
    def _get_relation_reason(self, info, score) -> str:
        supported = {"科技服务业", "先进制造业", "绿色低碳产业", "现代物流", "生物医药"}
        if info.industry in supported:
            return "所属行业受支持"
        return "行业一般"


tool = RiskScoringTool()


def run(company_name: str) -> Dict:
    """兼容外部直接函数式调用。"""
    r = tool.execute(company_name=company_name)
    return r.model_dump()