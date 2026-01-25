"""PDDL修改器接口定义"""
from abc import ABC, abstractmethod


class IPDDLModifier(ABC):
    """PDDL修改器接口 - 负责修改PDDL Domain文件"""

    @abstractmethod
    def add_action(self, domain_path: str, action_pddl: str) -> bool:
        """
        将新的PDDL Action添加到Domain文件

        :param domain_path: Domain文件路径
        :param action_pddl: 要添加的Action PDDL代码
        :return: 是否成功
        """
        pass

    @abstractmethod
    def remove_action(self, domain_path: str, action_name: str) -> bool:
        """
        从Domain文件中删除指定的Action

        :param domain_path: Domain文件路径
        :param action_name: 要删除的Action名称
        :return: 是否成功
        """
        pass

    @abstractmethod
    def action_exists(self, domain_path: str, action_name: str) -> bool:
        """
        检查Action是否已存在

        :param domain_path: Domain文件路径
        :param action_name: Action名称
        :return: 是否存在
        """
        pass
