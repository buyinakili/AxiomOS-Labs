"""执行器接口定义"""
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """执行结果数据类"""
    success: bool
    message: str
    add_facts: List[str] = None
    del_facts: List[str] = None

    def __post_init__(self):
        if self.add_facts is None:
            self.add_facts = []
        if self.del_facts is None:
            self.del_facts = []


class IExecutor(ABC):
    """执行器接口 - 负责执行规划的动作"""

    @abstractmethod
    def execute(self, action_str: str) -> ExecutionResult:
        """
        执行一个动作

        :param action_str: 动作字符串（如 "move file_a folder_x folder_y"）
        :return: ExecutionResult对象
        """
        pass

    @abstractmethod
    def get_execution_history(self) -> List[str]:
        """
        获取执行历史记录

        :return: 执行过的动作名称列表
        """
        pass

    @abstractmethod
    def clear_execution_history(self):
        """清空执行历史记录"""
        pass

    @abstractmethod
    def register_skill(self, skill: 'ISkill'):
        """
        注册一个技能

        :param skill: 技能实例
        """
        pass

    @abstractmethod
    def get_registered_skills(self) -> List[str]:
        """
        获取已注册的技能列表

        :return: 技能名称列表
        """
        pass
