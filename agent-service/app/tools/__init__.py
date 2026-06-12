"""Agent 工具集合。
每个文件包含一个 BaseTool 子类，并暴露一个 `run` 函数供外部调用。
"""
from . import company_search      # 企业基础信息检索（模拟爱企查/企查查）
from . import risk_scoring        # 评分卡打分工具
from . import rule_checker        # 风控规则校验（准入/负面/行业）
from . import credit_limit        # 授信额度/利率/期限测算
from . import report_summary      # 综合尽调报告生成

# 注册到工具注册表，供 Agent 调度使用
from .registry import tool_registry
from .company_search import tool as company_search_tool
from .risk_scoring import tool as risk_scoring_tool
from .rule_checker import tool as rule_checker_tool
from .credit_limit import tool as credit_limit_tool
from .report_summary import tool as report_summary_tool

tool_registry.register(company_search_tool)
tool_registry.register(risk_scoring_tool)
tool_registry.register(rule_checker_tool)
tool_registry.register(credit_limit_tool)
tool_registry.register(report_summary_tool)

__all__ = [
    "tool_registry",
    "company_search",
    "risk_scoring",
    "rule_checker",
    "credit_limit",
    "report_summary",
]
