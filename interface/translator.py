"""翻译器接口定义"""
from abc import ABC, abstractmethod
from typing import Set, List


class ITranslator(ABC):
    """翻译器接口 - 负责将自然语言转换为PDDL"""

    @abstractmethod
    def route_domain(self, user_goal: str) -> str:
        """
        路由任务到对应的领域

        :param user_goal: 用户目标描述
        :return: 领域名称（如 "file_management"）
        """
        pass

    @abstractmethod
    def translate(self, user_goal: str, memory_facts: Set[str], domain: str, execution_history: List[str] = None) -> str:
        """
        将用户目标和当前事实转换为PDDL Problem

        :param user_goal: 用户目标描述
        :param memory_facts: 当前的PDDL事实集合
        :param domain: 领域名称
        :param execution_history: 执行历史记录（动作名称列表），可选
        :return: PDDL Problem内容（字符串）
        """
        pass
