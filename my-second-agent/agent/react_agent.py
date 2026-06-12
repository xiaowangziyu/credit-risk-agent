import json
import re
from typing import Dict, Any, List, Optional, AsyncIterator

from tools.search_company import company_search_tool
from tools.check_rules import rule_check_tool
from tools.create_scorecard import scorecard_tool
from tools.calculate_credit import credit_calculator
from tools.read_knowledge_base import knowledge_base_reader
from tools.generate_report import report_generator
from services.llm_service import llm_service
from config.settings import settings
from agent.prompts import SYSTEM_PROMPT, get_user_prompt


class ReActAgent:
    def __init__(self):
        self.max_steps = 6
        self.available_tools = {
            "search_company": self._tool_search_company,
            "check_rules": self._tool_check_rules,
            "create_scorecard": self._tool_create_scorecard,
            "calculate_credit": self._tool_calculate_credit,
            "read_knowledge_base": self._tool_read_knowledge_base,
        }
        # 用于在工具间传递上下文
        self.context_store: Dict[str, Any] = {}

    # ======== 工具实现 ========
    async def _tool_search_company(self, company_name: str) -> Dict[str, Any]:
        result = await company_search_tool.search_company(company_name)
        self.context_store["company_data"] = result
        return result

    async def _tool_check_rules(self, company_data: Dict[str, Any] = None) -> Dict[str, Any]:
        data = company_data or self.context_store.get("company_data")
        if not data:
            return {"error": "缺少企业信息，请先调用 search_company"}
        result = rule_check_tool.check_rules(data)
        self.context_store["rule_result"] = result
        return result

    async def _tool_create_scorecard(self, company_data: Dict[str, Any] = None,
                                      rule_result: Dict[str, Any] = None) -> Dict[str, Any]:
        data = company_data or self.context_store.get("company_data")
        rules = rule_result or self.context_store.get("rule_result")
        if not data:
            return {"error": "缺少企业信息，请先调用 search_company"}
        if not rules:
            rules = rule_check_tool.check_rules(data)
            self.context_store["rule_result"] = rules
        scorecard = await scorecard_tool.create_scorecard(data, rules)
        self.context_store["scorecard"] = scorecard
        return scorecard

    async def _tool_calculate_credit(self, company_data: Dict[str, Any] = None,
                                      scorecard: Dict[str, Any] = None) -> Dict[str, Any]:
        data = company_data or self.context_store.get("company_data")
        score = scorecard or self.context_store.get("scorecard")
        if not data or not score:
            return {"error": "缺少企业信息或评分结果，请先调用 search_company 和 create_scorecard"}
        credit = await credit_calculator.calculate_credit(data, score)
        self.context_store["credit_suggestion"] = credit
        return credit

    async def _tool_read_knowledge_base(self, topic: str = "rules") -> Dict[str, Any]:
        content = knowledge_base_reader.read_document(f"{topic}.md")
        if not content:
            all_content = knowledge_base_reader.read_all()
            return {"topics": list(all_content.keys()), "note": "未找到指定文档，请尝试: rules, scorecard, credit"}
        return {"topic": topic, "content_preview": content[:500] + "..."}

    # ======== LLM 输出解析 ========
    def _parse_llm_output(self, text: str) -> Dict[str, Any]:
        """
        解析 LLM 的输出，提取 Thought / Action / Final Answer
        """
        result = {"thought": "", "action": None, "final": None}

        # 提取分析（Thought）
        analysis_match = re.search(r"##\s*分析\s*\n(.*?)(?=\n##\s|$)", text, re.DOTALL)
        if analysis_match:
            result["thought"] = analysis_match.group(1).strip()

        # 提取工具调用（Action）
        action_match = re.search(r"##\s*工具?调用\s*\n(.*?)(?=\n##\s|$)", text, re.DOTALL)
        if action_match:
            action_text = action_match.group(1).strip()
            # 提取JSON
            json_match = re.search(r"\{[\s\S]*\}", action_text)
            if json_match:
                try:
                    action_obj = json.loads(json_match.group())
                    if "tool" in action_obj:
                        result["action"] = action_obj
                except json.JSONDecodeError:
                    # 尝试清理
                    cleaned = re.sub(r"//.*?\n", "\n", json_match.group())
                    try:
                        result["action"] = json.loads(cleaned)
                    except:
                        result["action"] = None

        # 提取最终回答
        final_match = re.search(r"##\s*最终回答\s*\n(.*?)$", text, re.DOTALL)
        if final_match:
            final_text = final_match.group(1).strip()
            json_match = re.search(r"\{[\s\S]*\}", final_text)
            if json_match:
                try:
                    result["final"] = json.loads(json_match.group())
                except:
                    result["final"] = {"summary": final_text, "key_points": []}
            else:
                result["final"] = {"summary": final_text, "key_points": []}

        # Fallback：如果没找到结构化标记，尝试从全文提取
        if not result["thought"] and not result["action"] and not result["final"]:
            # 看有没有直接的JSON
            json_match = re.search(r"\{[\s\S]*\"tool\"[\s\S]*\}", text)
            if json_match:
                try:
                    result["action"] = json.loads(json_match.group())
                    result["thought"] = text[:json_match.start()].strip()
                except:
                    pass
            # 否则当做最终文本
            if not result["action"]:
                result["final"] = {"summary": text.strip(), "key_points": []}

        return result

    def _validate_action(self, action: Dict[str, Any]) -> Optional[str]:
        """验证工具调用是否合法"""
        if not action or "tool" not in action:
            return "未识别到工具调用"

        tool_name = action["tool"]
        if tool_name not in self.available_tools:
            return f"未知工具: {tool_name}"

        return None

    # ======== 工具定义（OpenAI Function Calling 格式） ========
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """定义工具的 schema，供 LLM function calling 使用"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_company",
                    "description": "查询企业的工商基础信息，包括注册资本、成立时间、经营状态、行业、年营收等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_name": {
                                "type": "string",
                                "description": "企业名称"
                            }
                        },
                        "required": ["company_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_rules",
                    "description": "对企业进行禁入规则校验，检查是否满足准入条件",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_scorecard",
                    "description": "创建信用评分卡，对企业进行综合评分",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_credit",
                    "description": "根据评分结果计算授信建议额度、期限、类型",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_knowledge_base",
                    "description": "读取风控知识库文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "知识库主题，如 rules/scorecard/credit"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]

    # ======== 主循环 ========
    async def run_full_analysis(self, company_name: str, session_id: str = None,
                                user_message: str = None) -> AsyncIterator[Dict[str, Any]]:
        """
        真正的 ReAct 循环（由 LLM 驱动的动态 while 循环）：
        Thought → Action → Observation → (LLM 决定继续/结束) → Final Answer

        核心逻辑：
        while True:
            1. LLM 分析当前状态，输出 Thought
            2. LLM 决定：调用工具 OR 输出最终答案
            3. 如果调用工具 → 执行工具 → 观察结果 → 继续循环
            4. 如果输出最终答案 → 退出循环

        【调试增强】全程追踪执行模式：
        - execution_mode: "llm" (LLM驱动) | "fallback" (完整降级流) | "fallback_complete" (降级补全流)
        - 每个关键分支会向前端发送 debug 类型 SSE 事件，前端可直接看到
        """
        self.context_store = {"company_name": company_name}
        conversation_history: List[str] = []
        tools_called: List[str] = []  # 追踪已调用的工具
        step = 0

        # 【调试】执行模式和降级原因追踪
        execution_mode = "llm"  # 初始假设走 LLM 流
        fallback_reason = None
        llm_call_count = 0
        llm_tool_call_count = 0

        yield {
            "type": "start",
            "content": f"开始对企业「{company_name}」进行风控尽调分析...",
            "step": 0
        }

        # 调试：打印配置 + 向前端推送配置信息
        print(f"[DEBUG] LLM_API_KEY: {settings.LLM_API_KEY[:10]}..." if settings.LLM_API_KEY else "[DEBUG] LLM_API_KEY: NOT SET")
        print(f"[DEBUG] LLM_MODEL: {settings.LLM_MODEL}")
        print(f"[DEBUG] LLM_API_URL: {settings.LLM_API_URL}")

        yield {
            "type": "debug",
            "content": f"🔍 [诊断] 初始化完成，尝试走 LLM 驱动模式 (model={settings.LLM_MODEL}, url={settings.LLM_API_URL})",
            "step": 0,
            "_execution_mode": execution_mode,
            "_llm_config": {
                "model": settings.LLM_MODEL,
                "api_url": settings.LLM_API_URL,
                "has_api_key": bool(settings.LLM_API_KEY)
            }
        }

        # 初始化消息
        system_msg = SYSTEM_PROMPT
        user_msg = get_user_prompt(company_name, user_message)

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]

        tool_definitions = self._get_tool_definitions()

        # ===== ReAct 核心循环：由 LLM 决定何时结束 =====
        while step < self.max_steps:
            step += 1

            # 给 LLM 看历史上下文
            self._inject_history_to_messages(messages, conversation_history)

            # ===== 1. Thought: LLM 思考下一步 =====
            yield {
                "type": "thought",
                "content": f"思考第 {step} 步...",
                "step": step
            }

            try:
                # 使用 function calling 调用 LLM
                llm_call_count += 1
                print(f"[DEBUG] Step {step}: 正在调用 LLM (第 {llm_call_count} 次)...")
                llm_message = await llm_service.chat_with_function(
                    messages, tool_definitions, temperature=0.5
                )
                print(f"[DEBUG] Step {step}: LLM 返回类型={type(llm_message)}, keys={list(llm_message.keys()) if isinstance(llm_message, dict) else 'N/A'}")

                # 安全检查：确保 llm_message 是有效字典
                if not isinstance(llm_message, dict):
                    fallback_reason = f"LLM 返回格式不是 dict，实际是: {type(llm_message).__name__}"
                    execution_mode = "fallback"
                    yield {
                        "type": "debug",
                        "content": f"⚠️ [诊断-降级] 触发降级: {fallback_reason}",
                        "step": step,
                        "_execution_mode": execution_mode,
                        "_fallback_reason": fallback_reason
                    }
                    yield {
                        "type": "thought",
                        "content": f"LLM 返回格式错误，切换到降级模式",
                        "step": step
                    }
                    async for fallback_step in self._fallback_flow(company_name, step):
                        yield fallback_step
                    return

                # 【调试】LLM 响应摘要
                llm_content = llm_message.get("content") or ""
                llm_tool_calls_raw = llm_message.get("tool_calls") or []
                yield {
                    "type": "debug",
                    "content": f"🔍 [诊断-LLM响应#{llm_call_count}] 内容长度={len(llm_content)} 字符, tool_calls 数量={len(llm_tool_calls_raw)}",
                    "step": step,
                    "_execution_mode": execution_mode,
                    "_llm_content_preview": llm_content[:200] if llm_content else "(空)",
                    "_llm_tool_calls": [
                        {
                            "name": tc.get("function", {}).get("name"),
                            "args": tc.get("function", {}).get("arguments")
                        }
                        for tc in (llm_tool_calls_raw if isinstance(llm_tool_calls_raw, list) else [])
                    ]
                }

                # 提取 LLM 的思考内容
                content = llm_message.get("content") or ""
                if content:
                    yield {
                        "type": "thought_detail",
                        "content": content,
                        "step": step
                    }

                # 提取工具调用
                tool_calls = llm_message.get("tool_calls") or []
                if not tool_calls:
                    # 没有工具调用，检查是否可以结束
                    final_text = llm_message.get("content", "") or ""

                    # 检查是否已调用关键工具
                    has_basic_info = self.context_store.get("company_data") is not None
                    has_check = self.context_store.get("rule_result") is not None
                    has_score = self.context_store.get("scorecard") is not None
                    has_credit = self.context_store.get("credit_suggestion") is not None

                    # 如果已调用所有关键工具，可以结束
                    if has_basic_info and has_check and has_score and has_credit:
                        yield {
                            "type": "debug",
                            "content": f"✅ [诊断] 已完成 4 个关键工具 (search/check/score/credit)，LLM 决定结束，进入最终报告",
                            "step": step,
                            "_execution_mode": execution_mode,
                            "_llm_calls_total": llm_call_count,
                            "_tool_calls_total": llm_tool_call_count
                        }
                        yield {
                            "type": "action_detail",
                            "content": "LLM 判断信息已充分，准备生成最终报告...",
                            "step": step
                        }
                        break

                    # 如果缺少关键工具，强制进入降级模式补全流程
                    if has_basic_info and has_check and not has_score:
                        fallback_reason = "LLM 未继续调用工具（缺少 scorecard），触发降级补全流程"
                        execution_mode = "fallback_complete"
                        yield {
                            "type": "debug",
                            "content": f"⚠️ [诊断-降级补全] {fallback_reason}",
                            "step": step,
                            "_execution_mode": execution_mode,
                            "_fallback_reason": fallback_reason,
                            "_context_state": {
                                "has_company_data": has_basic_info,
                                "has_rule_result": has_check,
                                "has_scorecard": has_score,
                                "has_credit": has_credit
                            }
                        }
                        async for fallback_step in self._fallback_flow_complete(company_name, step, self.context_store):
                            yield fallback_step
                        return

                    if has_basic_info and has_check and has_score and not has_credit:
                        fallback_reason = "LLM 未继续调用工具（缺少 credit），触发降级补全流程"
                        execution_mode = "fallback_complete"
                        yield {
                            "type": "debug",
                            "content": f"⚠️ [诊断-降级补全] {fallback_reason}",
                            "step": step,
                            "_execution_mode": execution_mode,
                            "_fallback_reason": fallback_reason
                        }
                        async for fallback_step in self._fallback_flow_complete(company_name, step, self.context_store):
                            yield fallback_step
                        return

                    # 如果有企业信息但还没校验，给提示
                    if has_basic_info and not has_check:
                        hint = "已获取企业信息，请调用 check_rules 进行规则校验。"
                    elif has_check and not has_score:
                        hint = "规则校验已完成，请调用 create_scorecard 进行评分。"
                    elif has_score and not has_credit:
                        hint = "评分已完成，请调用 calculate_credit 计算授信建议。"
                    else:
                        hint = "请通过 function calling 调用工具继续分析。"

                    yield {
                        "type": "debug",
                        "content": f"🔍 [诊断] LLM 未输出 tool_calls，上下文状态: company_data={has_basic_info}, rule_result={has_check}, scorecard={has_score}, credit={has_credit}。将给 LLM 补充提示后重试。",
                        "step": step,
                        "_execution_mode": execution_mode
                    }
                    yield {
                        "type": "observation",
                        "content": f"LLM 未输出工具调用。提示：{hint}",
                        "step": step
                    }

                    messages.append({
                        "role": "user",
                        "content": f"已获取的信息：企业信息={'有' if has_basic_info else '无'}, 规则校验={'已通过' if has_check else '未执行'}\n\n{hint}\n\n请通过 function calling 继续调用下一个工具。"
                    })
                    continue

                # ===== 2. Action: 执行工具 =====
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]

                    # 追踪已调用的工具
                    if function_name not in tools_called:
                        tools_called.append(function_name)
                    llm_tool_call_count += 1

                    try:
                        function_args = json.loads(tool_call["function"]["arguments"])
                    except (json.JSONDecodeError, KeyError):
                        function_args = {}

                    yield {
                        "type": "action",
                        "content": f"调用工具: {function_name}",
                        "tool": function_name,
                        "tool_input": function_args,
                        "step": step
                    }

                    # 执行工具
                    try:
                        tool_func = self.available_tools.get(function_name)
                        if not tool_func:
                            tool_result = {"error": f"未知工具: {function_name}"}
                        elif function_name == "search_company":
                            actual_name = function_args.get("company_name") or company_name
                            tool_result = await tool_func(actual_name)
                        elif function_name == "read_knowledge_base":
                            topic = function_args.get("topic", "rules")
                            tool_result = await tool_func(topic)
                        else:
                            tool_result = await tool_func()
                    except Exception as e:
                        tool_result = {"error": f"工具执行异常: {str(e)}"}

                    # 记录到对话历史
                    observation_text = self._summarize_tool_result(function_name, tool_result)
                    conversation_history.append(f"[Step {step}] Tool: {function_name} → {observation_text}")

                    # 把工具调用和结果添加到 messages，供 LLM 下一步参考
                    messages.append({
                        "role": "assistant",
                        "content": llm_message.get("content", ""),
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

                    # 更新context_store
                    if function_name == "search_company":
                        self.context_store["company_data"] = tool_result
                    elif function_name == "check_rules":
                        self.context_store["rule_result"] = tool_result
                    elif function_name == "create_scorecard":
                        self.context_store["scorecard"] = tool_result
                    elif function_name == "calculate_credit":
                        self.context_store["credit_suggestion"] = tool_result

                    # ===== 3. Observation: 观察结果 =====
                    yield {
                        "type": "observation",
                        "content": observation_text,
                        "data": self._sanitize_for_yield(function_name, tool_result),
                        "tool": function_name,
                        "step": step
                    }

                    # 业务规则：规则校验未通过则提前终止
                    if function_name == "check_rules" and tool_result and not tool_result.get("passed", True):
                        yield {
                            "type": "thought",
                            "content": "企业未通过禁入规则校验，终止分析",
                            "step": step
                        }
                        # 生成禁入报告并返回，不继续评分
                        report = report_generator.generate_report(
                            self.context_store.get("company_data", {}),
                            tool_result,
                            {"total_score": 0, "risk_level": "高风险", "dimensions": []},
                            {"suggested_amount": "不建议授信"}
                        )
                        yield {
                            "type": "final",
                            "content": "风控尽调完成（企业被禁入）",
                            "result": {
                                "company": self.context_store.get("company_data", {}),
                                "rule_check": tool_result,
                                "scorecard": None,
                                "credit_suggestion": None,
                                "report": report,
                                "status": "rejected"
                            },
                            "step": step
                        }
                        return  # 直接返回，不继续执行

            except Exception as e:
                # LLM 调用失败，切换到降级模式
                fallback_reason = f"LLM 调用异常: {type(e).__name__}: {str(e)}"
                execution_mode = "fallback"
                yield {
                    "type": "debug",
                    "content": f"⚠️ [诊断-降级] {fallback_reason}",
                    "step": step,
                    "_execution_mode": execution_mode,
                    "_fallback_reason": fallback_reason,
                    "_llm_calls_total": llm_call_count,
                    "_tool_calls_total": llm_tool_call_count
                }
                yield {
                    "type": "thought",
                    "content": f"LLM 调用失败: {str(e)}，切换到降级模式",
                    "step": step
                }
                async for fallback_step in self._fallback_flow(company_name, step):
                    yield fallback_step
                return

        # ===== 6. Final Answer: 生成最终报告 =====
        yield {
            "type": "debug",
            "content": f"🏁 [诊断-流程结束] 执行模式={execution_mode}, LLM 调用次数={llm_call_count}, 工具调用次数={llm_tool_call_count}" if execution_mode == "llm" else f"🏁 [诊断-流程结束] 执行模式={execution_mode}, 降级原因={fallback_reason}",
            "step": step,
            "_execution_mode": execution_mode,
            "_fallback_reason": fallback_reason,
            "_llm_calls_total": llm_call_count,
            "_tool_calls_total": llm_tool_call_count
        }
        yield {
            "type": "thought",
            "content": "分析循环结束，生成综合报告...",
            "step": step
        }

        company_data = self.context_store.get("company_data")
        rule_result = self.context_store.get("rule_result")
        scorecard = self.context_store.get("scorecard")
        credit_suggestion = self.context_store.get("credit_suggestion")

        report = report_generator.generate_report(
            company_data or {"name": company_name},
            rule_result or {"passed": True, "violations": []},
            scorecard or {"total_score": 0, "risk_level": "未知", "dimensions": []},
            credit_suggestion or {"suggested_amount": "请补充数据", "amount_range": "请补充数据"}
        )

        yield {
            "type": "final",
            "content": "风控尽调完成",
            "result": {
                "company": company_data,
                "rule_check": rule_result,
                "scorecard": scorecard,
                "credit_suggestion": credit_suggestion,
                "report": report,
                "status": "completed"
            },
            "step": step
        }

    async def _fallback_flow(self, company_name: str, start_step: int) -> AsyncIterator[Dict[str, Any]]:
        """
        降级模式：LLM 不可用时，按固定逻辑展示 ReAct 流程
        """
        step = start_step

        # 1. 查企业信息
        yield {"type": "thought", "content": "首先查询企业基础工商信息...", "step": step}
        yield {"type": "action", "content": "调用工具: search_company", "tool": "search_company", "step": step}
        company_data = company_search_tool.search_local(company_name)
        if not company_data:
            company_data = await company_search_tool.generate_demo_data(company_name)
        self.context_store["company_data"] = company_data
        yield {
            "type": "observation",
            "content": f"获取企业信息成功：{company_data.get('name', company_name)}，来源：{company_data.get('data_source', '本地库')}",
            "data": company_data,
            "step": step
        }
        step += 1

        # 2. 规则校验
        yield {"type": "thought", "content": "企业信息已获取，接下来进行禁入规则校验...", "step": step}
        yield {"type": "action", "content": "调用工具: check_rules", "tool": "check_rules", "step": step}
        rule_result = rule_check_tool.check_rules(company_data) if company_data else None
        self.context_store["rule_result"] = rule_result
        rule_passed = rule_result.get("passed", True) if rule_result else False
        yield {
            "type": "observation",
            "content": f"规则校验{'通过' if rule_passed else '未通过'}，违规项：{len(rule_result.get('violations', []) if rule_result else [])} 条",
            "data": rule_result,
            "step": step
        }
        step += 1

        if not rule_passed:
            report = report_generator.generate_report(
                company_data, rule_result,
                {"total_score": 0, "risk_level": "高风险", "dimensions": []},
                {"suggested_amount": "不建议授信"}
            )
            yield {
                "type": "final",
                "content": "风控尽调完成（企业被禁入）",
                "result": {
                    "company": company_data,
                    "rule_check": rule_result,
                    "scorecard": None,
                    "credit_suggestion": None,
                    "report": report,
                    "status": "rejected"
                },
                "step": step
            }
            return

        # 3. 评分卡
        yield {"type": "thought", "content": "规则校验通过，接下来创建评分卡，综合评估企业资质...", "step": step}
        yield {"type": "action", "content": "调用工具: create_scorecard", "tool": "create_scorecard", "step": step}
        scorecard = await scorecard_tool.create_scorecard(company_data, rule_result)
        self.context_store["scorecard"] = scorecard
        yield {
            "type": "observation",
            "content": f"评分完成：综合 {scorecard.get('total_score', 0)} 分，{scorecard.get('risk_level', '未知')}",
            "data": scorecard,
            "step": step
        }
        step += 1

        # 4. 授信建议
        yield {"type": "thought", "content": "评分已出，最后结合企业信息给出授信建议...", "step": step}
        yield {"type": "action", "content": "调用工具: calculate_credit", "tool": "calculate_credit", "step": step}
        credit_suggestion = await credit_calculator.calculate_credit(company_data, scorecard)
        self.context_store["credit_suggestion"] = credit_suggestion
        yield {
            "type": "observation",
            "content": f"授信建议已生成：额度 {credit_suggestion.get('suggested_amount', '待补充')}，期限 {credit_suggestion.get('suggested_period', '待补充')}",
            "data": credit_suggestion,
            "step": step
        }
        step += 1

        # 5. 最终报告
        report = report_generator.generate_report(company_data, rule_result, scorecard, credit_suggestion)
        yield {
            "type": "final",
            "content": "风控尽调完成",
            "result": {
                "company": company_data,
                "rule_check": rule_result,
                "scorecard": scorecard,
                "credit_suggestion": credit_suggestion,
                "report": report,
                "status": "completed"
            },
            "step": step
        }

    async def _fallback_flow_complete(self, company_name: str, start_step: int, 
                                       existing_context: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """
        降级模式补全流程：当LLM未完成全部工具调用时，用此方法补全
        """
        step = start_step

        company_data = existing_context.get("company_data")
        rule_result = existing_context.get("rule_result")

        # 如果企业信息不存在，先获取
        if not company_data:
            yield {"type": "thought", "content": "获取企业信息...", "step": step}
            yield {"type": "action", "content": "调用工具: search_company", "tool": "search_company", "step": step}
            company_data = await company_search_tool.search_company(company_name)
            self.context_store["company_data"] = company_data
            yield {
                "type": "observation",
                "content": f"获取企业信息：{company_data.get('name', company_name)}",
                "data": company_data,
                "step": step
            }
            step += 1

        # 如果规则校验未执行，先执行
        if not rule_result:
            yield {"type": "thought", "content": "执行禁入规则校验...", "step": step}
            yield {"type": "action", "content": "调用工具: check_rules", "tool": "check_rules", "step": step}
            rule_result = rule_check_tool.check_rules(company_data)
            self.context_store["rule_result"] = rule_result
            yield {
                "type": "observation",
                "content": f"规则校验{'通过' if rule_result.get('passed') else '未通过'}",
                "data": rule_result,
                "step": step
            }
            step += 1

        # 检查是否被禁入
        if not rule_result.get("passed", True):
            report = report_generator.generate_report(
                company_data, rule_result,
                {"total_score": 0, "risk_level": "高风险", "dimensions": []},
                {"suggested_amount": "不建议授信"}
            )
            yield {
                "type": "final",
                "content": "风控尽调完成（企业被禁入）",
                "result": {
                    "company": company_data,
                    "rule_check": rule_result,
                    "scorecard": None,
                    "credit_suggestion": None,
                    "report": report,
                    "status": "rejected"
                },
                "step": step
            }
            return

        # 创建评分卡
        scorecard = self.context_store.get("scorecard")
        if not scorecard:
            yield {"type": "thought", "content": "创建信用评分卡...", "step": step}
            yield {"type": "action", "content": "调用工具: create_scorecard", "tool": "create_scorecard", "step": step}
            scorecard = await scorecard_tool.create_scorecard(company_data, rule_result)
            self.context_store["scorecard"] = scorecard
            yield {
                "type": "observation",
                "content": f"评分完成：{scorecard.get('total_score', 0) if scorecard else 0} 分，{scorecard.get('risk_level', '未知') if scorecard else '未知'}",
                "data": scorecard,
                "step": step
            }
            step += 1

        # 计算授信建议
        credit_suggestion = self.context_store.get("credit_suggestion")
        if not credit_suggestion:
            yield {"type": "thought", "content": "计算授信建议...", "step": step}
            yield {"type": "action", "content": "调用工具: calculate_credit", "tool": "calculate_credit", "step": step}
            credit_suggestion = await credit_calculator.calculate_credit(company_data, scorecard)
            self.context_store["credit_suggestion"] = credit_suggestion
            yield {
                "type": "observation",
                "content": f"授信建议：{credit_suggestion.get('suggested_amount', '待补充') if credit_suggestion else '待补充'}",
                "data": credit_suggestion,
                "step": step
            }
            step += 1

        # 生成最终报告
        report = report_generator.generate_report(company_data, rule_result, scorecard, credit_suggestion)
        result = {
            "company": company_data,
            "rule_check": rule_result,
            "scorecard": scorecard,
            "credit_suggestion": credit_suggestion,
            "report": report,
            "status": "completed"
        }
        yield {
            "type": "final",
            "content": "风控尽调完成",
            "result": result,
            "step": step
        }

    # ======== 辅助方法 ========
    def _inject_history_to_messages(self, messages: List[Dict[str, str]], history: List[str]):
        """
        将历史观察结果注入到 LLM 对话中，让 LLM 知道已经掌握了什么信息
        智能截断机制：只保留最近3轮工具调用，同时提供状态摘要
        """
        # 只保留最近3轮工具调用历史，避免上下文过长
        recent_history = history[-3:] if len(history) > 3 else history
        
        if recent_history:
            context = "\n\n".join(recent_history)
            # 生成当前状态摘要，告诉LLM已掌握哪些关键信息
            status_summary = f"""【当前状态摘要】
- 企业信息：{'已获取' if self.context_store.get('company_data') else '未获取'}
- 规则校验：{'已通过' if self.context_store.get('rule_result', {}).get('passed') else '未执行'}
- 评分卡：{'已完成' if self.context_store.get('scorecard') else '未完成'}
- 授信建议：{'已生成' if self.context_store.get('credit_suggestion') else '未生成'}

"""
            summary_msg = f"{status_summary}【最近工具调用】\n{context}\n\n基于以上信息，请决定下一步调用什么工具或是否可以给出最终回答。"
            
            # 避免重复注入，检查最新的 user 消息是否已包含状态摘要
            last_user = None
            for m in reversed(messages):
                if m["role"] == "user":
                    last_user = m
                    break
            if last_user and "当前状态摘要" not in last_user["content"]:
                # 把上下文附加到最后一条 user 消息
                last_user["content"] = last_user["content"] + "\n\n---\n" + summary_msg
        
        # 限制消息总数不超过6条（保留system prompt + 最近5条）
        if len(messages) > 6:
            messages[:] = [messages[0]] + messages[-5:]

    def _summarize_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """把工具结果摘要成几句话，用于 LLM 上下文"""
        if tool_name == "search_company":
            return f"企业：{result.get('name', '未知')}，注册资本：{result.get('registered_capital', '未知')}，成立时间：{result.get('establishment_date', '未知')}，行业：{result.get('industry', '未知')}，年营收：{result.get('annual_revenue', '未知')}"
        elif tool_name == "check_rules":
            passed = result.get("passed", False)
            violations = result.get("violations", [])
            return f"规则校验{'通过' if passed else '未通过'}，{len(violations)} 项违规: {'; '.join(violations[:2])}" if violations else "规则校验通过"
        elif tool_name == "create_scorecard":
            return f"综合评分：{result.get('total_score', 0)} 分，风险等级：{result.get('risk_level', '未知')}，维度数：{len(result.get('dimensions', []))}"
        elif tool_name == "calculate_credit":
            return f"建议额度：{result.get('suggested_amount', '未知')}，期限：{result.get('suggested_period', '未知')}，类型：{result.get('primary_credit_type', '流动资金授信')}"
        elif tool_name == "read_knowledge_base":
            return f"知识库主题：{result.get('topic', '未知')}，预览长度：{len(result.get('content_preview', ''))} 字符"
        else:
            return str(result)[:200]

    def _sanitize_for_yield(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """对工具输出做安全裁剪，避免流式输出过大"""
        if not isinstance(result, dict):
            return {"result": str(result)[:500]}
        return result

    def list_local_companies(self) -> List[str]:
        return company_search_tool.list_local_companies()

    async def quick_search(self, company_name: str) -> Dict[str, Any]:
        """快速查询企业信息（用于前端下拉/快速预览）"""
        data = company_search_tool.search_local(company_name)
        if not data:
            return {"name": company_name, "not_found": True, "message": "未在本地库中找到该企业"}
        return data


react_agent = ReActAgent()
