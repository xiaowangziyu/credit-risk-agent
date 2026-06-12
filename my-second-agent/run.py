from main import app
from config.settings import settings

if __name__ == "__main__":
    print(f"🚀 小控风控 Agent 服务启动于 http://{settings.HOST}:{settings.PORT}")
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.RELOAD)
