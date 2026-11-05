"""
配置中心
- 智能体（Agent）提供商的 API 密钥统一从环境变量读取，避免硬编码密钥。
- 未配置密钥的厂商自动回退到内置「演示模式」，保证无密钥也能完整跑通、师生可直接测试。
"""
import os

# python-dotenv 为可选依赖：未安装时用标准库自解析 .env，保证零依赖模式同样生效
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    def _load_env_file(path):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key, value = key.strip(), value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except OSError:
            pass

    _load_env_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "companion.db")

# 默认激活的提供商：demo / openai / qianfan / moonshot / claude
ACTIVE_PROVIDER = os.getenv("ACTIVE_PROVIDER", "demo").strip().lower()

# OpenAI (GPT)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# 百度 文心一言 (QianFan / ERNIE)
QIANFAN_API_KEY = os.getenv("QIANFAN_API_KEY", "")
QIANFAN_SECRET_KEY = os.getenv("QIANFAN_SECRET_KEY", "")
QIANFAN_MODEL = os.getenv("QIANFAN_MODEL", "ernie-3.5-8k")

# 月之暗面 Kimi (Moonshot)
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")

# Anthropic Claude
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

# ESP32 硬件联动（可选加分项）：Web 端下发的复习提醒将 POST 到此地址
ESP32_ENDPOINT = os.getenv("ESP32_ENDPOINT", "")

PROVIDER_LABELS = {
    "demo": "内置演示模式（无需密钥）",
    "openai": "OpenAI GPT",
    "qianfan": "百度文心一言",
    "moonshot": "Kimi (Moonshot)",
    "claude": "Anthropic Claude",
}
