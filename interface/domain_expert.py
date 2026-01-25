"""领域专家接口定义"""
from abc import ABC, abstractmethod
from typing import List


class IDomainExpert(ABC):
    """领域专家接口 - 提供特定领域的规则和知识"""

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """领域名称"""
        pass

    @abstractmethod
    def get_rules(self) -> List[str]:
        """
        获取领域规则列表

        :return: 规则描述列表
        """
        pass

    @abstractmethod
    def get_domain_file(self) -> str:
        """
        获取Domain PDDL文件名

        :return: 文件名（如 "domain.pddl"）
        """
        pass
