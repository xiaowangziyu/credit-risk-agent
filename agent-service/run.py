"""启动脚本。运行此文件启动 Agent 服务。"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动企业授信智能风控 Agent 服务...")
    print("📍 服务地址: http://localhost:8000")
    print("📖 接口文档: http://localhost:8000/docs")
    print("")
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)