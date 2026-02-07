"""NervesLLM接口定义 - 原子动作分解"""
from abc import ABC, abstractmethod
from typing import List, Set, Optional


class INervesLLM(ABC):
    """NervesLLM接口 - 负责将单个任务分解为原子动作链"""

    @abstractmethod
    def decompose_action(
        self,
        task: str,
        current_facts: Set[str],
        domain: str,
        previous_failure_reason: Optional[str] = None
    ) -> List[str]:
        """
        将单个任务分解为PDDL格式的原子动作链

        :param task: PDDL格式任务，如 "(scan root)" 或 "(move file1 root backup)"
        :param current_facts: 当前环境事实集合
        :param domain: 领域名称（如 "file_management"）
        :param previous_failure_reason: 上一次失败的原因（用于重试）
        :return: PDDL格式原子动作链列表，如 ["(get_admin)", "(scan root)"]
        """
        pass

    @abstractmethod
    def extract_objects_from_facts(self, facts: Set[str], domain: str) -> Set[str]:
        """
        从环境事实中提取对象列表

        :param facts: 环境事实集合
        :param domain: 领域名称
        :return: 对象名称集合
        """
        pass