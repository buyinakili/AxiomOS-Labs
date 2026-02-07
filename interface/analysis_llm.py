"""AnalysisLLM接口定义 - 错误分析与修复建议"""
from abc import ABC, abstractmethod
from typing import List, Set, Optional


class IAnalysisLLM(ABC):
    """AnalysisLLM接口 - 负责分析错误并提供修复建议"""

    @abstractmethod
    def analyze_brain_failure(
        self,
        user_goal: str,
        current_facts: Optional[Set[str]],
        chain_of_mission: List[str],
        error_location: str,
        error_message: str
    ) -> str:
        """
        分析Brain层失败原因并提供修复建议

        :param user_goal: 用户目标描述
        :param current_facts: 当前环境事实集合（可选）
        :param chain_of_mission: 任务链
        :param error_location: 错误位置（如任务名称）
        :param error_message: 错误信息
        :return: 修复建议描述
        """
        pass

    @abstractmethod
    def analyze_nerves_failure(
        self,
        task: str,
        current_facts: Optional[Set[str]],
        chain_of_action: List[str],
        error_location: str,
        error_message: str
    ) -> str:
        """
        分析Nerves层失败原因并提供修复建议

        :param task: 当前任务
        :param current_facts: 当前环境事实集合（可选）
        :param chain_of_action: 动作链
        :param error_location: 错误位置（如动作名称）
        :param error_message: 错误信息
        :return: 修复建议描述
        """
        pass

    @abstractmethod
    def analyze_pddl_syntax_error(
        self,
        pddl_content: str,
        error_message: str,
        layer: str  # "brain" 或 "nerves"
    ) -> str:
        """
        分析PDDL语法错误并提供修复建议

        :param pddl_content: PDDL内容
        :param error_message: 错误信息
        :param layer: 错误发生的层
        :return: 修复建议描述
        """
        pass