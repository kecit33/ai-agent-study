"""百度文心一言（千帆 QianFan / ERNIE）提供商。

自动适配两种官方鉴权方式，密钥可在 .env、Web 设置页或 REST 接口配置：

1. 千帆 v2（推荐，OpenAI 兼容）
   base_url = https://qianfan.baidubce.com/v2/chat/completions
   使用 Authorization: Bearer <API Key>，只需 api_key，无需 access_token。
   模型如 ernie-4.5-8k / ernie-3.5-8k / ernie-speed-8k。

2. 旧版 WenxinWorkshop
   token_url = https://aip.baidubce.com/oauth/2.0/token
   base_url  = https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions
   先用 API Key + Secret Key 换 access_token（内存缓存 30 天），再带 token 调用。

base_url / token_url 均可覆盖，因此也能指向自建网关或本地模拟服务做联调。
"""
import time
import urllib.parse

from agents import credentials, http_client
from .base import AgentProvider


class QianFanProvider(AgentProvider):
    name = "qianfan"
    label = "百度文心一言"

    V2_URL = "https://qianfan.baidubce.com/v2/chat/completions"
    LEGACY_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
    LEGACY_CHAT_URL = ("https://aip.baidubce.com/rpc/2.0/ai_custom/"
                       "v1/wenxinworkshop/chat/completions")

    _token_cache = {}

    def is_available(self):
        return credentials.validate("qianfan")[0]

    def _get_token(self, c):
        url = c.get("token_url") or self.LEGACY_TOKEN_URL
        key = (c["api_key"], c.get("secret_key", ""), url)
        hit = self._token_cache.get(key)
        if hit and time.time() < hit[1] - 60:
            return hit[0]
        data = http_client.get_json(url, params={
            "grant_type": "client_credentials",
            "client_id": c["api_key"],
            "client_secret": c.get("secret_key", ""),
        }, timeout=30)
        token = data.get("access_token")
        if not token:
            raise RuntimeError("获取 access_token 失败：%s" % str(data)[:200])
        self._token_cache[key] = (token, time.time() + int(data.get("expires_in", 2592000)))
        return token

    def _call(self, system_prompt: str, messages: list) -> str:
        c = credentials.get("qianfan")
        msgs = [{"role": m["role"], "content": m["content"]} for m in messages]
        if credentials._is_qianfan_v2(c):
            url = c.get("base_url") or self.V2_URL
            payload = {"model": c["model"], "messages":
                       [{"role": "system", "content": system_prompt}] + msgs,
                       "temperature": 0.7}
            data = http_client.post_json(
                url, payload,
                headers={"Authorization": "Bearer %s" % c["api_key"]}, timeout=60)
            return http_client.extract_content(data)

        # 旧版：system 提示合并进首条 user，更稳妥
        if msgs:
            msgs[0]["content"] = system_prompt + "\n\n" + msgs[0]["content"]
        url = c.get("base_url") or self.LEGACY_CHAT_URL
        token = self._get_token(c)
        url += ("&" if "?" in url else "?") + "access_token=" + urllib.parse.quote(token)
        data = http_client.post_json(
            url, {"messages": msgs, "model": c["model"], "temperature": 0.7}, timeout=60)
        return http_client.extract_content(data)
