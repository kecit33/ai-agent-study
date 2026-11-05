"""Anthropic Claude 提供商。"""
from agents import credentials, http_client
from .base import AgentProvider


class ClaudeProvider(AgentProvider):
    name = "claude"
    label = "Anthropic Claude"

    def is_available(self):
        return credentials.validate("claude")[0]

    def _call(self, system_prompt: str, messages: list) -> str:
        c = credentials.get("claude")
        payload_msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
        data = http_client.post_json(
            c["base_url"],
            {"model": c["model"], "max_tokens": 2048,
             "system": system_prompt, "messages": payload_msgs},
            headers={"x-api-key": c["api_key"], "anthropic-version": "2023-06-01"},
            timeout=45,
        )
        return http_client.extract_content(data)
