"""智能体提供商工厂：选择厂商、运行时配置密钥、自动回退演示模式。"""
import time

from db import get_conn

from . import credentials
from .base import AgentProvider
from .demo_provider import DemoProvider
from .openai_provider import OpenAIProvider
from .moonshot_provider import MoonshotProvider
from .claude_provider import ClaudeProvider
from .qianfan_provider import QianFanProvider
from .custom_provider import CustomProvider

_PROVIDERS = {
    "openai": OpenAIProvider,
    "moonshot": MoonshotProvider,
    "claude": ClaudeProvider,
    "qianfan": QianFanProvider,
    "custom": CustomProvider,
    "demo": DemoProvider,
}


def get_active_provider_name() -> str:
    """从数据库设置读取当前激活的提供商名称。"""
    try:
        conn = get_conn()
        row = conn.execute("SELECT value FROM settings WHERE key='active_provider'").fetchone()
        conn.close()
        name = (row["value"] if row else "demo").strip().lower()
    except Exception:
        name = "demo"
    return name if name in _PROVIDERS else "demo"


def set_active_provider(name: str) -> bool:
    name = (name or "").strip().lower()
    if name not in _PROVIDERS:
        return False
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO settings(key, value) VALUES('active_provider', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (name,),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_provider(name: str = None) -> AgentProvider:
    """返回指定（或当前激活）的提供商实例；未配置密钥时回退演示模式。"""
    if name is None:
        name = get_active_provider_name()
    provider_cls = _PROVIDERS.get(name, DemoProvider)
    provider = provider_cls()
    if provider.is_available():
        return provider
    return DemoProvider()


def list_providers_status() -> list:
    """列出所有厂商及其可用性、配置来源与掩码信息，供前端「设置」页展示。"""
    active = get_active_provider_name()
    result = []
    for name, cls in _PROVIDERS.items():
        inst = cls()
        conf = credentials.status(name) if name != "demo" else {}
        row = {
            "name": name,
            "label": inst.label,
            "available": inst.is_available(),
            "active": name == active,
            "configured": True if name == "demo" else conf.get("configured"),
            "model": conf.get("model", ""),
            "source": "builtin" if name == "demo" else conf.get("source", "env"),
            "masked": conf.get("masked", {}),
            "required": conf.get("required", []),
            "optional": conf.get("optional", []),
            "hint": conf.get("hint", "") or credentials.PROVIDER_FIELDS.get(name, {}).get("hint", ""),
            "reason": conf.get("reason", ""),
        }
        result.append(row)
    return result


def probe(name: str = None) -> dict:
    """对指定（默认当前）提供商做一次真实连通性调用。"""
    name = name or get_active_provider_name()
    if name == "demo":
        return {"ok": True, "provider": "demo", "label": "内置演示模式（无需密钥）",
                "reply": "演示模式已就绪，无需连接外部模型", "latency_ms": 0}
    if name not in _PROVIDERS:
        return {"ok": False, "error": "未知提供商：%s" % name}
    result = _PROVIDERS[name]().probe()
    c = credentials.get(name)
    result["model"] = c.get("model", "")
    result["base_url"] = c.get("base_url", "")
    result["configured"] = credentials.validate(name)[0]
    return result


def direct_complete(system_prompt: str, messages: list, provider_name: str = None) -> dict:
    """通用模型透传接口：供自建系统调用当前配置的任意厂商模型。"""
    requested = provider_name or get_active_provider_name()
    provider = get_provider(requested)
    started = time.time()
    reply = provider.complete(system_prompt, messages)
    return {
        "reply": reply,
        "provider": provider.name,
        "requested_provider": requested,
        "model": credentials.get(provider.name).get("model", "") if provider.name != "demo" else "demo-rules",
        "fallback": provider.name == "demo" and requested != "demo",
        "latency_ms": int((time.time() - started) * 1000),
    }


def configure(provider: str, payload: dict, activate: bool = False) -> dict:
    """写入运行时密钥，可选立即切换为当前智能体。"""
    status = credentials.save(provider, payload)
    ok, reason = credentials.validate(provider)
    if activate and not ok:
        return {"ok": False, "status": status, "reason": reason,
                "message": "配置已保存，但必填项不全，未切换为当前智能体：%s" % reason}
    if activate:
        set_active_provider(provider)
    return {"ok": True, "status": status, "active_provider": get_active_provider_name(),
            "activated": bool(activate)}


def clear(provider: str) -> dict:
    status = credentials.clear(provider)
    if get_active_provider_name() == provider:
        set_active_provider("demo")
    return {"ok": True, "status": status, "active_provider": get_active_provider_name()}
