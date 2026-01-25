"""规划器接口定义"""
from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class PlanningResult:
    """规划结果数据类"""
    success: bool
    actions: List[Tuple[str, int]]  # [(action_str, step_num), ...]
    error: str = None


class IPlanner(ABC):
    """规划器接口 - 算法层只依赖这个接口"""

    @abstractmethod
    def plan(self, domain_content: str, problem_content: str) -> PlanningResult:
        """
        执行规划

        :param domain_content: Domain PDDL内容（字符串）
        :param problem_content: Problem PDDL内容（字符串）
        :return: PlanningResult对象
        """
        pass

    @abstractmethod
    def verify_syntax(self, domain_content: str) -> Tuple[bool, str]:
        """
        验证PDDL语法

        :param domain_content: Domain PDDL内容
        :return: (is_valid, error_message)
        """
        pass
