"""存储接口定义"""
from abc import ABC, abstractmethod


class IStorage(ABC):
    """存储接口 - 负责管理PDDL文件和物理存储"""

    @abstractmethod
    def read_domain(self, domain_name: str) -> str:
        """
        读取Domain PDDL内容

        :param domain_name: 领域名称
        :return: Domain PDDL内容（字符串）
        """
        pass

    @abstractmethod
    def write_domain(self, domain_name: str, content: str):
        """
        写入Domain PDDL内容

        :param domain_name: 领域名称
        :param content: Domain PDDL内容
        """
        pass

    @abstractmethod
    def read_problem(self) -> str:
        """
        读取Problem PDDL内容

        :return: Problem PDDL内容（字符串）
        """
        pass

    @abstractmethod
    def write_problem(self, content: str):
        """
        写入Problem PDDL内容

        :param content: Problem PDDL内容
        """
        pass

    @abstractmethod
    def get_storage_path(self) -> str:
        """
        获取物理存储路径

        :return: 存储路径
        """
        pass
