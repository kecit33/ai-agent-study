"""Kimi (Moonshot) 提供商，OpenAI 兼容接口格式。"""
from config import MOONSHOT_API_KEY, MOONSHOT_MODEL
from .base import AgentProvider


class MoonshotProvider(AgentProvider):
    name = "moonshot"
    label = "Kimi (Moonshot)"

    BASE_URL = "https://api.moonshot.cn/v1/chat/completions"

    def is_available(self):
        return bool(MOONSHOT_API_KEY)

    def complete(self, system_prompt: str, messages: list) -> str:
        if not self.is_available():
            return "（未配置 MOONSHOT_API_KEY，已回退演示模式）"
        import requests
        payload_msgs = [{"role": "system", "content": system_prompt}]
        payload_msgs += [{"role": m["role"], "content": m["content"]} for m in messages]
        try:
            resp = requests.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": MOONSHOT_MODEL, "messages": payload_msgs, "temperature": 0.7},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"（Kimi 接口调用失败，已回退演示模式：{e}）"
