"""沙盒管理器接口定义"""
from abc import ABC, abstractmethod


class ISandboxManager(ABC):
    """沙盒管理器接口 - 负责创建隔离的训练环境"""

    @abstractmethod
    def create_sandbox(self) -> str:
        """
        创建一个新的沙盒环境

        :return: 沙盒路径
        """
        pass

    @abstractmethod
    def reset_jail_storage(self):
        """
        重置沙盒的物理存储
        完全清空并重新镜像主系统的storage
        """
        pass

    @abstractmethod
    def get_pddl_path(self) -> str:
        """
        获取沙盒中的PDDL Domain文件路径

        :return: PDDL文件路径
        """
        pass

    @abstractmethod
    def get_storage_path(self) -> str:
        """
        获取沙盒的物理存储路径

        :return: 存储路径
        """
        pass

    @abstractmethod
    def get_sandbox_path(self) -> str:
        """
        获取当前沙盒的根路径

        :return: 沙盒根路径
        """
        pass

    @abstractmethod
    def clean_up(self):
        """清理沙盒（可选，调试时可能需要保留）"""
        pass
