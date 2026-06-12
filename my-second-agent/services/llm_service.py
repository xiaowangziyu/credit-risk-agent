import json
import asyncio
import httpx
from typing import List, Dict, Any, AsyncIterator, Optional
from config.settings import settings


class LLMService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.api_url = settings.LLM_API_URL
        # 增加超时时间，给LLM更充裕的思考时间（人的体感可接受的范围）
        self.timeout = 60.0  # 单次请求60秒
        self.max_retries = 2  # 最多重试2次
        self.retry_delay = 1.5  # 重试间隔1.5秒

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    async def _request_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """带重试机制的请求方法"""
        headers = self._get_headers()
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # 设置较长的超时时间，但比 429 重试的常规快
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.api_url, headers=headers, json=payload)

                    # 429 限流：等待后重试
                    if response.status_code == 429:
                        last_error = f"HTTP 429 (限流)"
                        if attempt < self.max_retries:
                            wait_time = self.retry_delay * (attempt + 1)
                            print(f"[LLM] 触发限流(429)，{wait_time}秒后重试 ({attempt + 1}/{self.max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"LLM API 被限流: {response.text[:200]}")

                    response.raise_for_status()
                    return response.json()

            except httpx.TimeoutException as e:
                last_error = f"请求超时: {str(e)}"
                if attempt < self.max_retries:
                    print(f"[LLM] 请求超时，{self.retry_delay}秒后重试 ({attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise Exception(f"LLM 请求超时（已重试{self.max_retries}次）")

            except httpx.HTTPStatusError as e:
                # 其他 HTTP 错误
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                if e.response.status_code in [500, 502, 503, 504] and attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise

            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    continue
                raise

        raise Exception(f"LLM 请求失败: {last_error}")

    async def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """普通对话调用"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }

        data = await self._request_with_retry(payload)
        return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> AsyncIterator[str]:
        """流式对话调用"""
        headers = self._get_headers()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self.api_url, headers=headers, json=payload) as response:
                async for chunk in response.aiter_lines():
                    if chunk.startswith("data: "):
                        chunk_data = chunk[6:]
                        if chunk_data.strip() == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(chunk_data)
                            delta = chunk_json["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    async def chat_with_function(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]],
                                 temperature: float = 0.7) -> Dict[str, Any]:
        """带 function calling 的对话调用"""
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": temperature,
            "stream": False
        }

        print(f"[LLM-TRACE] >>> 发送请求: model={self.model}, messages={len(messages)} 条, tools={len(tools)} 个, tool_choice=auto")
        data = await self._request_with_retry(payload)
        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])
        content = message.get("content", "")
        print(f"[LLM-TRACE] <<< 收到响应: content={len(content) if content else 0} chars, tool_calls={len(tool_calls) if tool_calls else 0}")
        if tool_calls:
            for i, tc in enumerate(tool_calls):
                func_name = tc.get("function", {}).get("name", "?")
                func_args = tc.get("function", {}).get("arguments", "{}")
                print(f"[LLM-TRACE]     tool_call#{i+1}: {func_name} args={func_args[:80]}")
        return message


llm_service = LLMService()
