"""通用 OpenAI 兼容提供商：把任意自建 / 第三方模型端点接进系统。

只要对方的请求/响应格式与 /v1/chat/completions 兼容即可，例如：
* Kimi、通义千问、DeepSeek、智谱、硅基流动等国内厂商的 OpenAI 兼容端点；
* 本地 Ollama / vLLM / LM Studio / FastChat；
* 校内自建的大模型网关或代理服务。

必填：api_key、base_url、model；均可在 Web 设置页或 REST 接口运行时配置。
"""
from agents import credentials, http_client
from .base import AgentProvider


class CustomProvider(AgentProvider):
    name = "custom"
    label = "自定义 OpenAI 兼容接口"

    def is_available(self):
        return credentials.validate("custom")[0]

    def _call(self, system_prompt: str, messages: list) -> str:
        c = credentials.get("custom")
        payload_msgs = [{"role": "system", "content": system_prompt}]
        payload_msgs += [{"role": m["role"], "content": m["content"]} for m in messages]
        headers = {"Authorization": "Bearer %s" % c["api_key"]}
        if c.get("secret_key"):
            headers["X-API-Key"] = c["secret_key"]
        data = http_client.post_json(
            c["base_url"],
            {"model": c["model"], "messages": payload_msgs, "temperature": 0.7},
            headers=headers, timeout=45,
        )
        return http_client.extract_content(data)
