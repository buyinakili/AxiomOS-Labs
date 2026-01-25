"""进化管理器接口定义"""
from abc import ABC, abstractmethod
from typing import Dict
from interface.sandbox_manager import ISandboxManager
from interface.llm import ILLM


class IEvolutionManager(ABC):
    """进化管理器接口 - 负责在沙盒中进化新技能"""

    @abstractmethod
    def run_evolution_loop(
        self,
        user_goal: str,
        sandbox_manager: ISandboxManager,
        task_data: Dict,
        llm_client: ILLM
    ) -> Dict:
        """
        运行进化循环，尝试学习新技能

        :param user_goal: 用户目标描述
        :param sandbox_manager: 沙盒管理器实例
        :param task_data: 任务数据（包含setup_actions等）
        :param llm_client: LLM客户端
        :return: 进化结果字典
                 成功时包含: success=True, pddl_patch, python_code, skill_file_path, action_name
                 失败时包含: success=False, error
        """
        pass
