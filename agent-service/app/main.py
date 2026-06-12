"""Agent 服务主入口。
对外暴露：
- POST /api/agent/search        企业基础信息检索（单步工具调用）
- POST /api/agent/score         评分卡打分
- POST /api/agent/rule          风控规则校验
- POST /api/agent/credit        授信测算
- POST /api/agent/report        综合尽调报告

可按需扩展为：
- 流式输出（Server-Sent Events）
- 外部 LLM 接入
- 会话记忆 / 消息历史
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import sys
import os

# 确保从项目根目录 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.storage import storage
from app.tools import company_search, risk_scoring, rule_checker, credit_limit, report_summary

app = FastAPI(title="企业授信智能风控 Agent", version="1.0.0")

# 允许前端访问，便于本地 / 云环境调试
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# 请求体
# ----------------------------------------------------------------------------
class CompanySearchRequest(BaseModel):
    company_name: str
    fuzzy: bool = False


class ScoreRequest(BaseModel):
    company_name: str


class RuleRequest(BaseModel):
    company_name: str
    category: str = "all"


class CreditRequest(BaseModel):
    company_name: str
    revenue: Optional[float] = None
    guarantee: str = "信用"
    industry: Optional[str] = None
    score: Optional[float] = None


class ReportRequest(BaseModel):
    company_name: str
    include_sections: Optional[List[str]] = None


# ----------------------------------------------------------------------------
# 基础响应辅助
# ----------------------------------------------------------------------------
def _warp(result: Dict[str, Any], cost_ms: float) -> Dict[str, Any]:
    return {"ok": result.get("ok", False), "data": result.get("data"),
            "message": result.get("message"), "cost_ms": cost_ms}


# ----------------------------------------------------------------------------
# 路由
# ----------------------------------------------------------------------------
@app.get("/")
def index():
    return {
        "name": "企业授信智能风控 Agent",
        "version": app.version,
        "tools": ["company_search", "risk_scoring", "rule_check", "credit_limit", "report_summary"],
        "companies_count": len(storage.list_companies()),
        "companies": storage.list_companies()[-10:],
    }


@app.post("/api/agent/search")
def api_search(req: CompanySearchRequest):
    """企业工商/司法/经营信息检索。"""
    start = datetime.now()
    result = company_search.run(req.company_name, fuzzy=req.fuzzy)
    return _warp(result, (datetime.now() - start).total_seconds() * 1000)


@app.post("/api/agent/score")
def api_score(req: ScoreRequest):
    """评分卡打分。需要先调用 search 获取基础信息。"""
    start = datetime.now()
    result = risk_scoring.run(req.company_name)
    return _warp(result, (datetime.now() - start).total_seconds() * 1000)


@app.post("/api/agent/rule")
def api_rule(req: RuleRequest):
    """准入/负面/行业规则校验。"""
    start = datetime.now()
    result = rule_checker.run(req.company_name, category=req.category)
    return _warp(result, (datetime.now() - start).total_seconds() * 1000)


@app.post("/api/agent/credit")
def api_credit(req: CreditRequest):
    """授信额度/利率/期限测算。"""
    start = datetime.now()
    result = credit_limit.run(
        req.company_name,
        revenue=req.revenue,
        guarantee=req.guarantee,
        industry=req.industry,
        score=req.score,
    )
    return _warp(result, (datetime.now() - start).total_seconds() * 1000)


@app.post("/api/agent/report")
def api_report(req: ReportRequest):
    """生成综合尽调报告（会自动读取此前工具产出）。"""
    start = datetime.now()
    result = report_summary.run(req.company_name, include_sections=req.include_sections)
    return _warp(result, (datetime.now() - start).total_seconds() * 1000)


@app.get("/api/agent/companies")
def list_companies():
    """列出已完成尽调的企业（演示/前端展示用）。"""
    names = storage.list_companies()
    return {"ok": True, "data": {"count": len(names), "companies": names}}


@app.get("/api/agent/company/{company_name}")
def get_company(company_name: str):
    """获取某企业完整信息（包含评分/规则/授信/报告）。"""
    info = storage.get_company(company_name)
    if not info:
        raise HTTPException(status_code=404, detail="未找到该企业")
    return {
        "ok": True,
        "data": {
            "info": info.model_dump(),
            "score": s.model_dump() if (s := storage.get_score(company_name)) else None,
            "rule": r.model_dump() if (r := storage.get_rule_result(company_name)) else None,
            "credit": c.model_dump() if (c := storage.get_credit(company_name)) else None,
            "report": rp.model_dump() if (rp := storage.get_report(company_name)) else None,
            "events": storage.list_events(company_name),
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
