from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import uuid
import os

from agent.react_agent import react_agent
from services.database import DatabaseService
from config.settings import settings

app = FastAPI(title="小控风控 Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（React 前端构建产物放在这里）
# 目录结构（由 build.bat 生成）：
#   static/index.html     ← React SPA 入口
#   static/assets/*       ← React 的 JS / CSS / 图片等
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# /static/*  → 开发模式 & 通用静态资源
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# /assets/*  → React 构建产物（Vite 默认输出到 dist/assets）
# 当 credit_agent 被 npm run build 后，dist/assets/ 会被复制到 static/assets/
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")
if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

db = DatabaseService()


class CompanyRequest(BaseModel):
    company_name: str
    session_id: Optional[str] = None


class ApplicationUpdateRequest(BaseModel):
    credit_type: Optional[str] = None
    application_amount: Optional[float] = None
    application_period: Optional[str] = None
    fund_purpose: Optional[str] = None
    status: Optional[str] = None


@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "name": "小控风控 Agent API",
        "version": "1.0.0",
        "description": "企业信用风控决策 Agent 后端服务"
    }


@app.get("/api/companies/local")
async def get_local_companies():
    companies = react_agent.list_local_companies()
    db_companies = db.list_enterprises()
    all_companies = list(set(companies + db_companies))
    return {"companies": all_companies}


@app.get("/api/companies/search/{company_name}")
async def search_company(company_name: str):
    result = await react_agent.quick_search(company_name)
    return result


@app.post("/api/agent/analyze")
async def analyze_company(request: CompanyRequest):
    if not request.company_name or not request.company_name.strip():
        raise HTTPException(status_code=400, detail="请输入企业名称")

    session_id = request.session_id or str(uuid.uuid4())

    async def generate():
        try:
            async for step in react_agent.run_full_analysis(request.company_name, session_id):
                yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/applications")
async def list_applications():
    applications = db.list_credit_applications()
    return {"applications": applications}


@app.get("/api/applications/{enterprise_name}")
async def get_application(enterprise_name: str):
    app_data = db.get_credit_application(enterprise_name)
    if not app_data:
        raise HTTPException(status_code=404, detail="未找到授信申请记录")
    return app_data


@app.put("/api/applications/{application_id}")
async def update_application(application_id: int, request: ApplicationUpdateRequest):
    kwargs = {}
    if request.credit_type:
        kwargs["credit_type"] = request.credit_type
    if request.application_amount is not None:
        kwargs["application_amount"] = request.application_amount
    if request.application_period:
        kwargs["application_period"] = request.application_period
    if request.fund_purpose:
        kwargs["fund_purpose"] = request.fund_purpose

    status = request.status or "draft"
    success = db.update_application_status(application_id, status, **kwargs)
    if not success:
        raise HTTPException(status_code=404, detail="未找到授信申请记录")
    return {"success": True, "message": "更新成功"}


@app.post("/api/applications/{application_id}/submit")
async def submit_application(application_id: int):
    success = db.update_application_status(application_id, "审批中")
    if not success:
        raise HTTPException(status_code=404, detail="未找到授信申请记录")
    return {"success": True, "message": "已提交审批", "status": "审批中"}


@app.post("/api/applications/{application_id}/withdraw")
async def withdraw_application(application_id: int):
    success = db.update_application_status(application_id, "draft")
    if not success:
        raise HTTPException(status_code=404, detail="未找到授信申请记录")
    return {"success": True, "message": "已撤回", "status": "draft"}


# SPA 前端入口：其它所有未匹配到路由都返回 index.html
# 这样 React Router 可以在客户端处理路由（单页应用回退）
@app.get("/{full_path:path}")
async def spa_catch_all(full_path: str):
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        # 如果 static/index.html 是 React 构建产物或我们自己的入口
        return FileResponse(index_path)
    # 还没构建前端，返回提示页
    return {
        "service": "小控风控 Agent API",
        "version": "1.0.0",
        "tip": "请先在 credit_agent/ 目录执行 npm run build，再把 dist/ 复制到 static/ 即可启用前端"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
