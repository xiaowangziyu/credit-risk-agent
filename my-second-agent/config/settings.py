import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    LLM_API_KEY = os.getenv("LLM_API_KEY", "your_api_key_here")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_API_URL = os.getenv("LLM_API_URL", "https://api.deepseek.com/v1/chat/completions")

    # 聚合数据API配置（企业工商信息查询）
    JUHE_API_KEY = os.getenv("JUHE_API_KEY", "")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agent.db")

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8001"))
    RELOAD = os.getenv("RELOAD", "true").lower() == "true"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
    SAMPLE_COMPANIES_DIR = os.path.join(BASE_DIR, "sample_companies")


settings = Settings()
