"""智能体提供商工厂：根据配置选择厂商，不可用时自动回退演示模式。"""
from db import get_conn

from .base import AgentProvider
from .demo_provider import DemoProvider
from .openai_provider import OpenAIProvider
from .moonshot_provider import MoonshotProvider
from .claude_provider import ClaudeProvider
from .qianfan_provider import QianFanProvider

_PROVIDERS = {
    "openai": OpenAIProvider,
    "moonshot": MoonshotProvider,
    "claude": ClaudeProvider,
    "qianfan": QianFanProvider,
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
    """返回指定（或当前激活）的提供商实例；若不可用则回退演示模式。"""
    if name is None:
        name = get_active_provider_name()
    provider_cls = _PROVIDERS.get(name, DemoProvider)
    provider = provider_cls()
    if provider.is_available():
        return provider
    # 不可用时回退到内置演示模式，保证系统永远可响应
    return DemoProvider()


def list_providers_status() -> list:
    """列出所有厂商及其可用性，供前端「设置」页展示。"""
    result = []
    for name, cls in _PROVIDERS.items():
        inst = cls()
        result.append(
            {
                "name": name,
                "label": inst.label,
                "available": inst.is_available(),
                "active": name == get_active_provider_name(),
            }
        )
    return result
