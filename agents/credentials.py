"""模型接入凭据中心：环境变量 + 运行时数据库配置。

优先级：运行时（Web 界面 / REST API 写入 SQLite） > .env 环境变量 > 空。
目的：老师或同学拿到文心一言 / Kimi 的 API Key 后，不需要改代码、不需要重启服务，
直接在「设置」页填入即可生效；也支持任何 OpenAI 兼容的自建模型端点。

安全约定：
* 列表/状态接口只返回掩码（如 sk-1****cdef），永不回传完整密钥；
* 密钥只存本地 SQLite（data/companion.db），不写日志、不进前端持久化；
* 生产环境建议给 /api/agent/* 增加鉴权，见 docs/模型接入接口说明.md。
"""
from datetime import datetime

from db import get_conn

PROVIDER_FIELDS = {
    "openai": {
        "label": "OpenAI GPT", "required": ["api_key"],
        "optional": ["model", "base_url"],
        "env": {"api_key": "OPENAI_API_KEY", "model": "OPENAI_MODEL",
                "base_url": "OPENAI_BASE_URL"},
    },
    "qianfan": {
        "label": "百度文心一言 (QianFan / ERNIE)", "required": ["api_key"],
        "optional": ["secret_key", "model", "base_url", "token_url"],
        "hint": "新版 v2 接口只需 API Key；旧版 WenxinWorkshop 还需 Secret Key 换取 access_token",
        "env": {"api_key": "QIANFAN_API_KEY", "secret_key": "QIANFAN_SECRET_KEY",
                "model": "QIANFAN_MODEL", "base_url": "QIANFAN_BASE_URL",
                "token_url": "QIANFAN_TOKEN_URL"},
    },
    "moonshot": {
        "label": "Kimi (Moonshot)", "required": ["api_key"],
        "optional": ["model", "base_url"],
        "env": {"api_key": "MOONSHOT_API_KEY", "model": "MOONSHOT_MODEL",
                "base_url": "MOONSHOT_BASE_URL"},
    },
    "claude": {
        "label": "Anthropic Claude", "required": ["api_key"],
        "optional": ["model", "base_url"],
        "env": {"api_key": "CLAUDE_API_KEY", "model": "CLAUDE_MODEL",
                "base_url": "CLAUDE_BASE_URL"},
    },
    "custom": {
        "label": "自定义 OpenAI 兼容接口", "required": ["api_key", "base_url", "model"],
        "optional": ["secret_key", "token_url"],
        "env": {"api_key": "CUSTOM_API_KEY", "base_url": "CUSTOM_BASE_URL",
                "model": "CUSTOM_MODEL", "secret_key": "CUSTOM_SECRET_KEY",
                "token_url": "CUSTOM_TOKEN_URL"},
    },
}

DEFAULT_MODELS = {
    "openai": "gpt-3.5-turbo", "qianfan": "ernie-3.5-8k",
    "moonshot": "moonshot-v1-8k", "claude": "claude-3-5-sonnet-20241022",
}

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "moonshot": "https://api.moonshot.cn/v1/chat/completions",
    "claude": "https://api.anthropic.com/v1/messages",
    "qianfan": "",  # 由 provider 根据鉴权方式选择官方端点
}

ALL_FIELDS = ["api_key", "secret_key", "model", "base_url", "token_url"]


def ensure_table():
    conn = get_conn()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS provider_credentials ("
        "provider TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    conn.commit()
    conn.close()


def _runtime(provider: str) -> dict:
    try:
        ensure_table()
        conn = get_conn()
        row = conn.execute(
            "SELECT data, updated_at FROM provider_credentials WHERE provider=?", (provider,)
        ).fetchone()
        conn.close()
        if not row:
            return {}
        import json
        data = json.loads(row["data"] or "{}")
        data["_updated_at"] = row["updated_at"]
        return data
    except Exception:
        return {}


def get(provider: str) -> dict:
    """取该提供商的最终生效配置（环境变量 + 运行时覆盖）。"""
    import os
    spec = PROVIDER_FIELDS.get(provider, {})
    env_map = spec.get("env", {})
    result = {}
    for field in ALL_FIELDS:
        env_name = env_map.get(field)
        result[field] = (os.getenv(env_name, "") if env_name else "").strip()
    if provider in DEFAULT_MODELS and not result["model"]:
        result["model"] = DEFAULT_MODELS[provider]
    if provider in DEFAULT_BASE_URLS and not result["base_url"]:
        result["base_url"] = DEFAULT_BASE_URLS[provider]

    runtime = _runtime(provider)
    for field in ALL_FIELDS:
        if field in runtime and str(runtime[field]).strip():
            result[field] = str(runtime[field]).strip()
    result["_runtime"] = {k: v for k, v in runtime.items() if not k.startswith("_")}
    result["_updated_at"] = runtime.get("_updated_at", "")
    result["_source"] = "runtime" if runtime.get("_updated_at") else "env"
    return result


def _is_qianfan_v2(creds: dict) -> bool:
    url = str(creds.get("base_url", "")).lower()
    return "qianfan.baidubce.com" in url or "/v2/" in url


def validate(provider: str, creds: dict = None):
    """返回 (是否可用, 缺失字段说明)。"""
    spec = PROVIDER_FIELDS.get(provider)
    if not spec:
        return False, "未知提供商：%s" % provider
    creds = creds if creds is not None else get(provider)
    missing = [f for f in spec["required"] if not str(creds.get(f, "")).strip()]
    if missing:
        return False, "缺少必填项：" + ", ".join(missing)
    if provider == "qianfan" and not _is_qianfan_v2(creds) and not str(creds.get("secret_key", "")).strip():
        return False, ("旧版 WenxinWorkshop 接口还需要 secret_key；"
                       "或把 base_url 设为 https://qianfan.baidubce.com/v2/chat/completions 使用新版")
    return True, ""


def mask(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    if len(s) <= 8:
        return s[:2] + "****"
    return s[:4] + "****" + s[-4:]


def status(provider: str) -> dict:
    spec = PROVIDER_FIELDS.get(provider)
    if not spec:
        return {}
    creds = get(provider)
    ok, reason = validate(provider, creds)
    return {
        "name": provider,
        "label": spec["label"],
        "configured": ok,
        "reason": "" if ok else reason,
        "required": spec["required"],
        "optional": spec["optional"],
        "source": creds["_source"],
        "updated_at": creds["_updated_at"],
        "model": creds.get("model", ""),
        "base_url": creds.get("base_url", ""),
        "token_url": creds.get("token_url", ""),
        "masked": {f: mask(creds.get(f, "")) for f in ALL_FIELDS if creds.get(f)},
        "env_names": spec["env"],
    }


def list_status() -> list:
    return [status(p) for p in PROVIDER_FIELDS]


def save(provider: str, payload: dict) -> dict:
    """写入运行时配置；只保存非空字段，空字段表示沿用环境变量。"""
    import json
    spec = PROVIDER_FIELDS.get(provider)
    if not spec:
        raise ValueError("未知提供商：%s，可选 %s" % (provider, "/".join(PROVIDER_FIELDS)))
    allowed = set(spec["required"] + spec["optional"])
    clean = {}
    for k, v in (payload or {}).items():
        if k in allowed and isinstance(v, (str, int, float)):
            v = str(v).strip()
            if v:
                clean[k] = v
    if not clean:
        raise ValueError("未提交任何有效配置字段（%s）" % "/".join(sorted(allowed)))
    merged = dict(_runtime(provider))
    merged = {k: v for k, v in merged.items() if not k.startswith("_")}
    merged.update(clean)
    ensure_table()
    conn = get_conn()
    conn.execute(
        "INSERT INTO provider_credentials(provider, data, updated_at) VALUES(?, ?, ?) "
        "ON CONFLICT(provider) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at",
        (provider, json.dumps(merged, ensure_ascii=False),
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()
    return status(provider)


def clear(provider: str) -> dict:
    if provider not in PROVIDER_FIELDS:
        raise ValueError("未知提供商：%s" % provider)
    ensure_table()
    conn = get_conn()
    conn.execute("DELETE FROM provider_credentials WHERE provider=?", (provider,))
    conn.commit()
    conn.close()
    return status(provider)
