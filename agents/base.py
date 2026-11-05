"""智能体提供商抽象基类。

所有厂商（OpenAI / 文心一言 / Kimi / Claude）与内置演示模式都实现同一接口，
业务层只依赖该接口，从而实现「可插拔」与「无密钥演示兜底」。
"""


class AgentProvider:
    """统一智能体接口。"""

    #: 提供商标识，如 openai / qianfan / moonshot / claude / demo
    name = "base"

    #: 人类可读标签
    label = "基础提供商"

    def complete(self, system_prompt: str, messages: list) -> str:
        """给定系统提示与对话历史，返回智能体回复文本。

        :param system_prompt: 系统提示词（含课程记忆上下文等）
        :param messages: 对话历史，元素为 {"role": "user"/"assistant", "content": "..."}
        :return: 回复文本
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """该提供商当前是否可用（如是否配置了密钥）。"""
        return True
