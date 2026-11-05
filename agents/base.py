"""智能体提供商统一接口（可插拔）。

所有厂商（GPT / 文心一言 / Kimi / Claude / 自定义兼容接口）与内置演示模式
都实现 `_call()`；业务层只调用 `complete()`，从而实现：

* 业务代码不感知厂商差异；
* 任何调用失败都自动回退「内置演示模式」，Web 应用永不因模型故障而不可用；
* `probe()` 提供连通性自检，供「设置」页与自动化验收脚本使用。

配置来源统一为 agents.credentials（环境变量 + 运行时 SQLite 覆盖）。
"""
import re
import time

_MODE_RE = re.compile(r"【MODE:\w+】\s*")


class AgentProvider:
    """统一智能体接口。"""

    #: 提供商标识，如 openai / qianfan / moonshot / claude / custom / demo
    name = "base"
    label = "基础提供商"

    #: 真实厂商需要剥离演示模式标记，演示模式自身依赖该标记分发任务
    strip_mode_marker = True

    def is_available(self) -> bool:
        """该提供商当前是否可用（密钥是否配置齐全）。"""
        return True

    def complete(self, system_prompt: str, messages: list) -> str:
        """给定系统提示与对话历史，返回回复文本；任何异常都降级为提示文案。"""
        if not self.is_available():
            return "（%s 未配置密钥，已回退演示模式）" % self.label
        sp = _MODE_RE.sub("", system_prompt or "") if self.strip_mode_marker else (system_prompt or "")
        try:
            return self._call(sp, messages)
        except Exception as e:
            return "（%s 接口调用失败，已回退演示模式：%s）" % (self.label, e)

    def _call(self, system_prompt: str, messages: list) -> str:
        """厂商实现：成功返回文本，失败抛异常（由 complete 统一兜底）。"""
        raise NotImplementedError

    def probe(self) -> dict:
        """连通性自检：返回结构化结果，不抛异常、不回传密钥。"""
        if not self.is_available():
            return {"ok": False, "provider": self.name, "label": self.label,
                    "error": "未配置密钥，请先填写 API Key（或检查环境变量）"}
        started = time.time()
        try:
            reply = self._call(
                "你是连通性测试助手，只输出用户要求的文本内容，不要解释。",
                [{"role": "user", "content": "请只回复四个字：连接成功"}],
            )
            return {"ok": True, "provider": self.name, "label": self.label,
                    "reply": str(reply)[:200], "latency_ms": int((time.time() - started) * 1000)}
        except Exception as e:
            return {"ok": False, "provider": self.name, "label": self.label,
                    "error": str(e), "latency_ms": int((time.time() - started) * 1000)}
