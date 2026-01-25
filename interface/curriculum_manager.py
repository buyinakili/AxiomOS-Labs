"""课程管理器接口定义"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from interface.executor import IExecutor


class ICurriculumManager(ABC):
    """课程管理器接口 - 负责生成训练任务"""

    @abstractmethod
    def propose_next_task(self, executor: IExecutor) -> Optional[Dict]:
        """
        根据当前系统能力提出下一个学习任务

        :param executor: 执行器实例（用于获取已有技能）
        :return: 任务数据字典，包含 task_name, goal, rationale, setup_actions
                 如果无法生成任务则返回None
        """
        pass

    @abstractmethod
    def propose_specific_task(self, task_goal: str, executor: IExecutor) -> Optional[Dict]:
        """
        根据用户指定的目标生成学习任务

        :param task_goal: 用户指定的任务目标（如"学习重命名文件"）
        :param executor: 执行器实例
        :return: 任务数据字典
        """
        pass
