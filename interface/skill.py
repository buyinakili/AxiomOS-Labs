"""技能接口定义"""
from abc import ABC, abstractmethod
from typing import List


class ISkill(ABC):
    """技能接口 - 所有技能必须实现此接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass

    @abstractmethod
    def execute(self, args: List[str]) -> 'ExecutionResult':
        """
        执行技能

        :param args: 参数列表
        :return: ExecutionResult对象
        """
        pass
