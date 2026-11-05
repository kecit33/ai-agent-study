"""Anthropic Claude 提供商。"""
from config import CLAUDE_API_KEY, CLAUDE_MODEL
from .base import AgentProvider


class ClaudeProvider(AgentProvider):
    name = "claude"
    label = "Anthropic Claude"

    BASE_URL = "https://api.anthropic.com/v1/messages"

    def is_available(self):
        return bool(CLAUDE_API_KEY)

    def complete(self, system_prompt: str, messages: list) -> str:
        if not self.is_available():
            return "（未配置 CLAUDE_API_KEY，已回退演示模式）"
        import requests
        # Anthropic 的 system 为顶层字段，messages 仅含 user/assistant
        payload_msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
        try:
            resp = requests.post(
                self.BASE_URL,
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": payload_msgs,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return "".join(block.get("text", "") for block in data.get("content", [])).strip()
        except Exception as e:
            return f"（Claude 接口调用失败，已回退演示模式：{e}）"
