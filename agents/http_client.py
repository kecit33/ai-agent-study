"""智能体厂商 HTTP 客户端（仅 Python 标准库 urllib，零第三方依赖）。

本机与部署环境可能无法安装 requests，因此所有厂商调用统一走这里；
异常统一转成 RuntimeError 并附带上游响应片段，便于界面显示真实原因。
"""
import json
import urllib.error
import urllib.parse
import urllib.request


def post_json(url, payload, headers=None, timeout=30):
    if not url:
        raise RuntimeError("未配置请求地址 base_url")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    hdr = {"Content-Type": "application/json", "Accept": "application/json"}
    hdr.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdr, method="POST")
    return _exec(req, timeout)


def get_json(url, params=None, headers=None, timeout=30):
    if not url:
        raise RuntimeError("未配置请求地址 token_url")
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    return _exec(req, timeout)


def _exec(req, timeout):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            body = ""
        raise RuntimeError("上游返回 HTTP %s：%s" % (e.code, body)) from e
    except urllib.error.URLError as e:
        raise RuntimeError("网络不可达：%s" % e.reason) from e
    except Exception as e:
        raise RuntimeError("请求失败：%s" % e) from e
    try:
        return json.loads(raw)
    except ValueError:
        raise RuntimeError("上游响应不是合法 JSON：%s" % raw[:200])


def extract_content(data) -> str:
    """兼容 OpenAI 兼容格式、文心旧版 result 字段与 Claude content 块。"""
    if not isinstance(data, dict):
        raise RuntimeError("上游响应格式异常")
    if "error" in data and data["error"]:
        err = data["error"]
        raise RuntimeError("上游报错：%s" % (err.get("message") if isinstance(err, dict) else err))
    if isinstance(data.get("choices"), list) and data["choices"]:
        msg = (data["choices"][0] or {}).get("message") or {}
        text = msg.get("content")
        if isinstance(text, list):
            text = "".join(b.get("text", "") for b in text if isinstance(b, dict))
        if text:
            return str(text).strip()
        if (data["choices"][0] or {}).get("text"):
            return str(data["choices"][0]["text"]).strip()
    if isinstance(data.get("content"), list):
        text = "".join(b.get("text", "") for b in data["content"] if isinstance(b, dict))
        if text:
            return text.strip()
    for key in ("result", "output", "response", "answer", "completion"):
        if data.get(key):
            return str(data[key]).strip()
    raise RuntimeError("上游响应缺少文本内容：%s" % json.dumps(data, ensure_ascii=False)[:200])
