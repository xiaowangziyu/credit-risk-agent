"""
工具注册表。
提供工具的注册、查找和调用能力。
"""
from typing import Dict, Type
from .base import BaseTool


class ToolRegistry:
    """工具注册表单例。"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """注册工具。"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> BaseTool:
        """获取工具。"""
        return self.tools.get(name)
    
    def list(self) -> list:
        """列出所有已注册工具。"""
        return list(self.tools.keys())
    
    def describe(self, name: str) -> dict:
        """获取工具描述。"""
        tool = self.get(name)
        if tool:
            return {
                "name": tool.name,
                "description": tool.description
            }
        return None
    
    def execute(self, name: str, **kwargs):
        """执行指定工具。"""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"工具 {name} 未注册")
        return tool.execute(**kwargs)


# 全局工具注册表
tool_registry = ToolRegistry()