"""BrainLLM接口定义 - 高层任务分解"""
from abc import ABC, abstractmethod
from typing import List, Set, Optional


class IBrainLLM(ABC):
    """BrainLLM接口 - 负责将用户任务分解为高层任务链"""

    @abstractmethod
    def decompose_task(
        self,
        user_goal: str,
        current_facts: Set[str],
        available_actions: List[str],
        previous_failure_reason: Optional[str] = None
    ) -> List[str]:
        """
        将用户任务分解为PDDL格式的任务链

        :param user_goal: 用户目标描述
        :param current_facts: 当前环境事实集合
        :param available_actions: 可用动作列表（PDDL格式）
        :param previous_failure_reason: 上一次失败的原因（用于重试）
        :return: PDDL格式任务链列表，如 ["(scan root)", "(move file1 root backup)"]
        """
        pass

    @abstractmethod
    def get_available_actions(self, domain: str) -> List[str]:
        """
        获取指定领域可用的动作列表

        :param domain: 领域名称（如 "file_management"）
        :return: 可用动作列表
        """
        pass