"""
工具基类定义。
提供统一的工具执行接口和结果格式。
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel


class Result(BaseModel):
    """工具执行结果封装。"""
    ok: bool
    message: str
    data: Optional[Dict[str, Any]] = None

    def model_dump(self):
        """兼容旧版字典输出。"""
        return {
            "ok": self.ok,
            "message": self.message,
            "data": self.data or {}
        }


class BaseTool:
    """所有工具的基类。"""
    
    name: str = ""
    description: str = ""
    
    def execute(self, **kwargs) -> Result:
        """执行工具，返回结构化结果。"""
        raise NotImplementedError
    
    def __call__(self, **kwargs) -> Result:
        return self.execute(**kwargs)