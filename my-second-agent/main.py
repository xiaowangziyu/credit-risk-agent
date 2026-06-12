from flask import Flask, request, jsonify, Response, send_from_directory, abort
from flask_cors import CORS
import json
import asyncio
import uuid
import os

from agent.react_agent import react_agent
from services.database import DatabaseService
from config.settings import settings

app = Flask(__name__)
CORS(app)

# 配置静态文件目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
FRONTEND_DIST_DIR = os.path.join(os.path.dirname(BASE_DIR), "credit_agent", "dist")

# 初始化数据库
db = DatabaseService()


# ======== API 路由 ========

@app.route("/")
def index():
    """首页 - 返回前端页面"""
    # 优先使用前端构建产物
    if os.path.isdir(FRONTEND_DIST_DIR) and os.path.exists(os.path.join(FRONTEND_DIST_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    # 备用：返回 API 信息
    return jsonify({
        "name": "小控风控 Agent API",
        "version": "1.0.0",
        "description": "企业信用风控决策 Agent 后端服务",
        "api_endpoints": [
            "GET  /api/companies/local",
            "GET  /api/companies/search/<company_name>",
            "POST /api/agent/analyze",
            "GET  /api/applications",
            "GET  /api/applications/<enterprise_name>",
            "PUT  /api/applications/<application_id>",
            "POST /api/applications/<application_id>/submit",
            "POST /api/applications/<application_id>/withdraw"
        ]
    })


@app.route("/api/companies/local")
def get_local_companies():
    """获取本地企业列表"""
    try:
        companies = react_agent.list_local_companies()
        db_companies = db.list_enterprises()
        all_companies = list(set(companies + db_companies))
        return jsonify({"companies": all_companies})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/companies/search/<company_name>")
def search_company(company_name):
    """快速查询企业信息"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(react_agent.quick_search(company_name))
        loop.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/agent/analyze", methods=["POST"])
def analyze_company():
    """对企业进行完整风控分析（Server-Sent Events 流式响应）"""
    data = request.get_json() or {}
    company_name = data.get("company_name", "").strip()

    if not company_name:
        return jsonify({"error": "请输入企业名称"}), 400

    session_id = data.get("session_id") or str(uuid.uuid4())

    def generate():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_analysis():
            try:
                async for step in react_agent.run_full_analysis(company_name, session_id):
                    yield "data: " + json.dumps(step, ensure_ascii=False) + "\n\n"
            except Exception as e:
                yield "data: " + json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False) + "\n\n"

        try:
            gen = run_analysis()
            while True:
                try:
                    value = loop.run_until_complete(gen.__anext__())
                    yield value
                except StopAsyncIteration:
                    break
        finally:
            loop.close()

    return Response(
        generate(), mimetype="text/event-stream")


@app.route("/api/applications")
def list_applications():
    """获取所有授信申请"""
    try:
        applications = db.list_credit_applications()
        return jsonify({"applications": applications})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/applications/<enterprise_name>")
def get_application(enterprise_name):
    """获取指定企业的授信申请"""
    try:
        app_data = db.get_credit_application(enterprise_name)
        if not app_data:
            return jsonify({"error": "未找到授信申请记录"}), 404
        return jsonify(app_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/applications/<int:application_id>", methods=["PUT"])
def update_application(application_id):
    """更新授信申请"""
    try:
        data = request.get_json() or {}
        kwargs = {}

        if data.get("credit_type"):
            kwargs["credit_type"] = data["credit_type"]
        if data.get("application_amount") is not None:
            kwargs["application_amount"] = data["application_amount"]
        if data.get("application_period"):
            kwargs["application_period"] = data["application_period"]
        if data.get("fund_purpose"):
            kwargs["fund_purpose"] = data["fund_purpose"]

        status = data.get("status") or "draft"
        success = db.update_application_status(application_id, status, **kwargs)
        if not success:
            return jsonify({"error": "未找到授信申请记录"}), 404
        return jsonify({"success": True, "message": "更新成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/applications/<int:application_id>/submit", methods=["POST"])
def submit_application(application_id):
    """提交授信申请"""
    try:
        success = db.update_application_status(application_id, "审批中")
        if not success:
            return jsonify({"error": "未找到授信申请记录"}), 404
        return jsonify({"success": True, "message": "已提交审批", "status": "审批中"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/applications/<int:application_id>/withdraw", methods=["POST"])
def withdraw_application(application_id):
    """撤回授信申请"""
    try:
        success = db.update_application_status(application_id, "draft")
        if not success:
            return jsonify({"error": "未找到授信申请记录"}), 404
        return jsonify({"success": True, "message": "已撤回", "status": "draft"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======== 前端静态文件路由 ========

@app.route("/static/<path:filename>")
def serve_static(filename):
    """提供前端静态文件（JavaScript/CSS/图片等）"""
    # 优先从前端构建目录提供
    if os.path.isdir(FRONTEND_DIST_DIR):
        static_subdir = os.path.join(FRONTEND_DIST_DIR, "static")
        if os.path.exists(os.path.join(static_subdir, filename)):
            return send_from_directory(static_subdir, filename)
        # 如果直接在 dist 目录下查找
        if os.path.exists(os.path.join(FRONTEND_DIST_DIR, filename)):
            return send_from_directory(FRONTEND_DIST_DIR, filename)
    # 备用：从 static 目录提供
    if os.path.exists(os.path.join(STATIC_DIR, filename)):
        return send_from_directory(STATIC_DIR, filename)
    return abort(404)


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    """提供前端构建产物的 assets 目录"""
    assets_dir = os.path.join(FRONTEND_DIST_DIR, "assets")
    if os.path.exists(os.path.join(assets_dir, filename)):
        return send_from_directory(assets_dir, filename)
    return abort(404)


# SPA 回退路由：未匹配的路径返回 index.html
@app.route("/<path:path>")
def spa_catch_all(path):
    """单页应用回退路由"""
    if os.path.isdir(FRONTEND_DIST_DIR) and os.path.exists(os.path.join(FRONTEND_DIST_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIST_DIR, "index.html")
    # 备用：static 目录
    if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
        return send_from_directory(STATIC_DIR, "index.html")
    # 都不存在，返回 API 信息
    return jsonify({
        "service": "小控风控 Agent API",
        "version": "1.0.0",
        "tip": "请先在 credit_agent/ 目录执行 npm run build 构建前端"
    }), 404


if __name__ == "__main__":
    print(f"🚀 小控风控 Agent 服务启动于 http://{settings.HOST}:{settings.PORT}")
    if os.path.isdir(FRONTEND_DIST_DIR):
        print(f"✅ 前端静态文件服务已启用: {FRONTEND_DIST_DIR}")
    else:
        print(f"⚠️ 前端构建目录不存在: {FRONTEND_DIST_DIR}")
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.RELOAD)
