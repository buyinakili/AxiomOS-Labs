"""技能基类实现"""
import os
from abc import ABC, abstractmethod
from typing import List
from interface.skill import ISkill
from interface.executor import ExecutionResult


class BaseSkill(ISkill, ABC):
    """技能基类 - 提供通用功能"""

    def __init__(self, base_path: str = None):
        """
        初始化技能

        :param base_path: 基础路径（物理存储路径）
        """
        self.base_path = base_path or ""

    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass

    @abstractmethod
    def execute(self, args: List[str]) -> ExecutionResult:
        """
        执行技能

        :param args: 参数列表
        :return: ExecutionResult对象
        """
        pass

    def _safe_path(self, *parts) -> str:
        """
        安全地构建文件路径，自动处理 _dot_ 转义

        :param parts: 路径组件
        :return: 完整的绝对路径
        """
        # 处理文件名中的 _dot_ 转义
        converted_parts = []
        for part in parts:
            if "_dot_" in part:
                part = part.replace("_dot_", ".")
            converted_parts.append(part)

        # 构建绝对路径
        return os.path.abspath(os.path.join(self.base_path, *converted_parts))

    def _to_pddl_name(self, filename: str) -> str:
        """
        将文件名转换为PDDL兼容格式

        :param filename: 原始文件名
        :return: PDDL格式文件名
        """
        return filename.replace(".", "_dot_")

    def _from_pddl_name(self, pddl_name: str) -> str:
        """
        将PDDL格式文件名转换回原始文件名

        :param pddl_name: PDDL格式文件名
        :return: 原始文件名
        """
        return pddl_name.replace("_dot_", ".")
