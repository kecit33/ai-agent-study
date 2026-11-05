"""OpenAI (GPT) 提供商，OpenAI 兼容接口格式。"""
from agents import credentials, http_client
from .base import AgentProvider


class OpenAIProvider(AgentProvider):
    name = "openai"
    label = "OpenAI GPT"

    def is_available(self):
        return credentials.validate("openai")[0]

    def _call(self, system_prompt: str, messages: list) -> str:
        c = credentials.get("openai")
        payload_msgs = [{"role": "system", "content": system_prompt}]
        payload_msgs += [{"role": m["role"], "content": m["content"]} for m in messages]
        data = http_client.post_json(
            c["base_url"],
            {"model": c["model"], "messages": payload_msgs, "temperature": 0.7},
            headers={"Authorization": "Bearer %s" % c["api_key"]},
            timeout=45,
        )
        return http_client.extract_content(data)
