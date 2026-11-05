"""Kimi（月之暗面 Moonshot）提供商，OpenAI 兼容接口格式。

密钥可在 .env 用 MOONSHOT_API_KEY 配置，也可在 Web「设置」页或
POST /api/agent/credentials 运行时写入，写入后立即生效、无需重启。
常用模型：moonshot-v1-8k / moonshot-v1-32k / moonshot-v1-128k / kimi-k2 系列。
"""
from agents import credentials, http_client
from .base import AgentProvider


class MoonshotProvider(AgentProvider):
    name = "moonshot"
    label = "Kimi (Moonshot)"

    def is_available(self):
        return credentials.validate("moonshot")[0]

    def _call(self, system_prompt: str, messages: list) -> str:
        c = credentials.get("moonshot")
        payload_msgs = [{"role": "system", "content": system_prompt}]
        payload_msgs += [{"role": m["role"], "content": m["content"]} for m in messages]
        data = http_client.post_json(
            c["base_url"],
            {"model": c["model"], "messages": payload_msgs, "temperature": 0.7},
            headers={"Authorization": "Bearer %s" % c["api_key"]},
            timeout=45,
        )
        return http_client.extract_content(data)
