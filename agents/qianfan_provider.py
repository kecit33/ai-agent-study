"""百度文心一言 (QianFan / ERNIE) 提供商。

调用流程：先用 API Key + Secret Key 换取 access_token，再携带 token 调用 ERNIE 对话接口。
token 有效期约 30 天，这里在内存中缓存。
"""
import time

from config import QIANFAN_API_KEY, QIANFAN_SECRET_KEY, QIANFAN_MODEL
from .base import AgentProvider


class QianFanProvider(AgentProvider):
    name = "qianfan"
    label = "百度文心一言"

    TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
    CHAT_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"

    _token = None
    _token_expire = 0

    def is_available(self):
        return bool(QIANFAN_API_KEY) and bool(QIANFAN_SECRET_KEY)

    def _get_token(self):
        import requests
        now = time.time()
        if self._token and now < self._token_expire - 60:
            return self._token
        resp = requests.get(
            self.TOKEN_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": QIANFAN_API_KEY,
                "client_secret": QIANFAN_SECRET_KEY,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(data.get("error_description", "获取 token 失败"))
        self._token = data["access_token"]
        self._token_expire = now + data.get("expires_in", 2592000)
        return self._token

    def complete(self, system_prompt: str, messages: list) -> str:
        if not self.is_available():
            return "（未配置文心一言密钥，已回退演示模式）"
        import requests
        payload_msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
        # 文心一言把系统提示合并进首条 user 消息更稳妥
        if payload_msgs:
            payload_msgs[0]["content"] = system_prompt + "\n\n" + payload_msgs[0]["content"]
        try:
            token = self._get_token()
            resp = requests.post(
                self.CHAT_URL,
                params={"access_token": token},
                headers={"Content-Type": "application/json"},
                json={"messages": payload_msgs, "temperature": 0.7},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            if "result" in data:
                return data["result"].strip()
            raise RuntimeError(data.get("error_msg", "未知错误"))
        except Exception as e:
            return f"（文心一言接口调用失败，已回退演示模式：{e}）"
